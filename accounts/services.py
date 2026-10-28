from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Book, BookLoan, LoanEvent

Status = BookLoan.Status

TRANSITIONS = {
    "issue": ([Status.REQUESTED], Status.ISSUED),
    "return": ([Status.ISSUED], Status.RETURNED),
    "cancel": ([Status.REQUESTED], Status.CANCELLED),
}


def log_event(loan, user, action, old_status=""):
    LoanEvent.objects.create(
        loan=loan,
        actor=user,
        action=action,
        old_status=old_status,
        new_status=loan.status,
    )


@transaction.atomic
def change_loan_status(loan_id, action, user):
    loan = BookLoan.objects.select_for_update().get(pk=loan_id)
    allowed_from, new_status = TRANSITIONS[action]
    if loan.status not in allowed_from:
        raise ValidationError(
            {"status": f"Недопустимый переход: заявка в статусе «{loan.get_status_display()}»."}
        )

    if action in ("issue", "return"):
        book = Book.objects.select_for_update().get(pk=loan.book_id)
        if action == "issue":
            if book.available_copies == 0:
                raise ValidationError({"book": "Нет свободных экземпляров этого учебника."})
            book.available_copies -= 1
        else:
            book.available_copies += 1
        book.save(update_fields=["available_copies"])

    old_status = loan.status
    loan.status = new_status
    loan.save(update_fields=["status"])
    log_event(loan, user, new_status, old_status)
    return loan
