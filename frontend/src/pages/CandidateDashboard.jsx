import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

export default function CandidateDashboard() {
  const navigate = useNavigate()
  const [jds, setJds] = useState([])
  const [jdId, setJdId] = useState('')
  const [file, setFile] = useState(null)
  const [extractedText, setExtractedText] = useState('')
  const [extractedFilename, setExtractedFilename] = useState('')
  const [extracting, setExtracting] = useState(false)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [questions, setQuestions] = useState(null)
  const [loadingQ, setLoadingQ] = useState(false)

  useEffect(() => {
    fetchJds()
  }, [])

  async function fetchJds() {
    try {
      const res = await client.get('/jd/public/all')
      setJds(res.data)
      if (res.data.length > 0) setJdId(res.data[0].id)
    } catch (err) {
      console.error('Failed to load JDs')
    }
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_role')
    navigate('/login')
  }

  async function handleFileChange(e) {
    const selected = e.target.files[0]
    if (!selected) return
    if (!selected.name.endsWith('.pdf')) {
      setError('Only PDF files are supported')
      return
    }
    setExtracting(true)
    setError('')
    setExtractedFilename(selected.name)
    try {
      const formData = new FormData()
      formData.append('file', selected)
      const res = await client.post('/upload/resume', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setExtractedText(res.data.extracted_text)
      setFile(selected)
    } catch (err) {
      setError('PDF extraction failed')
      setExtractedFilename('')
    } finally {
      setExtracting(false)
    }
  }

  async function handleScore(e) {
    e.preventDefault()
    if (!extractedText) { setError('Please upload your resume first'); return }
    if (!jdId) { setError('Please select a job description'); return }
    setLoading(true)
    setError('')
    setResult(null)
    setQuestions(null)
    try {
      const res = await client.post('/score', {
        jd_id: parseInt(jdId),
        resume_text: extractedText,
      })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Scoring failed')
    } finally {
      setLoading(false)
    }
  }

  async function fetchInterviewQuestions() {
    setLoadingQ(true)
    try {
      const res = await client.get(`/interview/${result.candidate_id}`)
      setQuestions(res.data)
    } catch (err) {
      setError('Failed to generate interview questions')
    } finally {
      setLoadingQ(false)
    }
  }

  const card = {
    background: '#e5dfd2',
    border: '1px solid #c8bea8',
    borderRadius: '8px',
    padding: '24px',
    marginBottom: '16px',
  }

  function QuestionSection({ title, questions, color, bg, border }) {
    return (
      <div style={{ marginBottom: '20px' }}>
        <h4 style={{
          fontFamily: 'Georgia, serif', fontSize: '14px',
          color, margin: '0 0 10px',
        }}>{title}</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {questions.map((q, i) => (
            <div key={i} style={{
              background: bg, border: `1px solid ${border}`,
              borderRadius: '6px', padding: '10px 14px',
              fontSize: '13px', color: '#4a3c2a', lineHeight: '1.5'
            }}>
              <span style={{ color, fontWeight: '500', marginRight: '8px' }}>{i + 1}.</span>
              {q}
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f0ebe0' }}>
      {/* Navbar */}
      <nav style={{
        borderBottom: '1px solid #c8bea8', background: '#e5dfd2',
        padding: '12px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between'
      }}>
        <span style={{ fontFamily: 'Georgia, serif', fontSize: '20px', color: '#2c2416', letterSpacing: '2px' }}>
          CALIBR
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{
            fontSize: '11px', color: '#9c8e76', letterSpacing: '1px',
            background: '#f0ebe0', padding: '3px 10px',
            borderRadius: '4px', border: '1px solid #c8bea8'
          }}>
            CANDIDATE
          </span>
          <button onClick={logout} style={{
            background: 'none', border: '1px solid #c8bea8', borderRadius: '6px',
            padding: '4px 12px', fontSize: '12px', color: '#6b5e47',
            cursor: 'pointer', letterSpacing: '1px'
          }}>LOGOUT</button>
        </div>
      </nav>

      <main style={{ maxWidth: '760px', margin: '0 auto', padding: '40px 24px' }}>
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{ fontFamily: 'Georgia, serif', fontSize: '24px', color: '#2c2416', margin: 0, letterSpacing: '1px' }}>
            Check Your ATS Score
          </h2>
          <p style={{ color: '#9c8e76', fontSize: '13px', marginTop: '6px' }}>
            Upload your resume and select a job description to see how well you match
          </p>
        </div>

        <div style={card}>
          <form onSubmit={handleScore}>

            {/* Resume upload */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: '#6b5e47', letterSpacing: '1px', marginBottom: '8px' }}>
                YOUR RESUME
              </label>
              <label style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                justifyContent: 'center', gap: '10px',
                background: '#f0ebe0', border: '2px dashed #c8bea8',
                borderRadius: '8px', padding: '32px 24px',
                cursor: 'pointer', textAlign: 'center',
              }}>
                <input type="file" accept=".pdf" onChange={handleFileChange} style={{ display: 'none' }} />
                {extracting ? (
                  <>
                    <span style={{ fontSize: '24px' }}>⏳</span>
                    <span style={{ fontSize: '13px', color: '#6b5e47' }}>Extracting text from PDF...</span>
                  </>
                ) : extractedFilename ? (
                  <>
                    <span style={{ fontSize: '24px' }}>✓</span>
                    <span style={{ fontSize: '13px', color: '#3a6b2a', fontWeight: '500' }}>{extractedFilename}</span>
                    <span style={{ fontSize: '12px', color: '#9c8e76' }}>{extractedText.length} characters extracted · Click to change</span>
                  </>
                ) : (
                  <>
                    <span style={{ fontSize: '32px' }}>📄</span>
                    <span style={{ fontSize: '14px', color: '#6b5e47', fontFamily: 'Georgia, serif' }}>Upload your resume PDF</span>
                    <span style={{ fontSize: '12px', color: '#9c8e76' }}>PDF only · Text extracted automatically</span>
                  </>
                )}
              </label>
            </div>

            {/* JD dropdown */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: '#6b5e47', letterSpacing: '1px', marginBottom: '8px' }}>
                JOB DESCRIPTION
              </label>
              {jds.length === 0 ? (
                <p style={{ color: '#9c8e76', fontSize: '13px' }}>
                  No job descriptions available yet.
                </p>
              ) : (
                <select
                  value={jdId} onChange={e => setJdId(e.target.value)}
                  style={{
                    width: '100%', background: '#f0ebe0', border: '1px solid #c8bea8',
                    borderRadius: '6px', padding: '10px 14px', fontSize: '13px',
                    color: '#2c2416', outline: 'none', cursor: 'pointer',
                  }}
                >
                  <option value="">Select a job description...</option>
                  {jds.map(jd => (
                    <option key={jd.id} value={jd.id}>
                      JD #{jd.id} — {jd.required_skills?.slice(0, 4).join(', ')}
                      {jd.required_skills?.length > 4 ? '...' : ''}
                      {jd.required_experience_years ? ` · ${jd.required_experience_years}yr exp` : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {error && (
              <div style={{ background: '#f5e8e5', border: '1px solid #c8a898', color: '#8b3a2a', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', marginBottom: '12px' }}>
                {error}
              </div>
            )}

            <button
              type="submit" disabled={loading || extracting || !extractedText || !jdId}
              style={{
                background: (loading || extracting || !extractedText || !jdId) ? '#9c8e76' : '#2c2416',
                color: '#f0ebe0', border: 'none', borderRadius: '6px',
                padding: '10px 28px', fontSize: '12px', letterSpacing: '2px',
                cursor: (loading || extracting || !extractedText || !jdId) ? 'default' : 'pointer',
              }}
            >
              {loading ? 'SCORING...' : 'CHECK MY SCORE'}
            </button>
          </form>
        </div>

        {/* Results */}
        {result && (
          <>
            <div style={{ ...card, textAlign: 'center', padding: '36px' }}>
              <p style={{ fontSize: '10px', color: '#9c8e76', letterSpacing: '2px', margin: '0 0 8px' }}>YOUR ATS SCORE</p>
              <p style={{ fontFamily: 'Georgia, serif', fontSize: '64px', color: '#2c2416', margin: '0 0 4px', fontWeight: '500', lineHeight: 1 }}>
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

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
              <div style={card}>
                <h3 style={{ fontFamily: 'Georgia, serif', color: '#3a6b2a', marginTop: 0, fontSize: '14px' }}>
                  ✓ You have ({result.matched_skills.length})
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {result.matched_skills.map(s => (
                    <span key={s} style={{ background: '#e8f0e5', border: '1px solid #a8c8a0', borderRadius: '4px', padding: '3px 8px', fontSize: '11px', color: '#3a6b2a' }}>{s}</span>
                  ))}
                  {result.matched_skills.length === 0 && <span style={{ color: '#9c8e76', fontSize: '13px' }}>None matched</span>}
                </div>
              </div>
              <div style={card}>
                <h3 style={{ fontFamily: 'Georgia, serif', color: '#8b3a2a', marginTop: 0, fontSize: '14px' }}>
                  ✗ You're missing ({result.missing_skills.length})
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {result.missing_skills.map(s => (
                    <span key={s} style={{ background: '#f5e8e5', border: '1px solid #c8a898', borderRadius: '4px', padding: '3px 8px', fontSize: '11px', color: '#8b3a2a' }}>{s}</span>
                  ))}
                  {result.missing_skills.length === 0 && <span style={{ color: '#9c8e76', fontSize: '13px' }}>None missing</span>}
                </div>
              </div>
            </div>

            <div style={card}>
              <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', marginTop: 0, fontSize: '16px' }}>
                Personalized Feedback
              </h3>
              <p style={{ color: '#6b5e47', fontSize: '14px', lineHeight: '1.8', margin: 0 }}>
                {result.explanation}
              </p>
            </div>

            {/* Interview Questions */}
            <div style={card}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: questions ? '20px' : '0' }}>
                <div>
                  <h3 style={{ fontFamily: 'Georgia, serif', color: '#2c2416', margin: 0, fontSize: '16px' }}>
                    Practice Interview Questions
                  </h3>
                  <p style={{ color: '#9c8e76', fontSize: '12px', margin: '4px 0 0' }}>
                    AI-generated questions tailored to your profile against this role
                  </p>
                </div>
                {!questions && (
                  <button
                    onClick={fetchInterviewQuestions}
                    disabled={loadingQ}
                    style={{
                      background: loadingQ ? '#9c8e76' : '#2c2416',
                      color: '#f0ebe0', border: 'none', borderRadius: '6px',
                      padding: '8px 18px', fontSize: '11px', letterSpacing: '1px',
                      cursor: loadingQ ? 'default' : 'pointer', whiteSpace: 'nowrap',
                    }}
                  >
                    {loadingQ ? 'GENERATING...' : 'GENERATE QUESTIONS'}
                  </button>
                )}
              </div>

              {questions && (
                <>
                  <QuestionSection
                    title="Technical Questions (based on your matched skills)"
                    questions={questions.technical}
                    color="#3a6b2a" bg="#e8f0e5" border="#a8c8a0"
                  />
                  <QuestionSection
                    title="Gap Questions (probing your missing skills)"
                    questions={questions.gap}
                    color="#8b7a2a" bg="#f0ece0" border="#c8c0a0"
                  />
                  <QuestionSection
                    title="Behavioral Questions"
                    questions={questions.behavioral}
                    color="#2c2416" bg="#f0ebe0" border="#c8bea8"
                  />
                </>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  )
}