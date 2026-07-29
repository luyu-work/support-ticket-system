"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { BrandLogo } from "@/components/ui/BrandLogo";
import { PasswordEyeIcon } from "@/components/ui/PasswordEyeIcon";
import { ApiError, loginUser } from "@/lib/api";
import { getPostLoginPath, saveAuthSession } from "@/lib/auth-storage";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<"error" | "success" | "">("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("Входим…");
    setMessageType("");
    try {
      const result = await loginUser(email.trim(), password);
      saveAuthSession(result.access_token, result.user_account);
      setMessage("Успешный вход");
      setMessageType("success");
      router.push(getPostLoginPath(result.user_account));
    } catch (error) {
      setMessageType("error");
      setMessage(
        error instanceof ApiError
          ? error.detail
          : "Сервер недоступен. Запущен ли python start_project.py?",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <BrandLogo />
      <div className="auth-wrapper">
        <div className="auth-title-block">
          <h1 className="auth-title">Вход</h1>
          <p className="auth-subtitle">
            Чтобы воспользоваться системой, пожалуйста, заполните поля ниже
          </p>
        </div>

        <form id="login-form" className="auth-form" onSubmit={onSubmit} noValidate>
          <div className="field">
            <label htmlFor="email">Почта</label>
            <div className="input-shell">
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="username"
                placeholder="example@gmail.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="field">
            <label htmlFor="password">Пароль</label>
            <div className="input-shell">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="********"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                className="password-toggle"
                aria-label={showPassword ? "Скрыть пароль" : "Показать пароль"}
                onClick={() => setShowPassword((v) => !v)}
              >
                <PasswordEyeIcon />
              </button>
            </div>
          </div>

          <p className={`auth-message ${messageType}`} aria-live="polite">
            {message}
          </p>
        </form>
      </div>

      <div className="auth-actions">
        <button className="btn-primary" type="submit" form="login-form" disabled={loading}>
          Войти
        </button>
        <p className="auth-footer">
          <span>Нет аккаунта?</span>
          <Link href="/register">Зарегистрироваться</Link>
        </p>
      </div>
    </main>
  );
}
