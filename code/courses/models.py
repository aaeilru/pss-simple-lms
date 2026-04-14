"""
Models untuk Simple LMS - Lab 05: Django ORM & Models

Deliverables:
- UserProfile  : role management (admin, instructor, student)
- Category     : self-referencing hierarchy
- Course       : dengan instructor, category, custom manager
- CourseMember : Enrollment dengan unique constraint
- CourseContent: Lesson dengan ordering
- Progress     : tracking lesson completion
- Comment      : komentar pada konten

Custom Managers:
- Course.objects.for_listing()             → optimized untuk list view
- CourseMember.objects.for_student_dashboard() → dengan progress
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# =============================================================================
# Custom QuerySets & Managers
# =============================================================================

class CourseQuerySet(models.QuerySet):
    def for_listing(self):
        """
        Optimized queryset untuk list view course.
        Menghindari N+1 problem dengan select_related + annotate.

        Tanpa ini: 1 query untuk courses + N query untuk teacher + N untuk category
        Dengan ini: 1 query untuk semua data
        """
        return (
            self
            .select_related('teacher', 'category')
            .annotate(
                enrollment_count=models.Count('coursemember', distinct=True),
                lesson_count=models.Count('coursecontent', distinct=True),
            )
        )


class EnrollmentQuerySet(models.QuerySet):
    def for_student_dashboard(self):
        """
        Optimized queryset untuk dashboard mahasiswa.
        Menggunakan prefetch_related untuk Progress agar tidak N+1.
        """
        return (
            self
            .select_related('course_id', 'course_id__teacher', 'course_id__category', 'user_id')
            .prefetch_related(
                models.Prefetch(
                    'progress_set',
                    queryset=Progress.objects.select_related('content_id'),
                )
            )
        )


# =============================================================================
# User Profile (role: admin, instructor, student)
# =============================================================================

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin',      'Admin'),
        ('instructor', 'Instructor'),
        ('student',    'Student'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='pengguna',
    )
    role = models.CharField(
        'peran',
        max_length=10,
        choices=ROLE_CHOICES,
        default='student',
        db_index=True,
    )
    bio       = models.TextField('bio', blank=True, default='')
    avatar    = models.ImageField('avatar', upload_to='avatars/', null=True, blank=True)
    joined_at = models.DateTimeField('bergabung', auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    class Meta:
        verbose_name        = 'Profil Pengguna'
        verbose_name_plural = 'Profil Pengguna'


# =============================================================================
# Category (self-referencing hierarchy)
# =============================================================================

class Category(models.Model):
    name        = models.CharField('nama kategori', max_length=100)
    description = models.TextField('deskripsi', blank=True, default='')
    parent      = models.ForeignKey(
        'self',
        verbose_name='kategori induk',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    def get_ancestors(self):
        """Kembalikan list dari root sampai parent langsung."""
        ancestors = []
        current = self.parent
        while current is not None:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    class Meta:
        verbose_name        = 'Kategori'
        verbose_name_plural = 'Kategori'
        ordering            = ['name']


# =============================================================================
# Course (dengan instructor, category, custom manager)
# =============================================================================

class Course(models.Model):
    objects = CourseQuerySet.as_manager()   # ← custom manager

    name        = models.CharField('nama matkul', max_length=100)
    description = models.TextField('deskripsi', default='-')
    price       = models.IntegerField('harga', default=10000)
    image       = models.ImageField('gambar', null=True, blank=True)
    teacher     = models.ForeignKey(
        User,
        verbose_name='pengajar',
        on_delete=models.RESTRICT,
        related_name='courses_taught',
    )
    category = models.ForeignKey(
        Category,
        verbose_name='kategori',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name        = 'Mata Kuliah'
        verbose_name_plural = 'Mata Kuliah'
        ordering            = ['-created_at']


# =============================================================================
# CourseMember / Enrollment (dengan unique constraint)
# =============================================================================

ROLE_OPTIONS = [
    ('std', 'Siswa'),
    ('ast', 'Asisten'),
]


class CourseMember(models.Model):
    objects = EnrollmentQuerySet.as_manager()   # ← custom manager

    course_id   = models.ForeignKey(Course, verbose_name='matkul', on_delete=models.RESTRICT)
    user_id     = models.ForeignKey(User,   verbose_name='siswa',  on_delete=models.RESTRICT)
    roles       = models.CharField('peran', max_length=3, choices=ROLE_OPTIONS, default='std')
    enrolled_at = models.DateTimeField('tanggal daftar', auto_now_add=True)

    def __str__(self):
        return f"{self.user_id} - {self.course_id} ({self.roles})"

    class Meta:
        verbose_name        = 'Anggota Kelas'
        verbose_name_plural = 'Anggota Kelas'
        unique_together     = ('course_id', 'user_id')   # ← unique constraint


# =============================================================================
# CourseContent / Lesson (dengan ordering)
# =============================================================================

class CourseContent(models.Model):
    name            = models.CharField('judul konten', max_length=200)
    description     = models.TextField('deskripsi', default='-')
    video_url       = models.CharField('URL Video', max_length=200, null=True, blank=True)
    file_attachment = models.FileField('File', null=True, blank=True)
    course_id       = models.ForeignKey(Course, verbose_name='matkul', on_delete=models.RESTRICT)
    parent_id       = models.ForeignKey(
        'self',
        verbose_name='induk',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
    )
    order      = models.PositiveIntegerField('urutan', default=0, db_index=True)  # ← ordering
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name        = 'Konten Kelas'
        verbose_name_plural = 'Konten Kelas'
        ordering            = ['order']


# =============================================================================
# Progress (tracking lesson completion)
# =============================================================================

class Progress(models.Model):
    member_id  = models.ForeignKey(
        CourseMember,
        verbose_name='anggota',
        on_delete=models.CASCADE,
        related_name='progress_set',
    )
    content_id = models.ForeignKey(
        CourseContent,
        verbose_name='konten',
        on_delete=models.CASCADE,
    )
    is_completed = models.BooleanField('selesai', default=False)
    completed_at = models.DateTimeField('waktu selesai', null=True, blank=True)

    def mark_complete(self):
        """Tandai lesson ini sebagai selesai."""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save(update_fields=['is_completed', 'completed_at'])

    def __str__(self):
        status = '✓' if self.is_completed else '✗'
        return f"{status} {self.member_id.user_id.username} – {self.content_id.name}"

    class Meta:
        verbose_name        = 'Progress'
        verbose_name_plural = 'Progress'
        unique_together     = ('member_id', 'content_id')


# =============================================================================
# Comment
# =============================================================================

class Comment(models.Model):
    content_id = models.ForeignKey(CourseContent, verbose_name='konten',   on_delete=models.CASCADE)
    member_id  = models.ForeignKey(CourseMember,  verbose_name='pengguna', on_delete=models.CASCADE)
    comment    = models.TextField('komentar')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Komentar oleh {self.member_id} pada {self.content_id}"

    class Meta:
        verbose_name        = 'Komentar'
        verbose_name_plural = 'Komentar'
        ordering            = ['-created_at']
