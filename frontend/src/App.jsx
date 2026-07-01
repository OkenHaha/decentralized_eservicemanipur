import React, { useState, useEffect } from 'react';
import { Shield, User, HelpCircle, LogOut, ArrowRight, BookOpen, Key, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import PortalHome from './components/PortalHome';
import CitizenPortal from './components/CitizenPortal';
import OfficialPortal from './components/OfficialPortal';

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001/api/v1';

function App() {
  const [token, setToken] = useState(localStorage.getItem('eseba_token') || '');
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('eseba_user') || 'null'));
  const [view, setView] = useState('home'); // 'home', 'citizen', 'official'
  const [showQuickLogin, setShowQuickLogin] = useState(false);
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    if (token) {
      localStorage.setItem('eseba_token', token);
    } else {
      localStorage.removeItem('eseba_token');
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem('eseba_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('eseba_user');
    }
  }, [user]);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const handleLogout = () => {
    setToken('');
    setUser(null);
    setView('home');
    addToast('Logged out successfully.', 'info');
  };

  const executeLogin = async (employee_id, password) => {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_id, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed.');
      }

      const data = await response.json();
      setToken(data.access_token);
      setUser({
        id: data.user_id,
        name: data.name,
        role: data.role,
      });

      addToast(`Welcome back, ${data.name}!`, 'success');
      setShowQuickLogin(false);

      if (data.role === 'CITIZEN') {
        setView('citizen');
      } else {
        setView('official');
      }
    } catch (err) {
      addToast(err.message, 'danger');
    }
  };

  const mockUsers = [
    { name: 'Citizen: Tomba Singh', id: '9876543210', pass: '123456', role: 'CITIZEN' },
    { name: 'Citizen: Bembem Devi', id: '9876543211', pass: '123456', role: 'CITIZEN' },
    { name: 'Lambu: Sanjit Singh', id: 'EMP-LAMBU-001', pass: 'password123', role: 'REVENUE_LAMBU' },
    { name: 'SDO: Dr. Premjit Singh', id: 'EMP-SDO-001', pass: 'password123', role: 'SDO' },
    { name: 'SDC: Ramesh Singh', id: 'EMP-SDC-001', pass: 'password123', role: 'SDC' },
    { name: 'Employment Officer', id: 'EMP-EXCH-001', pass: 'password123', role: 'EMP_EXCHANGE_OFFICER' },
  ];

  return (
    <div className="app-container">
      {/* Toast Notifications */}
      <div className="toast-container">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="toast"
            style={{
              backgroundColor:
                t.type === 'success'
                  ? 'rgba(16, 185, 129, 0.95)'
                  : t.type === 'danger'
                    ? 'rgba(239, 68, 68, 0.95)'
                    : t.type === 'warning'
                      ? 'rgba(245, 158, 11, 0.95)'
                      : 'rgba(59, 130, 246, 0.95)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            {t.type === 'success' && <CheckCircle size={20} />}
            {t.type === 'danger' && <AlertTriangle size={20} />}
            {t.type === 'warning' && <AlertTriangle size={20} />}
            {t.type === 'info' && <Info size={20} />}
            <span style={{ fontWeight: 500 }}>{t.message}</span>
          </div>
        ))}
      </div>

      {/* Navigation Header */}
      <header
        className="glass-panel"
        style={{
          margin: '16px 24px 0',
          padding: '16px 28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderRadius: '16px',
        }}
      >
        <div
          onClick={() => setView('home')}
          style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}
        >
          <div
            style={{
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
              padding: '10px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Shield size={24} color="#ffffff" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', lineHeight: 1.1 }}>e-Services Manipur</h2>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-gold)', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Anti-Tamper Ledgers
            </span>
          </div>
        </div>

        <nav style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            onClick={() => setView('home')}
            className={`btn ${view === 'home' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 16px', fontSize: '0.9rem' }}
          >
            Public Audit
          </button>

          {!token ? (
            <>
              <button
                onClick={() => {
                  setView('citizen');
                }}
                className={`btn ${view === 'citizen' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '8px 16px', fontSize: '0.9rem' }}
              >
                Citizen Portal
              </button>
              <button
                onClick={() => setShowQuickLogin(true)}
                className="btn btn-success"
                style={{ padding: '8px 16px', fontSize: '0.9rem' }}
              >
                <Key size={16} />
                Quick Login
              </button>
            </>
          ) : (
            <>
              <span
                className="glass-panel"
                style={{
                  padding: '8px 16px',
                  fontSize: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: 'rgba(255, 255, 255, 0.03)',
                }}
              >
                <User size={14} color="var(--color-primary)" />
                <span style={{ color: '#ffffff', fontWeight: 600 }}>{user?.name}</span>
                <span className="badge badge-submitted" style={{ fontSize: '0.65rem', padding: '2px 6px' }}>
                  {user?.role}
                </span>
              </span>

              <button
                onClick={() => setView(user?.role === 'CITIZEN' ? 'citizen' : 'official')}
                className="btn btn-primary"
                style={{ padding: '8px 16px', fontSize: '0.9rem' }}
              >
                My Workspace
              </button>

              <button
                onClick={handleLogout}
                className="btn btn-secondary"
                style={{ padding: '8px 12px', color: 'var(--color-danger)' }}
                title="Logout"
              >
                <LogOut size={16} />
              </button>
            </>
          )}
        </nav>
      </header>

      {/* Main Workspace Area */}
      <main className="main-content">
        {view === 'home' && (
          <PortalHome setView={setView} token={token} addToast={addToast} />
        )}
        {view === 'citizen' && (
          <CitizenPortal token={token} setToken={setToken} user={user} setUser={setUser} addToast={addToast} setView={setView} />
        )}
        {view === 'official' && (
          <OfficialPortal token={token} user={user} addToast={addToast} />
        )}
      </main>

      {/* Footer */}
      <footer style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', borderTop: '1px solid var(--border-muted)', marginTop: '40px' }}>
        <p>© 2026 Government of Manipur. Replica Platform e-service Manipur. Anchored on application-level cryptographic SQLite Hash-Chains.</p>
      </footer>

      {/* Quick Login Modal */}
      {showQuickLogin && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: '24px',
          }}
        >
          <div
            className="glass-panel"
            style={{
              width: '100%',
              maxWidth: '500px',
              padding: '32px',
              position: 'relative',
              boxShadow: 'var(--shadow-glow)',
            }}
          >
            <h3 style={{ fontSize: '1.5rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Key color="var(--color-gold)" /> Quick-Login Gateway
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px' }}>
              Select a mock profile to log in immediately. This bypasses active Aadhaar/OTP or DSC manual input checks for testing.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
              {mockUsers.map((m) => (
                <button
                  key={m.id}
                  onClick={() => executeLogin(m.id, m.pass)}
                  className="btn btn-secondary"
                  style={{
                    justifyContent: 'space-between',
                    padding: '14px 20px',
                    borderColor: m.role === 'CITIZEN' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                    <span style={{ fontWeight: 600, color: '#ffffff' }}>{m.name}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: {m.id}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className={`badge ${m.role === 'CITIZEN' ? 'badge-submitted' : 'badge-approved'}`} style={{ fontSize: '0.65rem' }}>
                      {m.role}
                    </span>
                    <ArrowRight size={16} />
                  </div>
                </button>
              ))}
            </div>

            <button
              onClick={() => setShowQuickLogin(false)}
              className="btn btn-secondary"
              style={{ width: '100%' }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
