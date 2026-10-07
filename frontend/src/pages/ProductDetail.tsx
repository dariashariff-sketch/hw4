import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { fetchProduct, money, type Product } from '../api'
import { useCart } from '../cart'
import { StockBadges } from '../components/ProductCard'
import Stars from '../components/Stars'
import Icon from '../components/Icon'

function stockText(qty: number) {
  if (qty === 0) return 'Sold out in this size'
  if (qty <= 5) return `Only ${qty} left, order soon!`
  return `${qty} in stock`
}

export default function ProductDetail() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const cart = useCart()

  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState('')
  const [size, setSize] = useState('')
  const [qty, setQty] = useState(1)
  const [added, setAdded] = useState(false)
  const [needSize, setNeedSize] = useState(false)

  useEffect(() => {
    setProduct(null)
    setError('')
    setSize('')
    setQty(1)
    fetchProduct(id)
      .then((p) => {
        setProduct(p)
        // preselect the only available size, if there's exactly one
        if (p.in_stock_sizes.length === 1) setSize(p.in_stock_sizes[0])
      })
      .catch(() => setError("We couldn't find that product."))
  }, [id])

  if (error)
    return (
      <div className="page">
        <p className="notice error">{error}</p>
        <Link to="/products"><Icon name="arrowLeft" size={15} /> Back to all products</Link>
      </div>
    )
  if (!product) return <div className="page notice">Loading…</div>

  const selected = product.inventory.find((s) => s.size === size)
  const max = selected?.quantity ?? 0

  function addToCart(goToCart: boolean) {
    if (!product) return
    if (!selected || max === 0) {
      setNeedSize(true)
      return
    }
    cart.add({
      product_id: product.product_id,
      name: product.name,
      image_url: product.image_url,
      price: product.price,
      size,
      quantity: qty,
      max,
    })
    if (goToCart) navigate('/cart')
    else {
      setAdded(true)
      setTimeout(() => setAdded(false), 2500)
    }
  }

  return (
    <div className="page">
      <nav className="crumbs">
        <Link to="/products">Products</Link> ›{' '}
        <Link to={`/products?category=${encodeURIComponent(product.category)}`}>{product.category}</Link> ›{' '}
        <span>{product.name}</span>
      </nav>

      <div className="pdp">
        <div className="pdp-img">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="pdp-info">
          <span className="card-cat">{product.garment_type}</span>
          <h1>{product.name}</h1>
          <Stars rating={product.rating} count={product.review_count} />
          <div className="pdp-price">{money(product.price)}</div>
          <StockBadges product={product} />

          <div className="pdp-block">
            <div className="label-row">
              <strong>Size</strong>
              {selected && <span className={max === 0 ? 'stock out' : max <= 5 ? 'stock low' : 'stock'}>{stockText(max)}</span>}
            </div>
            <div className="sizes">
              {product.inventory.map((s) => (
                <button
                  key={s.size}
                  className={`size ${size === s.size ? 'active' : ''}`}
                  disabled={s.quantity === 0}
                  title={stockText(s.quantity)}
                  onClick={() => {
                    setSize(s.size)
                    setQty(1)
                    setNeedSize(false)
                  }}
                >
                  {s.size}
                </button>
              ))}
            </div>
            {needSize && <p className="field-error">Please pick an available size first.</p>}
          </div>

          <div className="pdp-buy">
            <div className="qty">
              <button onClick={() => setQty((q) => Math.max(1, q - 1))} aria-label="Fewer">
                −
              </button>
              <span>{qty}</span>
              <button onClick={() => setQty((q) => Math.min(max || 1, q + 1))} aria-label="More" disabled={!selected || qty >= max}>
                +
              </button>
            </div>
            <button className="btn btn-primary btn-lg grow" onClick={() => addToCart(false)} disabled={product.total_stock === 0}>
              {added ? 'Added to cart' : 'Add to Cart'}
            </button>
          </div>
          <button className="btn btn-gold btn-lg block" onClick={() => addToCart(true)} disabled={product.total_stock === 0}>
            Buy Now
          </button>

          <div className="pdp-block">
            <strong>Description</strong>
            <p>{product.description}</p>
          </div>

          <div className="pdp-block">
            <strong>Colors</strong>
            <div className="tags">
              {product.colors.map((c) => (
                <span key={c} className="tag">
                  {c}
                </span>
              ))}
            </div>
          </div>

          <div className="pdp-block">
            <strong>Stock by size</strong>
            <table className="stock-table">
              <tbody>
                {product.inventory.map((s) => (
                  <tr key={s.size}>
                    <td>{s.size}</td>
                    <td className={s.quantity === 0 ? 'stock out' : s.quantity <= 5 ? 'stock low' : 'stock'}>
                      {s.quantity === 0 ? 'Sold out' : `${s.quantity} available`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pdp-note">
            <span>Visit us at 57 Broadway, New Haven</span>
            <span>30-day returns on unworn items</span>
          </div>
        </div>
      </div>

      <section className="reviews">
        <h2>Customer reviews</h2>
        {product.review_count === 0 ? (
          <div className="reviews-empty">
            <Stars rating={null} count={0} />
            <p>This piece doesn't have any reviews yet. Bought one? We'd love to hear what you think.</p>
          </div>
        ) : null}
      </section>
    </div>
  )
}
