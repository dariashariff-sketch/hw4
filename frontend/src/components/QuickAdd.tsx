import { useState } from 'react'
import type { Product } from '../api'
import { useCart } from '../cart'

// Problem 9, F1: pick a size and add to cart straight from a product card,
// without opening the product page. Sold-out sizes can't be picked.
export default function QuickAdd({ product }: { product: Product }) {
  const cart = useCart()
  const inStock = product.inventory.filter((s) => s.quantity > 0)
  const [size, setSize] = useState(inStock.length === 1 ? inStock[0].size : '')

  if (inStock.length === 0) return <div className="quick-add sold-out">Sold out in every size</div>

  const selected = product.inventory.find((s) => s.size === size)

  return (
    <div className="quick-add" onClick={(e) => e.stopPropagation()}>
      <div className="quick-sizes" role="radiogroup" aria-label={`Size for ${product.name}`}>
        {product.inventory.map((s) => (
          <button
            key={s.size}
            type="button"
            role="radio"
            aria-checked={size === s.size}
            className={`quick-size ${size === s.size ? 'active' : ''}`}
            disabled={s.quantity === 0}
            title={s.quantity === 0 ? 'Sold out' : s.quantity <= 5 ? `Only ${s.quantity} left` : `${s.quantity} in stock`}
            onClick={() => setSize(s.size)}
          >
            {s.size}
          </button>
        ))}
      </div>
      <button
        type="button"
        className="btn btn-primary btn-sm quick-btn"
        disabled={!selected}
        onClick={() =>
          selected &&
          cart.add({
            product_id: product.product_id,
            name: product.name,
            image_url: product.image_url,
            price: product.price,
            size: selected.size,
            quantity: 1,
            max: selected.quantity,
          })
        }
      >
        {selected ? `Add ${selected.size} to cart` : 'Pick a size'}
      </button>
    </div>
  )
}
