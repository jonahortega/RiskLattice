import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Welcome from './pages/Welcome'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import TickerDetail from './pages/TickerDetail'
import './App.css'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Welcome />} />
        <Route path="/home" element={<Home />} />
        <Route path="/watchlist" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/ticker/:symbol" element={<TickerDetail />} />
      </Routes>
    </Router>
  )
}

export default App

