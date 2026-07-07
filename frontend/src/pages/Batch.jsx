import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import client from '../api/client'

export default function Batch() {
  const navigate = useNavigate()
  const [jds, setJds] = useState([])
  const [selectedJd, setSelectedJd] = useState('')
  const [files, setFiles] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [job, setJob] = useState(null)
  const [polling, setPolling] = useState(false)
  const pollRef = useRef(null)

  useEffect(() => {
    fetchJds()
    return () => clearInterval(pollRef.current)
  }, [])

  async function fetchJds() {
    try {
      const res = await client.get('/jd')
      setJds(res.data)
      if (res.data.length > 0) setSelectedJd(res.data[0].id)
    } catch (err) {
      setError('Failed to load job descriptions')
    }
  }

  function handleFileChange(e) {
    const selected = Array.from(e.target.files).filter(f => f.name.endsWith('.pdf'))
    if (selected.length !== e.target.files.length) {
      setError('Some files were skipped — only PDFs are supported')
    } else {
      setError('')
    }
    setFiles(selected)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!selectedJd) { setError('Please select a JD'); return }
    if (files.length === 0) { setError('Please upload at least one PDF'); return }
    if (files.length > 100) { setError('Maximum 100 resumes per batch'); return }

    setSubmitting(true)
    setError('')

    try {
      // Extract text from each PDF one by one
      const resumeTexts = []
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        const res = await client.post('/upload/resume', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        resumeTexts.push(res.data.extracted_text)
      }

      // Submit batch scoring job to Celery
      const batchRes = await client.post('/batch/score', {
        jd_id: parseInt(selectedJd),
        resume_texts: resumeTexts,
      })

      setJob({
        id: batchRes.data.job_id,
        total: batchRes.data.total_resumes,
        processed: 0,
        status: 'pending',
        progress: 0,
      })

      // Start polling every 2 seconds
      setPolling(true)
      pollRef.current = setInterval(() => pollStatus(batchRes.data.job_id), 2000)

    } catch (err) {
      setError(err.response?.data?.detail || 'Batch submission failed')
    } finally {
      setSubmitting(false)
    }
  }

  async function pollStatus(jobId) {
    try {
      const res = await client.get(`/batch/status/${jobId}`)
      setJob(prev => ({
        ...prev,
        processed: res.data.processed_resumes,
        status: res.data.status,
        progress: res.data.progress_pct,
      }))

      if (res.data.status === 'done') {
        clearInterval(pollRef.current)
        setPolling(false)
        // Auto-redirect to rankings after 1.5 seconds
        setTimeout(() => navigate(`/rankings/${selectedJd}`), 1500)
      } else if (res.data.status === 'failed') {
        clearInterval(pollRef.current)
        setPolling(false)
        setError('Batch job failed. Please try again.')
      }
    } catch (err) {
      clearInterval(pollRef.current)
      setPolling(false)
    }
  }

  const card = {
    background: '#e5dfd2',
    border: '1px solid #c8bea8',
    borderRadius: '8px',
    padding: '24px',
    marginBottom: '16px',
  }

  return (
    <Layout>
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontFamily: 'Georgia, serif', fontSize: '22px', color: '#2c2416', margin: 0, letterSpacing: '1px' }}>
          Batch Resume Screening
        </h2>
        <p style={{ color: '#9c8e76', fontSize: '13px', marginTop: '4px' }}>
          Upload multiple resumes at once — all scored and ranked automatically
        </p>
      </div>

      {/* Job progress view */}
      {job && (
        <div style={{ ...card, textAlign: 'center', padding: '40px' }}>
          <p style={{ fontSize: '11px', color: '#9c8e76', letterSpacing: '2px', margin: '0 0 16px' }}>
            {job.status === 'done' ? 'COMPLETE — REDIRECTING TO RANKINGS...' :
             job.status === 'failed' ? 'JOB FAILED' :
             'PROCESSING RESUMES...'}
          </p>

          <div style={{ height: '8px', background: '#c8bea8', borderRadius: '4px', margin: '0 auto 16px', maxWidth: '400px' }}>
            <div style={{
              height: '8px', borderRadius: '4px',
              width: `${job.progress}%`,
              background: job.status === 'done' ? '#3a6b2a' : job.status === 'failed' ? '#8b3a2a' : '#2c2416',
              transition: 'width 0.5s ease',
            }} />
          </div>

          <p style={{ fontFamily: 'Georgia, serif', fontSize: '32px', color: '#2c2416', margin: '0 0 8px' }}>
            {job.processed} / {job.total}
          </p>
          <p style={{ fontSize: '13px', color: '#9c8e76', margin: 0 }}>
            resumes processed · {job.progress.toFixed(0)}% complete
          </p>

          {job.status === 'done' && (
            <div style={{ marginTop: '20px', padding: '12px 20px', background: '#e8f0e5', border: '1px solid #a8c8a0', borderRadius: '6px', display: 'inline-block' }}>
              <span style={{ fontSize: '13px', color: '#3a6b2a' }}>
                ✓ All {job.total} resumes scored — heading to rankings
              </span>
            </div>
          )}
        </div>
      )}

      {/* Upload form — hide while processing */}
      {!job && (
        <div style={card}>
          <form onSubmit={handleSubmit}>

            {/* JD selector */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: '#6b5e47', letterSpacing: '1px', marginBottom: '8px' }}>
                JOB DESCRIPTION
              </label>
              {jds.length === 0 ? (
                <p style={{ color: '#9c8e76', fontSize: '13px' }}>
                  No JDs found.{' '}
                  <span onClick={() => navigate('/dashboard')} style={{ color: '#6b5e47', textDecoration: 'underline', cursor: 'pointer' }}>
                    Create one first
                  </span>
                </p>
              ) : (
                <select
                  value={selectedJd} onChange={e => setSelectedJd(e.target.value)}
                  style={{
                    background: '#f0ebe0', border: '1px solid #c8bea8',
                    borderRadius: '6px', padding: '10px 14px', fontSize: '13px',
                    color: '#2c2416', outline: 'none', width: '100%', cursor: 'pointer',
                  }}
                >
                  {jds.map(jd => (
                    <option key={jd.id} value={jd.id}>
                      JD #{jd.id} — {jd.required_skills?.slice(0, 4).join(', ')}{jd.required_skills?.length > 4 ? '...' : ''}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* File upload */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: '#6b5e47', letterSpacing: '1px', marginBottom: '8px' }}>
                RESUME PDFs
              </label>
              <label style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                justifyContent: 'center', gap: '12px',
                background: '#f0ebe0', border: '2px dashed #c8bea8',
                borderRadius: '8px', padding: '40px 24px',
                cursor: 'pointer', textAlign: 'center',
              }}>
                <input type="file" accept=".pdf" multiple onChange={handleFileChange} style={{ display: 'none' }} />
                {files.length > 0 ? (
                  <>
                    <span style={{ fontSize: '28px' }}>📄</span>
                    <span style={{ fontSize: '15px', color: '#3a6b2a', fontFamily: 'Georgia, serif', fontWeight: '500' }}>
                      {files.length} PDF{files.length > 1 ? 's' : ''} selected
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center', maxWidth: '500px' }}>
                      {files.slice(0, 5).map((f, i) => (
                        <span key={i} style={{ background: '#e8f0e5', border: '1px solid #a8c8a0', borderRadius: '4px', padding: '2px 8px', fontSize: '11px', color: '#3a6b2a' }}>
                          {f.name}
                        </span>
                      ))}
                      {files.length > 5 && (
                        <span style={{ fontSize: '11px', color: '#9c8e76', padding: '2px 4px' }}>+{files.length - 5} more</span>
                      )}
                    </div>
                    <span style={{ fontSize: '12px', color: '#9c8e76' }}>Click to change selection</span>
                  </>
                ) : (
                  <>
                    <span style={{ fontSize: '36px' }}>📂</span>
                    <span style={{ fontSize: '15px', color: '#6b5e47', fontFamily: 'Georgia, serif' }}>
                      Click to select resume PDFs
                    </span>
                    <span style={{ fontSize: '12px', color: '#9c8e76' }}>
                      Select multiple files at once · Up to 100 PDFs · PDF only
                    </span>
                  </>
                )}
              </label>
            </div>

            {error && (
              <div style={{ background: '#f5e8e5', border: '1px solid #c8a898', color: '#8b3a2a', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', marginBottom: '16px' }}>
                {error}
              </div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <button
                type="submit" disabled={submitting || files.length === 0}
                style={{
                  background: (submitting || files.length === 0) ? '#9c8e76' : '#2c2416',
                  color: '#f0ebe0', border: 'none', borderRadius: '6px',
                  padding: '10px 28px', fontSize: '12px', letterSpacing: '2px',
                  cursor: (submitting || files.length === 0) ? 'default' : 'pointer',
                }}
              >
                {submitting ? 'EXTRACTING & QUEUING...' : `SCREEN ${files.length > 0 ? files.length : ''} RESUME${files.length !== 1 ? 'S' : ''}`}
              </button>
              {files.length > 0 && !submitting && (
                <span style={{ fontSize: '12px', color: '#9c8e76' }}>
                  Scored via Celery worker
                </span>
              )}
            </div>
          </form>
        </div>
      )}
    </Layout>
  )
}