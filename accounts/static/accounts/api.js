const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
const messageBlock = document.getElementById("message");

async function apiRequest(url, options = {}) {
    let response;
    try {
        response = await fetch(url, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
                ...(options.headers || {})
            },
            credentials: "same-origin"
        });
    } catch (error) {
        throw new Error("Сервер недоступен. Проверьте подключение к интернету и попробуйте позже.");
    }

    if (response.status >= 500) {
        throw new Error("Сервис временно недоступен. Попробуйте позже.");
    }

    let data = null;
    if (response.status !== 204) {
        data = await response.json().catch(() => null);
    }

    if (!response.ok) {
        let errorMsg = "Ошибка сервера";
        if (response.status === 403) {
            errorMsg = "Недостаточно прав для этого действия.";
        } else if (response.status === 404) {
            errorMsg = "Объект не найден или недоступен.";
        } else if (data) {
            const firstKey = Object.keys(data)[0];
            const val = data[firstKey];
            errorMsg = Array.isArray(val) ? val.join(" ") : val;
        }
        throw new Error(errorMsg);
    }
    return data;
}

function showMessage(text, isError = false) {
    messageBlock.textContent = text;
    messageBlock.className = `alert mb-3 ${isError ? "alert-danger" : "alert-success"}`;
}

function createButton(text, className, onClick) {
    const button = document.createElement("button");
    button.className = "btn btn-sm " + className;
    button.textContent = text;
    button.addEventListener("click", onClick);
    return button;
}
