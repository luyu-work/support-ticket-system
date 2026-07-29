/** Client tickets list + create modal + detail stub */

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

const MAX_TICKET_PHOTOS = 5;

/** @type {File[]} */
let selectedTicketPhotos = [];
let problemReasonsLoaded = false;
let problemReasonOptions = [];

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
      listElement.innerHTML =
        `<p class="muted-text">Пока нет тикетов. Нажмите «Обратная связь», чтобы создать первый.</p>`;
      return;
    }

    listElement.innerHTML = payload.items.map(buildTicketCardHtml).join("");

    listElement.querySelectorAll("[data-ticket-open]").forEach((cardButton) => {
      cardButton.addEventListener("click", () => {
        const ticketId = cardButton.getAttribute("data-ticket-id");
        const ticket = payload.items.find(
          (item) => String(item.support_ticket_id) === String(ticketId),
        );
        openTicketDetailModal(ticket);
      });
    });
  } catch {
    listElement.innerHTML = `<p class="muted-text">Не удалось загрузить тикеты</p>`;
  }
}

/* ----- Detail stub modal ----- */

function openTicketDetailModal(ticket) {
  const modal = document.getElementById("ticket-detail-modal");
  const title = document.getElementById("ticket-detail-title");
  const summary = document.getElementById("ticket-detail-summary");
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
  document.body.classList.add("modal-open");
}

function closeTicketDetailModal() {
  const modal = document.getElementById("ticket-detail-modal");
  if (modal) modal.hidden = true;
  if (!isAnyModalOpen()) {
    document.body.classList.remove("modal-open");
  }
}

/* ----- Create ticket modal ----- */

function updateCreateTicketFormScrollState() {
  const form = document.getElementById("create-ticket-form");
  const dialog = document.querySelector("#create-ticket-modal .ticket-modal-dialog");
  if (!form || !dialog) return;

  requestAnimationFrame(() => {
    const dialogMaxPx = parseFloat(window.getComputedStyle(dialog).maxHeight);
    const header = dialog.querySelector(".ticket-modal-header");
    const headerHeight = header ? header.getBoundingClientRect().height : 0;
    const availableForForm = dialogMaxPx - headerHeight;

    if (!Number.isFinite(availableForForm) || availableForForm <= 0) {
      form.classList.remove("is-scrollable");
      form.style.maxHeight = "";
      return;
    }

    form.style.maxHeight = `${availableForForm}px`;

    // Measure without toggling overflow first (avoids default-bar flash)
    const contentHeight = form.scrollHeight;
    const needsScroll = contentHeight > availableForForm + 2;

    if (needsScroll) {
      form.classList.add("is-scrollable");
    } else {
      form.classList.remove("is-scrollable");
      form.scrollTop = 0;
    }
  });
}

function openCreateTicketModal() {
  const modal = document.getElementById("create-ticket-modal");
  if (!modal) return;
  modal.hidden = false;
  document.body.classList.add("modal-open");
  loadProblemReasonsIntoSelect();
  updateCreateTicketFormScrollState();
}

function closeCreateTicketModal() {
  const modal = document.getElementById("create-ticket-modal");
  closeCustomProblemReasonSelect();
  if (modal) modal.hidden = true;
  resetCreateTicketForm();
  if (!isAnyModalOpen()) {
    document.body.classList.remove("modal-open");
  }
}

function isAnyModalOpen() {
  const createModal = document.getElementById("create-ticket-modal");
  const detailModal = document.getElementById("ticket-detail-modal");
  return (
    (createModal && !createModal.hidden) ||
    (detailModal && !detailModal.hidden)
  );
}

function resetCreateTicketForm() {
  const form = document.getElementById("create-ticket-form");
  if (form) form.reset();
  selectedTicketPhotos = [];
  renderPhotoPreviews();
  resetCustomProblemReasonSelect();
  const descriptionField = document.getElementById("description");
  if (descriptionField) {
    descriptionField.style.height = "120px";
  }
  const messageElement = document.getElementById("create-ticket-message");
  if (messageElement) {
    messageElement.textContent = "";
    messageElement.className = "auth-message";
  }
}

function resetCustomProblemReasonSelect() {
  const hiddenInput = document.getElementById("problem_reason");
  const valueLabel = document.getElementById("problem-reason-value");
  const selectRoot = document.getElementById("problem-reason-select");
  if (hiddenInput) hiddenInput.value = "";
  if (valueLabel) {
    valueLabel.textContent = "Выберите причину";
    valueLabel.classList.add("is-placeholder");
  }
  closeCustomProblemReasonSelect();
  if (selectRoot) {
    selectRoot.querySelectorAll(".custom-select-option").forEach((option) => {
      option.classList.remove("is-selected");
    });
  }
}

function openCustomProblemReasonSelect() {
  const selectRoot = document.getElementById("problem-reason-select");
  const dropdown = document.getElementById("problem-reason-dropdown");
  const trigger = document.getElementById("problem-reason-trigger");
  if (!selectRoot || !dropdown || !trigger) return;

  selectRoot.dataset.open = "true";
  dropdown.hidden = false;
  trigger.setAttribute("aria-expanded", "true");
}

function closeCustomProblemReasonSelect() {
  const selectRoot = document.getElementById("problem-reason-select");
  const dropdown = document.getElementById("problem-reason-dropdown");
  const trigger = document.getElementById("problem-reason-trigger");
  if (!selectRoot || !dropdown || !trigger) return;

  selectRoot.dataset.open = "false";
  dropdown.hidden = true;
  trigger.setAttribute("aria-expanded", "false");
}

function toggleCustomProblemReasonSelect() {
  const selectRoot = document.getElementById("problem-reason-select");
  if (!selectRoot) return;
  if (selectRoot.dataset.open === "true") {
    closeCustomProblemReasonSelect();
  } else {
    openCustomProblemReasonSelect();
  }
}

function selectProblemReason(value, label) {
  const hiddenInput = document.getElementById("problem_reason");
  const valueLabel = document.getElementById("problem-reason-value");
  const selectRoot = document.getElementById("problem-reason-select");

  if (hiddenInput) hiddenInput.value = value;
  if (valueLabel) {
    valueLabel.textContent = label;
    valueLabel.classList.remove("is-placeholder");
  }
  if (selectRoot) {
    selectRoot.querySelectorAll(".custom-select-option").forEach((option) => {
      option.classList.toggle("is-selected", option.dataset.value === value);
    });
  }
  closeCustomProblemReasonSelect();
}

function renderProblemReasonOptions(reasons) {
  const dropdown = document.getElementById("problem-reason-dropdown");
  if (!dropdown) return;

  dropdown.innerHTML = reasons
    .map(
      (reason) => `
      <button
        type="button"
        class="custom-select-option"
        role="option"
        data-value="${escapeHtml(reason.value)}"
      >
        ${escapeHtml(reason.label_ru)}
      </button>
    `,
    )
    .join("");

  dropdown.querySelectorAll(".custom-select-option").forEach((optionButton) => {
    optionButton.addEventListener("click", () => {
      selectProblemReason(optionButton.dataset.value, optionButton.textContent.trim());
    });
  });
}

async function loadProblemReasonsIntoSelect() {
  if (problemReasonsLoaded) return;

  try {
    const response = await fetch("/tickets/problem-reasons");
    if (!response.ok) throw new Error("load failed");
    problemReasonOptions = await response.json();
    renderProblemReasonOptions(problemReasonOptions);
    problemReasonsLoaded = true;
  } catch {
    const messageElement = document.getElementById("create-ticket-message");
    showFormMessage(messageElement, "Не удалось загрузить причины", "error");
  }
}

function initCustomProblemReasonSelect() {
  const trigger = document.getElementById("problem-reason-trigger");
  const selectRoot = document.getElementById("problem-reason-select");
  if (!trigger || !selectRoot) return;

  trigger.addEventListener("click", (event) => {
    event.preventDefault();
    toggleCustomProblemReasonSelect();
  });

  document.addEventListener("click", (event) => {
    if (!selectRoot.contains(event.target)) {
      closeCustomProblemReasonSelect();
    }
  });
}

function renderPhotoPreviews() {
  const listElement = document.getElementById("photo-preview-list");
  const addButton = document.getElementById("add-photo-button");
  if (!listElement || !addButton) return;

  listElement.querySelectorAll(".photo-preview-tile").forEach((node) => node.remove());

  selectedTicketPhotos.forEach((file, index) => {
    const tile = document.createElement("div");
    tile.className = "photo-preview-tile";
    const objectUrl = URL.createObjectURL(file);
    tile.innerHTML = `
      <img src="${objectUrl}" alt="" />
      <button type="button" class="photo-remove-button" data-photo-index="${index}" aria-label="Удалить фото">×</button>
    `;
    listElement.insertBefore(tile, addButton);
  });

  listElement.querySelectorAll("[data-photo-index]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const index = Number(button.getAttribute("data-photo-index"));
      selectedTicketPhotos.splice(index, 1);
      renderPhotoPreviews();
    });
  });

  // At 5 photos hide "+"; display:flex on the button would override [hidden] without CSS fix
  const isFull = selectedTicketPhotos.length >= MAX_TICKET_PHOTOS;
  addButton.hidden = isFull;
  addButton.setAttribute("aria-hidden", isFull ? "true" : "false");
  updateCreateTicketFormScrollState();
}

function initDescriptionResizeHandle() {
  const textarea = document.getElementById("description");
  const handle = document.getElementById("description-resize-handle");
  if (!textarea || !handle) return;

  const minHeight = 120;
  const maxHeight = 193;

  let isDragging = false;
  let startY = 0;
  let startHeight = 0;

  const onPointerMove = (event) => {
    if (!isDragging) return;
    const deltaY = event.clientY - startY;
    let nextHeight = startHeight + deltaY;
    nextHeight = Math.max(minHeight, Math.min(maxHeight, nextHeight));
    textarea.style.height = `${nextHeight}px`;
    updateCreateTicketFormScrollState();
  };

  const onPointerUp = () => {
    if (!isDragging) return;
    isDragging = false;
    handle.classList.remove("is-dragging");
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", onPointerUp);
    updateCreateTicketFormScrollState();
  };

  handle.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    isDragging = true;
    startY = event.clientY;
    startHeight = textarea.getBoundingClientRect().height;
    handle.classList.add("is-dragging");
    document.body.style.cursor = "ns-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
  });
}

function initPhotoPicker() {
  const addButton = document.getElementById("add-photo-button");
  const fileInput = document.getElementById("photos-input");
  if (!addButton || !fileInput) return;

  addButton.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", () => {
    const incoming = fileInput.files ? Array.from(fileInput.files) : [];
    const freeSlots = MAX_TICKET_PHOTOS - selectedTicketPhotos.length;
    selectedTicketPhotos = selectedTicketPhotos.concat(incoming.slice(0, freeSlots));
    fileInput.value = "";
    renderPhotoPreviews();
  });
}

async function submitCreateTicketForm(event) {
  event.preventDefault();

  const form = event.currentTarget;
  const messageElement = document.getElementById("create-ticket-message");
  const submitButton = form.querySelector('button[type="submit"]');
  const accessToken = getAccessToken();

  const problemReasonInput = document.getElementById("problem_reason");
  const problemReason = problemReasonInput ? problemReasonInput.value : "";
  const description = form.description.value.trim();

  if (!problemReason) {
    showFormMessage(messageElement, "Выберите причину", "error");
    return;
  }
  if (!description) {
    showFormMessage(messageElement, "Заполните описание", "error");
    return;
  }

  const formData = new FormData();
  formData.append("problem_reason", problemReason);
  formData.append("description", description);
  selectedTicketPhotos.forEach((file) => formData.append("photos", file));

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

    closeCreateTicketModal();
    await renderMyTicketsList();
  } catch {
    showFormMessage(messageElement, "Сервер недоступен", "error");
  } finally {
    if (submitButton) submitButton.disabled = false;
  }
}

function initCreateTicketModal() {
  const openButton = document.getElementById("open-create-ticket-button");
  const form = document.getElementById("create-ticket-form");
  const createModal = document.getElementById("create-ticket-modal");

  if (openButton) {
    openButton.addEventListener("click", openCreateTicketModal);
  }

  if (createModal) {
    createModal.querySelectorAll("[data-close-create-modal]").forEach((element) => {
      element.addEventListener("click", closeCreateTicketModal);
    });
  }

  initPhotoPicker();
  initDescriptionResizeHandle();
  initCustomProblemReasonSelect();

  if (form) {
    form.addEventListener("submit", submitCreateTicketForm);
  }

  window.addEventListener("resize", () => {
    if (createModal && !createModal.hidden) {
      updateCreateTicketFormScrollState();
    }
  });
}

function initDetailModal() {
  const detailModal = document.getElementById("ticket-detail-modal");
  if (!detailModal) return;

  detailModal.querySelectorAll("[data-close-detail-modal]").forEach((element) => {
    element.addEventListener("click", closeTicketDetailModal);
  });
}

function initModalKeyboard() {
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;

    const createModal = document.getElementById("create-ticket-modal");
    const detailModal = document.getElementById("ticket-detail-modal");

    if (createModal && !createModal.hidden) {
      const selectRoot = document.getElementById("problem-reason-select");
      if (selectRoot && selectRoot.dataset.open === "true") {
        closeCustomProblemReasonSelect();
        return;
      }
      closeCreateTicketModal();
      return;
    }
    if (detailModal && !detailModal.hidden) {
      closeTicketDetailModal();
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

async function initMyTicketsPage() {
  if (!requireClientSession()) return;
  fillClientProfile();
  initLogoutButton();
  initCreateTicketModal();
  initDetailModal();
  initModalKeyboard();
  await renderMyTicketsList();
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.body.dataset.page === "my-tickets") {
    initMyTicketsPage();
  }
});
