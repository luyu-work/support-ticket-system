"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthField } from "@/components/auth/AuthField";
import { AuthShell } from "@/components/auth/AuthShell";
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
    <AuthShell
      title="Регистрация"
      subtitle="Создайте аккаунт, чтобы отправлять обращения в поддержку"
      formId="register-form"
      onSubmit={onSubmit}
      message={message}
      messageType={messageType}
      submitLabel="Зарегистрироваться"
      loading={loading}
      footerHint="Уже есть аккаунт?"
      footerLinkHref="/login"
      footerLinkLabel="Войти"
    >
      <AuthField
        id="full_name"
        label="ФИО"
        autoComplete="name"
        placeholder="Иван Иванов"
        value={fullName}
        onChange={setFullName}
      />
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
        autoComplete="new-password"
        placeholder="••••••••"
        minLength={8}
        value={password}
        onChange={setPassword}
      />
    </AuthShell>
  );
}
