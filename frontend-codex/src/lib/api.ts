import { API_BASE_URL } from "./config";

export type Fetcher = (
  input: RequestInfo | URL,
  init?: RequestInit
) => Promise<Response>;

export class PaymentRequiredError extends Error {
  constructor(message?: string) {
    super(message || "Payment is required to continue.");
    this.name = "PaymentRequiredError";
  }
}

const jsonHeaders = {
  "Content-Type": "application/json",
};

const toJson = async (response: Response) => {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch (error) {
    console.warn("Failed to parse JSON response", error);
    return { message: text };
  }
};

const normalizePath = (path: string) =>
  path.startsWith("/") ? path : `/${path}`;

export type ChatRequest = {
  message: string;
  sessionId: string;
  context?: Record<string, unknown>;
};

export type ChatResponse = {
  reply: string;
  steps?: string[];
  referenceId?: string;
};

export async function sendChatMessage(
  payload: ChatRequest,
  fetcher: Fetcher
): Promise<ChatResponse> {
  const response = await fetcher(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  });

  if (response.status === 402) {
    throw new PaymentRequiredError(
      "The chat agent requested an infrastructure lease."
    );
  }

  if (!response.ok) {
    const errorDetails = await toJson(response);
    throw new Error(
      (errorDetails as { message?: string }).message ||
        `Chat API returned ${response.status}`
    );
  }

  const data = (await toJson(response)) as ChatResponse;
  return data.reply ? data : { reply: "Received an empty response." };
}

export type LeaseRequest = {
  sku: string;
  runtimeMinutes: number;
  payload?: Record<string, unknown>;
  walletAddress?: string | null;
  path: string;
};

export type LeaseResponse = {
  leaseId: string;
  status: string;
  expiresAt?: string;
  message?: string;
};

export async function requestInfrastructureLease(
  input: LeaseRequest,
  fetcher: Fetcher
): Promise<LeaseResponse> {
  const response = await fetcher(
    `${API_BASE_URL}${normalizePath(input.path)}`,
    {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({
        sku: input.sku,
        runtimeMinutes: input.runtimeMinutes,
        requester: input.walletAddress,
        payload: input.payload,
      }),
    }
  );

  if (response.status === 402) {
    throw new PaymentRequiredError(
      "Lease requires payment. Complete the wallet request to continue."
    );
  }

  const data = (await toJson(response)) as Partial<LeaseResponse>;

  if (!response.ok) {
    throw new Error(
      data.message || `Lease endpoint returned ${response.status}`
    );
  }

  return {
    leaseId:
      data.leaseId ||
      `local-${Date.now().toString(36)}-${Math.random().toString(16).slice(2)}`,
    status: data.status || "pending",
    expiresAt: data.expiresAt,
    message: data.message,
  };
}
