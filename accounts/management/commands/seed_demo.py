import random
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import AcademicGroup, Course, Department, StudentProfile

DATA = {
    'Институт №3': (['М3О-237Б', 'М3О-238Б'], ['Базы данных', 'Веб-разработка', 'Теория инноваций']),
    'Институт №8': (['М8О-201Б', 'М8О-202Б'], ['Алгоритмы', 'Машинное обучение']),
    'Институт №6': (['М6О-210Б'], ['Аэродинамика', 'Механика полёта']),
}

class Command(BaseCommand):
    help = 'Наполняет базу тестовыми данными для дашбордов'

    def handle(self, *args, **options):
        number = User.objects.count()
        for department_name, (group_names, course_titles) in DATA.items():
            department = Department.objects.create(name=department_name)
            courses = [
                Course.objects.create(title=title, department=department)
                for title in course_titles
            ]
            for group_name in group_names:
                group = AcademicGroup.objects.create(name=group_name, department=department)
                for _ in range(random.randint(4, 9)):
                    number += 1
                    user = User.objects.create_user(f'student{number}', password='student12345')
                    user.date_joined = timezone.now() - timedelta(days=random.randint(0, 180))
                    user.save()
                    
                    student = StudentProfile.objects.create(
                        user=user,
                        department=department,
                        academic_group=group
                    )
                    student.courses.set(random.sample(courses, random.randint(1, len(courses))))
                    
        self.stdout.write('Готово')