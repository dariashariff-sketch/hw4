import { createContext, useContext, useState, type ReactNode } from 'react'
import type { ProductMatches } from './api'

// Shared state between the chat widget (which receives search results from
// the agent) and the results shelf (which renders them on whatever page is open).

type ResultsCtx = {
  results: ProductMatches | null
  version: number // bumps on every new result set so the card animation replays
  searching: boolean
  chatOpen: boolean
  show: (results: ProductMatches) => void
  clear: () => void
  setSearching: (v: boolean) => void
  setChatOpen: (v: boolean) => void
}

const Ctx = createContext<ResultsCtx | null>(null)

export function ResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ProductMatches | null>(null)
  const [version, setVersion] = useState(0)
  const [searching, setSearching] = useState(false)
  const [chatOpen, setChatOpen] = useState(false)

  const value: ResultsCtx = {
    results,
    version,
    searching,
    chatOpen,
    show: (r) => {
      setResults(r)
      setVersion((v) => v + 1)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    },
    clear: () => setResults(null),
    setSearching,
    setChatOpen,
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useResults() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useResults must be used inside ResultsProvider')
  return ctx
}
