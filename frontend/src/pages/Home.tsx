import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchCategories, fetchProducts, money, type Category, type Product } from '../api'
import CategoryImage from '../components/CategoryImage'
import DormRoom from '../components/DormRoom'
import Reveal from '../components/Reveal'

// Hand-picked spread across categories for the editorial "lookbook" section.
const FEATURED = [
  'basic-hoodie-big-yale',
  'district-vit-crewneck-vintage-bulldog',
  'berkeley-1-4-zip',
  '2025-yale-vs-harvard-t-shirt',
]

const MARQUEE = ['Boola Boola', 'Officially licensed', '57 Broadway', 'Bulldog pride', 'New Haven, CT', 'Every college, every team']

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])

  useEffect(() => {
    fetchProducts()
      .then((all) => setFeatured(FEATURED.map((id) => all.find((p) => p.product_id === id)).filter((p): p is Product => !!p)))
      .catch(() => setFeatured([]))
    fetchCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  return (
    <>
      <DormRoom />

      <div className="marquee" aria-hidden>
        <div className="marquee-track">
          {[...MARQUEE, ...MARQUEE, ...MARQUEE].map((m, i) => (
            <span key={i}>
              {m}
              <i className="marquee-dot" />
            </span>
          ))}
        </div>
      </div>

      <section className="section">
        <Reveal className="section-head">
          <div>
            <span className="kicker">01 / Shop by style</span>
            <h2 className="display">
              Find your <em>fit</em>.
            </h2>
          </div>
          <Link to="/products" className="link-arrow">
            View everything
          </Link>
        </Reveal>
        <div className="cat-grid">
          {categories.map((c, i) => (
            <Reveal key={c.name} delay={i * 70}>
              <Link to={`/products?category=${encodeURIComponent(c.name)}`} className="cat-tile">
                <CategoryImage name={c.name} />
                <strong>{c.name}</strong>
                <small>{c.count} styles</small>
              </Link>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="section lookbook">
        <Reveal className="section-head">
          <div>
            <span className="kicker">02 / The lookbook</span>
            <h2 className="display">
              Picked for <em>you</em>.
            </h2>
          </div>
        </Reveal>
        <div className="lookbook-grid">
          {featured.map((p, i) => (
            <Reveal key={p.product_id} delay={i * 90} className={`look look-${i}`}>
              <Link to={`/products/${p.product_id}`} className="look-link">
                <div className="look-img">
                  <img src={p.image_url} alt={p.name} loading="lazy" />
                </div>
                <div className="look-meta">
                  <span className="look-num">{String(i + 1).padStart(2, '0')}</span>
                  <div>
                    <h3>{p.name}</h3>
                    <span className="muted">{p.category}</span>
                  </div>
                  <span className="price">{money(p.price)}</span>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="story-band">
        <Reveal className="story-inner">
          <span className="kicker kicker-light">03 / Since you asked</span>
          <h2 className="display display-light">
            Not sure what you want?
            <br />
            <em>Just ask.</em>
          </h2>
          <p>
            Our shopping assistant knows every style, size, and price we carry, live from our inventory. Tell it who you're
            shopping for and it will lay the options out right on the page.
          </p>
        </Reveal>
      </section>

      <section className="section values">
        {[
          ['Officially licensed', 'Real Yale marks on every piece. No knockoffs, ever.'],
          ['Local to campus', 'Visit our shop at 57 Broadway, steps from Old Campus.'],
          ['Easy returns', '30 days to send back unworn items with tags on.'],
        ].map(([t, d], i) => (
          <Reveal key={t} delay={i * 90} className="value">
            <span className="value-num">0{i + 1}</span>
            <h3>{t}</h3>
            <p>{d}</p>
          </Reveal>
        ))}
      </section>
    </>
  )
}
