const loanForm = document.getElementById("loan-form");
const bookSelect = document.getElementById("book-select");
const commentInput = document.getElementById("loan-comment");
const statusFilter = document.getElementById("filter-status");
const courseFilter = document.getElementById("filter-course");
const loanList = document.getElementById("loan-list");
const loanCard = document.getElementById("loan-card");
const isMethodist = !loanForm;

const STATUS_COLORS = {
    requested: "bg-yellow-lt",
    issued: "bg-blue-lt",
    returned: "bg-green-lt",
    cancelled: "bg-secondary-lt",
};

let selectedId = null;

function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

async function perform(request, successText) {
    try {
        await request();
        showMessage(successText);
        await refresh();
    } catch (error) {
        showMessage("Ошибка: " + error.message, true);
    }
}

async function loadCourseFilter() {
    const courses = await apiRequest("/api/courses/");
    for (const course of courses) {
        const option = el("option", "", course.title);
        option.value = course.id;
        courseFilter.append(option);
    }
}

async function loadBooks() {
    if (!bookSelect) return;
    const books = await apiRequest("/api/books/");
    bookSelect.replaceChildren();
    for (const book of books) {
        const option = el("option", "",
            `${book.title} (свободно ${book.available_copies} из ${book.total_copies})`);
        option.value = book.id;
        bookSelect.append(option);
    }
}

async function loadLoans() {
    const params = new URLSearchParams();
    if (statusFilter.value) params.set("status", statusFilter.value);
    if (courseFilter.value) params.set("course", courseFilter.value);
    const loans = await apiRequest(`/api/loans/?${params}`);

    loanList.replaceChildren();
    if (loans.length === 0) {
        loanList.append(el("p", "text-secondary mb-0", "Заявки не найдены"));
        return;
    }
    for (const loan of loans) {
        const row = el("div", "d-flex justify-content-between align-items-center border-bottom py-2 gap-2");
        row.style.cursor = "pointer";
        if (loan.id === selectedId) row.classList.add("bg-primary-lt");
        const title = isMethodist ? `${loan.reader_name} → ${loan.book_title}` : loan.book_title;
        row.append(el("div", "", title), el("span", "badge " + STATUS_COLORS[loan.status], loan.status_display));
        row.addEventListener("click", () => {
            selectedId = loan.id;
            refresh().catch((error) => showMessage("Ошибка: " + error.message, true));
        });
        loanList.append(row);
    }
}

function changeStatus(loan, action, successText) {
    return perform(
        () => apiRequest(`/api/loans/${loan.id}/${action}/`, { method: "POST" }),
        successText
    );
}

function deleteLoan(loan) {
    if (!confirm(`Удалить заявку на «${loan.book_title}»?`)) {
        return;
    }
    return perform(async () => {
        await apiRequest(`/api/loans/${loan.id}/`, { method: "DELETE" });
        selectedId = null;
    }, "Заявка удалена.");
}

async function showLoanCard() {
    if (!selectedId) {
        loanCard.replaceChildren(el("p", "text-secondary mb-0", "Выберите заявку в списке."));
        return;
    }
    const [loan, events] = await Promise.all([
        apiRequest(`/api/loans/${selectedId}/`),
        apiRequest(`/api/loans/${selectedId}/history/`),
    ]);

    loanCard.replaceChildren(
        el("h3", "mb-1", loan.book_title),
        el("div", "text-secondary mb-2", `${loan.course_title} · читатель: ${loan.reader_name}`),
        el("span", "badge mb-3 " + STATUS_COLORS[loan.status], loan.status_display),
    );

    if (!isMethodist && loan.status === "requested") {
        const input = el("input", "form-control mb-2");
        input.maxLength = 255;
        input.value = loan.comment;
        input.placeholder = "Комментарий";
        loanCard.append(input, createButton("Сохранить комментарий", "btn-outline-primary mb-3", () =>
            perform(() => apiRequest(`/api/loans/${loan.id}/`, {
                method: "PATCH",
                body: JSON.stringify({ comment: input.value }),
            }), "Комментарий сохранён.")
        ));
    } else if (loan.comment) {
        loanCard.append(el("p", "", "Комментарий: " + loan.comment));
    }

    const actions = el("div", "d-flex flex-wrap gap-2 mb-3");
    if (isMethodist && loan.status === "requested") {
        actions.append(createButton("Выдать", "btn-success", () => changeStatus(loan, "issue", "Учебник выдан.")));
    }
    if (isMethodist && loan.status === "issued") {
        actions.append(createButton("Принять возврат", "btn-primary", () => changeStatus(loan, "return", "Учебник возвращён.")));
    }
    if (loan.status === "requested") {
        actions.append(createButton("Отменить", "btn-outline-warning", () => changeStatus(loan, "cancel", "Заявка отменена.")));
    }
    if (loan.status === "requested" || loan.status === "cancelled") {
        actions.append(createButton("Удалить", "btn-outline-danger", () => deleteLoan(loan)));
    }
    loanCard.append(actions, el("h4", "mb-2", "История"));

    const history = el("ul", "list-unstyled mb-0");
    for (const event of events) {
        const time = new Date(event.created_at).toLocaleString("ru-RU");
        history.append(el("li", "border-bottom py-1", `${time} — ${event.action_display} (${event.actor_name || "—"})`));
    }
    loanCard.append(history);
}

async function refresh() {
    await Promise.all([loadBooks(), loadLoans(), showLoanCard()]);
}

if (loanForm) {
    loanForm.addEventListener("submit", (event) => {
        event.preventDefault();
        perform(async () => {
            const loan = await apiRequest("/api/loans/", {
                method: "POST",
                body: JSON.stringify({ book: Number(bookSelect.value), comment: commentInput.value }),
            });
            selectedId = loan.id;
            commentInput.value = "";
        }, "Заявка создана.");
    });
}

for (const filter of [statusFilter, courseFilter]) {
    filter.addEventListener("change", () =>
        loadLoans().catch((error) => showMessage("Ошибка: " + error.message, true))
    );
}

async function initialize() {
    try {
        await loadCourseFilter();
        await refresh();
    } catch (error) {
        showMessage("Ошибка загрузки: " + error.message, true);
    }
}

initialize();
