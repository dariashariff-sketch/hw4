import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchCategories, fetchProducts, type Category, type Product } from '../api'
import ProductCard from '../components/ProductCard'
import QuickAdd from '../components/QuickAdd'

type Sort = 'name' | 'price-asc' | 'price-desc'

export default function Products() {
  const [params, setParams] = useSearchParams()
  const category = params.get('category') ?? ''
  const q = params.get('q') ?? ''

  const [products, setProducts] = useState<Product[] | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [error, setError] = useState('')
  const [search, setSearch] = useState(q)
  const [sort, setSort] = useState<Sort>('name')
  const [inStockOnly, setInStockOnly] = useState(false)

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    setProducts(null)
    setError('')
    fetchProducts({ q, category })
      .then(setProducts)
      .catch(() => setError("We couldn't load products. Is the backend running?"))
  }, [q, category])

  // live search: update the URL shortly after typing stops
  useEffect(() => {
    const t = setTimeout(() => {
      if (search.trim() === q) return
      const next = new URLSearchParams(params)
      if (search.trim()) next.set('q', search.trim())
      else next.delete('q')
      setParams(next, { replace: true })
    }, 300)
    return () => clearTimeout(t)
  }, [search, q, params, setParams])

  const pickCategory = (name: string) => {
    const next = new URLSearchParams(params)
    if (name) next.set('category', name)
    else next.delete('category')
    setParams(next)
  }

  const shown = useMemo(() => {
    let list = products ?? []
    if (inStockOnly) list = list.filter((p) => p.total_stock > 0)
    const sorted = [...list]
    if (sort === 'price-asc') sorted.sort((a, b) => a.price - b.price || a.name.localeCompare(b.name))
    if (sort === 'price-desc') sorted.sort((a, b) => b.price - a.price || a.name.localeCompare(b.name))
    return sorted
  }, [products, sort, inStockOnly])

  return (
    <div className="page">
      <div className="page-head">
        <h1>{category || 'All Products'}</h1>
        <p>Every price and size on this page comes straight from our live inventory.</p>
      </div>

      <div className="toolbar">
        <input
          className="search"
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search hoodies, bulldog, Saybrook, navy…"
        />
        <select value={sort} onChange={(e) => setSort(e.target.value as Sort)} aria-label="Sort">
          <option value="name">Sort: A–Z</option>
          <option value="price-asc">Price: low to high</option>
          <option value="price-desc">Price: high to low</option>
        </select>
        <label className="check">
          <input type="checkbox" checked={inStockOnly} onChange={(e) => setInStockOnly(e.target.checked)} /> In stock
          only
        </label>
      </div>

      <div className="chips">
        <button className={!category ? 'chip active' : 'chip'} onClick={() => pickCategory('')}>
          All
        </button>
        {categories.map((c) => (
          <button
            key={c.name}
            className={category === c.name ? 'chip active' : 'chip'}
            onClick={() => pickCategory(c.name)}
          >
            {c.name} <small>{c.count}</small>
          </button>
        ))}
      </div>

      {error && <p className="notice error">{error}</p>}
      {!products && !error && <p className="notice">Loading the latest gear…</p>}
      {products && (
        <p className="result-count">
          {shown.length} {shown.length === 1 ? 'item' : 'items'}
        </p>
      )}
      {products && shown.length === 0 && (
        <p className="notice">No matches. Try a different word, or ask our chat assistant for ideas.</p>
      )}
      <div className="grid">
        {shown.map((p) => (
          <div key={p.product_id} className="card-with-add">
            <ProductCard product={p} />
            <QuickAdd product={p} />
          </div>
        ))}
      </div>
    </div>
  )
}
