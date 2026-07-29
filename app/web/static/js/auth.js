const ACCESS_TOKEN_STORAGE_KEY = "ticket_system_access_token";
const USER_ACCOUNT_STORAGE_KEY = "ticket_system_user_account";

function saveAuthSession(accessToken, userAccount) {
  localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, accessToken);
  localStorage.setItem(USER_ACCOUNT_STORAGE_KEY, JSON.stringify(userAccount));
}

function clearAuthSession() {
  localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_ACCOUNT_STORAGE_KEY);
}

function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
}

function getStoredUserAccount() {
  const raw = localStorage.getItem(USER_ACCOUNT_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function showFormMessage(messageElement, text, type) {
  messageElement.textContent = text;
  messageElement.className = `auth-message ${type}`;
}

function redirectAfterLogin(userAccount) {
  // Later: client → ticket form, agent → pool, admin → dashboard
  window.location.href = "/home";
}

async function submitLoginForm(event) {
  event.preventDefault();

  const form = event.currentTarget;
  const messageElement = document.getElementById("auth-message");
  const submitButton = form.querySelector('button[type="submit"]');
  const email = form.email.value.trim();
  const password = form.password.value;

  submitButton.disabled = true;
  showFormMessage(messageElement, "Входим…", "");

  try {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const payload = await response.json();

    if (!response.ok) {
      const detail = payload.detail || "Не удалось войти";
      showFormMessage(messageElement, typeof detail === "string" ? detail : "Ошибка входа", "error");
      return;
    }

    saveAuthSession(payload.access_token, payload.user_account);
    showFormMessage(messageElement, "Успешный вход", "success");
    redirectAfterLogin(payload.user_account);
  } catch {
    showFormMessage(messageElement, "Сервер недоступен. Запущен ли python start_project.py?", "error");
  } finally {
    submitButton.disabled = false;
  }
}

async function submitRegisterForm(event) {
  event.preventDefault();

  const form = event.currentTarget;
  const messageElement = document.getElementById("auth-message");
  const submitButton = form.querySelector('button[type="submit"]');
  const email = form.email.value.trim();
  const fullName = form.full_name.value.trim();
  const password = form.password.value;

  submitButton.disabled = true;
  showFormMessage(messageElement, "Регистрируем…", "");

  try {
    const response = await fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        full_name: fullName,
        password,
      }),
    });
    const payload = await response.json();

    if (!response.ok) {
      let detail = payload.detail || "Не удалось зарегистрироваться";
      if (Array.isArray(detail)) {
        detail = detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
      }
      showFormMessage(messageElement, detail, "error");
      return;
    }

    saveAuthSession(payload.access_token, payload.user_account);
    showFormMessage(messageElement, "Аккаунт создан", "success");
    redirectAfterLogin(payload.user_account);
  } catch {
    showFormMessage(messageElement, "Сервер недоступен. Запущен ли python start_project.py?", "error");
  } finally {
    submitButton.disabled = false;
  }
}

function initLoginPage() {
  const form = document.getElementById("login-form");
  if (form) {
    form.addEventListener("submit", submitLoginForm);
  }
}

function initRegisterPage() {
  const form = document.getElementById("register-form");
  if (form) {
    form.addEventListener("submit", submitRegisterForm);
  }
}

function initHomePage() {
  const userAccount = getStoredUserAccount();
  const accessToken = getAccessToken();
  const nameElement = document.getElementById("home-user-name");
  const roleElement = document.getElementById("home-user-role");
  const emailElement = document.getElementById("home-user-email");
  const logoutButton = document.getElementById("logout-button");

  if (!accessToken || !userAccount) {
    window.location.href = "/login";
    return;
  }

  if (nameElement) nameElement.textContent = userAccount.full_name;
  if (roleElement) roleElement.textContent = userAccount.role;
  if (emailElement) emailElement.textContent = userAccount.email;

  if (logoutButton) {
    logoutButton.addEventListener("click", () => {
      clearAuthSession();
      window.location.href = "/login";
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const pageName = document.body.dataset.page;
  if (pageName === "login") initLoginPage();
  if (pageName === "register") initRegisterPage();
  if (pageName === "home") initHomePage();
});
