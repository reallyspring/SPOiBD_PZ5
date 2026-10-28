from django.contrib.auth.models import User
from django.db import models
from django.conf import settings


class Department(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    max_students = models.PositiveIntegerField(default=30, verbose_name="Макс. количество студентов")
    def __str__(self):
        return self.title

class Enrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'на рассмотрении'
        APPROVED = 'approved', 'зачислен'
        REJECTED = 'rejected', 'отклонено'
        
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name='groups'
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Студент"
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.username} -> {self.course.title}"



class AcademicGroup(models.Model):
    name = models.CharField(max_length=50)
    department = models.ForeignKey(
    Department,
    on_delete=models.CASCADE,
    related_name='groups'
    )
    def __str__(self):
        return self.name

class StudentProfile(models.Model):
    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name='student_profile'
    )
    department = models.ForeignKey(
    Department,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='students'
    )
    academic_group = models.ForeignKey(
    AcademicGroup,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='students'
    )
    courses = models.ManyToManyField(
    Course,
    blank=True,
    related_name='students'
    )
    def __str__(self):
        return self.user.username

class Book(models.Model):
    title = models.CharField("Название", max_length=200)
    author = models.CharField("Автор", max_length=200, blank=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="books",
        verbose_name="Курс",
    )
    total_copies = models.PositiveIntegerField("Всего экземпляров", default=1)
    available_copies = models.PositiveIntegerField("Свободно экземпляров", default=1)

    def __str__(self):
        return self.title


class BookLoan(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Заявка создана"
        ISSUED = "issued", "Выдан"
        RETURNED = "returned", "Возвращён"
        CANCELLED = "cancelled", "Отменена"

    book = models.ForeignKey(
        Book,
        on_delete=models.PROTECT,
        related_name="loans",
        verbose_name="Учебник",
    )
    reader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="book_loans",
        verbose_name="Читатель",
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
    )
    comment = models.CharField("Комментарий", max_length=255, blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reader.username} -> {self.book.title}"


class LoanEvent(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Заявка создана"
        UPDATED = "updated", "Заявка изменена"
        ISSUED = "issued", "Учебник выдан"
        RETURNED = "returned", "Учебник возвращён"
        CANCELLED = "cancelled", "Заявка отменена"

    loan = models.ForeignKey(
        BookLoan,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Заявка",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Инициатор",
    )
    action = models.CharField("Событие", max_length=20, choices=Action.choices)
    old_status = models.CharField("Старый статус", max_length=20, blank=True)
    new_status = models.CharField("Новый статус", max_length=20)
    created_at = models.DateTimeField("Время", auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.loan_id}: {self.action}"


