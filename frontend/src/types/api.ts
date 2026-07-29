export type UserRole = "client" | "agent" | "admin";

export type TicketStatus =
  | "in_queue"
  | "important"
  | "in_progress"
  | "closed"
  | "transferred_to_engineers";

export interface UserAccount {
  user_account_id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_online: boolean;
  created_at: string;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
  user_account: UserAccount;
}

export interface TicketAttachment {
  ticket_attachment_id: number;
  original_file_name: string;
  storage_path: string;
  uploaded_at: string;
}

export interface SupportTicket {
  support_ticket_id: number;
  title: string;
  problem_reason: string;
  description: string;
  status: TicketStatus;
  due_date: string | null;
  created_at: string;
  updated_at: string;
  client_author_id: number;
  assigned_agent_id: number | null;
  attachments: TicketAttachment[];
}

export interface SupportTicketListResponse {
  items: SupportTicket[];
  total_ticket_count: number;
  page_number: number;
  page_size: number;
}

export interface ProblemReasonOption {
  value: string;
  label_ru: string;
}
