from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render, redirect, get_object_or_404
from .forms import AcademicGroupForm, CourseForm, DepartmentForm
from .models import AcademicGroup, Course, Department, StudentProfile
from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from .models import Enrollment
from .serializers import CourseSerializer, EnrollmentSerializer
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .models import Book, BookLoan, LoanEvent
from .serializers import BookLoanSerializer, BookSerializer, LoanEventSerializer
from . import services

def is_methodist(user):
    return user.groups.filter(name='Методист').exists()


@login_required
def department_list(request):
    departments = Department.objects.all()
    return render(
        request,
        'department_list.html',
        {
            'departments': departments,
            'is_methodist': is_methodist(request.user),
        }
    )


@login_required
@user_passes_test(is_methodist)
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm()
        
    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Добавление факультета',
        }
    )


@login_required
@user_passes_test(is_methodist)
def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
        
    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Изменение факультета',
        }
    )


@login_required
def profile(request):
    return render(
        request,
        'profile.html',
        {
            'is_methodist': is_methodist(request.user),
        }
    )


@login_required
def course_list(request):
    courses = Course.objects.select_related('department').all()
    return render(
        request,
        'course_list.html',
        {
            'courses': courses,
            'is_methodist': is_methodist(request.user), 
        }
    )
    
@login_required
@user_passes_test(is_methodist)
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        department.delete()
        return redirect('department_list')
        
    return render(
        request,
        'object_confirm_delete.html',
        {
            'object': department,
            'title': 'Удаление факультета',
        }
    )

@login_required
def academic_group_list(request):
    groups = AcademicGroup.objects.all()
    return render(
        request,
        'group_list.html',
        {
            'groups': groups,
            'is_methodist': is_methodist(request.user),
        }
    )

@login_required
@user_passes_test(is_methodist)
def academic_group_create(request):
    if request.method == 'POST':
        form = AcademicGroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('academic_group_list')
    else:
        form = AcademicGroupForm()
        
    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Добавление группы',
        }
    )

@login_required
@user_passes_test(is_methodist)
def academic_group_update(request, pk):
    group = get_object_or_404(AcademicGroup, pk=pk)
    
    if request.method == 'POST':
        form = AcademicGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect('academic_group_list')
    else:
        form = AcademicGroupForm(instance=group)
        
    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Изменение группы',
        }
    )

@login_required
@user_passes_test(is_methodist)
def academic_group_delete(request, pk):
    group = get_object_or_404(AcademicGroup, pk=pk)
    
    if request.method == 'POST':
        group.delete()
        return redirect('academic_group_list')
        
    return render(
        request,
        'object_confirm_delete.html',
        {
            'object': group,
            'title': 'Удаление группы',
        }
    )
@login_required
@user_passes_test(is_methodist)
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = CourseForm()

    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Добавление курса',
        }
    )


@login_required
@user_passes_test(is_methodist)
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_list')
    else:
        form = CourseForm(instance=course)

    return render(
        request,
        'object_form.html',
        {
            'form': form,
            'title': 'Изменение курса',
        }
    )


@login_required
@user_passes_test(is_methodist)
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if request.method == 'POST':
        course.delete()
        return redirect('course_list')

    return render(
        request,
        'object_confirm_delete.html',
        {
            'object': course,
            'title': 'Удаление курса',
        }
    )

def chart(rows, label_field, value_field):
    return {
        'labels': [str(getattr(row, label_field)) for row in rows],
        'values': [getattr(row, value_field) for row in rows],
    }

@login_required
def dashboard_overview(request):
    departments = Department.objects.annotate(
        courses_n=Count('courses', distinct=True),
        students_n=Count('students', distinct=True),
    )
    return render(
        request, 'dashboards/overview.html',
        {
            'active': 'overview',
            'departments_count': Department.objects.count(),
            'courses_count': Course.objects.count(),
            'groups_count': AcademicGroup.objects.count(),
            'students_count': StudentProfile.objects.count(),
            'courses_chart': chart(departments, 'name', 'courses_n'),
            'students_chart': chart(departments, 'name', 'students_n'),
        }
    )

@login_required
def dashboard_courses(request):
    courses = Course.objects.all()
    department_id = request.GET.get('department')
    
    if department_id:
        courses = courses.filter(department_id=department_id)
        
    courses = courses.annotate(students_n=Count('students'))
    top_courses = courses.order_by('-students_n')[:5]
    without_description = courses.filter(description='').count()
    by_department = Department.objects.annotate(enrollments_n=Count('courses__students'))
    return render(
        request, 'dashboards/courses.html',
        {
            'active': 'courses',
            'departments': Department.objects.all(),
            'selected': department_id,
            'courses_count': courses.count(),
            'enrollments_count': sum(course.students_n for course in courses),
            'without_description': without_description,
            'top_chart': chart(top_courses, 'title', 'students_n'),
             'departments_chart': chart(by_department, 'name', 'enrollments_n'),
        }
    )

@login_required
def dashboard_students(request):
    students = StudentProfile.objects.all()
    groups = AcademicGroup.objects.all()
    department_id = request.GET.get('department')
    
    if department_id:
        students = students.filter(department_id=department_id)
        groups = groups.filter(department_id=department_id)
        
    groups = groups.annotate(students_n=Count('students'))

    months = (
        User.objects.filter(student_profile__in=students)
        .annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(n=Count('id'))
        .order_by('month')
    )
    
    return render(
        request, 'dashboards/students.html',
        {
            'active': 'students',
            'departments': Department.objects.all(),
            'selected': department_id,
            'students_count': students.count(),
            'groups_count': groups.count(),
            'no_group_count': students.filter(academic_group=None).count(),
            'groups_chart': chart(groups, 'name', 'students_n'),
            'months_chart': {
                'labels': [row['month'].strftime('%m.%Y') for row in months],
                'values': [row['n'] for row in months],
            },
        }
    )

@login_required
@ensure_csrf_cookie
def api_dashboard(request):
    return render(
        request,
        "accounts/dashboard.html",
        {"is_methodist": is_methodist(request.user)},
    )
class IsMethodologist(BasePermission):
    def has_permission(self, request, view):
        return request.user and is_methodist(request.user)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsMethodologist()]
        return [IsAuthenticated()]


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if is_methodist(self.request.user):
            return Enrollment.objects.all().select_related("course", "student")
        return Enrollment.objects.filter(student=self.request.user).select_related("course")
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsMethodologist()]
        if self.action == 'destroy':
            return [IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

@login_required
@ensure_csrf_cookie
def library_page(request):
    return render(
        request,
        "accounts/library.html",
        {"is_methodist": is_methodist(request.user)},
    )


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.select_related("course").all()
    serializer_class = BookSerializer


class BookLoanViewSet(viewsets.ModelViewSet):
    serializer_class = BookLoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        loans = BookLoan.objects.select_related("book__course", "reader")
        if not is_methodist(self.request.user):
            loans = loans.filter(reader=self.request.user)

        if self.action == "list":
            status = self.request.query_params.get("status")
            course = self.request.query_params.get("course")
            if status:
                if status not in BookLoan.Status.values:
                    raise ValidationError({"status": "Неизвестный статус в фильтре."})
                loans = loans.filter(status=status)
            if course:
                if not course.isdigit():
                    raise ValidationError({"course": "Параметр course должен быть числом."})
                loans = loans.filter(book__course_id=course)
        return loans

    @transaction.atomic
    def perform_create(self, serializer):
        loan = serializer.save(reader=self.request.user)
        services.log_event(loan, self.request.user, LoanEvent.Action.CREATED)

    @transaction.atomic
    def perform_update(self, serializer):
        loan = serializer.instance
        if loan.reader != self.request.user:
            raise PermissionDenied()
        if loan.status != BookLoan.Status.REQUESTED:
            raise ValidationError({"status": "Изменять можно только заявку в статусе «Заявка создана»."})
        loan = serializer.save()
        services.log_event(loan, self.request.user, LoanEvent.Action.UPDATED, loan.status)

    def perform_destroy(self, instance):
        if instance.status not in (BookLoan.Status.REQUESTED, BookLoan.Status.CANCELLED):
            raise ValidationError({"status": "Удалить можно только новую или отменённую заявку."})
        instance.delete()

    def _change_status(self, action_name):
        loan = self.get_object()
        loan = services.change_loan_status(loan.pk, action_name, self.request.user)
        return Response(BookLoanSerializer(loan, context={"request": self.request}).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsMethodologist])
    def issue(self, request, pk=None):
        return self._change_status("issue")

    @action(detail=True, methods=["post"], url_path="return",
            permission_classes=[IsAuthenticated, IsMethodologist])
    def return_book(self, request, pk=None):
        return self._change_status("return")

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._change_status("cancel")

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        loan = self.get_object()
        events = loan.events.select_related("actor")
        return Response(LoanEventSerializer(events, many=True).data)
