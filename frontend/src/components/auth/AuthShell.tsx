"use client";

import Link from "next/link";
import { FormEvent, ReactNode } from "react";
import { BrandLogo } from "@/components/ui/BrandLogo";

interface AuthShellProps {
  title: string;
  subtitle: string;
  formId: string;
  onSubmit: (event: FormEvent) => void;
  children: ReactNode;
  message: string;
  messageType: "error" | "success" | "";
  submitLabel: string;
  loading: boolean;
  footerHint: string;
  footerLinkHref: string;
  footerLinkLabel: string;
}

export function AuthShell({
  title,
  subtitle,
  formId,
  onSubmit,
  children,
  message,
  messageType,
  submitLabel,
  loading,
  footerHint,
  footerLinkHref,
  footerLinkLabel,
}: AuthShellProps) {
  return (
    <main className="auth-page">
      <BrandLogo />
      <div className="auth-wrapper">
        <div className="auth-title-block">
          <h1 className="auth-title">{title}</h1>
          <p className="auth-subtitle">{subtitle}</p>
        </div>

        <form id={formId} className="auth-form" onSubmit={onSubmit} noValidate>
          {children}
          <p className={`auth-message ${messageType}`} aria-live="polite">
            {message}
          </p>
        </form>
      </div>

      <div className="auth-actions">
        <button className="btn-primary" type="submit" form={formId} disabled={loading}>
          {submitLabel}
        </button>
        <p className="auth-footer">
          <span>{footerHint}</span>
          <Link href={footerLinkHref}>{footerLinkLabel}</Link>
        </p>
      </div>
    </main>
  );
}
