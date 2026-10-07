import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="page center not-found">
      <span className="kicker">404</span>
      <h1 className="display">
        Lost on <em>campus</em>?
      </h1>
      <p className="muted">That page doesn't exist.</p>
      <Link to="/" className="btn btn-primary">
        Back to the room
      </Link>
    </div>
  )
}
