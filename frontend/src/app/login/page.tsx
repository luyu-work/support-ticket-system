"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthField } from "@/components/auth/AuthField";
import { AuthShell } from "@/components/auth/AuthShell";
import { ApiError, loginUser } from "@/lib/api";
import {
  getAccessToken,
  getPostLoginPath,
  getStoredUserAccount,
  saveAuthSession,
} from "@/lib/auth-storage";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState<"error" | "success" | "">("");
  const [loading, setLoading] = useState(false);

  // Already signed in → go to role home (do not bounce through "/")
  useEffect(() => {
    const token = getAccessToken();
    const user = getStoredUserAccount();
    if (token && user) {
      router.replace(getPostLoginPath(user));
    }
  }, [router]);

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
    <AuthShell
      title="Вход"
      subtitle="Чтобы воспользоваться системой, пожалуйста, заполните поля ниже"
      formId="login-form"
      onSubmit={onSubmit}
      message={message}
      messageType={messageType}
      submitLabel="Войти"
      loading={loading}
      footerHint="Нет аккаунта?"
      footerLinkHref="/register"
      footerLinkLabel="Зарегистрироваться"
    >
      <AuthField
        id="email"
        label="Почта"
        type="email"
        autoComplete="username"
        placeholder="example@gmail.com"
        value={email}
        onChange={setEmail}
      />
      <AuthField
        id="password"
        label="Пароль"
        type="password"
        autoComplete="current-password"
        placeholder="••••••••"
        value={password}
        onChange={setPassword}
      />
    </AuthShell>
  );
}
