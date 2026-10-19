from django.contrib import admin
from .models import (
 AcademicGroup,
 Course,
 Department,
 Enrollment,
 StudentProfile,
)
@admin.register(AcademicGroup)
class AcademicGroupAdmin(admin.ModelAdmin):
    list_display = (
    'id',
    'name',
    'department',
    )
    list_filter = (
    'department',
    )
    search_fields = (
    'name',
    )

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'department')
    list_filter = ('department',)
    search_fields = ('title',)
    
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "course", "status", "created_at")
    list_filter = ("status", "course")
    search_fields = ("student__username",)
    readonly_fields = ("created_at",)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'department')
    list_filter = ('department',)
    search_fields = ('user__username',)
    filter_horizontal = ('courses',)
    