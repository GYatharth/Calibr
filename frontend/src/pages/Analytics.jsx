import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import client from '../api/client'

export default function Analytics() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchAnalytics()
  }, [])

  async function fetchAnalytics() {
    try {
      const res = await client.get('/analytics')
      setData(res.data)
    } catch (err) {
      setError('Failed to load analytics')
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

  function StatCard({ label, value, sub }) {
    return (
      <div style={{ background: '#e5dfd2', border: '1px solid #c8bea8', borderRadius: '8px', padding: '20px' }}>
        <p style={{ fontSize: '10px', color: '#9c8e76', letterSpacing: '1.5px', margin: '0 0 6px' }}>{label}</p>
        <p style={{ fontFamily: 'Georgia, serif', fontSize: '32px', color: '#2c2416', margin: '0', fontWeight: '500' }}>{value}</p>
        {sub && <p style={{ fontSize: '11px', color: '#9c8e76', margin: '4px 0 0' }}>{sub}</p>}
      </div>
    )
  }

  function SkillBar({ skill, count, maxCount, color, bg, border }) {
    const pct = Math.round((count / maxCount) * 100)
    return (
      <div style={{ marginBottom: '10px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span style={{ fontSize: '12px', color: '#6b5e47' }}>{skill}</span>
          <span style={{ fontSize: '12px', color: '#9c8e76' }}>{count} candidates</span>
        </div>
        <div style={{ height: '6px', background: '#c8bea8', borderRadius: '3px' }}>
          <div style={{ height: '6px', width: `${pct}%`, background: color, borderRadius: '3px' }} />
        </div>
      </div>
    )
  }

  function ScoreDistBar({ label, count, total, color }) {
    const pct = total > 0 ? Math.round((count / total) * 100) : 0
    return (
      <div style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span style={{ fontSize: '12px', color: '#6b5e47' }}>{label}</span>
          <span style={{ fontSize: '12px', color: '#9c8e76' }}>{count} ({pct}%)</span>
        </div>
        <div style={{ height: '8px', background: '#c8bea8', borderRadius: '4px' }}>
          <div style={{ height: '8px', width: `${pct}%`, background: color, borderRadius: '4px' }} />
        </div>
      </div>
    )
  }

  return (
    <Layout>
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontFamily: 'Georgia, serif', fontSize: '22px', color: '#2c2416', margin: 0, letterSpacing: '1px' }}>
          Recruiter Analytics
        </h2>
        <p style={{ color: '#9c8e76', fontSize: '13px', marginTop: '4px' }}>
          Overview of all your job descriptions and candidates
        </p>
      </div>

      {error && (
        <div style={{ background: '#f5e8e5', border: '1px solid #c8a898', color: '#8b3a2a', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {loading ? (
        <p style={{ color: '#9c8e76' }}>Loading analytics...</p>
      ) : data && (
        <>
          {/* Top stats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
            <StatCard label="TOTAL JDS" value={data.total_jds} />
            <StatCard label="TOTAL CANDIDATES" value={data.total_candidates} />
            <StatCard label="AVG SCORE" value={data.avg_composite_score} sub="out of 100" />
            <StatCard label="TOP SCORE" value={data.top_score} sub="out of 100" />
          </div>

          {/* Hiring funnel */}
          <div style={card}>
            <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', marginTop: 0, fontSize: '16px' }}>
              Hiring Funnel
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              {[
                { label: 'SHORTLISTED', value: data.shortlisted_count, color: '#3a6b2a', bg: '#e8f0e5', border: '#a8c8a0' },
                { label: 'PENDING', value: data.pending_count, color: '#6b5e47', bg: '#f0ebe0', border: '#c8bea8' },
                { label: 'REJECTED', value: data.rejected_count, color: '#8b3a2a', bg: '#f5e8e5', border: '#c8a898' },
              ].map(item => (
                <div key={item.label} style={{
                  background: item.bg, border: `1px solid ${item.border}`,
                  borderRadius: '8px', padding: '16px', textAlign: 'center'
                }}>
                  <p style={{ fontSize: '10px', color: item.color, letterSpacing: '1.5px', margin: '0 0 6px' }}>{item.label}</p>
                  <p style={{ fontFamily: 'Georgia, serif', fontSize: '36px', color: item.color, margin: 0, fontWeight: '500' }}>{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Score distribution */}
          <div style={card}>
            <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', marginTop: 0, fontSize: '16px' }}>
              Score Distribution
            </h3>
            <ScoreDistBar label="75–100 (Strong fit)" count={data.score_distribution['75-100']} total={data.total_candidates} color="#3a6b2a" />
            <ScoreDistBar label="50–75 (Moderate fit)" count={data.score_distribution['50-75']} total={data.total_candidates} color="#8b7a2a" />
            <ScoreDistBar label="25–50 (Weak fit)" count={data.score_distribution['25-50']} total={data.total_candidates} color="#c8a898" />
            <ScoreDistBar label="0–25 (Poor fit)" count={data.score_distribution['0-25']} total={data.total_candidates} color="#8b3a2a" />
          </div>

          {/* Skill distribution */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div style={card}>
              <h3 style={{ fontFamily: 'Georgia, serif', color: '#3a6b2a', marginTop: 0, fontSize: '15px' }}>
                Most Matched Skills
              </h3>
              {data.most_common_matched_skills.length === 0 ? (
                <p style={{ color: '#9c8e76', fontSize: '13px' }}>No data yet</p>
              ) : data.most_common_matched_skills.map((s, i) => (
                <SkillBar
                  key={i} skill={s.skill} count={s.count}
                  maxCount={data.most_common_matched_skills[0].count}
                  color="#3a6b2a"
                />
              ))}
            </div>
            <div style={card}>
              <h3 style={{ fontFamily: 'Georgia, serif', color: '#8b3a2a', marginTop: 0, fontSize: '15px' }}>
                Most Missing Skills
              </h3>
              {data.most_common_missing_skills.length === 0 ? (
                <p style={{ color: '#9c8e76', fontSize: '13px' }}>No data yet</p>
              ) : data.most_common_missing_skills.map((s, i) => (
                <SkillBar
                  key={i} skill={s.skill} count={s.count}
                  maxCount={data.most_common_missing_skills[0].count}
                  color="#8b3a2a"
                />
              ))}
            </div>
          </div>

          {/* Top candidates */}
          <div style={card}>
            <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', marginTop: 0, fontSize: '16px' }}>
              Top Candidates
            </h3>
            {data.top_candidates.length === 0 ? (
              <p style={{ color: '#9c8e76', fontSize: '13px' }}>No candidates scored yet</p>
            ) : data.top_candidates.map((c, i) => (
              <div key={c.candidate_id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '12px 0',
                borderBottom: i < data.top_candidates.length - 1 ? '1px solid #c8bea8' : 'none'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
                  <span style={{
                    width: '28px', height: '28px', borderRadius: '50%',
                    background: i === 0 ? '#2c2416' : '#f0ebe0',
                    border: '1px solid #c8bea8',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontFamily: 'Georgia, serif', fontSize: '12px',
                    color: i === 0 ? '#f0ebe0' : '#6b5e47', flexShrink: 0,
                  }}>{i + 1}</span>
                  <div>
                    <p style={{ fontSize: '12px', color: '#6b5e47', margin: '0 0 2px' }}>
                      Candidate #{c.candidate_id} · JD #{c.jd_id}
                    </p>
                    {c.candidate_summary && (
                      <p style={{ fontSize: '12px', color: '#9c8e76', margin: 0, fontStyle: 'italic' }}>
                        "{c.candidate_summary}"
                      </p>
                    )}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{
                    fontSize: '11px', padding: '2px 8px', borderRadius: '4px',
                    background: c.status === 'shortlisted' ? '#e8f0e5' : c.status === 'rejected' ? '#f5e8e5' : '#f0ebe0',
                    color: c.status === 'shortlisted' ? '#3a6b2a' : c.status === 'rejected' ? '#8b3a2a' : '#9c8e76',
                    border: `1px solid ${c.status === 'shortlisted' ? '#a8c8a0' : c.status === 'rejected' ? '#c8a898' : '#c8bea8'}`,
                  }}>{c.status}</span>
                  <span style={{ fontFamily: 'Georgia, serif', fontSize: '20px', color: '#2c2416', fontWeight: '500' }}>
                    {c.composite_score.toFixed(1)}
                  </span>
                  <button
                    onClick={() => navigate(`/breakdown/${c.candidate_id}`)}
                    style={{
                      background: 'none', color: '#6b5e47', border: '1px solid #c8bea8',
                      borderRadius: '6px', padding: '4px 12px', fontSize: '11px',
                      letterSpacing: '1px', cursor: 'pointer',
                    }}
                  >
                    VIEW →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </Layout>
  )
}