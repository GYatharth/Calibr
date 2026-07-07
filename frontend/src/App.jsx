import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Score from './pages/Score'
import Rankings from './pages/Rankings'
import Breakdown from './pages/Breakdown'
import Batch from './pages/Batch'
import CandidateDashboard from './pages/CandidateDashboard'

function PrivateRoute({ children, requiredRole }) {
  const token = localStorage.getItem('access_token')
  const role = localStorage.getItem('user_role')
  if (!token) return <Navigate to="/login" />
  if (requiredRole && role !== requiredRole) {
    return <Navigate to={role === 'recruiter' ? '/dashboard' : '/candidate'} />
  }
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* Recruiter routes */}
        <Route path="/dashboard" element={<PrivateRoute requiredRole="recruiter"><Dashboard /></PrivateRoute>} />
        <Route path="/score" element={<PrivateRoute requiredRole="recruiter"><Score /></PrivateRoute>} />
        <Route path="/batch" element={<PrivateRoute requiredRole="recruiter"><Batch /></PrivateRoute>} />
        <Route path="/rankings/:jdId" element={<PrivateRoute requiredRole="recruiter"><Rankings /></PrivateRoute>} />
        <Route path="/breakdown/:candidateId" element={<PrivateRoute requiredRole="recruiter"><Breakdown /></PrivateRoute>} />

        {/* Candidate routes */}
        <Route path="/candidate" element={<PrivateRoute requiredRole="candidate"><CandidateDashboard /></PrivateRoute>} />

        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  )
}