from unittest.mock import patch
from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Book, BookLoan, Course, Department, LoanEvent


class LibraryProcessTests(TestCase):
    def setUp(self):
        department = Department.objects.create(name="Институт №3")
        self.course = Course.objects.create(title="Базы данных", department=department)
        other_course = Course.objects.create(title="Алгоритмы", department=department)
        self.book = Book.objects.create(title="Учебник БД", course=self.course,
                                        total_copies=1, available_copies=1)
        self.other_book = Book.objects.create(title="Учебник алгоритмов", course=other_course,
                                              total_copies=1, available_copies=1)

        self.student = User.objects.create_user("student", password="pass12345")
        self.roman = User.objects.create_user("roman", password="pass12345")
        self.methodist = User.objects.create_user("methodist", password="pass12345")
        self.methodist.groups.add(Group.objects.create(name="Методист"))

        self.client = APIClient()
        self.client.force_authenticate(self.student)

    def create_loan(self, book=None):
        response = self.client.post("/api/loans/", {"book": (book or self.book).id}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return BookLoan.objects.get(pk=response.data["id"])

    def as_methodist(self):
        client = APIClient()
        client.force_authenticate(self.methodist)
        return client

    def test_create_adds_loan_and_event(self):
        loan = self.create_loan()
        self.assertEqual(loan.status, BookLoan.Status.REQUESTED)
        self.assertEqual(loan.reader, self.student)
        self.assertEqual(list(loan.events.values_list("action", flat=True)), ["created"])

    def test_issue_changes_status_stock_and_history(self):
        loan = self.create_loan()
        response = self.as_methodist().post(f"/api/loans/{loan.id}/issue/")
        self.assertEqual(response.status_code, 200)
        loan.refresh_from_db()
        self.book.refresh_from_db()
        self.assertEqual(loan.status, BookLoan.Status.ISSUED)
        self.assertEqual(self.book.available_copies, 0)
        self.assertEqual(loan.events.count(), 2)

    def test_forbidden_transition_changes_nothing(self):
        loan = self.create_loan()
        methodist = self.as_methodist()
        methodist.post(f"/api/loans/{loan.id}/issue/")
        methodist.post(f"/api/loans/{loan.id}/return/")
        response = methodist.post(f"/api/loans/{loan.id}/issue/")
        self.assertEqual(response.status_code, 400)
        loan.refresh_from_db()
        self.book.refresh_from_db()
        self.assertEqual(loan.status, BookLoan.Status.RETURNED)
        self.assertEqual(self.book.available_copies, 1)
        self.assertEqual(loan.events.count(), 3)

    def test_status_cannot_be_changed_by_patch(self):
        loan = self.create_loan()
        response = self.as_methodist().patch(f"/api/loans/{loan.id}/", {"status": "issued"}, format="json")
        self.assertEqual(response.status_code, 400)
        loan.refresh_from_db()
        self.assertEqual(loan.status, BookLoan.Status.REQUESTED)

    def test_failure_rolls_back_whole_operation(self):
        loan = self.create_loan()
        client = self.as_methodist()
        client.raise_request_exception = False
        with patch.object(LoanEvent.objects, "create", side_effect=RuntimeError("сбой записи истории")):
            response = client.post(f"/api/loans/{loan.id}/issue/")
        self.assertEqual(response.status_code, 500)
        loan.refresh_from_db()
        self.book.refresh_from_db()
        self.assertEqual(loan.status, BookLoan.Status.REQUESTED)
        self.assertEqual(self.book.available_copies, 1)
        self.assertEqual(loan.events.count(), 1)

    def test_other_user_cannot_access_loan(self):
        loan = self.create_loan()
        roman = APIClient()
        roman.force_authenticate(self.roman)
        self.assertEqual(roman.get(f"/api/loans/{loan.id}/").status_code, 404)
        self.assertEqual(roman.patch(f"/api/loans/{loan.id}/", {"comment": "x"}, format="json").status_code, 404)
        self.assertEqual(roman.delete(f"/api/loans/{loan.id}/").status_code, 404)
        self.assertEqual(roman.get("/api/loans/").data, [])

    def test_student_cannot_issue(self):
        loan = self.create_loan()
        self.assertEqual(self.client.post(f"/api/loans/{loan.id}/issue/").status_code, 403)

    def test_no_free_copies(self):
        first = self.create_loan()
        self.as_methodist().post(f"/api/loans/{first.id}/issue/")
        roman = APIClient()
        roman.force_authenticate(self.roman)
        second_id = roman.post("/api/loans/", {"book": self.book.id}, format="json").data["id"]
        response = self.as_methodist().post(f"/api/loans/{second_id}/issue/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(BookLoan.objects.get(pk=second_id).status, BookLoan.Status.REQUESTED)

    def test_duplicate_active_request(self):
        self.create_loan()
        response = self.client.post("/api/loans/", {"book": self.book.id}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_edit_and_delete_rules(self):
        loan = self.create_loan()
        self.assertEqual(self.client.patch(f"/api/loans/{loan.id}/", {"comment": "к сессии"}, format="json").status_code, 200)
        self.assertEqual(loan.events.last().action, "updated")
        self.as_methodist().post(f"/api/loans/{loan.id}/issue/")
        self.assertEqual(self.client.delete(f"/api/loans/{loan.id}/").status_code, 400)
        self.assertTrue(BookLoan.objects.filter(pk=loan.id).exists())

        new_loan = self.create_loan(self.other_book)
        self.assertEqual(self.client.delete(f"/api/loans/{new_loan.id}/").status_code, 204)

    def test_filters(self):
        self.create_loan()
        other = self.create_loan(self.other_book)
        self.as_methodist().post(f"/api/loans/{other.id}/issue/")
        data = self.client.get(f"/api/loans/?status=issued&course={self.other_book.course_id}").data
        self.assertEqual([item["id"] for item in data], [other.id])
        self.assertEqual(self.client.get(f"/api/loans/?status=issued&course={self.course.id}").data, [])
        self.assertEqual(self.client.get("/api/loans/?status=bad").status_code, 400)

    def test_history_endpoint(self):
        loan = self.create_loan()
        data = self.client.get(f"/api/loans/{loan.id}/history/").data
        self.assertEqual(data[0]["action"], "created")
        self.assertEqual(data[0]["actor_name"], "student")
