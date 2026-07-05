import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import client from '../api/client'

export default function Dashboard() {
  const [jds, setJds] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [jdText, setJdText] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchJds()
  }, [])

  async function fetchJds() {
    try {
      const res = await client.get('/jd')
      setJds(res.data)
    } catch (err) {
      setError('Failed to load job descriptions')
    } finally {
      setLoading(false)
    }
  }

  async function createJd(e) {
    e.preventDefault()
    setCreating(true)
    setError('')
    try {
      await client.post('/jd', { raw_text: jdText })
      setJdText('')
      setShowForm(false)
      fetchJds()
    } catch (err) {
      setError('Failed to create JD')
    } finally {
      setCreating(false)
    }
  }

  const card = {
    background: '#e5dfd2',
    border: '1px solid #c8bea8',
    borderRadius: '8px',
    padding: '20px 24px',
    marginBottom: '12px',
  }

  return (
    <Layout>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h2 style={{ fontFamily: 'Georgia, serif', fontSize: '22px', color: '#2c2416', margin: 0, letterSpacing: '1px' }}>
            Job Descriptions
          </h2>
          <p style={{ color: '#9c8e76', fontSize: '13px', marginTop: '4px' }}>
            Upload a JD to start screening candidates
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            background: '#2c2416', color: '#f0ebe0', border: 'none',
            borderRadius: '6px', padding: '8px 20px', fontSize: '12px',
            letterSpacing: '1px', cursor: 'pointer',
          }}
        >
          + NEW JD
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{ background: '#f5e8e5', border: '1px solid #c8a898', color: '#8b3a2a', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {/* New JD form */}
      {showForm && (
        <div style={{ ...card, marginBottom: '24px' }}>
          <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', marginTop: 0, fontSize: '16px' }}>
            New Job Description
          </h3>
          <form onSubmit={createJd}>
            <textarea
              value={jdText}
              onChange={e => setJdText(e.target.value)}
              required
              rows={8}
              placeholder="Paste the full job description here..."
              style={{
                width: '100%', background: '#f0ebe0', border: '1px solid #c8bea8',
                borderRadius: '6px', padding: '12px', fontSize: '13px',
                color: '#2c2416', outline: 'none', resize: 'vertical',
                boxSizing: 'border-box', fontFamily: 'system-ui, sans-serif',
                lineHeight: '1.6',
              }}
            />
            <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
              <button
                type="submit" disabled={creating}
                style={{
                  background: creating ? '#9c8e76' : '#2c2416', color: '#f0ebe0',
                  border: 'none', borderRadius: '6px', padding: '8px 20px',
                  fontSize: '12px', letterSpacing: '1px', cursor: creating ? 'default' : 'pointer',
                }}
              >
                {creating ? 'SAVING...' : 'SAVE JD'}
              </button>
              <button
                type="button" onClick={() => setShowForm(false)}
                style={{
                  background: 'none', color: '#6b5e47', border: '1px solid #c8bea8',
                  borderRadius: '6px', padding: '8px 20px', fontSize: '12px',
                  letterSpacing: '1px', cursor: 'pointer',
                }}
              >
                CANCEL
              </button>
            </div>
          </form>
        </div>
      )}

      {/* JD list */}
      {loading ? (
        <p style={{ color: '#9c8e76', fontSize: '14px' }}>Loading...</p>
      ) : jds.length === 0 ? (
        <div style={{ ...card, textAlign: 'center', padding: '48px' }}>
          <p style={{ color: '#9c8e76', fontSize: '14px', margin: 0 }}>
            No job descriptions yet. Create one to get started.
          </p>
        </div>
      ) : (
        jds.map(jd => (
          <div key={jd.id} style={card}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', color: '#9c8e76', letterSpacing: '1px' }}>JD #{jd.id}</span>
                  <span style={{ fontSize: '11px', color: '#9c8e76' }}>•</span>
                  <span style={{ fontSize: '11px', color: '#9c8e76' }}>
                    {jd.required_skills?.length || 0} skills detected
                  </span>
                </div>
                <p style={{ color: '#2c2416', fontSize: '13px', margin: '0 0 10px', lineHeight: '1.5' }}>
                  {jd.raw_text.slice(0, 120)}...
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {(jd.required_skills || []).slice(0, 6).map(skill => (
                    <span key={skill} style={{
                      background: '#f0ebe0', border: '1px solid #c8bea8',
                      borderRadius: '4px', padding: '2px 8px',
                      fontSize: '11px', color: '#6b5e47', letterSpacing: '0.5px',
                    }}>{skill}</span>
                  ))}
                  {(jd.required_skills || []).length > 6 && (
                    <span style={{ fontSize: '11px', color: '#9c8e76', padding: '2px 4px' }}>
                      +{jd.required_skills.length - 6} more
                    </span>
                  )}
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginLeft: '20px' }}>
                <button
                  onClick={() => navigate(`/rankings/${jd.id}`)}
                  style={{
                    background: '#2c2416', color: '#f0ebe0', border: 'none',
                    borderRadius: '6px', padding: '6px 14px', fontSize: '11px',
                    letterSpacing: '1px', cursor: 'pointer', whiteSpace: 'nowrap',
                  }}
                >
                  VIEW RANKINGS
                </button>
                <button
                  onClick={() => navigate('/score', { state: { jdId: jd.id } })}
                  style={{
                    background: 'none', color: '#6b5e47', border: '1px solid #c8bea8',
                    borderRadius: '6px', padding: '6px 14px', fontSize: '11px',
                    letterSpacing: '1px', cursor: 'pointer', whiteSpace: 'nowrap',
                  }}
                >
                  SCORE RESUME
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </Layout>
  )
}