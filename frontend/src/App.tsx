import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Watchlist from './pages/Watchlist'
import AddProduct from './pages/AddProduct'
import Sales from './pages/Sales'
import Settings from './pages/Settings'
import ProductDetail from './pages/ProductDetail'
import AllProducts from './pages/AllProducts';

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode')
    return saved ? JSON.parse(saved) : false
  })

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode))
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  return (
    <Router>
      <Layout darkMode={darkMode} setDarkMode={setDarkMode}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/add" element={<AddProduct />} />
          <Route path="/sales" element={<Sales />} />
          <Route path="/settings" element={<Settings darkMode={darkMode} setDarkMode={setDarkMode} />} />
          <Route path="/product/:productId" element={<ProductDetail />} />
          <Route path="/all-products" element={<AllProducts />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App