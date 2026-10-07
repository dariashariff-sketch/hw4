// The few line icons the site uses, only for familiar UI patterns (cart, account, menu,
// close, chat, added-to-cart check, back). No emoji anywhere on the site. 24x24, stroke = currentColor.
const PATHS: Record<string, string> = {
  cart: 'M3 4h2l2.4 11.2a1.5 1.5 0 0 0 1.5 1.2h8.6a1.5 1.5 0 0 0 1.5-1.1L21 8H6.2 M9.5 20.5h.01 M17.5 20.5h.01',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M4.5 20.5c1.2-3.6 4.1-5.5 7.5-5.5s6.3 1.9 7.5 5.5',
  chat: 'M20 12.5c0 4.1-3.6 7-8 7-1.2 0-2.3-.2-3.3-.6L4 20l1.3-3.6C4.5 15.3 4 14 4 12.5 4 8.4 7.6 5.5 12 5.5s8 2.9 8 7z',
  close: 'M6 6l12 12 M18 6L6 18',
  menu: 'M4 7h16 M4 12h16 M4 17h16',
  arrowLeft: 'M19 12H5 M11 6l-6 6 6 6',
  check: 'M5 12.5l4.5 4.5L19 7.5',
}

export default function Icon({ name, size = 20, className = '' }: { name: keyof typeof PATHS | string; size?: number; className?: string }) {
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d={PATHS[name] ?? ''} />
    </svg>
  )
}

export function Star({ filled }: { filled: boolean }) {
  return (
    <svg className="star" width="13" height="13" viewBox="0 0 24 24" aria-hidden>
      <path
        d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.8l-5.2 2.8 1-5.8L3.5 9.7l5.9-.8z"
        fill={filled ? 'currentColor' : 'none'}
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  )
}
