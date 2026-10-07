import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

export type CartLine = {
  product_id: string
  name: string
  image_url: string
  price: number
  size: string
  quantity: number
  max: number // stock for this size when added, so the cart can't exceed it
}

type CartCtx = {
  lines: CartLine[]
  count: number
  subtotal: number
  add: (line: CartLine) => void
  setQty: (product_id: string, size: string, quantity: number) => void
  remove: (product_id: string, size: string) => void
  clear: () => void
  // mini-cart drawer (Problem 9, F1): slides in after every add so checkout is one click away
  lastAdded: CartLine | null
  drawerOpen: boolean
  closeDrawer: () => void
  openDrawer: () => void
}

const Ctx = createContext<CartCtx | null>(null)
const KEY = 'cc-cart'

export function CartProvider({ children }: { children: ReactNode }) {
  const [lines, setLines] = useState<CartLine[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(KEY) ?? '[]')
    } catch {
      return []
    }
  })

  const [lastAdded, setLastAdded] = useState<CartLine | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(lines))
  }, [lines])

  const same = (l: CartLine, id: string, size: string) => l.product_id === id && l.size === size

  const add = (line: CartLine) => {
    setLastAdded(line)
    setDrawerOpen(true)
    setLines((prev) => {
      const existing = prev.find((l) => same(l, line.product_id, line.size))
      if (!existing) return [...prev, { ...line, quantity: Math.min(line.quantity, line.max) }]
      return prev.map((l) =>
        same(l, line.product_id, line.size)
          ? { ...l, max: line.max, quantity: Math.min(l.quantity + line.quantity, line.max) }
          : l,
      )
    })
  }

  const setQty = (id: string, size: string, quantity: number) =>
    setLines((prev) =>
      prev.map((l) =>
        same(l, id, size) ? { ...l, quantity: Math.max(1, Math.min(quantity, l.max)) } : l,
      ),
    )

  const remove = (id: string, size: string) =>
    setLines((prev) => prev.filter((l) => !same(l, id, size)))

  const value: CartCtx = {
    lines,
    count: lines.reduce((n, l) => n + l.quantity, 0),
    subtotal: lines.reduce((n, l) => n + l.quantity * l.price, 0),
    add,
    setQty,
    remove,
    clear: () => setLines([]),
    lastAdded,
    drawerOpen,
    closeDrawer: () => setDrawerOpen(false),
    openDrawer: () => setDrawerOpen(true),
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useCart() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useCart must be used inside CartProvider')
  return ctx
}
