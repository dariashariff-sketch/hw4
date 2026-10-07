import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { useCart } from '../cart'
import Icon from './Icon'

const LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function Navbar() {
  const { count } = useCart()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const close = () => setOpen(false)

  return (
    <header className="navbar">
      <div className="announce">Officially licensed Yale gear · 57 Broadway, New Haven</div>
      <nav className="nav-inner">
        <Link to="/" className="brand" onClick={close}>
          <span className="brand-text">
            Campus Customs
            <small>Yale gear · 57 Broadway</small>
          </span>
        </Link>

        <button className="nav-toggle" aria-label="Menu" onClick={() => setOpen((o) => !o)}>
          <Icon name="menu" size={24} />
        </button>

        <div className={`nav-links ${open ? 'open' : ''}`}>
          {LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} onClick={close}>
              {l.label}
            </NavLink>
          ))}
          <span className="nav-spacer" />
          {user ? (
            <>
              <NavLink to="/account" onClick={close}>
                <Icon name="user" size={17} /> {user.first_name}
              </NavLink>
              <button
                className="btn btn-outline-light btn-sm"
                onClick={async () => {
                  close()
                  await logout()
                  navigate('/')
                }}
              >
                Log Out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" onClick={close}>
                Log In
              </NavLink>
              <NavLink to="/signup" className="btn btn-outline-light btn-sm" onClick={close}>
                Create Account
              </NavLink>
            </>
          )}
          <NavLink to="/cart" className="cart-link" onClick={close} aria-label="Cart">
            <Icon name="cart" size={20} /> <span className="cart-count">{count}</span>
          </NavLink>
        </div>
      </nav>
    </header>
  )
}
