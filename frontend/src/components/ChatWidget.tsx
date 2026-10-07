import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import { clearChatHistory, fetchChatHistory, streamChat, type PageInfo, type ProductMatches } from '../api'
import { useAuth } from '../auth'
import { useResults } from '../results'
import RichText from './RichText'
import Icon from './Icon'

type Msg = {
  role: 'user' | 'assistant'
  content: string
  results?: ProductMatches
  divider?: boolean
  streaming?: boolean
}

const greeting = (firstName?: string, returning = false): Msg => ({
  role: 'assistant',
  content: firstName
    ? returning
      ? `Welcome back, ${firstName}! I remember our last chat (it's above). What can I help you find today?`
      : `Hi ${firstName}! I'm the Campus Customs assistant. Ask me about gear, sizes, prices, or stock. Our chat is saved to your account.`
    : "Hi! I'm the Campus Customs assistant. Ask me about hoodies, sizes, prices, or what's in stock, and I'll put matching gear right on the page.",
})

// Tell the agent what's on screen, so "do you have this in rainbow?" means the product being viewed.
function usePageInfo(shelfTitle?: string): PageInfo {
  const { pathname, search } = useLocation()
  const params = new URLSearchParams(search)
  const match = pathname.match(/^\/products\/([^/]+)$/)
  return {
    path: pathname + search,
    product_id: match ? decodeURIComponent(match[1]) : undefined,
    category: params.get('category') ?? undefined,
    search: params.get('q') ?? undefined,
    shelf_title: shelfTitle,
  }
}

// Problem 9, F2: one-tap questions that fit where the shopper is.
function suggestionsFor(page: PageInfo, shelfTitle?: string): string[] {
  if (page.product_id)
    return ['Is this in stock in M?', 'What colors does this come in?', 'Show me similar items', "What's your return policy?"]
  if (shelfTitle)
    return ['Which of these have M in stock?', 'Anything cheaper?', 'Show me hoodies instead', 'Gifts under $40']
  if (page.category)
    return [`${page.category} under $60`, `Which ${page.category.toLowerCase()} have XL in stock?`, 'Anything with a bulldog?']
  return ['What hoodies do you have?', 'Gifts under $40', 'Anything with a bulldog?', 'Quarter-zips in size M']
}

export default function ChatWidget() {
  const { user, loading: authLoading } = useAuth()
  const shelf = useResults()
  const page = usePageInfo(shelf.results?.title)

  const open = shelf.chatOpen // shared so the dorm-room bulldog can open the chat
  const [messages, setMessages] = useState<Msg[]>([greeting()])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('') // Problem 9, F3: "Searching quarter-zips…"
  const endRef = useRef<HTMLDivElement>(null)

  // Customer memory: when someone logs in (or returns logged in), reload their saved chat.
  // Logging out wipes the on-screen chat back to a fresh guest greeting.
  useEffect(() => {
    if (authLoading) return
    if (!user) {
      setMessages([greeting()])
      return
    }
    let alive = true
    fetchChatHistory()
      .then((h) => {
        if (!alive) return
        const saved: Msg[] = h.messages.map((m) => ({ role: m.role, content: m.content, results: m.results ?? undefined }))
        setMessages(
          saved.length
            ? [...saved, { ...greeting(user.first_name, true), divider: true }]
            : [greeting(user.first_name)],
        )
      })
      .catch(() => alive && setMessages([greeting(user.first_name)]))
    return () => {
      alive = false
    }
  }, [user, authLoading])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy, open, status])

  const toggle = (next: boolean) => shelf.setChatOpen(next)

  async function startOver() {
    if (user) await clearChatHistory().catch(() => {})
    setMessages([greeting(user?.first_name)])
  }

  // replace the in-progress assistant bubble (always the last message while streaming)
  const updateLast = (patch: Partial<Msg>) =>
    setMessages((m) => {
      const copy = [...m]
      copy[copy.length - 1] = { ...copy[copy.length - 1], ...patch }
      return copy
    })

  async function send(text: string) {
    text = text.trim()
    if (!text || busy) return
    setInput('')
    // Guests send their tab's transcript; for logged-in shoppers the server uses the saved history.
    const history = messages
      .filter((m) => !m.divider && m !== messages[0])
      .map(({ role, content }) => ({ role, content }))
    setMessages((m) => [...m, { role: 'user', content: text }, { role: 'assistant', content: '', streaming: true }])
    setBusy(true)
    setStatus('Thinking…')
    shelf.setSearching(true)
    try {
      // Problem 9, B2: the reply streams in word by word, with tool progress in between
      const res = await streamChat(text, user ? [] : history, page, (ev) => {
        if (ev.type === 'status') setStatus(ev.text)
        if (ev.type === 'reply') updateLast({ content: ev.text })
      })
      updateLast({ content: res.reply, results: res.results ?? undefined, streaming: false })
      // API contract: structured matches from the agent -> cards on the page
      if (res.results) shelf.show(res.results)
    } catch {
      updateLast({ content: "Sorry, I can't reach the shop right now. Please try again in a moment.", streaming: false })
    } finally {
      setBusy(false)
      setStatus('')
      shelf.setSearching(false)
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    send(input)
  }

  const chips = suggestionsFor(page, shelf.results?.title)

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Chat with Campus Customs">
          <header className="chat-head">
            <div>
              <strong>Shopping Assistant</strong>
              <small>{user ? `Saved to ${user.first_name}'s account` : 'Guest chat · log in to save it'}</small>
            </div>
            <div className="chat-head-actions">
              <button title="Start a new chat" onClick={startOver} className="chat-new">
                New chat
              </button>
              <button aria-label="Close chat" onClick={() => toggle(false)}>
                <Icon name="close" size={18} />
              </button>
            </div>
          </header>
          {page.product_id && (
            <div className="chat-context">
              Asking about the product you're viewing
            </div>
          )}
          <div className="chat-body">
            {messages.map((m, i) => (
              <div key={i}>
                {m.divider && <div className="chat-divider">Today</div>}
                <div className={`msg msg-${m.role}`}>
                  {m.streaming && !m.content ? (
                    <div className="bubble status-bubble" aria-live="polite">
                      <span className="typing">
                        <span />
                        <span />
                        <span />
                      </span>
                      <span className="status-text">{status}</span>
                    </div>
                  ) : (
                    <div className={`bubble ${m.streaming ? 'is-streaming' : ''}`}>
                      <RichText text={m.content} />
                    </div>
                  )}
                  {m.streaming && m.content && status && <div className="status-under">{status}</div>}
                  {m.results && (
                    <button className="results-chip" onClick={() => shelf.show(m.results!)}>
                      {m.results.products.length} {m.results.products.length === 1 ? 'item' : 'items'} on the page ·{' '}
                      {m.results.title}
                    </button>
                  )}
                </div>
              </div>
            ))}
            <div ref={endRef} />
          </div>
          {!busy && (
            <div className="chat-chips" aria-label="Suggested questions">
              {chips.map((c) => (
                <button key={c} className="chat-chip" onClick={() => send(c)}>
                  {c}
                </button>
              ))}
            </div>
          )}
          <form className="chat-input" onSubmit={submit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={page.product_id ? 'e.g. do you have this in medium?' : 'e.g. what quarter-zips do you have?'}
              autoFocus
            />
            <button className="btn btn-primary btn-sm" disabled={busy || !input.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button className="chat-fab" onClick={() => toggle(!open)} aria-label="Open chat">
        <Icon name={open ? 'close' : 'chat'} size={22} />
        {!open && <span className="chat-fab-label">Chat with us</span>}
      </button>
    </div>
  )
}
