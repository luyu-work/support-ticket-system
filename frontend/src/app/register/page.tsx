"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { BrandLogo } from "@/components/ui/BrandLogo";
import { ApiError, registerClient } from "@/lib/api";
import { getPostLoginPath, saveAuthSession } from "@/lib/auth-storage";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<"error" | "success" | "">("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("Регистрируем…");
    setMessageType("");
    try {
      const result = await registerClient(email.trim(), fullName.trim(), password);
      saveAuthSession(result.access_token, result.user_account);
      setMessage("Аккаунт создан");
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
          <h1 className="auth-title">Регистрация</h1>
          <p className="auth-subtitle">
            Создайте аккаунт, чтобы отправлять обращения в поддержку
          </p>
        </div>

        <form id="register-form" className="auth-form" onSubmit={onSubmit} noValidate>
          <div className="field">
            <label htmlFor="full_name">ФИО</label>
            <div className="input-shell">
              <input
                id="full_name"
                name="full_name"
                type="text"
                autoComplete="name"
                placeholder="Иван Иванов"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
          </div>

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
                type="password"
                autoComplete="new-password"
                placeholder="••••••••"
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <p className={`auth-message ${messageType}`} aria-live="polite">
            {message}
          </p>
        </form>
      </div>

      <div className="auth-actions">
        <button className="btn-primary" type="submit" form="register-form" disabled={loading}>
          Зарегистрироваться
        </button>
        <p className="auth-footer">
          <span>Уже есть аккаунт?</span>
          <Link href="/login">Войти</Link>
        </p>
      </div>
    </main>
  );
}
