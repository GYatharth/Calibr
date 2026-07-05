import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import Layout from '../components/Layout'
import client from '../api/client'

export default function Score() {
  const location = useLocation()
  const navigate = useNavigate()
  const [jdId, setJdId] = useState(location.state?.jdId || '')
  const [resumeText, setResumeText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleScore(e) {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await client.post('/score', {
        jd_id: parseInt(jdId),
        resume_text: resumeText,
      })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Scoring failed')
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

  function ScoreBar({ label, score, weight }) {
    return (
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
          <span style={{ fontSize: '11px', color: '#6b5e47', letterSpacing: '1px' }}>{label}</span>
          <div style={{ display: 'flex', gap: '12px' }}>
            <span style={{ fontSize: '11px', color: '#9c8e76' }}>weight: {weight}</span>
            <span style={{ fontSize: '13px', fontWeight: '500', color: '#2c2416', fontFamily: 'Georgia, serif' }}>
              {score.toFixed(1)}
            </span>
          </div>
        </div>
        <div style={{ height: '4px', background: '#c8bea8', borderRadius: '2px' }}>
          <div style={{
            height: '4px', width: `${score}%`,
            background: score > 60 ? '#3a6b2a' : score > 35 ? '#8b7a2a' : '#8b3a2a',
            borderRadius: '2px', transition: 'width 0.6s ease'
          }} />
        </div>
      </div>
    )
  }

  return (
    <Layout>
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontFamily: 'Georgia, serif', fontSize: '22px', color: '#2c2416', margin: 0, letterSpacing: '1px' }}>
          Score a Resume
        </h2>
        <p style={{ color: '#9c8e76', fontSize: '13px', marginTop: '4px' }}>
          Paste a resume to score it against a job description
        </p>
      </div>

      {/* Input form */}
      <div style={card}>
        <form onSubmit={handleScore}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '11px', color: '#6b5e47', letterSpacing: '1px', marginBottom: '6px' }}>
              JD ID
            </label>
            <input
              type="number" value={jdId} onChange={e => setJdId(e.target.value)} required
              placeholder="e.g. 2"
              style={{
                width: '120px', background: '#f0ebe0', border: '1px solid #c8bea8',
                borderRadius: '6px', padding: '8px 12px', fontSize: '14px',
                color: '#2c2416', outline: 'none', boxSizing: 'border-box'
              }}
            />
            <span style={{ fontSize: '12px', color: '#9c8e76', marginLeft: '10px' }}>
              Find this on your dashboard
            </span>
          </div>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '11px', color: '#6b5e47', letterSpacing: '1px', marginBottom: '6px' }}>
              RESUME TEXT
            </label>
            <textarea
              value={resumeText} onChange={e => setResumeText(e.target.value)} required
              rows={10}
              placeholder="Paste the candidate's resume text here..."
              style={{
                width: '100%', background: '#f0ebe0', border: '1px solid #c8bea8',
                borderRadius: '6px', padding: '12px', fontSize: '13px',
                color: '#2c2416', outline: 'none', resize: 'vertical',
                boxSizing: 'border-box', fontFamily: 'system-ui, sans-serif', lineHeight: '1.6'
              }}
            />
          </div>
          {error && (
            <div style={{ background: '#f5e8e5', border: '1px solid #c8a898', color: '#8b3a2a', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', marginBottom: '12px' }}>
              {error}
            </div>
          )}
          <button
            type="submit" disabled={loading}
            style={{
              background: loading ? '#9c8e76' : '#2c2416', color: '#f0ebe0',
              border: 'none', borderRadius: '6px', padding: '10px 28px',
              fontSize: '12px', letterSpacing: '2px', cursor: loading ? 'default' : 'pointer',
            }}
          >
            {loading ? 'SCORING...' : 'SCORE RESUME'}
          </button>
        </form>
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Composite score */}
          <div style={{ ...card, textAlign: 'center', padding: '32px' }}>
            <p style={{ fontSize: '11px', color: '#9c8e76', letterSpacing: '2px', margin: '0 0 8px' }}>
              COMPOSITE ATS SCORE
            </p>
            <p style={{ fontFamily: 'Georgia, serif', fontSize: '56px', color: '#2c2416', margin: '0 0 4px', fontWeight: '500' }}>
              {result.composite_score.toFixed(1)}
            </p>
            <p style={{ fontSize: '13px', color: '#9c8e76', margin: 0 }}>out of 100</p>
            <div style={{ height: '6px', background: '#c8bea8', borderRadius: '3px', margin: '20px 0 0' }}>
              <div style={{
                height: '6px', width: `${result.composite_score}%`,
                background: result.composite_score > 60 ? '#3a6b2a' : result.composite_score > 35 ? '#8b7a2a' : '#8b3a2a',
                borderRadius: '3px'
              }} />
            </div>
          </div>

          {/* Signal breakdown */}
          <div style={card}>
            <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', marginTop: 0, fontSize: '16px', letterSpacing: '0.5px' }}>
              Signal Breakdown
            </h3>
            <ScoreBar label="SKILL MATCH" score={result.skill_score} weight="0.45" />
            <ScoreBar label="SEMANTIC SIMILARITY" score={result.semantic_score} weight="0.35" />
            <ScoreBar label="EXPERIENCE RELEVANCE" score={result.experience_score} weight="0.20" />
          </div>

          {/* Skills */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div style={card}>
              <h3 style={{ fontFamily: 'Georgia, serif', color: '#3a6b2a', marginTop: 0, fontSize: '14px' }}>
                Matched Skills ({result.matched_skills.length})
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {result.matched_skills.map(s => (
                  <span key={s} style={{
                    background: '#e8f0e5', border: '1px solid #a8c8a0',
                    borderRadius: '4px', padding: '3px 8px',
                    fontSize: '11px', color: '#3a6b2a'
                  }}>{s}</span>
                ))}
              </div>
            </div>
            <div style={card}>
              <h3 style={{ fontFamily: 'Georgia, serif', color: '#8b3a2a', marginTop: 0, fontSize: '14px' }}>
                Missing Skills ({result.missing_skills.length})
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {result.missing_skills.map(s => (
                  <span key={s} style={{
                    background: '#f5e8e5', border: '1px solid #c8a898',
                    borderRadius: '4px', padding: '3px 8px',
                    fontSize: '11px', color: '#8b3a2a'
                  }}>{s}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Explanation */}
          <div style={card}>
            <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', marginTop: 0, fontSize: '16px' }}>
              Analysis
            </h3>
            <p style={{ color: '#6b5e47', fontSize: '14px', lineHeight: '1.7', margin: 0 }}>
              {result.explanation}
            </p>
          </div>
        </>
      )}
    </Layout>
  )
}