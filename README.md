
## Cara Setup

### 1. Rebuild Docker image

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 2. Jalankan migrations

```bash
# Migration dari starter (0001)
docker-compose exec app python manage.py migrate

# Atau jika sudah ada 0001, langsung migrate semua
docker-compose exec app python manage.py migrate courses
```

### 3. Load fixtures (data awal)

```bash
docker-compose exec app python manage.py loaddata fixtures/initial_data.json
```

### 4. Buat superuser untuk Django Admin

```bash
docker-compose exec app python manage.py createsuperuser
```

### 5. Seed data dummy (dari starter)

```bash
docker-compose exec app python manage.py seed_data
```

### 6. Jalankan Query Optimization Demo

```bash
docker-compose exec app python manage.py query_demo
```

### 7. Akses aplikasi

| URL | Keterangan |
|-----|-----------|
| http://localhost:8000/admin/ | Django Admin |
| http://localhost:8000/silk/  | Query Profiling Dashboard |

---

## Deliverables yang Dikerjakan

### ✅ Data Models

| Model | Keterangan |
|-------|-----------|
| `UserProfile` | Role management: admin, instructor, student (OneToOne dengan User) |
| `Category` | Self-referencing hierarchy (parent → children) |
| `Course` | Dengan instructor (ForeignKey User), category (ForeignKey Category) |
| `CourseMember` | Enrollment dengan `unique_together = ('course_id', 'user_id')` |
| `CourseContent` | Lesson dengan field `order` untuk pengurutan |
| `Progress` | Tracking lesson completion per anggota |
| `Comment` | Komentar pada konten |

### ✅ Custom Model Managers

```python
# Optimized untuk list view course
Course.objects.for_listing()
# → select_related('teacher', 'category')
# → annotate(enrollment_count, lesson_count)

# Optimized untuk student dashboard
CourseMember.objects.for_student_dashboard()
# → select_related('course_id', 'course_id__teacher', ...)
# → prefetch_related('progress_set')
```

### ✅ Django Admin

- `CourseAdmin`: inline LessonInline, annotate enrollment_count & lesson_count
- `CourseMemberAdmin`: inline ProgressInline, tampilkan persentase progress
- `CategoryAdmin`: tampilkan jumlah course per kategori
- Semua admin punya `search_fields`, `list_filter`, `ordering`

### ✅ Query Optimization Demo

```bash
python manage.py query_demo
```

Output menunjukkan:
- Jumlah query sebelum optimasi (N+1 problem)
- Jumlah query setelah optimasi
- Persentase penghematan query

### ✅ Migrations

- `0001_initial.py` — dari starter (Course, CourseMember, CourseContent, Comment)
- `0002_add_fields_and_models.py` — tambahan (UserProfile, Category, Progress, field baru)

### ✅ Fixtures

```bash
python manage.py loaddata fixtures/initial_data.json
```

Berisi: 6 Category, 3 User, 3 UserProfile, 2 Course, 4 CourseContent, 1 CourseMember
