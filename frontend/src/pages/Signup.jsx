import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import client from '../api/client'

export default function Signup() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSignup(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await client.post('/auth/signup', { email, password })
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)
      const res = await client.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      localStorage.setItem('access_token', res.data.access_token)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', background: '#f0ebe0',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px'
    }}>
      <div style={{ width: '100%', maxWidth: '400px' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h1 style={{
            fontFamily: 'Georgia, serif', fontSize: '36px',
            color: '#2c2416', letterSpacing: '4px', margin: 0
          }}>CALIBR</h1>
          <p style={{ color: '#9c8e76', fontSize: '13px', marginTop: '6px', letterSpacing: '1px' }}>
            HYBRID RESUME SCREENING
          </p>
        </div>

        <div style={{
          background: '#e5dfd2', borderRadius: '8px',
          padding: '32px', border: '1px solid #c8bea8'
        }}>
          <h2 style={{
            fontFamily: 'Georgia, serif', fontSize: '18px',
            color: '#2c2416', marginTop: 0, marginBottom: '24px'
          }}>Create account</h2>

          {error && (
            <div style={{
              background: '#f5e8e5', border: '1px solid #c8a898',
              color: '#8b3a2a', padding: '10px 14px',
              borderRadius: '6px', fontSize: '13px', marginBottom: '16px'
            }}>{error}</div>
          )}

          <form onSubmit={handleSignup}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: '#6b5e47', letterSpacing: '1px', marginBottom: '6px' }}>
                EMAIL
              </label>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)} required
                placeholder="you@example.com"
                style={{
                  width: '100%', background: '#f0ebe0', border: '1px solid #c8bea8',
                  borderRadius: '6px', padding: '10px 12px', fontSize: '14px',
                  color: '#2c2416', outline: 'none', boxSizing: 'border-box'
                }}
              />
            </div>
            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: '#6b5e47', letterSpacing: '1px', marginBottom: '6px' }}>
                PASSWORD
              </label>
              <input
                type="password" value={password} onChange={e => setPassword(e.target.value)} required
                placeholder="••••••••"
                style={{
                  width: '100%', background: '#f0ebe0', border: '1px solid #c8bea8',
                  borderRadius: '6px', padding: '10px 12px', fontSize: '14px',
                  color: '#2c2416', outline: 'none', boxSizing: 'border-box'
                }}
              />
            </div>
            <button
              type="submit" disabled={loading}
              style={{
                width: '100%', background: loading ? '#9c8e76' : '#2c2416',
                color: '#f0ebe0', border: 'none', borderRadius: '6px',
                padding: '11px', fontSize: '12px', fontWeight: '500',
                letterSpacing: '2px', cursor: loading ? 'default' : 'pointer',
              }}
            >
              {loading ? 'CREATING...' : 'CREATE ACCOUNT'}
            </button>
          </form>

          <p style={{ textAlign: 'center', color: '#9c8e76', fontSize: '13px', marginTop: '20px', marginBottom: 0 }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: '#6b5e47', textDecoration: 'underline' }}>
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}