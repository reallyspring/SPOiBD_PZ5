from rest_framework import serializers
from .models import Course, Enrollment


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
