import React, { useState, useEffect } from 'react';
import { Layers, FileText, CheckCircle, XCircle, FileSpreadsheet, Eye, User, Edit3, Send, Signature, HelpCircle, ArrowLeft } from 'lucide-react';
import { API_BASE } from '../App';

function OfficialPortal({ token, user, addToast }) {
  const [queue, setQueue] = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);
  const [loading, setLoading] = useState(false);

  // Lambu Field Inspection Verification States
  const [lambuVerdict, setLambuVerdict] = useState('VALID');
  const [lambuFindings, setLambuFindings] = useState('');
  const [lambuRecommendation, setLambuRecommendation] = useState('');
  const [lambuLocation, setLambuLocation] = useState('');
  const [checklist, setChecklist] = useState({
    IsAddressMatch: true,
    IsIdentityVerified: true,
    IsCasteMatch: true
  });
  const [lambuSignature, setLambuSignature] = useState('0xLAMBU_KEY_IMPHAL_WEST');

  // SDO Approval Decision States
  const [sdoDecision, setSdoDecision] = useState('ISSUE');
  const [sdoSignature, setSdoSignature] = useState('0xSDO_KEY_IMPHAL_WEST');

  // Query / Remarks states
  const [remarkText, setRemarkText] = useState('');
  const [requireCitizenResponse, setRequireCitizenResponse] = useState(false);
  const [submittingRemark, setSubmittingRemark] = useState(false);

  const isLambu = user?.role === 'REVENUE_LAMBU';
  const isSDO = user?.role === 'SDO' || user?.role === 'SDC';

  // Load Queue
  const loadQueue = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/admin/queue`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch official workspace queue.');
      }

      const data = await response.json();
      setQueue(data);
    } catch (err) {
      addToast(err.message, 'danger');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [token]);

  // Set default values depending on active profile loaded
  useEffect(() => {
    if (user?.id === 'lambu-imphal-west') {
      setLambuSignature('0xLAMBU_KEY_IMPHAL_WEST');
    } else if (user?.id === 'sdo-imphal-west') {
      setSdoSignature('0xSDO_KEY_IMPHAL_WEST');
    } else if (user?.id === 'sdc-lamphel') {
      setSdoSignature('0xSDC_KEY_LAMPHEL');
    }
  }, [user]);

  // Submit Lambu Verification
  const handleSubmitVerification = async (e) => {
    e.preventDefault();
    if (!lambuFindings) {
      addToast('Please provide findings details.', 'warning');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/verify/${selectedApp.application_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          verdict: lambuVerdict,
          findings: lambuFindings,
          recommendation: lambuRecommendation,
          visit_location: lambuLocation,
          checklist_responses: checklist,
          lambu_signature_token: lambuSignature
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to submit verification check.');
      }

      addToast('Field inspection report successfully signed and locked on blockchain ledger.', 'success');
      setSelectedApp(null);
      // Reset forms
      setLambuFindings('');
      setLambuRecommendation('');
      setLambuLocation('');
      loadQueue();
    } catch (err) {
      addToast(err.message, 'danger');
    } finally {
      setLoading(false);
    }
  };

  // Submit SDO Approval
  const handleSubmitSDOApproval = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/authorize/${selectedApp.application_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          decision: sdoDecision,
          sdo_signature_token: sdoSignature
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Final decision signature failed.');
      }

      if (sdoDecision === 'ISSUE') {
        const cert = await response.json();
        addToast(`Approved! Certificate ${cert.certificate_number} minted on ledger chain.`, 'success');
      } else {
        addToast('Application rejected. Ledgers marked accordingly.', 'warning');
      }

      setSelectedApp(null);
      loadQueue();
    } catch (err) {
      addToast(err.message, 'danger');
    } finally {
      setLoading(false);
    }
  };

  // Add application remark
  const handleAddRemark = async (e) => {
    e.preventDefault();
    if (!remarkText.trim()) return;

    setSubmittingRemark(true);
    try {
      const response = await fetch(`${API_BASE}/admin/remarks/${selectedApp.application_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          remark_text: remarkText.trim(),
          requires_citizen_response: requireCitizenResponse
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to submit comment remark.');
      }

      addToast(requireCitizenResponse ? 'Remarks sent. Application returned to citizen.' : 'Remark comment added.', 'success');
      setRemarkText('');
      setRequireCitizenResponse(false);
      
      // If returned to citizen, go back to queue since it leaves current office queue status
      if (requireCitizenResponse) {
        setSelectedApp(null);
        loadQueue();
      }
    } catch (err) {
      addToast(err.message, 'danger');
    } finally {
      setSubmittingRemark(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* Official Dashboard header */}
      <div 
        className="glass-panel" 
        style={{ 
          padding: '20px 28px', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          borderLeft: '4px solid var(--color-success)'
        }}
      >
        <div>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-success)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
            Government of Manipur • Officer Panel
          </span>
          <h2 style={{ fontSize: '1.4rem', marginTop: '2px' }}>Workspace: {user?.name}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Role Authority: <span style={{ color: '#ffffff', fontWeight: 600 }}>{user?.role}</span></p>
        </div>
        <button onClick={loadQueue} className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
          Refresh Queue
        </button>
      </div>

      {selectedApp ? (
        /* Workspace Application Review Panel */
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px' }}>
          
          <div className="glass-panel" style={{ padding: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid var(--border-muted)', paddingBottom: '16px' }}>
              <div>
                <button onClick={() => setSelectedApp(null)} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem', display: 'inline-flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                  <ArrowLeft size={14} /> Back to Queue
                </button>
                <h3 style={{ fontSize: '1.4rem' }}>Review Workspace</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Application ID: <code className="font-mono">{selectedApp.application_id}</code></p>
              </div>
              <span className={`badge badge-${selectedApp.current_status.toLowerCase()}`}>{selectedApp.current_status}</span>
            </div>

            {/* Ingestion Data */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', marginBottom: '32px' }}>
              <div>
                <h4 style={{ fontSize: '1.1rem', marginBottom: '12px', borderBottom: '1px solid var(--border-muted)', paddingBottom: '6px' }}>Application Parameters</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.9rem' }}>
                  {Object.entries(selectedApp.form_data || {}).map(([k, v]) => (
                    <div key={k}>
                      <span style={{ color: 'var(--text-muted)' }}>{k.replace(/([A-Z])/g, ' $1')}: </span>
                      <strong style={{ color: '#ffffff' }}>{v}</strong>
                    </div>
                  ))}
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Purpose: </span>
                    <strong style={{ color: '#ffffff' }}>{selectedApp.purpose}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Submitted at: </span>
                    <span>{new Date(selectedApp.submitted_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 style={{ fontSize: '1.1rem', marginBottom: '12px', borderBottom: '1px solid var(--border-muted)', paddingBottom: '6px' }}>Uploaded Documents ({selectedApp.documents.length})</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {selectedApp.documents.map((doc) => (
                    <div key={doc.document_id} style={{ background: 'rgba(0,0,0,0.15)', padding: '10px 14px', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                      <div>
                        <p style={{ fontWeight: 600, textTransform: 'capitalize' }}>{doc.document_type.replace(/_/g, ' ')}</p>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{doc.original_filename} ({(doc.file_size_bytes / 1024).toFixed(0)} KB)</p>
                      </div>
                      <a 
                        href={`http://localhost:8000/api/v1/applications/mine`} // Simple bypass to show they check
                        target="_blank" 
                        rel="noreferrer"
                        className="btn btn-secondary" 
                        style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                      >
                        <Eye size={12} /> Inspect File
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Workflow Decisional Action Panels */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
              
              {/* Lambu Inspection Actions */}
              {isLambu && selectedApp.current_status === 'SUBMITTED' && (
                <div className="glass-panel" style={{ padding: '24px', borderColor: 'rgba(245, 158, 11, 0.2)' }}>
                  <h4 style={{ fontSize: '1.15rem', marginBottom: '16px', color: 'var(--color-warning)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Signature /> Lambu Field Inspection
                  </h4>
                  <form onSubmit={handleSubmitVerification} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    <div className="form-group">
                      <label className="form-label">Inspection Verdict</label>
                      <select className="form-input" value={lambuVerdict} onChange={(e) => setLambuVerdict(e.target.value)}>
                        <option value="VALID">VALID (Documents & Address verified)</option>
                        <option value="INVALID">INVALID (Tampered / Address mismatch)</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Visit / Verification Location</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        placeholder="e.g. Kwakeithel Ward No 4" 
                        value={lambuLocation}
                        onChange={(e) => setLambuLocation(e.target.value)}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Findings & Remarks</label>
                      <textarea 
                        className="form-input" 
                        style={{ minHeight: '80px', fontFamily: 'inherit' }}
                        placeholder="Detail physical confirmation findings..."
                        value={lambuFindings}
                        onChange={(e) => setLambuFindings(e.target.value)}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label className="form-label">Recommendation for SDO</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        placeholder="e.g. Recommended for certificate approval"
                        value={lambuRecommendation}
                        onChange={(e) => setLambuRecommendation(e.target.value)}
                      />
                    </div>

                    {/* Inspection checklists */}
                    <div style={{ background: 'rgba(0,0,0,0.15)', padding: '12px', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <span className="form-label" style={{ fontSize: '0.75rem', marginBottom: '2px' }}>Circle Verification Checklist</span>
                      <label style={{ display: 'flex', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
                        <input type="checkbox" checked={checklist.IsAddressMatch} onChange={(e) => setChecklist({ ...checklist, IsAddressMatch: e.target.checked })} />
                        <span>Physical Address Checks Out</span>
                      </label>
                      <label style={{ display: 'flex', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
                        <input type="checkbox" checked={checklist.IsIdentityVerified} onChange={(e) => setChecklist({ ...checklist, IsIdentityVerified: e.target.checked })} />
                        <span>Identity cross-referenced in registry</span>
                      </label>
                      <label style={{ display: 'flex', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
                        <input type="checkbox" checked={checklist.IsCasteMatch} onChange={(e) => setChecklist({ ...checklist, IsCasteMatch: e.target.checked })} />
                        <span>Sub-caste matches official gazette</span>
                      </label>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Inspector Cryptographic DSC Wallet Signature</label>
                      <input 
                        type="text" 
                        className="form-input font-mono" 
                        value={lambuSignature} 
                        onChange={(e) => setLambuSignature(e.target.value)}
                        required 
                      />
                    </div>

                    <button type="submit" className="btn btn-warning" style={{ width: '100%' }}>
                      Submit & Sign Block
                    </button>
                  </form>
                </div>
              )}

              {/* SDO final approval Actions */}
              {isSDO && selectedApp.current_status === 'FIELD_VERIFIED' && (
                <div className="glass-panel" style={{ padding: '24px', borderColor: 'rgba(16, 185, 129, 0.2)' }}>
                  <h4 style={{ fontSize: '1.15rem', marginBottom: '16px', color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Signature /> SDO Final Decision Approval
                  </h4>
                  <form onSubmit={handleSubmitSDOApproval} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div className="form-group">
                      <label className="form-label">Select Final Decision</label>
                      <select className="form-input" value={sdoDecision} onChange={(e) => setSdoDecision(e.target.value)}>
                        <option value="ISSUE">ISSUE (Approve and mint certificate)</option>
                        <option value="DENY">DENY (Reject application)</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">SDO Cryptographic DSC Signature Token</label>
                      <input 
                        type="text" 
                        className="form-input font-mono" 
                        value={sdoSignature}
                        onChange={(e) => setSdoSignature(e.target.value)}
                        required 
                      />
                    </div>

                    <button type="submit" className="btn btn-success" style={{ width: '100%' }}>
                      Approve & Mint Certificate
                    </button>
                  </form>
                </div>
              )}

              {/* Admin Remark Query form */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <h4 style={{ fontSize: '1.15rem', marginBottom: '16px', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Edit3 size={18} /> Administrative Remark / Query
                </h4>
                <form onSubmit={handleAddRemark} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <div className="form-group">
                    <label className="form-label">Query Text</label>
                    <textarea 
                      className="form-input" 
                      style={{ minHeight: '80px', fontFamily: 'inherit' }}
                      placeholder="Ask citizen for missing fields, updates, or clarify details..."
                      value={remarkText}
                      onChange={(e) => setRemarkText(e.target.value)}
                      required
                    />
                  </div>

                  <div style={{ background: 'rgba(139, 92, 246, 0.05)', padding: '12px', borderRadius: '8px', marginBottom: '4px' }}>
                    <label style={{ display: 'flex', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
                      <input 
                        type="checkbox" 
                        checked={requireCitizenResponse} 
                        onChange={(e) => setRequireCitizenResponse(e.target.checked)} 
                      />
                      <span>Return application to Citizen (Requires updates)</span>
                    </label>
                  </div>

                  <button type="submit" className="btn btn-secondary" style={{ width: '100%' }} disabled={submittingRemark}>
                    {submittingRemark ? 'Posting...' : 'Post Remark'}
                  </button>
                </form>
              </div>

            </div>

          </div>

        </div>
      ) : (
        /* Applications Review Queue List */
        <div className="glass-panel" style={{ padding: '32px' }}>
          <h3 style={{ fontSize: '1.4rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers color="var(--color-primary)" /> Ingestion Inspection Queue
          </h3>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px', fontSize: '0.9rem' }}>
            {isLambu && 'List of newly SUBMITTED applications requiring Circle Lambu physical checkups and local verifications.'}
            {isSDO && 'List of FIELD_VERIFIED applications requiring final SDO approval signature to mint certificate.'}
          </p>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <div className="animate-spin-slow" style={{ border: '4px solid rgba(255,255,255,0.1)', borderTopColor: 'var(--color-primary)', borderRadius: '50%', width: '40px', height: '40px', margin: '0 auto 16px' }} />
              <p style={{ color: 'var(--text-muted)' }}>Fetching queue list...</p>
            </div>
          ) : queue.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
              <CheckCircle size={40} style={{ color: 'var(--color-success)', opacity: 0.4, marginBottom: '16px' }} />
              <p style={{ fontWeight: 600, color: '#ffffff' }}>Your review queue is clear!</p>
              <p style={{ fontSize: '0.85rem', marginTop: '4px' }}>All certificate requests for your office have been processed.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {queue.map((app) => (
                <div 
                  key={app.application_id} 
                  className="glass-panel" 
                  style={{ 
                    padding: '20px 24px', 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '16px',
                    backgroundColor: 'rgba(255, 255, 255, 0.01)'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <h4 style={{ fontSize: '1.15rem' }}>
                        {app.form_data?.ApplicantName || 'Citizen Request'}
                      </h4>
                      <span className={`badge badge-${app.current_status.toLowerCase()}`}>{app.current_status}</span>
                    </div>

                    <div style={{ display: 'flex', gap: '16px', marginTop: '6px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      <span>Tracking ID: <code className="font-mono">{app.application_id}</code></span>
                      <span>•</span>
                      <span>Purpose: {app.purpose}</span>
                    </div>
                  </div>

                  <button 
                    onClick={() => setSelectedApp(app)} 
                    className="btn btn-primary" 
                    style={{ padding: '8px 16px', fontSize: '0.85rem' }}
                  >
                    Open Review Workspace
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

    </div>
  );
}

export default OfficialPortal;
