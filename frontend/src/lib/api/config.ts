const raw = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000"

export const API_BASE = raw
export const WS_BASE = raw.replace(/^http/, "ws")
