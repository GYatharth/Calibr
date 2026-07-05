import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import client from '../api/client'

export default function Breakdown() {
  const { candidateId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchBreakdown()
  }, [candidateId])

  async function fetchBreakdown() {
    try {
      const res = await client.get(`/candidates/${candidateId}/breakdown`)
      setData(res.data)
    } catch (err) {
      setError('Failed to load breakdown')
    } finally {
      setLoading(false)
    }
  }

  const card = {
    background: '#e5dfd2',
    border: '1px solid #c8bea8',
    borderRadius: '8px',
    padding: '24px',
    marginBottom: '16px',
  }

  function SignalRow({ label, score, weight, contribution }) {
    const color = score > 60 ? '#3a6b2a' : score > 35 ? '#8b7a2a' : '#8b3a2a'
    const bg = score > 60 ? '#e8f0e5' : score > 35 ? '#f0ece0' : '#f5e8e5'
    const border = score > 60 ? '#a8c8a0' : score > 35 ? '#c8c0a0' : '#c8a898'
    return (
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', color: '#6b5e47', letterSpacing: '1px' }}>{label}</span>
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', color: '#9c8e76' }}>weight: {weight}</span>
            <span style={{ fontSize: '11px', color: '#9c8e76' }}>contribution: {contribution.toFixed(1)}</span>
            <span style={{
              background: bg, border: `1px solid ${border}`, color,
              borderRadius: '6px', padding: '3px 10px',
              fontFamily: 'Georgia, serif', fontSize: '16px', fontWeight: '500',
            }}>
              {score.toFixed(1)}
            </span>
          </div>
        </div>
        <div style={{ height: '5px', background: '#c8bea8', borderRadius: '3px' }}>
          <div style={{
            height: '5px', width: `${score}%`, background: color,
            borderRadius: '3px', transition: 'width 0.6s ease'
          }} />
        </div>
      </div>
    )
  }

  return (
    <Layout>
      <div style={{ marginBottom: '28px' }}>
        <button
          onClick={() => navigate(-1)}
          style={{ background: 'none', border: 'none', color: '#9c8e76', cursor: 'pointer', fontSize: '13px', padding: 0, marginBottom: '8px', display: 'block' }}
        >
          ← Back
        </button>
        <h2 style={{ fontFamily: 'Georgia, serif', fontSize: '22px', color: '#2c2416', margin: 0, letterSpacing: '1px' }}>
          Score Breakdown
        </h2>
        <p style={{ color: '#9c8e76', fontSize: '13px', marginTop: '4px' }}>
          Candidate #{candidateId} — full signal analysis
        </p>
      </div>

      {error && (
        <div style={{ background: '#f5e8e5', border: '1px solid #c8a898', color: '#8b3a2a', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <p style={{ color: '#9c8e76' }}>Loading...</p>
      ) : data && (
        <>
          {/* Composite score hero */}
          <div style={{ ...card, textAlign: 'center', padding: '40px' }}>
            <p style={{ fontSize: '10px', color: '#9c8e76', letterSpacing: '2px', margin: '0 0 8px' }}>
              COMPOSITE ATS SCORE
            </p>
            <p style={{ fontFamily: 'Georgia, serif', fontSize: '64px', color: '#2c2416', margin: '0 0 4px', fontWeight: '500', lineHeight: 1 }}>
              {data.composite_score.toFixed(1)}
            </p>
            <p style={{ fontSize: '13px', color: '#9c8e76', margin: '0 0 24px' }}>out of 100</p>
            <div style={{ height: '6px', background: '#c8bea8', borderRadius: '3px' }}>
              <div style={{
                height: '6px', width: `${data.composite_score}%`,
                background: data.composite_score > 60 ? '#3a6b2a' : data.composite_score > 35 ? '#8b7a2a' : '#8b3a2a',
                borderRadius: '3px'
              }} />
            </div>
          </div>

          {/* Signal breakdown */}
          <div style={card}>
            <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', marginTop: 0, fontSize: '16px', marginBottom: '20px' }}>
              Signal Breakdown
            </h3>
            <SignalRow
              label="SKILL MATCH"
              score={data.signal_breakdown.skill_match.score}
              weight={data.signal_breakdown.skill_match.weight}
              contribution={data.signal_breakdown.skill_match.contribution}
            />
            <SignalRow
              label="SEMANTIC SIMILARITY"
              score={data.signal_breakdown.semantic_similarity.score}
              weight={data.signal_breakdown.semantic_similarity.weight}
              contribution={data.signal_breakdown.semantic_similarity.contribution}
            />
            <SignalRow
              label="EXPERIENCE RELEVANCE"
              score={data.signal_breakdown.experience_relevance.score}
              weight={data.signal_breakdown.experience_relevance.weight}
              contribution={data.signal_breakdown.experience_relevance.contribution}
            />
            {/* Formula */}
            <div style={{ marginTop: '16px', padding: '12px 16px', background: '#f0ebe0', borderRadius: '6px', border: '1px solid #c8bea8' }}>
              <p style={{ fontSize: '12px', color: '#6b5e47', margin: 0, fontFamily: 'Georgia, serif' }}>
                {data.signal_breakdown.skill_match.contribution.toFixed(1)} + {data.signal_breakdown.semantic_similarity.contribution.toFixed(1)} + {data.signal_breakdown.experience_relevance.contribution.toFixed(1)} = <strong>{data.composite_score.toFixed(1)}</strong>
              </p>
            </div>
          </div>

          {/* Skills */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div style={card}>
              <h3 style={{ fontFamily: 'Georgia, serif', color: '#3a6b2a', marginTop: 0, fontSize: '15px' }}>
                Matched ({data.matched_skills.length})
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {data.matched_skills.map(s => (
                  <span key={s} style={{
                    background: '#e8f0e5', border: '1px solid #a8c8a0',
                    borderRadius: '4px', padding: '3px 10px',
                    fontSize: '12px', color: '#3a6b2a'
                  }}>{s}</span>
                ))}
                {data.matched_skills.length === 0 && (
                  <span style={{ color: '#9c8e76', fontSize: '13px' }}>None matched</span>
                )}
              </div>
            </div>
            <div style={card}>
              <h3 style={{ fontFamily: 'Georgia, serif', color: '#8b3a2a', marginTop: 0, fontSize: '15px' }}>
                Missing ({data.missing_skills.length})
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {data.missing_skills.map(s => (
                  <span key={s} style={{
                    background: '#f5e8e5', border: '1px solid #c8a898',
                    borderRadius: '4px', padding: '3px 10px',
                    fontSize: '12px', color: '#8b3a2a'
                  }}>{s}</span>
                ))}
                {data.missing_skills.length === 0 && (
                  <span style={{ color: '#9c8e76', fontSize: '13px' }}>None missing</span>
                )}
              </div>
            </div>
          </div>

          {/* Explanation */}
          {data.explanation && (
            <div style={card}>
              <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', marginTop: 0, fontSize: '16px' }}>
                Analysis
              </h3>
              <p style={{ color: '#6b5e47', fontSize: '14px', lineHeight: '1.8', margin: 0 }}>
                {data.explanation}
              </p>
            </div>
          )}

          {/* Meta */}
          <div style={{ textAlign: 'center', padding: '16px 0' }}>
            <p style={{ fontSize: '11px', color: '#9c8e76', letterSpacing: '1px' }}>
              JD #{data.jd_id} · EXPERIENCE {data.total_experience_months} MONTHS · SCORED {new Date(data.scored_at).toLocaleDateString()}
            </p>
          </div>
        </>
      )}
    </Layout>
  )
}