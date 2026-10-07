import { Link } from 'react-router-dom'
import Reveal from '../components/Reveal'

export default function About() {
  return (
    <>
      <section className="page-hero">
        <div className="page-hero-inner">
          <span className="kicker kicker-light">About Campus Customs</span>
          <h1 className="display display-light">
            Made for the <em>Yale</em> family.
          </h1>
          <p>Students, alumni, parents, and the fans who just love New Haven are all welcome here.</p>
        </div>
      </section>

      <div className="page about">
        <Reveal as="section" className="about-split">
          <span className="kicker">Who we are</span>
          <p className="lead">
            Campus Customs is a neighborhood shop at 57 Broadway, a short walk from Old Campus. We sell officially licensed Yale
            apparel, and we think school spirit should feel as good as it looks: soft fleece, sturdy stitching, and designs
            you'll still want to wear long after graduation.
          </p>
        </Reveal>

        <section className="about-values">
          {[
            ['Pride for everyone', "There's something for first-years, proud grandparents, and everyone in between, from every residential college, team, and school."],
            ['Comfort first', "Classic cuts and cozy fabrics you'll reach for on cold New Haven mornings."],
            ['Straight answers', "The prices and stock on our site come from our live inventory. If a size is sold out, we'll tell you, and our chat assistant follows the same rule."],
          ].map(([t, d], i) => (
            <Reveal key={t} delay={i * 100} className="about-value">
              <span className="big-num">0{i + 1}</span>
              <h3>{t}</h3>
              <p>{d}</p>
            </Reveal>
          ))}
        </section>

        <Reveal as="section" className="about-split">
          <span className="kicker">Visit or reach out</span>
          <ul className="info-list">
            <li>
              57 Broadway, New Haven, CT
            </li>
            <li>
              (475) 301-4205
            </li>
            <li>
              orderdept@campuscustoms.com
            </li>
          </ul>
        </Reveal>

        <Reveal as="section" className="about-split">
          <span className="kicker">Returns, simply</span>
          <p>
            Changed your mind? Send unworn items back with their tags on within 30 days of shipping, and email your tracking
            number to our order team. Custom and final-sale pieces can't be returned. If we made a mistake with your order,
            we'll cover the return shipping.
          </p>
        </Reveal>

        <div className="cta-row">
          <Link to="/products" className="btn btn-primary btn-lg">
            Browse the collection
          </Link>
        </div>
      </div>
    </>
  )
}
