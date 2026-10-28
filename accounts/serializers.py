from rest_framework import serializers
from .models import Course, Enrollment, LoanEvent, Book, BookLoan


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "title", "description", "department", "max_students")


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(
        source="course.title",
        read_only=True
    )
    
    student_name = serializers.CharField(
        source="student.username",
        read_only=True
    )

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "course",
            "course_title",
            "student",
            "student_name",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "created_at", "student")

    def validate(self, attrs):
        if self.instance is None:
            student = self.context['request'].user
            course = attrs.get('course')
            if Enrollment.objects.filter(student=student, course=course).exists():
                raise serializers.ValidationError({"course": "Вы уже подали заявку на этот курс."})
            if attrs.get("status", Enrollment.Status.PENDING) != Enrollment.Status.PENDING:
                raise serializers.ValidationError({"status": "Новая заявка должна иметь статус «на рассмотрении»."})
        return attrs

    def validate_status(self, value):
        if self.instance:
            old_status = self.instance.status
            allowed_transitions = {
                Enrollment.Status.PENDING: [Enrollment.Status.APPROVED, Enrollment.Status.REJECTED],
                Enrollment.Status.APPROVED: [],
                Enrollment.Status.REJECTED: [],
            }
            if value != old_status and value not in allowed_transitions.get(old_status, []):
                raise serializers.ValidationError("Недопустимый переход статуса.")
            
            if value == Enrollment.Status.APPROVED and old_status != Enrollment.Status.APPROVED:
                course = self.instance.course
                approved_count = Enrollment.objects.filter(
                    course=course, status=Enrollment.Status.APPROVED
                ).count()
                if approved_count >= course.max_students:
                    raise serializers.ValidationError("На курсе не осталось свободных мест.")
        return value

class BookSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Book
        fields = ("id", "title", "author", "course", "course_title",
                  "total_copies", "available_copies")


class BookLoanSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    course_title = serializers.CharField(source="book.course.title", read_only=True)
    reader_name = serializers.CharField(source="reader.username", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = BookLoan
        fields = ("id", "book", "book_title", "course_title", "reader", "reader_name",
                  "status", "status_display", "comment", "created_at")
        read_only_fields = ("id", "reader", "status", "created_at")

    def validate(self, attrs):
        if "status" in self.initial_data:
            raise serializers.ValidationError(
                {"status": "Статус меняется только действиями issue, return и cancel."}
            )
        return attrs

    def validate_book(self, book):
        user = self.context["request"].user
        active = BookLoan.objects.filter(
            reader=user,
            book=book,
            status__in=[BookLoan.Status.REQUESTED, BookLoan.Status.ISSUED],
        )
        if self.instance:
            active = active.exclude(pk=self.instance.pk)
        if active.exists():
            raise serializers.ValidationError("У вас уже есть активная заявка на этот учебник.")
        return book


class LoanEventSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source="get_action_display", read_only=True)
    actor_name = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = LoanEvent
        fields = ("id", "action", "action_display", "old_status", "new_status", "actor_name", "created_at")
