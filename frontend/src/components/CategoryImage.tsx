import { useEffect, useState } from 'react'

// Bulldog-per-category art lives in frontend/public/categories/<slug>.<ext>.
// Photos (png/jpg) win over the drawn SVGs from scripts/draw_bulldogs.py.
export const categorySlug = (name: string) =>
  name.toLowerCase().replace(/&/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

const EXTENSIONS = ['png', 'jpg', 'svg']

function firstLoadable(urls: string[]): Promise<string | null> {
  return urls.reduce<Promise<string | null>>(
    (found, url) =>
      found.then(
        (hit) =>
          hit ??
          new Promise((resolve) => {
            const img = new Image()
            img.onload = () => resolve(url)
            img.onerror = () => resolve(null)
            img.src = url
          }),
      ),
    Promise.resolve(null),
  )
}

export default function CategoryImage({ name }: { name: string }) {
  // undefined = still looking, null = nothing found
  const [src, setSrc] = useState<string | null | undefined>(undefined)

  useEffect(() => {
    let alive = true
    const slug = categorySlug(name)
    firstLoadable(EXTENSIONS.map((ext) => `/categories/${slug}.${ext}`)).then((url) => {
      if (alive) setSrc(url)
    })
    return () => {
      alive = false
    }
  }, [name])

  if (src === undefined) return <span className="cat-img" aria-hidden />
  if (src === null)
    return (
      <span className="cat-img cat-img-placeholder" aria-hidden>
        {name.charAt(0)}
      </span>
    )
  return <img className="cat-img" src={src} alt={`Bulldog wearing ${name.toLowerCase()}`} />
}
