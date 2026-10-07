import { useState } from 'react'
import { Link } from 'react-router-dom'
import { money } from '../api'
import { useCart } from '../cart'
import Icon from '../components/Icon'

export default function Cart() {
  const cart = useCart()
  const [msg, setMsg] = useState('')

  if (cart.lines.length === 0)
    return (
      <div className="page center empty-cart">
        <h1>Your cart is empty</h1>
        <p className="muted">Let's fix that. There's a hoodie with your name on it.</p>
        <Link to="/products" className="btn btn-primary btn-lg">
          Start shopping
        </Link>
      </div>
    )

  return (
    <div className="page">
      <h1>Your cart</h1>
      <div className="cart-layout">
        <div className="cart-lines">
          {cart.lines.map((l) => (
            <div key={`${l.product_id}-${l.size}`} className="cart-line">
              <Link to={`/products/${l.product_id}`}>
                <img src={l.image_url} alt={l.name} />
              </Link>
              <div className="grow">
                <Link to={`/products/${l.product_id}`} className="cart-name">
                  {l.name}
                </Link>
                <div className="muted">
                  Size {l.size} · {money(l.price)}
                </div>
                <button className="link-btn" onClick={() => cart.remove(l.product_id, l.size)}>
                  Remove
                </button>
              </div>
              <div className="qty">
                <button onClick={() => cart.setQty(l.product_id, l.size, l.quantity - 1)}>−</button>
                <span>{l.quantity}</span>
                <button onClick={() => cart.setQty(l.product_id, l.size, l.quantity + 1)} disabled={l.quantity >= l.max}>
                  +
                </button>
              </div>
              <strong className="line-total">{money(l.price * l.quantity)}</strong>
            </div>
          ))}
        </div>
        <aside className="summary">
          <h2>Order summary</h2>
          <div className="sum-row">
            <span>Items ({cart.count})</span>
            <span>{money(cart.subtotal)}</span>
          </div>
          <div className="sum-row muted">
            <span>Shipping</span>
            <span>Calculated at checkout</span>
          </div>
          <div className="sum-row total">
            <span>Subtotal</span>
            <span>{money(cart.subtotal)}</span>
          </div>
          <button
            className="btn btn-gold btn-lg block"
            onClick={() => setMsg('Checkout is coming soon. Your cart is saved on this device.')}
          >
            Checkout
          </button>
          {msg && <p className="notice">{msg}</p>}
          <Link to="/products" className="center block-link">
            <Icon name="arrowLeft" size={15} /> Keep shopping
          </Link>
        </aside>
      </div>
    </div>
  )
}
