import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Account() {
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()
  const welcome = (useLocation().state as { welcome?: boolean } | null)?.welcome

  if (loading) return <div className="page notice">Loading…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: '/account' }} />

  return (
    <div className="page auth">
      <div className="auth-card">
        {welcome && <p className="notice">Your account is ready. Welcome to Campus Customs!</p>}
        <h1>Hi, {user.first_name}!</h1>
        <p className="muted">You're logged in.</p>
        <ul className="info-list">
          <li>
            <strong>Name:</strong> {user.first_name} {user.last_name}
          </li>
          <li>
            <strong>Email:</strong> {user.email}
          </li>
        </ul>
        <Link to="/products" className="btn btn-primary btn-lg block">
          Keep shopping
        </Link>
        <button
          className="btn btn-outline btn-lg block"
          onClick={async () => {
            await logout()
            navigate('/')
          }}
        >
          Log out
        </button>
      </div>
    </div>
  )
}
