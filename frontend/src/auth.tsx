import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

// The session lives in an HttpOnly cookie set by the backend, so the browser
// never sees the token. We only keep the public user profile in React state.

export type User = { id: number; first_name: string; last_name: string; email: string; member_since?: string }

export type SignupData = {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

type AuthCtx = {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<User>
  signup: (data: SignupData) => Promise<User>
  logout: () => Promise<void>
}

const Ctx = createContext<AuthCtx | null>(null)

async function post(url: string, body?: unknown) {
  const res = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    // FastAPI sends a string for our errors, or a list for schema validation errors
    const detail = typeof data.detail === 'string' ? data.detail : 'Please check the form and try again.'
    throw new Error(detail)
  }
  return data
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then((r) => r.json())
      .then((d) => setUser(d.user ?? null))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const value: AuthCtx = {
    user,
    loading,
    login: async (email, password) => {
      const d = await post('/api/auth/login', { email, password })
      setUser(d.user)
      return d.user
    },
    signup: async (data) => {
      const d = await post('/api/auth/signup', data)
      setUser(d.user)
      return d.user
    },
    logout: async () => {
      await post('/api/auth/logout').catch(() => {})
      setUser(null)
    },
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useAuth() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
