import { useNavigate } from 'react-router-dom'

export default function Layout({ children }) {
  const navigate = useNavigate()

  function logout() {
    localStorage.removeItem('access_token')
    navigate('/login')
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f0ebe0' }}>
      {/* Navbar */}
      <nav style={{
        borderBottom: '1px solid #c8bea8',
        background: '#e5dfd2',
        padding: '12px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <span
          onClick={() => navigate('/dashboard')}
          style={{
            fontFamily: 'Georgia, serif',
            fontSize: '20px',
            fontWeight: '500',
            color: '#2c2416',
            letterSpacing: '2px',
            cursor: 'pointer',
          }}
        >
          CALIBR
        </span>
        <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
          <span
            onClick={() => navigate('/score')}
            style={{ fontSize: '13px', color: '#6b5e47', cursor: 'pointer', letterSpacing: '1px' }}
          >
            SCORE
          </span>
          <span
            onClick={() => navigate('/dashboard')}
            style={{ fontSize: '13px', color: '#6b5e47', cursor: 'pointer', letterSpacing: '1px' }}
          >
            MY JDS
          </span>
          <button
            onClick={logout}
            style={{
              background: 'none',
              border: '1px solid #c8bea8',
              borderRadius: '6px',
              padding: '4px 12px',
              fontSize: '12px',
              color: '#6b5e47',
              cursor: 'pointer',
              letterSpacing: '1px',
            }}
          >
            LOGOUT
          </button>
        </div>
      </nav>
      {/* Content */}
      <main style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 24px' }}>
        {children}
      </main>
    </div>
  )
}