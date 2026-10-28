const courseSelect = document.getElementById("course-select");
const form = document.getElementById("enrollment-form");
const myList = document.getElementById("my-enrollments-list");
const allList = document.getElementById("all-enrollments-list");
const list = allList || myList;
const isMethodist = Boolean(allList);

const STATUS_LABELS = {
    pending: "На рассмотрении",
    approved: "Зачислен",
    rejected: "Отклонена",
};

async function loadCourses() {
    const courses = await apiRequest("/api/courses/");
    if (courseSelect) {
        courseSelect.replaceChildren();
        for (const course of courses) {
            const option = document.createElement("option");
            option.value = course.id;
            option.textContent = `${course.title} (мест: ${course.max_students})`;
            courseSelect.append(option);
        }
    }
    document.getElementById("kpi-courses").textContent = courses.length;
}

async function loadEnrollments() {
    const enrollments = await apiRequest("/api/enrollments/");
    list.replaceChildren();

    document.getElementById("kpi-total").textContent = enrollments.length;
    document.getElementById("kpi-pending").textContent =
        enrollments.filter((e) => e.status === "pending").length;

    if (enrollments.length === 0) {
        const empty = document.createElement("p");
        empty.textContent = "Заявки не найдены";
        list.append(empty);
        return;
    }

    for (const enrollment of enrollments) {
        const row = document.createElement("div");
        row.className =
            "d-flex justify-content-between align-items-center border-bottom py-3 gap-3";

        const title = document.createElement("div");
        title.textContent = isMethodist
            ? enrollment.student_name + " → " + enrollment.course_title
            : enrollment.course_title;

        const status = document.createElement("span");
        status.className = "badge bg-blue-lt";
        status.textContent = STATUS_LABELS[enrollment.status] || enrollment.status;

        const actions = document.createElement("div");
        actions.className = "d-flex align-items-center gap-2";
        actions.append(status);

        if (isMethodist && enrollment.status === "pending") {
            actions.append(
                createButton("Зачислить", "btn-success", () =>
                    changeStatus(enrollment.id, "approved", "Студент зачислен.")
                ),
                createButton("Отклонить", "btn-outline-danger", () =>
                    changeStatus(enrollment.id, "rejected", "Заявка отклонена.")
                )
            );
        }
        if (!isMethodist) {
            actions.append(
                createButton("Удалить", "btn-outline-danger", () =>
                    deleteEnrollment(enrollment.id, enrollment.course_title)
                )
            );
        }

        row.append(title, actions);
        list.append(row);
    }
}

async function changeStatus(enrollmentId, newStatus, successText) {
    try {
        await apiRequest(`/api/enrollments/${enrollmentId}/`, {
            method: "PATCH",
            body: JSON.stringify({ status: newStatus })
        });
        showMessage(successText);
        await loadEnrollments();
    } catch (error) {
        showMessage("Ошибка: " + error.message, true);
    }
}

async function deleteEnrollment(enrollmentId, courseTitle) {
    const confirmed = confirm(`Удалить заявку на курс «${courseTitle}»?`);
    if (!confirmed) {
        return;
    }
    try {
        await apiRequest(`/api/enrollments/${enrollmentId}/`, { method: "DELETE" });
        showMessage("Заявка удалена.");
        await loadEnrollments();
    } catch (error) {
        showMessage("Ошибка: " + error.message, true);
    }
}

if (form) {
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        try {
            await apiRequest("/api/enrollments/", {
                method: "POST",
                body: JSON.stringify({ course: Number(courseSelect.value) })
            });
            showMessage("Заявка успешно подана!");
            await loadEnrollments();
        } catch (error) {
            showMessage("Ошибка: " + error.message, true);
        }
    });
}
async function initialize() {
    try {
        await loadCourses();
        await loadEnrollments();
    } catch (error) {
        showMessage("Ошибка загрузки: " + error.message, true);
    }
}

initialize();