import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Score from './pages/Score'
import Rankings from './pages/Rankings'
import Breakdown from './pages/Breakdown'

function PrivateRoute({ children }) {
  const token = localStorage.getItem('access_token')
  return token ? children : <Navigate to="/login" />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/score" element={<PrivateRoute><Score /></PrivateRoute>} />
        <Route path="/rankings/:jdId" element={<PrivateRoute><Rankings /></PrivateRoute>} />
        <Route path="/breakdown/:candidateId" element={<PrivateRoute><Breakdown /></PrivateRoute>} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  )
}