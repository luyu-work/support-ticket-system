"use client";

import { ChangeEvent } from "react";

interface AuthFieldProps {
  id: string;
  label: string;
  type?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  autoComplete?: string;
  minLength?: number;
  required?: boolean;
}

export function AuthField({
  id,
  label,
  type = "text",
  value,
  onChange,
  placeholder,
  autoComplete,
  minLength,
  required = true,
}: AuthFieldProps) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className="input-shell">
        <input
          id={id}
          name={id}
          type={type}
          autoComplete={autoComplete}
          placeholder={placeholder}
          minLength={minLength}
          value={value}
          onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
          required={required}
        />
      </div>
    </div>
  );
}
