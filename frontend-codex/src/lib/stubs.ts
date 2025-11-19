export function buildStubbedChatReply(prompt: string): string {
  const normalized = prompt.toLowerCase();

  if (normalized.includes("status") || normalized.includes("health")) {
    return [
      "Cluster heartbeat is nominal.",
      "CPU pressure on compute pool c3 is at 62% and trending down after the last round of vertical scaling.",
      "No pending incidents. The next scheduled maintenance window is 23:00 UTC.",
    ].join(" ");
  }

  if (
    normalized.includes("deploy") ||
    normalized.includes("lease") ||
    normalized.includes("container") ||
    normalized.includes("vm")
  ) {
    return [
      "I can lease fresh capacity for you.",
      "Tap one of the orange lease buttons and the control plane will raise a 402 that x402-fetch can settle automatically once your wallet approves it.",
      "After the payment clears I'll attach the new worker to the orchestrator within ~45 seconds.",
    ].join(" ");
  }

  if (normalized.includes("cost") || normalized.includes("price")) {
    return "Small burst containers are $0.02/min, memory-heavy VMs are $0.07/min, and GPU rigs are currently $0.65/min.";
  }

  return `Noted. Until the backend agent is wired up I'll keep responses local, but I recorded your instruction: "${prompt}".`;
}

export function buildStubbedLeaseMessage(action: string) {
  return `Simulated lease for "${action}" queued locally. Replace the API endpoint once the FastAPI controller is ready.`;
}
