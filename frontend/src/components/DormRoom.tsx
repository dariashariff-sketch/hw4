import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useResults } from '../results'

// Problem 10: the home page hero. An illustrated Yale dorm room at night (inspired by
// Gucci's Gift Giving rooms). Every object is a doorway into the shop: hover to see what
// it is, click to zoom the "camera" into it and land on that part of the site.

type Spot = {
  id: string
  label: string
  to?: string // route to open; omitted for the bulldog, which opens the chat
  zoom: { x: number; y: number; s: number } // camera target in viewBox units
  tag: { x: number; y: number } // where the hover label sits
  mark: { x: number; y: number } // pulsing "clickable" marker, placed on the object
}

const SPOTS: Record<string, Spot> = {
  hoodie: { id: 'hoodie', label: 'Shop hoodies', to: '/products?category=Hoodies', zoom: { x: 752, y: 470, s: 3.4 }, tag: { x: 752, y: 300 }, mark: { x: 752, y: 405 } },
  crewnecks: { id: 'crewnecks', label: 'Shop crewnecks', to: '/products?category=Crewnecks', zoom: { x: 1205, y: 420, s: 3.8 }, tag: { x: 1205, y: 330 }, mark: { x: 1250, y: 392 } },
  tees: { id: 'tees', label: 'Shop T-shirts', to: '/products?category=T-Shirts', zoom: { x: 1478, y: 268, s: 4.6 }, tag: { x: 1478, y: 206 }, mark: { x: 1520, y: 252 } },
  quarterzip: { id: 'quarterzip', label: 'Shop quarter-zips', to: '/products?category=Quarter-Zips', zoom: { x: 562, y: 290, s: 3.6 }, tag: { x: 562, y: 112 }, mark: { x: 562, y: 300 } },
  fleece: { id: 'fleece', label: 'Shop jackets & fleece', to: '/products?category=Jackets%20%26%20Fleece', zoom: { x: 1086, y: 560, s: 3.8 }, tag: { x: 1040, y: 462 }, mark: { x: 1062, y: 566 } },
  laptop: { id: 'laptop', label: 'Browse everything', to: '/products', zoom: { x: 415, y: 482, s: 4.6 }, tag: { x: 415, y: 400 }, mark: { x: 415, y: 480 } },
  pennant: { id: 'pennant', label: 'Our story', to: '/about', zoom: { x: 1200, y: 205, s: 4 }, tag: { x: 1205, y: 296 }, mark: { x: 1300, y: 202 } },
  bulldog: { id: 'bulldog', label: 'Chat with our assistant', zoom: { x: 1030, y: 730, s: 1 }, tag: { x: 1032, y: 606 }, mark: { x: 1090, y: 660 } },
}

// string-light bulbs along a sagging curve
const BULBS = Array.from({ length: 23 }, (_, i) => {
  const t = i / 22
  return { x: (1 - t) ** 2 * 60 + 2 * (1 - t) * t * 800 + t ** 2 * 1540, y: (1 - t) ** 2 * 64 + 2 * (1 - t) * t * 150 + t ** 2 * 64 + 10 }
})
const STARS = [[668, 132], [700, 210], [742, 118], [812, 148], [846, 232], [930, 254], [952, 128], [690, 300], [780, 196], [918, 210]]

type HotspotProps = { spot: Spot; active: Spot | null; onGo: (s: Spot) => void; onHover: () => void; children: ReactNode }

// Declared at module level so mouse-move re-renders don't remount the objects (keeps hover stable).
function Hotspot({ spot, active, onGo, onHover, children }: HotspotProps) {
  return (
    <g
      className={`hs hs-${spot.id} ${active?.id === spot.id ? 'is-active' : ''}`}
      role="link"
      tabIndex={0}
      aria-label={spot.label}
      onClick={() => onGo(spot)}
      onKeyDown={(e: KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onGo(spot)
        }
      }}
      onPointerEnter={onHover}
    >
      <g className="hs-art">{children}</g>
      <g className="hs-tag" transform={`translate(${spot.tag.x} ${spot.tag.y})`}>
        <rect x={-spot.label.length * 6.4 - 22} y={-22} width={spot.label.length * 12.8 + 44} height={44} rx={22} />
        <text textAnchor="middle" y={7}>
          {spot.label}
        </text>
      </g>
    </g>
  )
}

export default function DormRoom() {
  const navigate = useNavigate()
  const { setChatOpen } = useResults()
  const wrap = useRef<HTMLDivElement>(null)
  const [mouse, setMouse] = useState({ x: 0, y: 0 })
  const [active, setActive] = useState<Spot | null>(null)
  const [hint, setHint] = useState(true)

  // parallax: layers drift opposite the mouse at different depths
  useEffect(() => {
    const el = wrap.current
    if (!el || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const onMove = (e: PointerEvent) => {
      const r = el.getBoundingClientRect()
      setMouse({ x: ((e.clientX - r.left) / r.width - 0.5) * 2, y: ((e.clientY - r.top) / r.height - 0.5) * 2 })
    }
    el.addEventListener('pointermove', onMove)
    return () => el.removeEventListener('pointermove', onMove)
  }, [])

  const go = (spot: Spot) => {
    setHint(false)
    if (!spot.to) {
      setChatOpen(true) // the bulldog opens the assistant
      return
    }
    setActive(spot)
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    window.setTimeout(() => navigate(spot.to!), reduced ? 0 : 950)
  }

  const hsProps = { active, onGo: go, onHover: () => setHint(false) }

  const layer = (depth: number): CSSProperties => ({
    transform: active ? undefined : `translate(${-mouse.x * 14 * depth}px, ${-mouse.y * 8 * depth}px)`,
  })

  const camera: CSSProperties = active
    ? { transform: `translate(800px, 450px) scale(${active.zoom.s}) translate(${-active.zoom.x}px, ${-active.zoom.y}px)` }
    : {}

  return (
    <section className={`dorm ${active ? 'is-zooming' : ''}`} ref={wrap} aria-label="Campus Customs dorm room">
      <svg className="dorm-svg" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" role="img">
        <defs>
          <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#0d2145" />
            <stop offset="1" stopColor="#13305c" />
          </linearGradient>
          <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#081633" />
            <stop offset="1" stopColor="#24467c" />
          </linearGradient>
          <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#3d2b22" />
            <stop offset="1" stopColor="#24180f" />
          </linearGradient>
          <radialGradient id="lampGlow" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor="#fff8ee" stopOpacity="0.55" />
            <stop offset="1" stopColor="#fff8ee" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="moonGlow" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor="#f6efd8" stopOpacity="0.5" />
            <stop offset="1" stopColor="#f6efd8" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="screen" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#2b5a9e" />
            <stop offset="1" stopColor="#173865" />
          </linearGradient>
          <clipPath id="windowClip">
            <path d="M648 468 L648 214 Q648 112 800 92 Q952 112 952 214 L952 468 Z" />
          </clipPath>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" />
          </filter>
        </defs>

        <g className="camera" style={camera}>
          {/* ---------- layer 0: wall + window ---------- */}
          <g className="layer" style={layer(0.3)}>
            <rect x="-60" y="-40" width="1720" height="700" fill="url(#wall)" />
            {/* subtle wallpaper stripes */}
            {Array.from({ length: 34 }, (_, i) => (
              <rect key={i} x={-60 + i * 52} y="-40" width="2" height="700" fill="#ffffff" opacity="0.025" />
            ))}
            <circle cx="880" cy="170" r="140" fill="url(#moonGlow)" />
            <g clipPath="url(#windowClip)">
              <rect x="640" y="80" width="320" height="400" fill="url(#sky)" />
              {STARS.map(([x, y], i) => (
                <circle key={i} className="star-twinkle" cx={x} cy={y} r={i % 3 ? 1.6 : 2.4} fill="#fdf6e3" style={{ animationDelay: `${i * 0.37}s` }} />
              ))}
              <circle cx="890" cy="168" r="24" fill="#f6efd8" />
              <circle cx="880" cy="162" r="5" fill="#e6dcc0" opacity="0.7" />
              {/* New Haven skyline: Harkness-style tower + collegiate gothic halls */}
              <g fill="#0a1730">
                <rect x="736" y="262" width="44" height="210" />
                <rect x="742" y="236" width="32" height="30" />
                <rect x="748" y="214" width="20" height="24" />
                <path d="M752 214 L758 176 L764 214 Z" />
                <path d="M736 262 l4 -12 4 12 M772 262 l4 -12 4 12" />
                <path d="M640 470 L640 372 L662 372 L662 360 L676 360 L676 372 L700 372 L700 340 L716 322 L732 340 L732 470 Z" />
                <path d="M784 470 L784 352 L800 352 L800 342 L812 342 L812 352 L840 352 L840 384 L870 384 L870 368 L884 368 L884 384 L960 384 L960 470 Z" />
              </g>
              <g fill="#fbf6ea">
                {[[748, 300], [762, 300], [748, 340], [762, 340], [750, 392], [814, 402], [832, 402], [900, 410], [924, 410], [662, 400], [684, 420], [712, 396]].map(([x, y], i) => (
                  <rect key={i} className="win-light" x={x} y={y} width="7" height="11" rx="1" style={{ animationDelay: `${i * 0.8}s` }} />
                ))}
              </g>
            </g>
            {/* stone gothic window frame */}
            <path d="M648 468 L648 214 Q648 112 800 92 Q952 112 952 214 L952 468 Z" fill="none" stroke="#d8ccb1" strokeWidth="16" />
            <path d="M800 96 L800 468 M648 300 L952 300" stroke="#d8ccb1" strokeWidth="7" />
            <path d="M664 300 Q664 190 800 176 Q936 190 936 300" fill="none" stroke="#d8ccb1" strokeWidth="4" opacity="0.7" />
            <rect x="624" y="466" width="352" height="22" rx="3" fill="#cfc1a3" />
            <rect x="624" y="486" width="352" height="6" fill="#000" opacity="0.18" />
          </g>

          {/* ---------- layer 1: things on the wall ---------- */}
          <g className="layer" style={layer(0.5)}>
            {/* string lights */}
            <path d="M60 74 Q800 160 1540 74" fill="none" stroke="#1a1a1a" strokeWidth="2.5" />
            {BULBS.map((b, i) => (
              <g key={i} className="bulb" style={{ animationDelay: `${(i * 0.53) % 4}s` }}>
                <circle cx={b.x} cy={b.y} r="13" fill="#fffaf2" opacity="0.35" filter="url(#glow)" />
                <circle cx={b.x} cy={b.y} r="5.5" fill="#ffffff" />
              </g>
            ))}

            {/* pennant -> About */}
            <Hotspot spot={SPOTS.pennant} {...hsProps}>
              <g transform="rotate(-5 1076 206)">
                <path d="M1076 158 L1346 208 L1076 254 Z" fill="#00356b" stroke="#001f40" strokeWidth="3" />
                <rect x="1062" y="152" width="18" height="108" rx="3" fill="#f5efe4" />
                <text x="1104" y="222" fill="#f5efe4" fontFamily="Fraunces, Georgia, serif" fontWeight="700" fontSize="44" letterSpacing="4">
                  YALE
                </text>
              </g>
              <circle cx="1070" cy="150" r="5" fill="#e9edf2" />
            </Hotspot>

            {/* hook + hanging quarter-zip -> Quarter-Zips */}
            <Hotspot spot={SPOTS.quarterzip} {...hsProps}>
              <g transform="translate(42 0)">
              <circle cx="520" cy="148" r="8" fill="#c3c8cf" />
              <path d="M520 150 q0 -18 12 -12 M520 156 L520 172" stroke="#c3c8cf" strokeWidth="4" fill="none" strokeLinecap="round" />
              <path d="M466 196 L520 170 L574 196" stroke="#8a6b3b" strokeWidth="5" fill="none" strokeLinecap="round" />
              {/* sleeves */}
              <path d="M462 200 Q440 260 446 360 L466 362 Q470 280 484 228 Z" fill="#b9bfc8" stroke="#7f8794" strokeWidth="2.5" />
              <path d="M578 200 Q600 260 594 360 L574 362 Q570 280 556 228 Z" fill="#b9bfc8" stroke="#7f8794" strokeWidth="2.5" />
              {/* body */}
              <path d="M462 200 Q492 186 506 184 L534 184 Q548 186 578 200 L572 384 Q520 394 468 384 Z" fill="#c9ced6" stroke="#7f8794" strokeWidth="2.5" />
              {/* stand collar + zip */}
              <path d="M500 182 L506 168 L534 168 L540 182 L520 196 Z" fill="#aeb4be" stroke="#7f8794" strokeWidth="2" />
              <path d="M520 190 L520 250" stroke="#f5efe4" strokeWidth="4" strokeLinecap="round" />
              <rect x="515" y="238" width="10" height="18" rx="3" fill="#e9edf2" />
              <rect x="468" y="372" width="104" height="12" rx="3" fill="#aeb4be" />
              <path d="M492 230 l12 0 l-2 12 z" fill="#a8473a" opacity="0.9" />
              </g>
            </Hotspot>

            {/* shelf + folded tees -> T-Shirts */}
            <rect x="1384" y="300" width="196" height="12" rx="2" fill="#6e4b34" />
            <path d="M1404 312 l0 18 l16 -18 M1556 312 l0 18 l-16 -18" stroke="#4a3122" strokeWidth="5" fill="none" />
            <rect x="1384" y="424" width="196" height="12" rx="2" fill="#6e4b34" />
            {[['#a8473a', 18, 70], ['#e9edf2', 14, 82], ['#f5efe4', 20, 66], ['#2f5d50', 16, 78], ['#00356b', 22, 86], ['#8a6b3b', 14, 72]].map(([c, w, h], i, arr) => {
              const x = 1398 + arr.slice(0, i).reduce((n, a) => n + (a[1] as number) + 4, 0)
              return <rect key={i} x={x} y={424 - (h as number)} width={w as number} height={h as number} rx="2" fill={c as string} stroke="#0a1730" strokeWidth="1.5" />
            })}
            <path d="M1530 424 q-6 -30 6 -46 q14 14 6 46 z M1546 424 q4 -26 20 -34 q2 20 -12 34 z" fill="#4f7d5c" />
            <rect x="1528" y="408" width="34" height="16" rx="3" fill="#c3c8cf" />
            <Hotspot spot={SPOTS.tees} {...hsProps}>
              {[['#00356b', 0], ['#a7adb5', 16], ['#fbf8f2', 32]].map(([c, dy], i) => (
                <g key={i} transform={`translate(0 ${-(dy as number)})`}>
                  <path d="M1414 300 L1414 282 Q1414 276 1420 276 L1536 276 Q1542 276 1542 282 L1542 300 Z" fill={c as string} stroke="#0a1730" strokeWidth="2" />
                  <path d="M1460 276 Q1478 288 1496 276" fill="none" stroke="#0a1730" strokeWidth="1.8" opacity="0.6" />
                </g>
              ))}
            </Hotspot>
          </g>

          {/* ---------- layer 2: floor, bed, desk ---------- */}
          <g className="layer" style={layer(0.75)}>
            <rect x="-60" y="640" width="1720" height="300" fill="url(#floor)" />
            {Array.from({ length: 9 }, (_, i) => (
              <path key={i} d={`M-60 ${660 + i * 28} L1660 ${660 + i * 28}`} stroke="#000" strokeWidth="1.5" opacity="0.18" />
            ))}
            <rect x="-60" y="634" width="1720" height="10" fill="#0a1730" opacity="0.5" />

            {/* rug */}
            <ellipse cx="930" cy="812" rx="400" ry="62" fill="#00356b" />
            <ellipse cx="930" cy="812" rx="372" ry="50" fill="none" stroke="#e9edf2" strokeWidth="4" strokeDasharray="2 10" />
            <ellipse cx="930" cy="812" rx="340" ry="40" fill="none" stroke="#f5efe4" strokeWidth="2" opacity="0.5" />

            {/* bed */}
            <rect x="1070" y="596" width="560" height="20" fill="#4a3122" />
            <rect x="1090" y="616" width="16" height="70" fill="#3a271b" />
            <rect x="1060" y="520" width="580" height="80" rx="8" fill="#ece3d0" stroke="#b9ad93" strokeWidth="2" />
            <path d="M1180 508 L1640 508 L1640 600 L1196 600 Q1170 560 1180 508 Z" fill="#00356b" />
            <path d="M1186 540 L1640 540" stroke="#f5efe4" strokeWidth="10" opacity="0.9" />
            <path d="M1190 560 L1640 560" stroke="#f5efe4" strokeWidth="4" opacity="0.6" />
            <rect x="1470" y="462" width="150" height="58" rx="24" fill="#fbf8f2" stroke="#cfc4ac" strokeWidth="2" />


            {/* dresser beside the bed: crewnecks on top, fleece jacket hung on its side */}
            <ellipse cx="1205" cy="652" rx="118" ry="10" fill="#000" opacity="0.3" />
            <rect x="1108" y="456" width="194" height="186" rx="4" fill="#7a5238" stroke="#4a3122" strokeWidth="2.5" />
            <rect x="1098" y="442" width="214" height="16" rx="4" fill="#8f6344" stroke="#4a3122" strokeWidth="2.5" />
            {[466, 524, 582].map((y) => (
              <g key={y}>
                <rect x="1120" y={y} width="170" height="50" rx="3" fill="#6a4630" stroke="#4a3122" strokeWidth="2" />
                <circle cx="1170" cy={y + 25} r="5" fill="#e9edf2" />
                <circle cx="1240" cy={y + 25} r="5" fill="#e9edf2" />
              </g>
            ))}
            <rect x="1114" y="640" width="14" height="12" fill="#4a3122" />
            <rect x="1282" y="640" width="14" height="12" fill="#4a3122" />
            {/* brass hook on the dresser's side */}
            <path d="M1108 478 L1094 478 q-8 0 -8 8" stroke="#c3c8cf" strokeWidth="4" fill="none" strokeLinecap="round" />
            <Hotspot spot={SPOTS.fleece} {...hsProps}>
              <g transform="translate(258 197) scale(0.72)">
              {/* hanger */}
              <path d="M1150 398 q0 -12 9 -9" stroke="#c3c8cf" strokeWidth="3.5" fill="none" strokeLinecap="round" />
              <path d="M1100 432 L1150 404 L1200 432" stroke="#c3c8cf" strokeWidth="4" fill="none" strokeLinecap="round" />
              {/* sleeves hanging straight down */}
              <path d="M1096 436 Q1076 470 1074 600 L1098 604 Q1102 520 1112 470 Z" fill="#7d8794" stroke="#2f3640" strokeWidth="2.5" strokeLinejoin="round" />
              <path d="M1204 436 Q1224 470 1226 600 L1202 604 Q1198 520 1188 470 Z" fill="#7d8794" stroke="#2f3640" strokeWidth="2.5" strokeLinejoin="round" />
              <rect x="1073" y="592" width="27" height="14" rx="4" fill="#00356b" />
              <rect x="1200" y="592" width="27" height="14" rx="4" fill="#00356b" />
              {/* body */}
              <path d="M1096 436 Q1122 422 1138 420 L1162 420 Q1178 422 1204 436 L1200 616 L1100 616 Z" fill="#8e98a5" stroke="#2f3640" strokeWidth="2.5" strokeLinejoin="round" />
              {/* fleece texture */}
              {[[1112, 470], [1126, 512], [1114, 556], [1132, 590], [1186, 470], [1172, 520], [1188, 562], [1168, 596]].map(([x, y], i) => (
                <circle key={i} cx={x} cy={y} r="3" fill="#a9b2bd" />
              ))}
              {/* stand collar */}
              <path d="M1128 420 L1132 404 L1168 404 L1172 420 L1150 432 Z" fill="#00356b" stroke="#2f3640" strokeWidth="2" strokeLinejoin="round" />
              {/* full zip + pull */}
              <path d="M1150 428 L1150 616" stroke="#00356b" strokeWidth="5" />
              <path d="M1150 428 L1150 616" stroke="#cfd8e6" strokeWidth="1.3" strokeDasharray="2 3" />
              <rect x="1146" y="436" width="8" height="15" rx="2.5" fill="#e9edf2" />
              {/* zip pockets + hem band */}
              <path d="M1112 560 L1130 548 M1188 560 L1170 548" stroke="#2f3640" strokeWidth="3" strokeLinecap="round" />
              <rect x="1100" y="604" width="100" height="12" fill="#00356b" />
              {/* small chest logo */}
              <path d="M1170 452 l10 0 l-1 10 l-4 3 l-4 -3 z" fill="#f5efe4" opacity="0.9" />
              </g>
            </Hotspot>

            {/* folded crewneck stack -> Crewnecks */}
            <Hotspot spot={SPOTS.crewnecks} {...hsProps}>
              <g transform="translate(-88 -78)">
              {[['#00356b', 0], ['#a7adb5', 22], ['#f1e9d6', 44]].map(([c, dy], i) => (
                <g key={i} transform={`translate(0 ${-(dy as number)})`}>
                  <path d="M1222 520 L1222 496 Q1222 488 1230 488 L1356 488 Q1364 488 1364 496 L1364 520 Z" fill={c as string} stroke="#0a1730" strokeWidth="2" />
                  <path d="M1270 488 Q1293 504 1316 488" fill="none" stroke={i === 0 ? '#f5efe4' : '#0a1730'} strokeWidth="2" opacity="0.7" />
                  <path d="M1222 512 L1364 512" stroke="#0a1730" strokeWidth="1" opacity="0.25" />
                </g>
              ))}
              <text x="1293" y="466" textAnchor="middle" fill="#00356b" fontFamily="Fraunces, Georgia, serif" fontWeight="700" fontSize="12">
                YALE
              </text>
              </g>
            </Hotspot>

            {/* desk */}
            <rect x="100" y="540" width="480" height="24" rx="4" fill="#7a5238" />
            <rect x="100" y="562" width="480" height="8" fill="#000" opacity="0.2" />
            <rect x="116" y="564" width="140" height="196" fill="#6a4630" />
            <path d="M126 610 L246 610 M126 664 L246 664 M126 718 L246 718" stroke="#3e2819" strokeWidth="3" />
            <circle cx="186" cy="590" r="4" fill="#e9edf2" />
            <circle cx="186" cy="642" r="4" fill="#e9edf2" />
            <circle cx="186" cy="694" r="4" fill="#e9edf2" />
            <rect x="552" y="564" width="16" height="196" fill="#5a3b28" />

            {/* lamp + warm glow */}
            <ellipse cx="240" cy="520" rx="210" ry="150" fill="url(#lampGlow)" className="lamp-glow" />
            <path d="M176 540 L216 540 L206 530 L186 530 Z" fill="#1d1d1d" />
            <path d="M196 530 L226 438 L262 410" stroke="#1d1d1d" strokeWidth="7" fill="none" strokeLinecap="round" />
            <path d="M246 388 L312 414 L292 446 L236 420 Z" fill="#e9edf2" stroke="#aab2bd" strokeWidth="2" />
            <path d="M292 446 L236 420 L196 534 L360 534 Z" fill="#ffffff" opacity="0.14" />

            {/* books + mug */}
            <rect x="130" y="508" width="120" height="14" rx="2" fill="#a8473a" />
            <rect x="138" y="494" width="104" height="14" rx="2" fill="#2f5d50" />
            <rect x="134" y="522" width="116" height="18" rx="2" fill="#00356b" />
            <path d="M516 504 L544 504 L540 540 L520 540 Z" fill="#f5efe4" stroke="#0a1730" strokeWidth="2" />
            <path d="M544 512 q14 2 0 18" fill="none" stroke="#0a1730" strokeWidth="2.5" />
            <text x="530" y="527" textAnchor="middle" fontSize="12" fontWeight="800" fill="#00356b" fontFamily="Fraunces, Georgia, serif">
              Y
            </text>

            {/* laptop -> all products */}
            <Hotspot spot={SPOTS.laptop} {...hsProps}>
              <path d="M342 432 L488 432 L488 528 L342 528 Z" fill="#1c1c22" />
              <rect x="350" y="440" width="130" height="80" rx="3" fill="url(#screen)" className="screen" />
              <rect x="358" y="448" width="40" height="6" rx="2" fill="#f5efe4" opacity="0.9" />
              {[0, 1, 2].map((c) =>
                [0, 1].map((r) => <rect key={`${c}${r}`} x={358 + c * 40} y={462 + r * 28} width="32" height="22" rx="2" fill="#f5efe4" opacity={0.25 + 0.15 * ((c + r) % 2)} />),
              )}
              <path d="M326 528 L504 528 L516 540 L314 540 Z" fill="#2b2b33" />
            </Hotspot>
          </g>

          {/* ---------- layer 3: chair with the hoodie + the bulldog ---------- */}
          <g className="layer" style={layer(1)}>
            {/* chair base */}
            <ellipse cx="752" cy="842" rx="150" ry="16" fill="#000" opacity="0.35" />
            <path d="M752 690 L752 790 M752 790 L640 826 M752 790 L864 826 M752 790 L700 840 M752 790 L806 840" stroke="#1d2129" strokeWidth="12" strokeLinecap="round" />
            {[[640, 830], [864, 830], [700, 846], [806, 846]].map(([x, y], i) => (
              <circle key={i} cx={x} cy={y} r="10" fill="#111" />
            ))}
            <rect x="740" y="640" width="24" height="60" fill="#2a2f3a" />
            <rect x="612" y="616" width="280" height="44" rx="18" fill="#2c3340" />
            <rect x="660" y="372" width="184" height="252" rx="40" fill="#2c3340" />

            {/* the hero hoodie, draped over the chair -> Hoodies */}
            <Hotspot spot={SPOTS.hoodie} {...hsProps}>
              {/* hood hanging behind the chair back */}
              <path d="M690 380 Q690 326 752 322 Q814 326 814 380 Q790 352 752 352 Q714 352 690 380 Z" fill="#00254a" stroke="#00142b" strokeWidth="3" />
              {/* sleeves dangling down the sides */}
              <path d="M650 398 Q616 470 622 610 Q634 622 650 612 Q652 500 680 430 Z" fill="#003063" stroke="#00142b" strokeWidth="3" />
              <path d="M854 398 Q888 470 882 610 Q870 622 854 612 Q852 500 824 430 Z" fill="#003063" stroke="#00142b" strokeWidth="3" />
              <rect x="618" y="596" width="36" height="22" rx="6" fill="#00254a" />
              <rect x="850" y="596" width="36" height="22" rx="6" fill="#00254a" />
              {/* body */}
              <path d="M650 396 Q700 368 752 372 Q804 368 854 396 L846 574 Q752 594 658 574 Z" fill="#00356b" stroke="#00142b" strokeWidth="3" />
              {/* drawstrings */}
              <path d="M734 378 L728 436 M770 378 L776 436" stroke="#f5efe4" strokeWidth="4" strokeLinecap="round" />
              <circle cx="728" cy="440" r="4" fill="#f5efe4" />
              <circle cx="776" cy="440" r="4" fill="#f5efe4" />
              <text x="752" y="496" textAnchor="middle" fill="#f5efe4" fontFamily="Fraunces, Georgia, serif" fontWeight="800" fontSize="52" letterSpacing="3">
                YALE
              </text>
              {/* kangaroo pocket + ribbed hem */}
              <path d="M694 520 L810 520 L822 560 L682 560 Z" fill="#003063" stroke="#00142b" strokeWidth="2" />
              <path d="M658 566 Q752 586 846 566" fill="none" stroke="#00254a" strokeWidth="10" />
            </Hotspot>

            {/* the bulldog -> opens the chat */}
            <Hotspot spot={SPOTS.bulldog} {...hsProps}>
              <ellipse cx="1032" cy="834" rx="88" ry="14" fill="#000" opacity="0.3" />
              <path d="M968 830 Q960 744 1032 734 Q1104 744 1096 830 Z" fill="#d9a066" stroke="#2b1d14" strokeWidth="3" />
              <ellipse cx="1032" cy="790" rx="34" ry="42" fill="#f6e6cf" />
              <ellipse cx="996" cy="830" rx="20" ry="10" fill="#d9a066" stroke="#2b1d14" strokeWidth="3" />
              <ellipse cx="1068" cy="830" rx="20" ry="10" fill="#d9a066" stroke="#2b1d14" strokeWidth="3" />
              {/* head */}
              <path d="M1032 652 C1068 652 1088 666 1090 690 C1092 708 1084 720 1072 726 C1066 736 1052 740 1042 736 Q1032 740 1022 736 C1012 740 998 736 992 726 C980 720 972 708 974 690 C976 666 996 652 1032 652 Z" fill="#d9a066" stroke="#2b1d14" strokeWidth="3" />
              <path d="M998 662 Q978 652 964 664 Q968 672 976 672 Q980 684 990 678 Z M1066 662 Q1086 652 1100 664 Q1096 672 1088 672 Q1084 684 1074 678 Z" fill="#b9824a" stroke="#2b1d14" strokeWidth="2.5" />
              <path d="M1002 712 C1002 700 1018 696 1032 698 C1046 696 1062 700 1062 712 C1062 726 1050 734 1042 732 Q1032 736 1022 732 C1014 734 1002 726 1002 712 Z" fill="#f6e6cf" />
              <circle cx="1010" cy="686" r="5.5" fill="#2b1d14" />
              <circle cx="1054" cy="686" r="5.5" fill="#2b1d14" />
              <circle cx="1012" cy="684" r="1.8" fill="#fff" />
              <circle cx="1056" cy="684" r="1.8" fill="#fff" />
              <path d="M1022 700 Q1032 694 1042 700 Q1042 708 1032 709 Q1022 708 1022 700 Z" fill="#2b1d14" />
              <path d="M1018 718 Q1032 730 1046 718" fill="none" stroke="#2b1d14" strokeWidth="2.5" strokeLinecap="round" />
              <rect x="1025" y="716" width="4" height="5" rx="1" fill="#fff" />
              <rect x="1035" y="716" width="4" height="5" rx="1" fill="#fff" />
              {/* navy collar + gold tag */}
              <path d="M992 740 Q1032 756 1072 740" fill="none" stroke="#00356b" strokeWidth="9" strokeLinecap="round" />
              <circle cx="1032" cy="758" r="8" fill="#e9edf2" stroke="#aab2bd" strokeWidth="2" />
            </Hotspot>
          </g>

          {/* pulsing markers so shoppers know what's clickable */}
          <g className="markers" style={layer(0.75)}>
            {Object.values(SPOTS).map((s) => (
              <g key={s.id} className={`marker marker-${s.id}`} transform={`translate(${s.mark.x} ${s.mark.y})`}>
                <circle r="16" className="marker-ring" />
                <circle r="6" className="marker-dot" />
              </g>
            ))}
          </g>
        </g>
      </svg>

      <div className="dorm-copy">
        <h1>
          Step into your
          <br />
          <em>Yale</em> room.
        </h1>
        <p>Everything in here is for sale. Click anything that glows.</p>
      </div>
      <div className="dorm-actions">
          <button className="btn btn-gold" onClick={() => go(SPOTS.hoodie)}>
            Start with the hoodie
          </button>
          <Link to="/products" className="btn btn-ghost-light">
            Skip to the shop
          </Link>
      </div>

      <div className={`dorm-hint ${hint ? '' : 'is-hidden'}`}>Move your mouse to look around. Click any glowing object.</div>
      <div className="dorm-curtain" aria-hidden />
    </section>
  )
}
