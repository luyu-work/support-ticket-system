const STATUS_LABELS_RU = {
  in_queue: "В очереди",
  important: "Важное",
  in_progress: "В работе",
  closed: "Закрыт",
  transferred_to_engineers: "Передан инженерам",
};

async function loadProblemReasons() {
  const selectElement = document.getElementById("problem_reason");
  if (!selectElement) return;

  const response = await fetch("/tickets/problem-reasons");
  if (!response.ok) {
    throw new Error("Не удалось загрузить причины");
  }
  const reasons = await response.json();
  reasons.forEach((reason) => {
    const option = document.createElement("option");
    option.value = reason.value;
    option.textContent = reason.label_ru;
    selectElement.appendChild(option);
  });
}

async function loadMyTickets() {
  const listElement = document.getElementById("my-tickets-list");
  if (!listElement) return;

  const accessToken = getAccessToken();
  const response = await fetch("/tickets/my", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (!response.ok) {
    listElement.innerHTML = `<p class="muted-text">Не удалось загрузить тикеты</p>`;
    return;
  }

  const payload = await response.json();
  if (!payload.items.length) {
    listElement.innerHTML = `<p class="muted-text">Пока нет тикетов — создайте первый</p>`;
    return;
  }

  listElement.innerHTML = payload.items
    .map((ticket) => {
      const statusLabel = STATUS_LABELS_RU[ticket.status] || ticket.status;
      const photoCount = (ticket.attachments || []).length;
      const photoText = photoCount ? ` · фото: ${photoCount}` : "";
      return `
        <article class="ticket-card">
          <h3 class="ticket-card-title">#${ticket.support_ticket_id} · ${escapeHtml(ticket.title)}</h3>
          <p class="ticket-card-meta">${escapeHtml(ticket.description).slice(0, 160)}</p>
          <span class="status-pill">${statusLabel}${photoText}</span>
        </article>
      `;
    })
    .join("");
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function initPhotoHint() {
  const photosInput = document.getElementById("photos");
  const hintElement = document.getElementById("photos-hint");
  if (!photosInput || !hintElement) return;

  photosInput.addEventListener("change", () => {
    const count = photosInput.files ? photosInput.files.length : 0;
    if (count === 0) {
      hintElement.textContent = "Файлы не выбраны";
    } else if (count > 10) {
      hintElement.textContent = `Выбрано ${count} — максимум 10, лишние не отправятся`;
    } else {
      hintElement.textContent = `Выбрано файлов: ${count}`;
    }
  });
}

async function submitNewTicketForm(event) {
  event.preventDefault();

  const form = event.currentTarget;
  const messageElement = document.getElementById("ticket-message");
  const submitButton = form.querySelector('button[type="submit"]');
  const accessToken = getAccessToken();

  const problemReason = form.problem_reason.value;
  const description = form.description.value.trim();
  const photosInput = form.photos;

  if (!problemReason) {
    showFormMessage(messageElement, "Выберите причину проблемы", "error");
    return;
  }
  if (!description) {
    showFormMessage(messageElement, "Заполните описание", "error");
    return;
  }

  const formData = new FormData();
  formData.append("problem_reason", problemReason);
  formData.append("description", description);

  const files = photosInput.files ? Array.from(photosInput.files).slice(0, 10) : [];
  files.forEach((file) => formData.append("photos", file));

  if (submitButton) submitButton.disabled = true;
  showFormMessage(messageElement, "Отправляем тикет…", "");

  try {
    const response = await fetch("/tickets", {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      body: formData,
    });
    const payload = await response.json();

    if (!response.ok) {
      let detail = payload.detail || "Не удалось создать тикет";
      if (Array.isArray(detail)) {
        detail = detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
      }
      showFormMessage(messageElement, detail, "error");
      return;
    }

    showFormMessage(
      messageElement,
      `Тикет #${payload.support_ticket_id} создан и в очереди`,
      "success",
    );
    form.reset();
    const hintElement = document.getElementById("photos-hint");
    if (hintElement) hintElement.textContent = "Файлы не выбраны";
    await loadMyTickets();
  } catch {
    showFormMessage(messageElement, "Сервер недоступен", "error");
  } finally {
    if (submitButton) submitButton.disabled = false;
  }
}

async function initNewTicketPage() {
  const userAccount = getStoredUserAccount();
  const accessToken = getAccessToken();
  const logoutButton = document.getElementById("logout-button");
  const form = document.getElementById("new-ticket-form");

  if (!accessToken || !userAccount) {
    window.location.href = "/login";
    return;
  }

  if (userAccount.role !== "client") {
    window.location.href = "/home";
    return;
  }

  if (logoutButton) {
    logoutButton.addEventListener("click", () => {
      clearAuthSession();
      window.location.href = "/login";
    });
  }

  initPhotoHint();

  try {
    await loadProblemReasons();
    await loadMyTickets();
  } catch {
    const listElement = document.getElementById("my-tickets-list");
    if (listElement) {
      listElement.innerHTML = `<p class="muted-text">Ошибка загрузки данных</p>`;
    }
  }

  if (form) {
    form.addEventListener("submit", submitNewTicketForm);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.body.dataset.page === "new-ticket") {
    initNewTicketPage();
  }
});
