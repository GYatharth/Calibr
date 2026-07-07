import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import client from '../api/client'

export default function Rankings() {
  const { jdId } = useParams()
  const navigate = useNavigate()
  const [rankings, setRankings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchRankings()
  }, [jdId])

  async function fetchRankings() {
    try {
      const res = await client.get(`/rankings/${jdId}`)
      setRankings(res.data)
    } catch (err) {
      setError('Failed to load rankings')
    } finally {
      setLoading(false)
    }
  }

  const card = {
    background: '#e5dfd2',
    border: '1px solid #c8bea8',
    borderRadius: '8px',
    padding: '20px 24px',
    marginBottom: '10px',
  }

  function ScorePill({ score }) {
    const color = score > 60 ? '#3a6b2a' : score > 35 ? '#8b7a2a' : '#8b3a2a'
    const bg = score > 60 ? '#e8f0e5' : score > 35 ? '#f0ece0' : '#f5e8e5'
    const border = score > 60 ? '#a8c8a0' : score > 35 ? '#c8c0a0' : '#c8a898'
    return (
      <span style={{
        background: bg, border: `1px solid ${border}`,
        color, borderRadius: '6px', padding: '4px 12px',
        fontFamily: 'Georgia, serif', fontSize: '18px', fontWeight: '500',
        minWidth: '60px', display: 'inline-block', textAlign: 'center'
      }}>
        {score.toFixed(1)}
      </span>
    )
  }

  return (
    <Layout>
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px' }}>
          <button
            onClick={() => navigate('/dashboard')}
            style={{ background: 'none', border: 'none', color: '#9c8e76', cursor: 'pointer', fontSize: '13px', padding: 0 }}
          >
            ← Dashboard
          </button>
        </div>
        <h2 style={{ fontFamily: 'Georgia, serif', fontSize: '22px', color: '#2c2416', margin: 0, letterSpacing: '1px' }}>
          Rankings — JD #{jdId}
        </h2>
        <p style={{ color: '#9c8e76', fontSize: '13px', marginTop: '4px' }}>
          Candidates ranked by composite ATS score
        </p>
      </div>

      {error && (
        <div style={{ background: '#f5e8e5', border: '1px solid #c8a898', color: '#8b3a2a', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <p style={{ color: '#9c8e76' }}>Loading rankings...</p>
      ) : rankings?.candidates?.length === 0 ? (
        <div style={{ ...card, textAlign: 'center', padding: '48px' }}>
          <p style={{ color: '#9c8e76', fontSize: '14px', margin: 0 }}>
            No candidates scored yet.
          </p>
        </div>
      ) : (
        <>
          {/* Summary stats */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '24px' }}>
            {[
              { label: 'TOTAL CANDIDATES', value: rankings?.total_candidates },
              { label: 'TOP SCORE', value: rankings?.candidates?.[0]?.composite_score?.toFixed(1) },
              { label: 'AVG SCORE', value: (rankings?.candidates?.reduce((a, c) => a + c.composite_score, 0) / rankings?.candidates?.length).toFixed(1) }
            ].map(stat => (
              <div key={stat.label} style={{ background: '#e5dfd2', border: '1px solid #c8bea8', borderRadius: '8px', padding: '16px 20px' }}>
                <p style={{ fontSize: '10px', color: '#9c8e76', letterSpacing: '1.5px', margin: '0 0 6px' }}>{stat.label}</p>
                <p style={{ fontFamily: 'Georgia, serif', fontSize: '28px', color: '#2c2416', margin: 0, fontWeight: '500' }}>{stat.value}</p>
              </div>
            ))}
          </div>

          {/* Candidate list */}
          {rankings?.candidates?.map(candidate => (
            <div key={candidate.candidate_id} style={card}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1 }}>
                  {/* Rank badge */}
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '50%',
                    background: candidate.rank === 1 ? '#2c2416' : '#f0ebe0',
                    border: '1px solid #c8bea8',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontFamily: 'Georgia, serif', fontSize: '14px',
                    color: candidate.rank === 1 ? '#f0ebe0' : '#6b5e47',
                    flexShrink: 0,
                  }}>
                    {candidate.rank}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '12px', color: '#6b5e47', letterSpacing: '0.5px' }}>
                        Candidate #{candidate.candidate_id}
                      </span>
                      <span style={{ fontSize: '11px', color: '#9c8e76' }}>•</span>
                      <span style={{ fontSize: '11px', color: '#9c8e76' }}>
                        Skill {candidate.skill_score.toFixed(0)} · Semantic {candidate.semantic_score.toFixed(0)} · Exp {candidate.experience_score.toFixed(0)}
                      </span>
                    </div>

                    {/* AI one-line summary */}
                    {candidate.candidate_summary && (
                      <p style={{
                        fontSize: '13px', color: '#4a3c2a', margin: '0 0 8px',
                        fontStyle: 'italic', lineHeight: '1.4',
                      }}>
                        "{candidate.candidate_summary}"
                      </p>
                    )}

                    {/* Skill tags */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {candidate.matched_skills.slice(0, 5).map(s => (
                        <span key={s} style={{
                          background: '#e8f0e5', border: '1px solid #a8c8a0',
                          borderRadius: '3px', padding: '1px 6px',
                          fontSize: '10px', color: '#3a6b2a'
                        }}>{s}</span>
                      ))}
                      {candidate.missing_skills.slice(0, 3).map(s => (
                        <span key={s} style={{
                          background: '#f5e8e5', border: '1px solid #c8a898',
                          borderRadius: '3px', padding: '1px 6px',
                          fontSize: '10px', color: '#8b3a2a'
                        }}>{s}</span>
                      ))}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <ScorePill score={candidate.composite_score} />
                  <button
                    onClick={() => navigate(`/breakdown/${candidate.candidate_id}`)}
                    style={{
                      background: 'none', color: '#6b5e47', border: '1px solid #c8bea8',
                      borderRadius: '6px', padding: '6px 14px', fontSize: '11px',
                      letterSpacing: '1px', cursor: 'pointer', whiteSpace: 'nowrap',
                    }}
                  >
                    BREAKDOWN →
                  </button>
                </div>
              </div>
            </div>
          ))}
        </>
      )}
    </Layout>
  )
}