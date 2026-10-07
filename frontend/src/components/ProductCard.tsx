import { Link } from 'react-router-dom'
import { money, shortDescription, type Product } from '../api'
import Stars from './Stars'

export function StockBadges({ product }: { product: Product }) {
  const sizes = product.inventory.length
  const soldOut = product.total_stock === 0
  return (
    <div className="badges">
      {product.bestseller && <span className="badge badge-gold">Bestseller</span>}
      {soldOut && <span className="badge badge-muted">Sold out</span>}
      {!soldOut && product.in_stock_sizes.length < sizes && (
        <span className="badge badge-muted">{product.in_stock_sizes.length} of {sizes} sizes available</span>
      )}
      {!soldOut && product.low_stock_sizes.length > 0 && (
        <span className="badge badge-warn">Low stock: {product.low_stock_sizes.join(', ')}</span>
      )}
    </div>
  )
}

export default function ProductCard({ product }: { product: Product }) {
  return (
    <Link to={`/products/${product.product_id}`} className="card">
      <div className="card-img">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {product.bestseller && <span className="ribbon">Bestseller</span>}
      </div>
      <div className="card-body">
        <span className="card-cat">{product.category}</span>
        <h3>{product.name}</h3>
        <Stars rating={product.rating} count={product.review_count} />
        <p className="card-desc">{shortDescription(product.description)}</p>
        <div className="card-foot">
          <span className="price">{money(product.price)}</span>
          <span className="card-cta">View</span>
        </div>
        <StockBadges product={product} />
      </div>
    </Link>
  )
}
