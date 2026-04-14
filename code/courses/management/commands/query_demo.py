"""
Management Command: Demo Query Optimization

Menunjukkan:
  1. N+1 problem — banyak query tidak efisien
  2. Optimized queries — menggunakan select_related & prefetch_related
  3. Perbandingan query count

Jalankan dengan:
    python manage.py query_demo
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries

from courses.models import Course, CourseMember


def get_query_count():
    return len(connection.queries)


class Command(BaseCommand):
    help = 'Demo N+1 problem vs optimized queries dengan perbandingan query count'

    def handle(self, *args, **options):
        # Aktifkan query logging
        settings.DEBUG = True

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('  Demo Query Optimization — Simple LMS')
        self.stdout.write('=' * 60)

        self._demo_course_list()
        self._demo_enrollment_dashboard()
        self._print_conclusion()

    # -------------------------------------------------------------------------
    # Demo 1: Course List
    # -------------------------------------------------------------------------
    def _demo_course_list(self):
        self.stdout.write('\n📋  DEMO 1: Course List View')
        self.stdout.write('-' * 60)

        # --- N+1 Problem ---
        self.stdout.write('\n[❌] N+1 Problem (tanpa optimasi):')
        reset_queries()

        courses = Course.objects.all()[:10]
        output = []
        for course in courses:
            # Setiap akses .teacher dan .category memicu query terpisah!
            teacher_name = course.teacher.get_full_name() or course.teacher.username
            category_name = course.category.name if course.category else '-'
            output.append(f"  - {course.name} | {teacher_name} | {category_name}")

        n1_count = get_query_count()
        self.stdout.write(f'  Query dijalankan: {n1_count}')
        self.stdout.write(f'  (1 query courses + {n1_count - 1} query teacher/category)')

        # --- Optimized ---
        self.stdout.write('\n[✅] Optimized (dengan select_related + annotate):')
        reset_queries()

        courses = Course.objects.for_listing()[:10]
        output = []
        for course in courses:
            teacher_name = course.teacher.get_full_name() or course.teacher.username
            category_name = course.category.name if course.category else '-'
            output.append(
                f"  - {course.name} | {teacher_name} | {category_name} "
                f"| {course.enrollment_count} siswa | {course.lesson_count} lesson"
            )

        opt_count = get_query_count()
        self.stdout.write(f'  Query dijalankan: {opt_count}')

        self._print_comparison(n1_count, opt_count)

    # -------------------------------------------------------------------------
    # Demo 2: Student Dashboard
    # -------------------------------------------------------------------------
    def _demo_enrollment_dashboard(self):
        self.stdout.write('\n\n📊  DEMO 2: Student Dashboard (Enrollment + Progress)')
        self.stdout.write('-' * 60)

        # --- N+1 Problem ---
        self.stdout.write('\n[❌] N+1 Problem (tanpa optimasi):')
        reset_queries()

        enrollments = CourseMember.objects.all()[:10]
        for enrollment in enrollments:
            # Akses course, teacher, dan progress masing-masing memicu query!
            course_name   = enrollment.course_id.name
            teacher_name  = enrollment.course_id.teacher.username
            progress_list = enrollment.progress_set.filter(is_completed=True).count()

        n1_count = get_query_count()
        self.stdout.write(f'  Query dijalankan: {n1_count}')

        # --- Optimized ---
        self.stdout.write('\n[✅] Optimized (dengan select_related + prefetch_related):')
        reset_queries()

        enrollments = CourseMember.objects.for_student_dashboard()[:10]
        for enrollment in enrollments:
            course_name   = enrollment.course_id.name
            teacher_name  = enrollment.course_id.teacher.username
            # progress sudah di-prefetch, tidak ada query tambahan
            progress_list = [p for p in enrollment.progress_set.all() if p.is_completed]

        opt_count = get_query_count()
        self.stdout.write(f'  Query dijalankan: {opt_count}')

        self._print_comparison(n1_count, opt_count)

    # -------------------------------------------------------------------------
    # Helper: Cetak Perbandingan
    # -------------------------------------------------------------------------
    def _print_comparison(self, n1_count, opt_count):
        saved = n1_count - opt_count
        if n1_count > 0:
            reduction_pct = int(saved / n1_count * 100)
        else:
            reduction_pct = 0

        self.stdout.write(f'\n  📊 Perbandingan:')
        self.stdout.write(f'     Sebelum : {n1_count:>3} queries')
        self.stdout.write(f'     Sesudah : {opt_count:>3} queries')
        self.stdout.write(
            self.style.SUCCESS(f'     Hemat   : {saved:>3} queries ({reduction_pct}% lebih efisien)')
        )

    def _print_conclusion(self):
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('  Kesimpulan:'))
        self.stdout.write('  - select_related  → JOIN untuk ForeignKey & OneToOne')
        self.stdout.write('  - prefetch_related → query terpisah tapi hanya 1x')
        self.stdout.write('  - annotate         → hitung COUNT di sisi database')
        self.stdout.write('  Gunakan Course.objects.for_listing() untuk list view')
        self.stdout.write('  Gunakan CourseMember.objects.for_student_dashboard()')
        self.stdout.write('=' * 60 + '\n')
