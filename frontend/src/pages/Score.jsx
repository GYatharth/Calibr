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
  const [tab, setTab] = useState('upload') // 'upload' or 'paste'
  const [file, setFile] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const [extractedFilename, setExtractedFilename] = useState('')
  const [parsedData, setParsedData] = useState(null)

  async function handleFileChange(e) {
    const selected = e.target.files[0]
    if (!selected) return
    if (!selected.name.endsWith('.pdf')) {
      setError('Only PDF files are supported')
      return
    }
    setFile(selected)
    setError('')
    setExtracting(true)
    setExtractedFilename(selected.name)
    setParsedData(null)

    try {
      const formData = new FormData()
      formData.append('file', selected)
      const res = await client.post('/upload/resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setResumeText(res.data.extracted_text)
      setParsedData(res.data.parsed)
    } catch (err) {
      setError(err.response?.data?.detail || 'PDF extraction failed')
      setFile(null)
      setExtractedFilename('')
    } finally {
      setExtracting(false)
    }
  }

  async function handleScore(e) {
    e.preventDefault()
    if (!resumeText.trim()) {
      setError('Please upload a PDF or paste resume text first')
      return
    }
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
            borderRadius: '2px',
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
          Upload a PDF or paste resume text to score against a job description
        </p>
      </div>

      <div style={card}>
        <form onSubmit={handleScore}>

          {/* JD ID */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '11px', color: '#6b5e47', letterSpacing: '1px', marginBottom: '6px' }}>
              JD ID
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <input
                type="number" value={jdId} onChange={e => setJdId(e.target.value)} required
                placeholder="e.g. 2"
                style={{
                  width: '100px', background: '#f0ebe0', border: '1px solid #c8bea8',
                  borderRadius: '6px', padding: '8px 12px', fontSize: '14px',
                  color: '#2c2416', outline: 'none',
                }}
              />
              <span style={{ fontSize: '12px', color: '#9c8e76' }}>
                Find this on your dashboard
              </span>
            </div>
          </div>

          {/* Tabs */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '11px', color: '#6b5e47', letterSpacing: '1px', marginBottom: '10px' }}>
              RESUME INPUT
            </label>
            <div style={{ display: 'flex', gap: '0', marginBottom: '16px', border: '1px solid #c8bea8', borderRadius: '6px', overflow: 'hidden', width: 'fit-content' }}>
              {['upload', 'paste'].map(t => (
                <button
                  key={t} type="button" onClick={() => { setTab(t); setError('') }}
                  style={{
                    padding: '7px 20px', fontSize: '11px', letterSpacing: '1px',
                    border: 'none', cursor: 'pointer',
                    background: tab === t ? '#2c2416' : '#f0ebe0',
                    color: tab === t ? '#f0ebe0' : '#6b5e47',
                  }}
                >
                  {t === 'upload' ? 'UPLOAD PDF' : 'PASTE TEXT'}
                </button>
              ))}
            </div>

            {/* Upload tab */}
            {tab === 'upload' && (
              <div>
                <label style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center',
                  justifyContent: 'center', gap: '10px',
                  background: '#f0ebe0', border: '2px dashed #c8bea8',
                  borderRadius: '8px', padding: '40px 24px',
                  cursor: 'pointer', textAlign: 'center',
                }}>
                  <input
                    type="file" accept=".pdf"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                  />
                  {extracting ? (
                    <>
                      <span style={{ fontSize: '24px' }}>⏳</span>
                      <span style={{ fontSize: '13px', color: '#6b5e47' }}>Extracting text from PDF...</span>
                    </>
                  ) : extractedFilename ? (
                    <>
                      <span style={{ fontSize: '24px' }}>✓</span>
                      <span style={{ fontSize: '13px', color: '#3a6b2a', fontWeight: '500' }}>
                        {extractedFilename}
                      </span>
                      <span style={{ fontSize: '12px', color: '#9c8e76' }}>
                        {resumeText.length} characters extracted · Click to change
                      </span>
                    </>
                  ) : (
                    <>
                      <span style={{ fontSize: '32px' }}>📄</span>
                      <span style={{ fontSize: '14px', color: '#6b5e47', fontFamily: 'Georgia, serif' }}>
                        Click to upload resume PDF
                      </span>
                      <span style={{ fontSize: '12px', color: '#9c8e76' }}>
                        PDF files only · Text will be extracted automatically
                      </span>
                    </>
                  )}
                </label>

                {/* Parsed resume data */}
                {parsedData && (
                  <div style={{
                    background: '#f0ebe0', border: '1px solid #c8bea8',
                    borderRadius: '8px', padding: '16px', marginTop: '16px',
                  }}>
                    <p style={{ fontSize: '11px', color: '#6b5e47', letterSpacing: '1px', margin: '0 0 12px', fontWeight: '500' }}>
                      EXTRACTED FROM RESUME
                    </p>

                    {/* Experience */}
                    {parsedData.experience.length > 0 && (
                      <div style={{ marginBottom: '12px' }}>
                        <p style={{ fontSize: '11px', color: '#9c8e76', letterSpacing: '1px', margin: '0 0 6px' }}>EXPERIENCE</p>
                        {parsedData.experience.map((exp, i) => (
                          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                            <span style={{ fontSize: '12px', color: '#4a3c2a' }}>{exp.title_line}</span>
                            <span style={{ fontSize: '11px', color: '#9c8e76' }}>{exp.duration_months} months</span>
                          </div>
                        ))}
                        <p style={{ fontSize: '11px', color: '#9c8e76', margin: '6px 0 0' }}>
                          Total: {parsedData.total_experience_months} months ({(parsedData.total_experience_months / 12).toFixed(1)} years)
                        </p>
                      </div>
                    )}

                    {/* Skills */}
                    {parsedData.skills.length > 0 && (
                      <div style={{ marginBottom: '8px' }}>
                        <p style={{ fontSize: '11px', color: '#9c8e76', letterSpacing: '1px', margin: '0 0 6px' }}>
                          SKILLS DETECTED ({parsedData.skills.length})
                        </p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {parsedData.skills.map(s => (
                            <span key={s} style={{
                              background: '#e8f0e5', border: '1px solid #a8c8a0',
                              borderRadius: '3px', padding: '2px 7px',
                              fontSize: '11px', color: '#3a6b2a'
                            }}>{s}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {parsedData.skills.length === 0 && parsedData.experience.length === 0 && (
                      <p style={{ fontSize: '12px', color: '#9c8e76', margin: 0 }}>
                        Text extracted but structured data could not be parsed — scoring will still work.
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Paste tab */}
            {tab === 'paste' && (
              <textarea
                value={resumeText} onChange={e => setResumeText(e.target.value)}
                rows={10}
                placeholder="Paste the candidate's resume text here..."
                style={{
                  width: '100%', background: '#f0ebe0', border: '1px solid #c8bea8',
                  borderRadius: '6px', padding: '12px', fontSize: '13px',
                  color: '#2c2416', outline: 'none', resize: 'vertical',
                  boxSizing: 'border-box', fontFamily: 'system-ui, sans-serif', lineHeight: '1.6'
                }}
              />
            )}
          </div>

          {error && (
            <div style={{ background: '#f5e8e5', border: '1px solid #c8a898', color: '#8b3a2a', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', marginBottom: '12px' }}>
              {error}
            </div>
          )}

          <button
            type="submit" disabled={loading || extracting}
            style={{
              background: (loading || extracting) ? '#9c8e76' : '#2c2416',
              color: '#f0ebe0', border: 'none', borderRadius: '6px',
              padding: '10px 28px', fontSize: '12px', letterSpacing: '2px',
              cursor: (loading || extracting) ? 'default' : 'pointer',
            }}
          >
            {loading ? 'SCORING...' : 'SCORE RESUME'}
          </button>
        </form>
      </div>

      {/* Results */}
      {result && (
        <>
          <div style={{ background: '#e5dfd2', border: '1px solid #c8bea8', borderRadius: '8px', padding: '32px', marginBottom: '16px', textAlign: 'center' }}>
            <p style={{ fontSize: '10px', color: '#9c8e76', letterSpacing: '2px', margin: '0 0 8px' }}>COMPOSITE ATS SCORE</p>
            <p style={{ fontFamily: 'Georgia, serif', fontSize: '56px', color: '#2c2416', margin: '0 0 4px', fontWeight: '500' }}>
              {result.composite_score.toFixed(1)}
            </p>
            <p style={{ fontSize: '13px', color: '#9c8e76', margin: '0 0 20px' }}>out of 100</p>
            <div style={{ height: '6px', background: '#c8bea8', borderRadius: '3px' }}>
              <div style={{
                height: '6px', width: `${result.composite_score}%`,
                background: result.composite_score > 60 ? '#3a6b2a' : result.composite_score > 35 ? '#8b7a2a' : '#8b3a2a',
                borderRadius: '3px'
              }} />
            </div>
          </div>

          <div style={{ background: '#e5dfd2', border: '1px solid #c8bea8', borderRadius: '8px', padding: '24px', marginBottom: '16px' }}>
            <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', marginTop: 0, fontSize: '16px' }}>Signal Breakdown</h3>
            <ScoreBar label="SKILL MATCH" score={result.skill_score} weight="0.45" />
            <ScoreBar label="SEMANTIC SIMILARITY" score={result.semantic_score} weight="0.35" />
            <ScoreBar label="EXPERIENCE RELEVANCE" score={result.experience_score} weight="0.20" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div style={{ background: '#e5dfd2', border: '1px solid #c8bea8', borderRadius: '8px', padding: '20px' }}>
              <h3 style={{ fontFamily: 'Georgia, serif', color: '#3a6b2a', marginTop: 0, fontSize: '14px' }}>
                Matched Skills ({result.matched_skills.length})
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {result.matched_skills.map(s => (
                  <span key={s} style={{ background: '#e8f0e5', border: '1px solid #a8c8a0', borderRadius: '4px', padding: '3px 8px', fontSize: '11px', color: '#3a6b2a' }}>{s}</span>
                ))}
              </div>
            </div>
            <div style={{ background: '#e5dfd2', border: '1px solid #c8bea8', borderRadius: '8px', padding: '20px' }}>
              <h3 style={{ fontFamily: 'Georgia, serif', color: '#8b3a2a', marginTop: 0, fontSize: '14px' }}>
                Missing Skills ({result.missing_skills.length})
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {result.missing_skills.map(s => (
                  <span key={s} style={{ background: '#f5e8e5', border: '1px solid #c8a898', borderRadius: '4px', padding: '3px 8px', fontSize: '11px', color: '#8b3a2a' }}>{s}</span>
                ))}
              </div>
            </div>
          </div>

          <div style={{ background: '#e5dfd2', border: '1px solid #c8bea8', borderRadius: '8px', padding: '24px', marginBottom: '16px' }}>
            <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', marginTop: 0, fontSize: '16px' }}>Analysis</h3>
            <p style={{ color: '#6b5e47', fontSize: '14px', lineHeight: '1.7', margin: 0 }}>
              {result.explanation}
            </p>
          </div>
        </>
      )}
    </Layout>
  )
}