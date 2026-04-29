export function createSessionId(): string {
  if ("randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
