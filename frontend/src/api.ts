// Typed client for the CC FastAPI backend. Every price and stock number shown
// on the site comes from these calls, which read data/campus_customs.db.

export type SizeStock = { size: string; quantity: number }

export type Product = {
  product_id: string
  name: string
  garment_type: string
  category: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  inventory: SizeStock[]
  total_stock: number
  in_stock_sizes: string[]
  low_stock_sizes: string[]
  // No review/sales data exists in the DB yet; the API returns null/0/false.
  rating: number | null
  review_count: number
  bestseller: boolean
}

export type Category = { name: string; count: number }

// API contract for POST /api/chat (mirrors backend/models.py ChatReply)
export type ProductMatches = { title: string; products: Product[] }
export type ChatReply = { reply: string; results: ProductMatches | null; saved: boolean }

// Where the shopper is, so "do you have this in rainbow?" means the product on screen.
export type PageInfo = {
  path: string
  product_id?: string
  category?: string
  search?: string
  shelf_title?: string
}

export type SavedMessage = { role: 'user' | 'assistant'; content: string; results: ProductMatches | null; created_at: string }
export type ChatHistory = { logged_in: boolean; messages: SavedMessage[] }

export const fetchChatHistory = () => getJson<ChatHistory>('/api/chat/history', { credentials: 'include' })

export const clearChatHistory = () =>
  getJson<{ deleted: number }>('/api/chat/history', { method: 'DELETE', credentials: 'include' })

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export function fetchProducts(params: { q?: string; category?: string } = {}) {
  const qs = new URLSearchParams()
  if (params.q) qs.set('q', params.q)
  if (params.category) qs.set('category', params.category)
  return getJson<Product[]>(`/api/products?${qs}`)
}

export const fetchProduct = (id: string) =>
  getJson<Product>(`/api/products/${encodeURIComponent(id)}`)

export const fetchCategories = () => getJson<Category[]>('/api/categories')

export type ChatTurn = { role: 'user' | 'assistant'; content: string }

// history = earlier turns (used for guests; logged-in shoppers' history comes from the DB).
// The session cookie tells the backend who is chatting; page tells it what's on screen.
export const sendChat = (message: string, history: ChatTurn[], page: PageInfo) =>
  getJson<ChatReply>('/api/chat', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, page }),
  })

// Streaming chat (Server-Sent Events over a POST). Calls onEvent for each event as it arrives.
export type StreamEvent =
  | { type: 'status'; text: string }
  | { type: 'reply'; text: string }
  | ({ type: 'done' } & ChatReply)
  | { type: 'error'; detail: string }

export async function streamChat(
  message: string,
  history: ChatTurn[],
  page: PageInfo,
  onEvent: (e: StreamEvent) => void,
): Promise<ChatReply> {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, page }),
  })
  if (!res.ok || !res.body) throw new Error(`${res.status} ${res.statusText}`)
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let final: ChatReply | null = null
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() ?? ''
    for (const chunk of chunks) {
      const line = chunk.split('\n').find((l) => l.startsWith('data:'))
      if (!line) continue
      const event = JSON.parse(line.slice(5)) as StreamEvent
      onEvent(event)
      if (event.type === 'done') final = event
      if (event.type === 'error') throw new Error(event.detail)
    }
  }
  if (!final) throw new Error('stream ended early')
  return final
}

export const money = (n: number) =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

export const shortDescription = (text: string, max = 90) => {
  const first = text.split(/(?<=\.)\s/)[0]
  return first.length <= max ? first : first.slice(0, max).replace(/\s+\S*$/, '') + '…'
}
