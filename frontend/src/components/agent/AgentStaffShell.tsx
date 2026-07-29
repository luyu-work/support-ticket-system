"use client";

import { useRouter } from "next/navigation";
import { ReactNode } from "react";
import { BrandLogo } from "@/components/ui/BrandLogo";
import { logoutAndClearSession } from "@/lib/api";
import { formatAgentBadge } from "@/lib/auth-storage";
import type { UserAccount } from "@/types/api";

export type AgentNavKey = "agents" | "pool" | "archive";

interface AgentStaffShellProps {
  user: UserAccount;
  activeNav: AgentNavKey;
  children: ReactNode;
}

export function AgentStaffShell({ user, activeNav, children }: AgentStaffShellProps) {
  const router = useRouter();
  const isAdmin = user.role === "admin";
  const roleLabel = isAdmin
    ? "Администратор"
    : formatAgentBadge(user.user_account_id, user.agent_number);

  return (
    <div className="agent-page">
      <div className="agent-top-row">
        <div className="agent-nav-card">
          <div className="agent-nav-logo">
            <BrandLogo />
          </div>
          <div className="agent-nav-list">
            {isAdmin ? (
              <button
                type="button"
                className={`agent-nav-item${activeNav === "agents" ? " is-active" : ""}`}
                onClick={() => router.push("/agent/agents")}
              >
                Агенты
              </button>
            ) : (
              <>
                <button
                  type="button"
                  className={`agent-nav-item${activeNav === "pool" ? " is-active" : ""}`}
                  onClick={() => router.push("/agent/pool")}
                >
                  Пул тикетов
                </button>
                <button
                  type="button"
                  className={`agent-nav-item${activeNav === "archive" ? " is-active" : ""}`}
                  onClick={() => router.push("/agent/archive")}
                >
                  Архив
                </button>
                <button type="button" className="agent-nav-item" disabled title="Скоро">
                  База знаний
                </button>
              </>
            )}
          </div>
        </div>

        <div className="agent-profile-card">
          <div className="agent-profile-text">
            <div className="agent-profile-name">{user.full_name}</div>
            <div className="agent-profile-role">{roleLabel}</div>
          </div>
          <button
            type="button"
            className="icon-button"
            aria-label="Выйти"
            title="Выйти"
            onClick={() => {
              void logoutAndClearSession().then(() => router.push("/login"));
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
              <path
                d="M8 6.00008L10 8.00008L8 10.0001M10 8.00008H2.66667M6 4.83247V4.80021C6 4.05347 6 3.67983 6.14533 3.39461C6.27316 3.14373 6.47698 2.9399 6.72787 2.81207C7.01308 2.66675 7.38673 2.66675 8.13346 2.66675H11.2001C11.9469 2.66675 12.3197 2.66675 12.6049 2.81207C12.8558 2.9399 13.0603 3.14373 13.1882 3.39461C13.3333 3.67955 13.3333 4.05274 13.3333 4.79802V11.2025C13.3333 11.9477 13.3333 12.3204 13.1882 12.6053C13.0603 12.8562 12.8558 13.0604 12.6049 13.1882C12.32 13.3334 11.9473 13.3334 11.2021 13.3334H8.13127C7.386 13.3334 7.0128 13.3334 6.72787 13.1882C6.47698 13.0604 6.27316 12.856 6.14533 12.6051C6 12.3199 6 11.9468 6 11.2001V11.1667"
                stroke="#333333"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>

      {children}
    </div>
  );
}
