from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from accounts.models import Book, Course


class Command(BaseCommand):
    help = "Создаёт группу «Методист» и по одному учебнику для каждого курса"

    def handle(self, *args, **options):
        Group.objects.get_or_create(name="Методист")
        for course in Course.objects.all():
            Book.objects.get_or_create(
                title=f"Учебник по курсу «{course.title}»",
                course=course,
                defaults={"total_copies": 2, "available_copies": 2},
            )
        self.stdout.write(f"Готово, учебников в базе: {Book.objects.count()}")
