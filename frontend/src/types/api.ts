/** Mirrors backend `ActionItem` / `ProcessResponse` (see `backend/app/schemas/meeting.py`). */

export type ActionItem = {
  task: string
  owner?: string | null
  due?: string | null
}

export type ProcessMeta = {
  duration_sec?: number | null
  model_versions?: { whisper?: string | null; llm?: string | null } | null
  cached?: boolean | null
  cached_summary?: boolean | null
} | null

export type ProcessResponse = {
  transcript: string
  summary: string
  participants?: string[]
  decisions?: string[]
  action_items?: ActionItem[]
  language?: string | null
  meta?: ProcessMeta
}

/** `/api/auth/me` payload (see `backend/app/api/routes/auth.py`). */
export type AuthMe = {
  email: string
  name?: string | null
  picture?: string | null
  enabled: boolean
  role?: string | null
  limits: {
    summariesTotalLimit: number
    summariesTotalUsed: number
  }
}
