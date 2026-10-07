import { useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import ChatWidget from './components/ChatWidget'
import Footer from './components/Footer'
import MiniCart from './components/MiniCart'
import Navbar from './components/Navbar'
import ResultsShelf from './components/ResultsShelf'
import About from './pages/About'
import Account from './pages/Account'
import Cart from './pages/Cart'
import Home from './pages/Home'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import ProductDetail from './pages/ProductDetail'
import Products from './pages/Products'
import Signup from './pages/Signup'

export default function App() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return (
    <div className={`app ${pathname === '/' ? 'is-home' : ''}`}>
      <Navbar />
      <main>
        <ResultsShelf />
        {/* keyed by path so every page change plays the fade-up transition */}
        <div className="route" key={pathname}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:id" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/account" element={<Account />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
        </div>
      </main>
      <Footer />
      <ChatWidget />
      <MiniCart />
    </div>
  )
}
