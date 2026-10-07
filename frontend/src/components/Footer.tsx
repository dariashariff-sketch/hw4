import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-hero">
        <p className="footer-word">
          Boola <em>Boola.</em>
        </p>
        <Link to="/products" className="btn btn-gold btn-lg">
          Shop the collection
        </Link>
      </div>
      <div className="footer-inner">
        <div>
          <div className="brand footer-brand">
            <span className="brand-mark">CC</span> Campus Customs
          </div>
          <p>Bulldog pride, stitched in New Haven.</p>
        </div>
        <div>
          <h4>Shop</h4>
          <Link to="/products">All products</Link>
          <Link to="/products?category=Hoodies">Hoodies</Link>
          <Link to="/products?category=Crewnecks">Crewnecks</Link>
          <Link to="/products?category=T-Shirts">T-Shirts</Link>
        </div>
        <div>
          <h4>Visit</h4>
          <span>57 Broadway, New Haven, CT</span>
          <span>(475) 301-4205</span>
          <span>orderdept@campuscustoms.com</span>
        </div>
        <div>
          <h4>Help</h4>
          <Link to="/about">About us</Link>
          <span>30-day returns on unworn items</span>
          <span>Custom pieces are final sale</span>
        </div>
      </div>
      <div className="footer-base">© {new Date().getFullYear()} Campus Customs · Officially licensed Yale merchandise</div>
    </footer>
  )
}
