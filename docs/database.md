# База данных

Все модели находятся в `accounts/models.py`. Пользователи и группы — стандартные модели Django `auth.User` и `auth.Group`; роль методиста — это группа с названием «Методист».

## Схема моделей

```mermaid
erDiagram
    Department ||--o{ Course : "courses"
    Department ||--o{ AcademicGroup : "groups"
    Department |o--o{ StudentProfile : "students"
    AcademicGroup |o--o{ StudentProfile : "students"
    User ||--o| StudentProfile : "student_profile"
    StudentProfile }o--o{ Course : "courses"
    Course ||--o{ Enrollment : "заявки на курс"
    User ||--o{ Enrollment : "enrollments"
    Course ||--o{ Book : "books"
    Book ||--o{ BookLoan : "loans"
    User ||--o{ BookLoan : "book_loans"
    BookLoan ||--o{ LoanEvent : "events"
    User |o--o{ LoanEvent : "инициатор"

    Course {
        int id PK
        string title
        text description
        int department_id FK
        int max_students
    }
    Enrollment {
        int id PK
        int course_id FK
        int student_id FK
        string status
        datetime created_at
    }
    Book {
        int id PK
        string title
        string author
        int course_id FK
        int total_copies
        int available_copies
    }
    BookLoan {
        int id PK
        int book_id FK
        int reader_id FK
        string status
        string comment
        datetime created_at
    }
    LoanEvent {
        int id PK
        int loan_id FK
        int actor_id FK
        string action
        string old_status
        string new_status
        datetime created_at
    }
```

## Сущности

| Модель | Назначение | Ключевые поля | Связи и удаление |
|---|---|---|---|
| `Department` | факультет (институт) | `name` | — |
| `Course` | учебный курс | `title`, `description`, `max_students` — число мест | `department` → Department, CASCADE |
| `AcademicGroup` | учебная группа | `name` | `department` → Department, CASCADE |
| `StudentProfile` | профиль студента | — | `user` → User (один к одному), CASCADE; `department`, `academic_group` — SET_NULL; `courses` — многие ко многим с Course |
| `Enrollment` | заявка на запись на курс | `status`: `pending` / `approved` / `rejected`; `created_at` | `course` → Course, PROTECT (курс с заявками не удаляется); `student` → User, CASCADE |
| `Book` | учебник по курсу | `total_copies` — всего экземпляров, `available_copies` — свободно сейчас | `course` → Course, PROTECT |
| `BookLoan` | заявка на выдачу учебника (основная сущность СРС №7) | `status`: `requested` / `issued` / `returned` / `cancelled`; `comment`; `created_at` | `book` → Book, PROTECT; `reader` → User (владелец), CASCADE |
| `LoanEvent` | событие истории заявки | `action`: `created` / `updated` / `issued` / `returned` / `cancelled`; `old_status`, `new_status`, `created_at` | `loan` → BookLoan, CASCADE; `actor` → User (инициатор), SET_NULL |

## Ограничения целостности

- Поля `max_students`, `total_copies`, `available_copies` имеют тип `PositiveIntegerField`: база данных не примет отрицательное значение.
- `PROTECT` у `Enrollment.course`, `Book.course` и `BookLoan.book` не даёт удалить курс или учебник, на которые есть заявки.
- Изменение статуса заявки на учебник и числа свободных экземпляров выполняется в одной транзакции (`accounts/services.py`), поэтому эти данные не расходятся.
- Записи `LoanEvent` создаются только сервером, через API их нельзя изменить или удалить.

## Миграции

| Миграция | Что добавляет |
|---|---|
| `0001_initial` | Department, Course, StudentProfile |
| `0002_course_description` | поле описания курса |
| `0003_academicgroup_studentprofile_academic_group` | учебные группы |
| `0004_course_max_students_enrollment` | число мест на курсе и заявки на курсы (ПЗ №7) |
| `0005_book_bookloan_loanevent` | учебники, заявки на выдачу, история (СРС №7) |

Команда `python manage.py showmigrations accounts` показывает, какие миграции применены к текущей базе. Локальная SQLite (`db.sqlite3`) и PostgreSQL на Render — разные базы: миграции и тестовые данные применяются к каждой отдельно.
