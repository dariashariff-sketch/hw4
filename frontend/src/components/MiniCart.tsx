import { useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { money } from '../api'
import { useCart } from '../cart'
import Icon from './Icon'

// Problem 9, F1: slides in after every "Add to cart" so the next step (checkout) is obvious.
export default function MiniCart() {
  const cart = useCart()
  const { pathname } = useLocation()
  const { drawerOpen, closeDrawer, lastAdded } = cart

  // close on navigation and on Escape
  useEffect(() => {
    closeDrawer()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname])
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && closeDrawer()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [closeDrawer])

  return (
    <>
      <div className={`drawer-backdrop ${drawerOpen ? 'show' : ''}`} onClick={closeDrawer} />
      <aside className={`mini-cart ${drawerOpen ? 'open' : ''}`} aria-hidden={!drawerOpen} aria-label="Cart">
        <header className="mini-head">
          <strong>
            <Icon name="check" size={18} /> Added to your cart
          </strong>
          <button onClick={closeDrawer} aria-label="Close cart">
            <Icon name="close" size={18} />
          </button>
        </header>

        {lastAdded && (
          <div className="mini-added">
            <img src={lastAdded.image_url} alt="" />
            <div>
              <div className="mini-name">{lastAdded.name}</div>
              <div className="muted">
                Size {lastAdded.size} · {money(lastAdded.price)}
              </div>
            </div>
          </div>
        )}

        <div className="mini-lines">
          {cart.lines.map((l) => (
            <div key={`${l.product_id}-${l.size}`} className="mini-line">
              <img src={l.image_url} alt="" />
              <div className="grow">
                <div className="mini-line-name">{l.name}</div>
                <div className="muted">
                  {l.size} · qty {l.quantity}
                </div>
              </div>
              <strong>{money(l.price * l.quantity)}</strong>
            </div>
          ))}
        </div>

        <footer className="mini-foot">
          <div className="sum-row total">
            <span>Subtotal ({cart.count} {cart.count === 1 ? 'item' : 'items'})</span>
            <span>{money(cart.subtotal)}</span>
          </div>
          <Link to="/cart" className="btn btn-gold btn-lg block" onClick={closeDrawer}>
            Checkout
          </Link>
          <button className="btn btn-outline btn-lg block" onClick={closeDrawer}>
            Keep shopping
          </button>
        </footer>
      </aside>
    </>
  )
}
