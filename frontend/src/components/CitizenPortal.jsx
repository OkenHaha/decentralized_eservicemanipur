import React, { useState, useEffect } from 'react';
import { Shield, CreditCard, Layers, PlusCircle, CheckCircle, Upload, Eye, FileText, Download, ChevronRight, UserCheck, AlertTriangle } from 'lucide-react';
import { API_BASE } from '../App';

function CitizenPortal({ token, setToken, user, setUser, addToast, setView }) {
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard', 'apply', 'profile'
  const [profile, setProfile] = useState(null);
  const [applications, setApplications] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);

  // Auth / Aadhaar Registration States
  const [aadhaar, setAadhaar] = useState('');
  const [mobile, setMobile] = useState('');
  const [captchaChallenge, setCaptchaChallenge] = useState({ id: '', text: '' });
  const [captchaInput, setCaptchaInput] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [authStep, setAuthStep] = useState(1); // 1: Aadhaar + Captcha, 2: OTP verification

  // New Application States
  const [selectedService, setSelectedService] = useState(null);
  const [formData, setFormData] = useState({});
  const [purpose, setPurpose] = useState('');
  const [declaration, setDeclaration] = useState(false);

  // Document Upload workspace
  const [selectedApp, setSelectedApp] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({}); // doc_type -> loading state
  
  // Certificate view state
  const [certificateData, setCertificateData] = useState(null);

  // Load CAPTCHA challenge
  const fetchCaptcha = async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/captcha`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setCaptchaChallenge({ id: data.captcha_id, text: data.captcha_text });
      }
    } catch (err) {
      console.error('Error fetching captcha:', err);
    }
  };

  useEffect(() => {
    if (!token) {
      fetchCaptcha();
    }
  }, [token]);

  // Load dashboard / profile data
  const loadCitizenData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      // Load profile
      const resProfile = await fetch(`${API_BASE}/citizens/me`, { headers });
      if (resProfile.ok) {
        const pData = await resProfile.json();
        setProfile(pData);
      }

      // Load applications
      const resApps = await fetch(`${API_BASE}/applications/mine`, { headers });
      if (resApps.ok) {
        const appsData = await resApps.json();
        setApplications(appsData);
      }

      // Load service catalog
      const resServices = await fetch(`${API_BASE}/applications/services`);
      if (resServices.ok) {
        const servicesData = await resServices.json();
        setServices(servicesData);
      }
    } catch (err) {
      addToast(err.message, 'danger');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      loadCitizenData();
    }
  }, [token]);

  // Aadhaar step 1: Request OTP
  const handleRequestOtp = async (e) => {
    e.preventDefault();
    if (!aadhaar || !mobile || !captchaInput) {
      addToast('Please fill all validation parameters.', 'warning');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/auth/otp/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mobile,
          captcha_id: captchaChallenge.id,
          captcha_value: captchaInput,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'OTP Dispatch failed. Verify CAPTCHA.');
      }

      addToast('A mock OTP code was logged to your system logs. Use 123456.', 'info');
      setAuthStep(2);
    } catch (err) {
      addToast(err.message, 'danger');
      fetchCaptcha(); // Refresh CAPTCHA on failure
      setCaptchaInput('');
    }
  };

  // Aadhaar step 2: Verify & Register
  const handleVerifyRegister = async (e) => {
    e.preventDefault();
    if (!otpCode) return;

    try {
      // 1. Verify OTP first
      const resVerify = await fetch(`${API_BASE}/auth/otp/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mobile, otp_code: otpCode }),
      });

      if (!resVerify.ok) {
        const err = await resVerify.json();
        throw new Error(err.detail || 'Invalid OTP code.');
      }

      // 2. Perform Register (locks mock Aadhaar metrics)
      const resRegister = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          aadhaar_number: aadhaar,
          mobile,
          otp_code: otpCode,
        }),
      });

      if (!resRegister.ok) {
        const err = await resRegister.json();
        throw new Error(err.detail || 'Onboarding registration failed.');
      }

      const data = await resRegister.json();
      setToken(data.access_token);
      setUser({
        id: data.user_id,
        name: data.name,
        role: data.role,
      });

      addToast(`Onboarded successfully! Welcome, ${data.name}.`, 'success');
    } catch (err) {
      addToast(err.message, 'danger');
    }
  };

  // Submit new application
  const handleApply = async (e) => {
    e.preventDefault();
    if (!declaration) {
      addToast('You must accept the legal declaration.', 'warning');
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/applications/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          service_code: selectedService.service_code,
          form_data: formData,
          purpose,
          declaration_accepted: declaration,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to submit application.');
      }

      const newApp = await response.json();
      addToast('Application Draft created. Please upload required files.', 'success');
      setSelectedApp(newApp); // Switch straight to uploads
      setSelectedService(null);
      setFormData({});
      setPurpose('');
      setDeclaration(false);
      setActiveTab('dashboard');
      loadCitizenData();
    } catch (err) {
      addToast(err.message, 'danger');
    }
  };

  // Handle file uploads
  const handleUploadFile = async (appId, docType, file) => {
    if (!file) return;
    
    setUploadProgress((prev) => ({ ...prev, [docType]: true }));
    const formPayload = new FormData();
    formPayload.append('file', file);

    try {
      const response = await fetch(
        `${API_BASE}/applications/${appId}/documents?document_type=${docType}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formPayload,
        }
      );

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'File upload failed.');
      }

      const data = await response.json();
      addToast(data.message, 'success');

      if (data.is_locked_and_submitted) {
        addToast('All documents uploaded! Genesis block generated and ledger state locked.', 'success');
      }

      // Reload selected application status & global lists
      const resSingle = await fetch(`${API_BASE}/applications/${appId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resSingle.ok) {
        const appDetail = await resSingle.json();
        setSelectedApp(appDetail);
      }
      loadCitizenData();
    } catch (err) {
      addToast(err.message, 'danger');
    } finally {
      setUploadProgress((prev) => ({ ...prev, [docType]: false }));
    }
  };

  // View certificate handler
  const handleViewCertificate = async (appId) => {
    try {
      const response = await fetch(`${API_BASE}/authorize/${appId}/certificate`);
      if (!response.ok) {
        throw new Error('Certificate not found or not yet signed.');
      }
      const data = await response.json();
      setCertificateData(data);
    } catch (err) {
      addToast(err.message, 'danger');
    }
  };

  // Render Auth panel if not logged in
  if (!token) {
    return (
      <div style={{ maxWidth: '480px', margin: '40px auto' }} className="glass-panel">
        <div style={{ padding: '32px' }}>
          <div style={{ textAlign: 'center', marginBottom: '28px' }}>
            <div style={{ display: 'inline-flex', background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-primary)', padding: '16px', borderRadius: '50%', marginBottom: '16px' }}>
              <Shield size={32} />
            </div>
            <h3 style={{ fontSize: '1.5rem' }}>Secure Citizen Onboarding</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '4px' }}>
              Verify identity using simulated Aadhaar (UIDAI) OTP checks.
            </p>
          </div>

          {authStep === 1 ? (
            <form onSubmit={handleRequestOtp} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Aadhaar Number (12 Digits)</label>
                <input
                  type="text"
                  maxLength={12}
                  className="form-input font-mono"
                  placeholder="Enter 12-digit Aadhaar"
                  value={aadhaar}
                  onChange={(e) => setAadhaar(e.target.value.replace(/\D/g, ''))}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Linked Mobile Phone</label>
                <input
                  type="tel"
                  maxLength={10}
                  className="form-input font-mono"
                  placeholder="Enter 10-digit Phone"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value.replace(/\D/g, ''))}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Verification CAPTCHA</label>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '8px' }}>
                  <div 
                    className="glass-panel" 
                    style={{ 
                      flex: 1, 
                      padding: '10px', 
                      textAlign: 'center', 
                      fontSize: '1.2rem', 
                      fontWeight: 700, 
                      letterSpacing: '4px',
                      background: 'rgba(255,255,255,0.03)',
                      color: 'var(--color-gold)'
                    }}
                  >
                    {captchaChallenge.text}
                  </div>
                  <button type="button" onClick={fetchCaptcha} className="btn btn-secondary" style={{ padding: '10px 14px' }}>
                    Refresh
                  </button>
                </div>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Enter CAPTCHA value"
                  value={captchaInput}
                  onChange={(e) => setCaptchaInput(e.target.value)}
                  required
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '8px' }}>
                Request Authentication OTP
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerifyRegister} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Enter verification OTP Code</label>
                <input
                  type="text"
                  maxLength={6}
                  className="form-input font-mono"
                  style={{ textAlign: 'center', fontSize: '1.5rem', letterSpacing: '8px' }}
                  placeholder="------"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                  required
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '6px', textAlign: 'center' }}>
                  Enter standard verification bypass code: <strong style={{ color: 'var(--color-primary)' }}>123456</strong>
                </span>
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
                <button type="button" onClick={() => setAuthStep(1)} className="btn btn-secondary" style={{ flex: 1 }}>
                  Back
                </button>
                <button type="submit" className="btn btn-primary" style={{ flex: 2 }}>
                  Verify & Login
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* Dashboard Top Navigation bar */}
      <div 
        className="glass-panel" 
        style={{ 
          padding: '12px 24px', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div style={{ display: 'flex', gap: '12px' }}>
          <button 
            onClick={() => { setActiveTab('dashboard'); setSelectedApp(null); }} 
            className={`btn ${activeTab === 'dashboard' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 16px', fontSize: '0.9rem' }}
          >
            Dashboard
          </button>
          <button 
            onClick={() => { setActiveTab('apply'); setSelectedApp(null); }} 
            className={`btn ${activeTab === 'apply' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 16px', fontSize: '0.9rem' }}
          >
            New Application
          </button>
          <button 
            onClick={() => { setActiveTab('profile'); setSelectedApp(null); }} 
            className={`btn ${activeTab === 'profile' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '8px 16px', fontSize: '0.9rem' }}
          >
            Profile
          </button>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Aadhaar Hash: <code className="font-mono">{profile?.aadhaar_hash?.substring(0, 12) || 'Loading...'}...</code>
        </div>
      </div>

      {/* Profile Tab View */}
      {activeTab === 'profile' && profile && (
        <div className="glass-panel" style={{ padding: '32px' }}>
          <h3 style={{ fontSize: '1.4rem', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <UserCheck color="var(--color-primary)" /> Immutable Aadhaar Ledger Identity
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '32px' }}>
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '16px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>FULL NAME</span>
              <p style={{ fontWeight: 600, fontSize: '1.1rem', marginTop: '4px' }}>{profile.full_name}</p>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '16px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>FATHER'S NAME</span>
              <p style={{ fontWeight: 600, fontSize: '1.1rem', marginTop: '4px' }}>{profile.father_name}</p>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '16px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>DATE OF BIRTH</span>
              <p style={{ fontWeight: 600, fontSize: '1.1rem', marginTop: '4px' }}>{profile.date_of_birth}</p>
            </div>
            <div style={{ background: 'rgba(0,0,0,0.15)', padding: '16px', borderRadius: '8px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PRIMARY PHONE</span>
              <p style={{ fontWeight: 600, fontSize: '1.1rem', marginTop: '4px' }}>{profile.phone_primary}</p>
            </div>
          </div>

          <h3 style={{ fontSize: '1.2rem', marginBottom: '16px' }}>Registered Addresses</h3>
          {profile.addresses && profile.addresses.length > 0 ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
              {profile.addresses.map((a) => (
                <div key={a.address_id} className="glass-panel" style={{ padding: '16px', backgroundColor: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span className="badge badge-submitted">{a.address_type}</span>
                    {a.is_primary && <span className="badge badge-approved">Primary</span>}
                  </div>
                  <p style={{ fontSize: '0.9rem', lineHeight: 1.4, color: 'var(--text-main)' }}>
                    House No. {a.house_no}, {a.street_locality}, {a.village_town}, Sub-Division: {a.sub_division}, District: {a.district}, PIN: {a.pin_code}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No address records added.</p>
          )}
        </div>
      )}

      {/* New Application Form Tab View */}
      {activeTab === 'apply' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {!selectedService ? (
            <div className="glass-panel" style={{ padding: '32px' }}>
              <h3 style={{ fontSize: '1.5rem', marginBottom: '8px' }}>Certificate Ingestion Catalog</h3>
              <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>Select an administrative certificate to apply for. All services lock onto the secure ledger database.</p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
                {services.map((s) => (
                  <div key={s.service_id} className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-primary)', fontWeight: 700 }}>{s.department}</span>
                      <h4 style={{ fontSize: '1.25rem', margin: '4px 0 8px' }}>{s.service_name}</h4>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: 1.4, marginBottom: '16px' }}>{s.description || 'Certificate request processing.'}</p>
                    </div>
                    <button 
                      onClick={() => {
                        setSelectedService(s);
                        // Setup default form fields based on backend schema and prefill profile values
                        const fields = {};
                        const primaryAddress = profile?.addresses?.find(a => a.is_primary) || profile?.addresses?.[0];
                        
                        (s.required_fields_schema?.fields || []).forEach(k => {
                          if (k === 'ApplicantName') fields[k] = profile?.full_name || '';
                          else if (k === 'Gender') fields[k] = profile?.gender || '';
                          else if (k === 'MobileNumber') fields[k] = profile?.phone_primary || '';
                          else if (k === 'District') fields[k] = primaryAddress?.district || '';
                          else if (k === 'SubDivision') fields[k] = primaryAddress?.sub_division || '';
                          else if (k === 'Circle') fields[k] = primaryAddress?.circle || '';
                          else if (k === 'Locality') fields[k] = primaryAddress?.street_locality || '';
                          else if (k === 'Pin Code') fields[k] = primaryAddress?.pin_code || '';
                          else if (k === 'SelectedOfficeDropdown') fields[k] = 'SDO-IW';
                          else if (k === 'DeclarationCheckbox') fields[k] = 'true';
                          else if (k === 'DateOfBirth') fields[k] = profile?.date_of_birth || '';
                          else fields[k] = '';
                        });
                        setFormData(fields);
                      }} 
                      className="btn btn-primary" 
                      style={{ width: '100%', padding: '10px' }}
                    >
                      Select Service
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="glass-panel" style={{ padding: '32px', maxWidth: '800px', margin: '0 auto', width: '100%' }}>
              <h3 style={{ fontSize: '1.5rem', marginBottom: '8px' }}>Application Form: {selectedService.service_name}</h3>
              <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>Enter validation parameters. Attributes will be cross-referenced with your locked profile.</p>
 
              <form onSubmit={handleApply} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                {(selectedService.required_fields_schema?.fields || []).map((fieldName) => {
                  const fieldLabel = fieldName.replace(/([A-Z])/g, ' $1').trim();
                  return (
                    <div key={fieldName} className="form-group">
                      <label className="form-label">{fieldLabel}</label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder={`Enter ${fieldLabel}`}
                        value={formData[fieldName] || ''}
                        onChange={(e) => setFormData({ ...formData, [fieldName]: e.target.value })}
                        required
                      />
                    </div>
                  );
                })}

                <div className="form-group">
                  <label className="form-label">Purpose of Application</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Admission, Higher Education, Job"
                    value={purpose}
                    onChange={(e) => setPurpose(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Processing Office</label>
                  <select className="form-input" required defaultValue="SDO-IW">
                    <option value="SDO-IW">Sub-Divisional Office, Imphal West (SDO-IW)</option>
                  </select>
                </div>

                <div style={{ background: 'rgba(245, 158, 11, 0.05)', border: '1px solid rgba(245, 158, 11, 0.2)', padding: '16px', borderRadius: '8px', marginBottom: '8px' }}>
                  <label style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={declaration}
                      onChange={(e) => setDeclaration(e.target.checked)}
                      style={{ marginTop: '4px' }}
                      required
                    />
                    <span style={{ fontSize: '0.85rem', lineHeight: 1.4, color: 'var(--text-main)' }}>
                      I hereby declare that all the information provided above is correct to the best of my knowledge, and I understand that any false statement will result in immediate cancellation of the certificate and legal prosecution under the Anti-Corruption Act.
                    </span>
                  </label>
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <button type="button" onClick={() => setSelectedService(null)} className="btn btn-secondary" style={{ flex: 1 }}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" style={{ flex: 2 }}>
                    Create Application Draft
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      )}

      {/* Citizen Dashboard Tab View */}
      {activeTab === 'dashboard' && (
        <div style={{ display: 'grid', gridTemplateColumns: selectedApp ? '1fr' : '1fr', gap: '24px' }}>
          
          {selectedApp ? (
            /* Document Upload Center Workspace */
            <div className="glass-panel" style={{ padding: '32px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid var(--border-muted)', paddingBottom: '16px' }}>
                <div>
                  <span className="badge badge-submitted" style={{ marginBottom: '4px' }}>{selectedApp.current_status}</span>
                  <h3 style={{ fontSize: '1.4rem' }}>Document Attachment Vault</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>ID: <code className="font-mono">{selectedApp.application_id}</code></p>
                </div>
                <button onClick={() => setSelectedApp(null)} className="btn btn-secondary" style={{ padding: '8px 16px' }}>
                  Back to Queue
                </button>
              </div>

              {selectedApp.current_status !== 'DRAFT' && selectedApp.current_status !== 'SUBMITTED' ? (
                <div style={{ background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '16px', borderRadius: '8px', display: 'flex', gap: '12px', marginBottom: '24px' }}>
                  <CheckCircle color="var(--color-success)" />
                  <div>
                    <h5 style={{ fontWeight: 600 }}>Documents Locked in Ledger</h5>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      This application has advanced past the ingestion state. All files have been sealed cryptographically and cannot be modified.
                    </p>
                  </div>
                </div>
              ) : (
                <div style={{ background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.2)', padding: '16px', borderRadius: '8px', display: 'flex', gap: '12px', marginBottom: '24px' }}>
                  <Layers color="var(--color-primary)" />
                  <div>
                    <h5 style={{ fontWeight: 600 }}>Ledger Genesis Pending</h5>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Upload all required files to compute the unified SHA-256 block hash. Once all documents check out, the block is sealed on the blockchain.
                    </p>
                  </div>
                </div>
              )}

              {/* Upload Workspace List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {services.find(s => s.service_id === selectedApp.service_id)?.required_documents_schema?.documents?.map((docType) => {
                  const label = docType.replace(/_/g, ' ');
                  const uploadedFile = selectedApp.documents.find(d => d.document_type === docType);
                  const isUploading = uploadProgress[docType];

                  return (
                    <div 
                      key={docType} 
                      className="glass-panel" 
                      style={{ 
                        padding: '16px 20px', 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        backgroundColor: uploadedFile ? 'rgba(16, 185, 129, 0.02)' : 'rgba(0,0,0,0.1)'
                      }}
                    >
                      <div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Required File Slot</span>
                        <h4 style={{ fontSize: '1rem', marginTop: '2px', textTransform: 'capitalize' }}>{label}</h4>
                        {uploadedFile && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            <FileText size={12} color="var(--color-success)" />
                            <span>{uploadedFile.original_filename}</span>
                            <span>•</span>
                            <span>{(uploadedFile.file_size_bytes / 1024).toFixed(1)} KB</span>
                            <span>•</span>
                            <code style={{ color: 'var(--color-gold)' }}>Hash: {uploadedFile.file_hash.substring(0, 10)}...</code>
                          </div>
                        )}
                      </div>

                      <div>
                        {uploadedFile ? (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: 'var(--color-success)', fontSize: '0.9rem', fontWeight: 600 }}>
                            <CheckCircle size={16} /> Attached
                          </span>
                        ) : (
                          <label className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '0.85rem', cursor: 'pointer' }}>
                            <Upload size={14} />
                            {isUploading ? 'Uploading...' : 'Upload PDF'}
                            <input
                              type="file"
                              accept="application/pdf,image/*"
                              style={{ display: 'none' }}
                              disabled={isUploading || selectedApp.current_status !== 'DRAFT'}
                              onChange={(e) => handleUploadFile(selectedApp.application_id, docType, e.target.files[0])}
                            />
                          </label>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

            </div>
          ) : (
            /* Citizen Applications Queue */
            <div className="glass-panel" style={{ padding: '32px' }}>
              <h3 style={{ fontSize: '1.5rem', marginBottom: '16px' }}>My Applications Dashboard</h3>
              
              {applications.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  <FileText size={48} style={{ opacity: 0.2, marginBottom: '16px' }} />
                  <p>You have not submitted any certificate applications yet.</p>
                  <button onClick={() => setActiveTab('apply')} className="btn btn-primary" style={{ marginTop: '16px' }}>
                    Create First Application
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {applications.map((app) => {
                    const serviceName = services.find(s => s.service_id === app.service_id)?.service_name || 'Certificate';
                    return (
                      <div key={app.application_id} className="glass-panel" style={{ padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <h4 style={{ fontSize: '1.15rem' }}>{serviceName}</h4>
                            <span className={`badge badge-${app.current_status.toLowerCase()}`}>{app.current_status}</span>
                          </div>
                          
                          <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            <span>ID: <code className="font-mono">{app.application_id}</code></span>
                            <span>•</span>
                            <span>Created: {new Date(app.created_at).toLocaleDateString()}</span>
                          </div>

                          {app.current_status === 'RETURNED' && app.return_reason && (
                            <div style={{ marginTop: '10px', background: 'rgba(139, 92, 246, 0.05)', border: '1px solid rgba(139, 92, 246, 0.2)', padding: '10px 14px', borderRadius: '6px', fontSize: '0.85rem' }}>
                              <strong style={{ color: 'var(--color-accent)' }}>Query/Remark from Official:</strong> {app.return_reason}
                            </div>
                          )}
                        </div>

                        <div style={{ display: 'flex', gap: '10px' }}>
                          <button 
                            onClick={() => setSelectedApp(app)} 
                            className="btn btn-secondary" 
                            style={{ padding: '8px 14px', fontSize: '0.85rem' }}
                          >
                            <Eye size={14} /> View Files ({app.documents.length})
                          </button>

                          {app.current_status === 'APPROVED' && (
                            <button 
                              onClick={() => handleViewCertificate(app.application_id)}
                              className="btn btn-success" 
                              style={{ padding: '8px 14px', fontSize: '0.85rem' }}
                            >
                              <Download size={14} /> View Certificate
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

          )}

        </div>
      )}

      {/* Certificate Modal Viewer */}
      {certificateData && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.85)',
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
              maxWidth: '650px',
              backgroundColor: '#ffffff',
              color: '#111827',
              padding: '40px',
              borderRadius: '8px',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
              fontFamily: 'serif',
              position: 'relative'
            }}
          >
            {/* Certificate Style Shell */}
            <div style={{ border: '8px double #1f2937', padding: '24px', textAlign: 'center' }}>
              <span style={{ fontSize: '0.9rem', letterSpacing: '2px', textTransform: 'uppercase', color: '#4b5563', display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
                Government of Manipur
              </span>
              <h2 style={{ fontSize: '2rem', color: '#1f2937', marginBottom: '16px', fontFamily: 'serif' }}>
                Office of the Sub-Divisional Magistrate
              </h2>
              
              <div style={{ width: '80px', height: '2px', backgroundColor: '#1f2937', margin: '0 auto 20px' }} />

              <span style={{ fontSize: '1rem', fontStyle: 'italic', color: '#4b5563', display: 'block', marginBottom: '8px' }}>
                This is to certify that
              </span>
              <h3 style={{ fontSize: '1.6rem', color: '#111827', margin: '4px 0', fontWeight: 'bold' }}>
                {profile?.full_name}
              </h3>
              <span style={{ fontSize: '0.9rem', color: '#4b5563', display: 'block' }}>
                Son/Daughter of <strong style={{ color: '#111827' }}>{profile?.father_name}</strong>
              </span>

              <p style={{ margin: '20px auto', fontSize: '1rem', lineHeight: 1.6, color: '#1f2937', maxWidth: '500px' }}>
                has been verified as belonging to the <strong style={{ textTransform: 'uppercase' }}>{certificateData.certificate_type}</strong> category under the state regulations.
              </p>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '36px', padding: '0 16px' }}>
                <div style={{ textAlign: 'left', fontSize: '0.85rem', color: '#4b5563' }}>
                  <p>Certificate No: <strong style={{ color: '#111827' }}>{certificateData.certificate_number}</strong></p>
                  <p>Issued On: {new Date(certificateData.issued_at).toLocaleDateString()}</p>
                </div>
                
                {/* QR Block Code representation */}
                <div style={{ textAlign: 'center' }}>
                  <div 
                    style={{ 
                      width: '75px', 
                      height: '75px', 
                      backgroundColor: '#111827', 
                      margin: '0 auto 4px', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      color: '#ffffff',
                      fontSize: '8px',
                      fontWeight: 'bold',
                      flexDirection: 'column'
                    }}
                  >
                    <span>SECURE QR</span>
                    <span style={{ fontSize: '6px', opacity: 0.7 }}>{certificateData.qr_code_hash.substring(0, 8)}</span>
                  </div>
                  <span style={{ fontSize: '0.65rem', color: '#6b7280', display: 'block' }}>Verify on Ledger</span>
                </div>

                <div style={{ textAlign: 'right', fontSize: '0.85rem' }}>
                  <p style={{ fontWeight: 'bold', fontStyle: 'italic', textDecoration: 'underline' }}>SDO Magistrate</p>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280' }}>Digitally Signed DSC</p>
                </div>
              </div>
            </div>

            <button 
              onClick={() => setCertificateData(null)} 
              className="btn btn-secondary" 
              style={{ width: '100%', marginTop: '24px', backgroundColor: '#f3f4f6', color: '#111827', borderColor: '#d1d5db' }}
            >
              Close
            </button>
          </div>
        </div>
      )}

    </div>
  );
}

export default CitizenPortal;
