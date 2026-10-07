import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const MIN_PASSWORD = 8

export default function Signup() {
  const { user, signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first: '', last: '', email: '', password: '', confirm: '' })
  const [showPw, setShowPw] = useState(false)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  if (user && !busy) return <Navigate to="/account" replace />

  const set = (k: keyof typeof form) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  const tooShort = form.password.length > 0 && form.password.length < MIN_PASSWORD
  const mismatch = form.confirm.length > 0 && form.password !== form.confirm

  async function submit(e: FormEvent) {
    e.preventDefault()
    setErr('')
    if (form.password.length < MIN_PASSWORD) return setErr(`Password must be at least ${MIN_PASSWORD} characters.`)
    if (form.password !== form.confirm) return setErr("Passwords don't match.")
    setBusy(true)
    try {
      await signup({
        first_name: form.first,
        last_name: form.last,
        email: form.email,
        password: form.password,
        confirm_password: form.confirm,
      })
      navigate('/account', { replace: true, state: { welcome: true } })
    } catch (e) {
      setErr((e as Error).message)
      setBusy(false)
    }
  }

  return (
    <div className="page auth">
      <form className="auth-card" onSubmit={submit}>
        <h1>Join Campus Customs</h1>
        <p className="muted">Create an account to save your chats and check out faster.</p>
        <div className="two-col">
          <label>
            First name
            <input required autoComplete="given-name" value={form.first} onChange={set('first')} />
          </label>
          <label>
            Last name
            <input required autoComplete="family-name" value={form.last} onChange={set('last')} />
          </label>
        </div>
        <label>
          Email
          <input
            type="email"
            required
            autoComplete="email"
            value={form.email}
            onChange={set('email')}
            placeholder="you@yale.edu"
          />
        </label>
        <label>
          Password
          <div className="pw-field">
            <input
              type={showPw ? 'text' : 'password'}
              required
              autoComplete="new-password"
              value={form.password}
              onChange={set('password')}
            />
            <button type="button" className="pw-toggle" onClick={() => setShowPw((s) => !s)}>
              {showPw ? 'Hide' : 'Show'}
            </button>
          </div>
          <small className={tooShort ? 'hint bad' : 'hint'}>At least {MIN_PASSWORD} characters</small>
        </label>
        <label>
          Confirm password
          <input
            type={showPw ? 'text' : 'password'}
            required
            autoComplete="new-password"
            value={form.confirm}
            onChange={set('confirm')}
          />
          {mismatch && <small className="hint bad">Passwords don't match</small>}
        </label>
        {err && <p className="field-error">{err}</p>}
        <button className="btn btn-primary btn-lg block" disabled={busy}>
          {busy ? 'Creating account…' : 'Create Account'}
        </button>
        <p className="muted center">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  )
}
