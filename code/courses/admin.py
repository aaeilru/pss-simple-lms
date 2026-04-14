"""
Django Admin Configuration - Simple LMS Lab 05

Deliverables:
- List display yang informatif
- Search dan filter functionality
- Inline models untuk Lesson (CourseContent)
"""

from django.contrib import admin
from django.db.models import Count
from .models import (
    UserProfile, Category,
    Course, CourseMember, CourseContent,
    Progress, Comment,
)


# =============================================================================
# User Profile
# =============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'role', 'get_email', 'joined_at')
    list_filter   = ('role',)
    search_fields = ('user__username', 'user__email', 'user__first_name')
    ordering      = ('user__username',)

    @admin.display(description='Email')
    def get_email(self, obj):
        return obj.user.email


# =============================================================================
# Category
# =============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'parent', 'course_count', 'created_at')
    list_filter   = ('parent',)
    search_fields = ('name', 'description')
    ordering      = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _course_count=Count('courses', distinct=True)
        )

    @admin.display(description='Jumlah Course', ordering='_course_count')
    def course_count(self, obj):
        return obj._course_count


# =============================================================================
# Inline: CourseContent (Lesson) di dalam Course
# =============================================================================

class LessonInline(admin.TabularInline):
    model   = CourseContent
    extra   = 1
    fields  = ('order', 'name', 'video_url', 'parent_id')
    ordering = ('order',)
    verbose_name        = 'Konten/Lesson'
    verbose_name_plural = 'Konten/Lesson'


# =============================================================================
# Course
# =============================================================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display  = ('name', 'teacher', 'category', 'price', 'enrollment_count', 'lesson_count', 'created_at')
    list_filter   = ('category', 'teacher', 'created_at')
    search_fields = ('name', 'description', 'teacher__username')
    ordering      = ('-created_at',)
    inlines       = [LessonInline]
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Informasi Utama', {
            'fields': ('name', 'description', 'image')
        }),
        ('Pengajar & Kategori', {
            'fields': ('teacher', 'category', 'price')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher', 'category').annotate(
            _enrollment_count=Count('coursemember', distinct=True),
            _lesson_count=Count('coursecontent', distinct=True),
        )

    @admin.display(description='Siswa', ordering='_enrollment_count')
    def enrollment_count(self, obj):
        return obj._enrollment_count

    @admin.display(description='Konten', ordering='_lesson_count')
    def lesson_count(self, obj):
        return obj._lesson_count


# =============================================================================
# Inline: Progress di dalam CourseMember
# =============================================================================

class ProgressInline(admin.TabularInline):
    model         = Progress
    extra         = 0
    fields        = ('content_id', 'is_completed', 'completed_at')
    readonly_fields = ('completed_at',)


# =============================================================================
# CourseMember (Enrollment)
# =============================================================================

@admin.register(CourseMember)
class CourseMemberAdmin(admin.ModelAdmin):
    list_display  = ('user_id', 'course_id', 'roles', 'progress_pct', 'enrolled_at')
    list_filter   = ('roles', 'course_id')
    search_fields = ('user_id__username', 'course_id__name')
    ordering      = ('-enrolled_at',)
    inlines       = [ProgressInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user_id', 'course_id').annotate(
            _total=Count('progress_set', distinct=True),
            _done=Count('progress_set', filter=models.Q(progress_set__is_completed=True), distinct=True),
        )

    @admin.display(description='Progress')
    def progress_pct(self, obj):
        if obj._total == 0:
            return '—'
        pct = int(obj._done / obj._total * 100)
        return f"{pct}% ({obj._done}/{obj._total})"


# need models.Q — import it
from django.db import models as django_models


# =============================================================================
# CourseContent (Lesson)
# =============================================================================

@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    list_display  = ('name', 'course_id', 'order', 'parent_id', 'created_at')
    list_filter   = ('course_id',)
    search_fields = ('name', 'description')
    ordering      = ('course_id', 'order')


# =============================================================================
# Progress
# =============================================================================

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display  = ('member_id', 'content_id', 'is_completed', 'completed_at')
    list_filter   = ('is_completed',)
    search_fields = ('member_id__user_id__username', 'content_id__name')
    ordering      = ('-completed_at',)


# =============================================================================
# Comment
# =============================================================================

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ('member_id', 'content_id', 'short_comment', 'created_at')
    list_filter   = ('content_id__course_id',)
    search_fields = ('member_id__user_id__username', 'comment')
    ordering      = ('-created_at',)

    @admin.display(description='Komentar')
    def short_comment(self, obj):
        return obj.comment[:60] + '…' if len(obj.comment) > 60 else obj.comment
