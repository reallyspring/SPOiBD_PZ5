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