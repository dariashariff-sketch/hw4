import { useEffect, useState, type CSSProperties } from 'react'
import { useLocation } from 'react-router-dom'
import { useResults } from '../results'
import ProductCard from './ProductCard'
import QuickAdd from './QuickAdd'

// Product matches from the chat agent, shown at the top of whatever page is open.
// Cards are the same ProductCard used on /products, so clicking one opens the
// normal single-item page.
export default function ResultsShelf() {
  const { results, version, searching, chatOpen, clear } = useResults()
  const { pathname } = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  // Moving to any other page (nav link, opening a card) collapses the shelf to a slim
  // bar, so the new page is visible right away instead of hidden under 30 cards...
  useEffect(() => {
    setCollapsed(true)
  }, [pathname])
  // ...and every new result set from the chat expands it again. (Declared second so
  // that on first render, when both run, the shelf starts expanded.)
  useEffect(() => {
    setCollapsed(false)
  }, [version])

  if (!results) return null
  const n = results.products.length

  return (
    <section className={`shelf ${chatOpen ? 'shelf-chat-open' : ''} ${collapsed ? 'shelf-collapsed' : ''}`} id="chat-results" aria-live="polite">
      <div className="shelf-inner">
        <header className="shelf-head">
          <div>
            <span className="shelf-eyebrow">
              From your chat
            </span>
            <h2>
              {results.title} <span className="shelf-count">{n} {n === 1 ? 'item' : 'items'}</span>
            </h2>
          </div>
          <div className="shelf-actions">
            {searching && <span className="shelf-searching">Searching…</span>}
            <button className="shelf-btn" onClick={() => setCollapsed((c) => !c)}>
              {collapsed ? `Show all ${n}` : 'Hide'}
            </button>
            <button className="shelf-btn" onClick={clear} aria-label="Clear results">
              Clear
            </button>
          </div>
        </header>

        {!collapsed && (
          <div className={`shelf-grid ${searching ? 'is-refreshing' : ''}`} key={version}>
            {results.products.map((p, i) => (
              <div key={p.product_id} className="shelf-card" style={{ '--i': i } as CSSProperties}>
                <ProductCard product={p} />
                <QuickAdd product={p} />
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
