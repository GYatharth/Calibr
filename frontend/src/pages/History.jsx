import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

export default function History() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchHistory()
  }, [])

  async function fetchHistory() {
    try {
      const res = await client.get('/history')
      setData(res.data)
    } catch (err) {
      setError('Failed to load history')
    } finally {
      setLoading(false)
    }
  }

  const card = {
    background: '#e5dfd2',
    border: '1px solid #c8bea8',
    borderRadius: '8px',
    padding: '20px 24px',
    marginBottom: '12px',
  }

  function ScoreBadge({ score }) {
    const color = score > 60 ? '#3a6b2a' : score > 35 ? '#8b7a2a' : '#8b3a2a'
    const bg = score > 60 ? '#e8f0e5' : score > 35 ? '#f0ece0' : '#f5e8e5'
    const border = score > 60 ? '#a8c8a0' : score > 35 ? '#c8c0a0' : '#c8a898'
    return (
      <span style={{
        background: bg, border: `1px solid ${border}`, color,
        borderRadius: '6px', padding: '4px 14px',
        fontFamily: 'Georgia, serif', fontSize: '20px', fontWeight: '500',
        minWidth: '60px', display: 'inline-block', textAlign: 'center'
      }}>
        {score.toFixed(1)}
      </span>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f0ebe0' }}>
      {/* Navbar */}
      <nav style={{
        borderBottom: '1px solid #c8bea8', background: '#e5dfd2',
        padding: '12px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between'
      }}>
        <span
          onClick={() => navigate('/candidate')}
          style={{ fontFamily: 'Georgia, serif', fontSize: '20px', color: '#2c2416', letterSpacing: '2px', cursor: 'pointer' }}
        >
          CALIBR
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <span
            onClick={() => navigate('/candidate')}
            style={{ fontSize: '13px', color: '#6b5e47', cursor: 'pointer', letterSpacing: '1px' }}
          >
            CHECK SCORE
          </span>
          <span style={{ fontSize: '13px', color: '#2c2416', letterSpacing: '1px', fontWeight: '500', borderBottom: '1px solid #2c2416' }}>
            HISTORY
          </span>
          <button
            onClick={() => { localStorage.removeItem('access_token'); localStorage.removeItem('user_role'); navigate('/login') }}
            style={{ background: 'none', border: '1px solid #c8bea8', borderRadius: '6px', padding: '4px 12px', fontSize: '12px', color: '#6b5e47', cursor: 'pointer', letterSpacing: '1px' }}
          >
            LOGOUT
          </button>
        </div>
      </nav>

      <main style={{ maxWidth: '760px', margin: '0 auto', padding: '40px 24px' }}>
        <div style={{ marginBottom: '28px' }}>
          <h2 style={{ fontFamily: 'Georgia, serif', fontSize: '22px', color: '#2c2416', margin: 0, letterSpacing: '1px' }}>
            Score History
          </h2>
          <p style={{ color: '#9c8e76', fontSize: '13px', marginTop: '4px' }}>
            All your previous ATS checks
          </p>
        </div>

        {error && (
          <div style={{ background: '#f5e8e5', border: '1px solid #c8a898', color: '#8b3a2a', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', marginBottom: '16px' }}>
            {error}
          </div>
        )}

        {loading ? (
          <p style={{ color: '#9c8e76' }}>Loading history...</p>
        ) : data && (
          <>
            {/* Summary stats */}
            {data.total_attempts > 0 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '24px' }}>
                {[
                  { label: 'TOTAL CHECKS', value: data.total_attempts },
                  { label: 'BEST SCORE', value: data.best_score },
                  { label: 'LATEST SCORE', value: data.latest_score },
                  { label: 'AVG SCORE', value: data.average_score },
                ].map(stat => (
                  <div key={stat.label} style={{ background: '#e5dfd2', border: '1px solid #c8bea8', borderRadius: '8px', padding: '14px 16px' }}>
                    <p style={{ fontSize: '9px', color: '#9c8e76', letterSpacing: '1.5px', margin: '0 0 4px' }}>{stat.label}</p>
                    <p style={{ fontFamily: 'Georgia, serif', fontSize: '24px', color: '#2c2416', margin: 0, fontWeight: '500' }}>{stat.value}</p>
                  </div>
                ))}
              </div>
            )}

            {data.total_attempts === 0 ? (
              <div style={{ ...card, textAlign: 'center', padding: '48px' }}>
                <p style={{ color: '#9c8e76', fontSize: '14px', margin: 0 }}>
                  No score history yet. Go check your ATS score first.
                </p>
                <button
                  onClick={() => navigate('/candidate')}
                  style={{ marginTop: '16px', background: '#2c2416', color: '#f0ebe0', border: 'none', borderRadius: '6px', padding: '8px 20px', fontSize: '12px', letterSpacing: '1px', cursor: 'pointer' }}
                >
                  CHECK MY SCORE
                </button>
              </div>
            ) : (
              data.history.map((entry, i) => (
                <div key={entry.candidate_id} style={card}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                        <span style={{ fontSize: '11px', color: '#9c8e76', letterSpacing: '0.5px' }}>
                          JD #{entry.jd_id}
                        </span>
                        <span style={{ fontSize: '11px', color: '#9c8e76' }}>•</span>
                        <span style={{ fontSize: '11px', color: '#9c8e76' }}>
                          {new Date(entry.scored_at).toLocaleDateString('en-IN', {
                            day: 'numeric', month: 'short', year: 'numeric'
                          })}
                        </span>
                        {i === 0 && (
                          <span style={{ fontSize: '10px', background: '#e8f0e5', border: '1px solid #a8c8a0', borderRadius: '3px', padding: '1px 6px', color: '#3a6b2a' }}>
                            LATEST
                          </span>
                        )}
                      </div>

                      {entry.candidate_summary && (
                        <p style={{ fontSize: '13px', color: '#4a3c2a', margin: '0 0 8px', fontStyle: 'italic' }}>
                          "{entry.candidate_summary}"
                        </p>
                      )}

                      {/* Mini signal bars */}
                      <div style={{ display: 'flex', gap: '12px', marginBottom: '8px' }}>
                        {[
                          { label: 'Skill', score: entry.skill_score },
                          { label: 'Semantic', score: entry.semantic_score },
                          { label: 'Exp', score: entry.experience_score },
                        ].map(sig => (
                          <div key={sig.label} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <span style={{ fontSize: '10px', color: '#9c8e76' }}>{sig.label}</span>
                            <div style={{ width: '40px', height: '4px', background: '#c8bea8', borderRadius: '2px' }}>
                              <div style={{
                                height: '4px', width: `${sig.score}%`,
                                background: sig.score > 60 ? '#3a6b2a' : sig.score > 35 ? '#8b7a2a' : '#8b3a2a',
                                borderRadius: '2px'
                              }} />
                            </div>
                            <span style={{ fontSize: '10px', color: '#6b5e47' }}>{sig.score.toFixed(0)}</span>
                          </div>
                        ))}
                      </div>

                      {/* Skills */}
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {entry.matched_skills.slice(0, 4).map(s => (
                          <span key={s} style={{ background: '#e8f0e5', border: '1px solid #a8c8a0', borderRadius: '3px', padding: '1px 6px', fontSize: '10px', color: '#3a6b2a' }}>{s}</span>
                        ))}
                        {entry.missing_skills.slice(0, 2).map(s => (
                          <span key={s} style={{ background: '#f5e8e5', border: '1px solid #c8a898', borderRadius: '3px', padding: '1px 6px', fontSize: '10px', color: '#8b3a2a' }}>{s}</span>
                        ))}
                      </div>
                    </div>

                    <div style={{ marginLeft: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                      <ScoreBadge score={entry.composite_score} />
                      <button
                        onClick={() => navigate(`/breakdown/${entry.candidate_id}`)}
                        style={{ background: 'none', color: '#6b5e47', border: '1px solid #c8bea8', borderRadius: '6px', padding: '4px 10px', fontSize: '10px', letterSpacing: '1px', cursor: 'pointer' }}
                      >
                        DETAILS
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </>
        )}
      </main>
    </div>
  )
}
