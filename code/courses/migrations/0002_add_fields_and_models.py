"""
Migration 0002: Menambahkan model dan field baru untuk Lab 05

Perubahan dari 0001:
  + UserProfile  (model baru: role management)
  + Category     (model baru: self-referencing hierarchy)
  + Course.category  (FK ke Category)
  + CourseMember.enrolled_at  + unique_together
  + CourseContent.order + created_at
  + Progress     (model baru: tracking lesson completion)
  + Comment.created_at
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ------------------------------------------------------------------
        # 1. Category (self-referencing)
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name',        models.CharField(max_length=100, verbose_name='nama kategori')),
                ('description', models.TextField(blank=True, default='', verbose_name='deskripsi')),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('parent',      models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='children',
                    to='courses.category',
                    verbose_name='kategori induk',
                )),
            ],
            options={
                'verbose_name': 'Kategori',
                'verbose_name_plural': 'Kategori',
                'ordering': ['name'],
            },
        ),

        # ------------------------------------------------------------------
        # 2. UserProfile
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id',        models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role',      models.CharField(
                    choices=[('admin', 'Admin'), ('instructor', 'Instructor'), ('student', 'Student')],
                    db_index=True, default='student', max_length=10, verbose_name='peran',
                )),
                ('bio',       models.TextField(blank=True, default='', verbose_name='bio')),
                ('avatar',    models.ImageField(blank=True, null=True, upload_to='avatars/', verbose_name='avatar')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name='bergabung')),
                ('user',      models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='pengguna',
                )),
            ],
            options={
                'verbose_name': 'Profil Pengguna',
                'verbose_name_plural': 'Profil Pengguna',
            },
        ),

        # ------------------------------------------------------------------
        # 3. Course: tambah kolom category
        # ------------------------------------------------------------------
        migrations.AddField(
            model_name='course',
            name='category',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='courses',
                to='courses.category',
                verbose_name='kategori',
            ),
        ),

        # ------------------------------------------------------------------
        # 4. CourseMember: tambah enrolled_at + unique_together
        # ------------------------------------------------------------------
        migrations.AddField(
            model_name='coursemember',
            name='enrolled_at',
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name='tanggal daftar',
            ),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='coursemember',
            unique_together={('course_id', 'user_id')},
        ),

        # ------------------------------------------------------------------
        # 5. CourseContent: tambah order + created_at
        # ------------------------------------------------------------------
        migrations.AddField(
            model_name='coursecontent',
            name='order',
            field=models.PositiveIntegerField(db_index=True, default=0, verbose_name='urutan'),
        ),
        migrations.AddField(
            model_name='coursecontent',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name='dibuat',
            ),
            preserve_default=False,
        ),

        # ------------------------------------------------------------------
        # 6. Progress (model baru)
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name='Progress',
            fields=[
                ('id',           models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_completed', models.BooleanField(default=False, verbose_name='selesai')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='waktu selesai')),
                ('member_id',    models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='progress_set',
                    to='courses.coursemember',
                    verbose_name='anggota',
                )),
                ('content_id',   models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='courses.coursecontent',
                    verbose_name='konten',
                )),
            ],
            options={
                'verbose_name': 'Progress',
                'verbose_name_plural': 'Progress',
                'unique_together': {('member_id', 'content_id')},
            },
        ),

        # ------------------------------------------------------------------
        # 7. Comment: tambah created_at
        # ------------------------------------------------------------------
        migrations.AddField(
            model_name='comment',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name='dibuat',
            ),
            preserve_default=False,
        ),
    ]
