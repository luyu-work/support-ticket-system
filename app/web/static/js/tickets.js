/** Shared labels for ticket UI */

const STATUS_LABELS_RU = {
  in_queue: "В очереди",
  important: "Важное",
  in_progress: "В работе",
  closed: "Закрыт",
  transferred_to_engineers: "Передан инженерам",
};

const PROBLEM_REASON_LABELS_RU = {
  bug_report: "Баги",
  payment_issue: "Проблема с оплатой",
  feature_request: "Предложения по улучшению",
  login_issue: "Проблема со входом",
  other: "Другое",
};

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function getCategoryLabel(problemReason) {
  return PROBLEM_REASON_LABELS_RU[problemReason] || problemReason;
}

function getStatusLabel(status) {
  return STATUS_LABELS_RU[status] || status;
}

function getFirstLetter(fullName) {
  const trimmed = (fullName || "").trim();
  return trimmed ? trimmed[0].toUpperCase() : "?";
}

function buildTicketCardHtml(ticket) {
  const number = ticket.support_ticket_id;
  const category = getCategoryLabel(ticket.problem_reason);
  const status = ticket.status;
  const statusLabel = getStatusLabel(status);
  const description = ticket.description || "";

  return `
    <button
      type="button"
      class="ticket-card"
      data-ticket-id="${number}"
      data-ticket-open
    >
      <div class="ticket-card-top">
        <div class="ticket-card-content">
          <div class="ticket-card-number">Тикет №${number}</div>
          <div class="ticket-card-category">${escapeHtml(category)}</div>
        </div>
        <span class="status-tag status-tag--${escapeHtml(status)}">${escapeHtml(statusLabel)}</span>
      </div>
      <p class="ticket-card-description">${escapeHtml(description)}</p>
    </button>
  `;
}

async function fetchMyTickets() {
  const accessToken = getAccessToken();
  const response = await fetch("/tickets/my?page_size=100", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error("Не удалось загрузить тикеты");
  }
  return response.json();
}

async function renderMyTicketsList() {
  const listElement = document.getElementById("my-tickets-list");
  if (!listElement) return;

  try {
    const payload = await fetchMyTickets();
    if (!payload.items.length) {
      listElement.innerHTML = `<p class="muted-text">Пока нет тикетов. Нажмите «Обратная связь», чтобы создать первый.</p>`;
      return;
    }

    // Newest first already from API; show as-is
    listElement.innerHTML = payload.items.map(buildTicketCardHtml).join("");

    listElement.querySelectorAll("[data-ticket-open]").forEach((cardButton) => {
      cardButton.addEventListener("click", () => {
        const ticketId = cardButton.getAttribute("data-ticket-id");
        const ticket = payload.items.find(
          (item) => String(item.support_ticket_id) === String(ticketId),
        );
        openTicketModalStub(ticket);
      });
    });
  } catch {
    listElement.innerHTML = `<p class="muted-text">Не удалось загрузить тикеты</p>`;
  }
}

function openTicketModalStub(ticket) {
  const modal = document.getElementById("ticket-modal");
  const title = document.getElementById("ticket-modal-title");
  const summary = document.getElementById("ticket-modal-summary");
  if (!modal || !title || !summary) return;

  if (!ticket) {
    title.textContent = "Тикет";
    summary.textContent = "";
  } else {
    title.textContent = `Тикет №${ticket.support_ticket_id}`;
    summary.textContent = [
      `Категория: ${getCategoryLabel(ticket.problem_reason)}`,
      `Статус: ${getStatusLabel(ticket.status)}`,
      "",
      ticket.description,
    ].join("\n");
  }

  modal.hidden = false;
}

function closeTicketModal() {
  const modal = document.getElementById("ticket-modal");
  if (modal) modal.hidden = true;
}

function initTicketModal() {
  const modal = document.getElementById("ticket-modal");
  if (!modal) return;

  modal.querySelectorAll("[data-close-modal]").forEach((element) => {
    element.addEventListener("click", closeTicketModal);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hidden) {
      closeTicketModal();
    }
  });
}

function fillClientProfile() {
  const userAccount = getStoredUserAccount();
  if (!userAccount) return;

  const nameElement = document.getElementById("profile-full-name");
  const avatarElement = document.getElementById("profile-avatar");
  if (nameElement) nameElement.textContent = userAccount.full_name;
  if (avatarElement) avatarElement.textContent = getFirstLetter(userAccount.full_name);
}

function initLogoutButton() {
  const logoutButton = document.getElementById("logout-button");
  if (!logoutButton) return;
  logoutButton.addEventListener("click", () => {
    clearAuthSession();
    window.location.href = "/login";
  });
}

function requireClientSession() {
  const userAccount = getStoredUserAccount();
  const accessToken = getAccessToken();

  if (!accessToken || !userAccount) {
    window.location.href = "/login";
    return null;
  }
  if (userAccount.role !== "client") {
    window.location.href = "/home";
    return null;
  }
  return userAccount;
}

/* ----- New ticket form ----- */

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

function initPhotoHint() {
  const photosInput = document.getElementById("photos");
  const hintElement = document.getElementById("photos-hint");
  if (!photosInput || !hintElement) return;

  photosInput.addEventListener("change", () => {
    const count = photosInput.files ? photosInput.files.length : 0;
    if (count === 0) {
      hintElement.textContent = "Файлы не выбраны";
    } else if (count > 10) {
      hintElement.textContent = `Выбрано ${count} — максимум 10`;
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
  showFormMessage(messageElement, "Отправляем…", "");

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

    // Back to list after create
    window.location.href = "/tickets";
  } catch {
    showFormMessage(messageElement, "Сервер недоступен", "error");
  } finally {
    if (submitButton) submitButton.disabled = false;
  }
}

async function initMyTicketsPage() {
  if (!requireClientSession()) return;
  fillClientProfile();
  initLogoutButton();
  initTicketModal();
  await renderMyTicketsList();
}

async function initNewTicketPage() {
  if (!requireClientSession()) return;
  initLogoutButton();
  initPhotoHint();

  try {
    await loadProblemReasons();
  } catch {
    showFormMessage(
      document.getElementById("ticket-message"),
      "Не удалось загрузить категории",
      "error",
    );
  }

  const form = document.getElementById("new-ticket-form");
  if (form) {
    form.addEventListener("submit", submitNewTicketForm);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const pageName = document.body.dataset.page;
  if (pageName === "my-tickets") initMyTicketsPage();
  if (pageName === "new-ticket") initNewTicketPage();
});
