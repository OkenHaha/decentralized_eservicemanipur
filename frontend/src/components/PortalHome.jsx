import React, { useState } from 'react';
import { Search, ShieldAlert, Cpu, HardDrive, CheckCircle2, ChevronRight, AlertCircle, Copy, Check } from 'lucide-react';
import { API_BASE } from '../App';

function PortalHome({ setView, token, addToast }) {
  const [appId, setAppId] = useState('');
  const [blocks, setBlocks] = useState(null);
  const [integrity, setIntegrity] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState('');

  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    addToast('Copied hash to clipboard.', 'info');
    setTimeout(() => setCopiedId(''), 2000);
  };

  const handleAudit = async (e) => {
    e.preventDefault();
    if (!appId.trim()) return;

    setLoading(true);
    setBlocks(null);
    setIntegrity(null);

    try {
      // 1. Fetch blocks
      const resBlocks = await fetch(`${API_BASE}/audit/${appId.trim()}`);
      if (!resBlocks.ok) {
        throw new Error('No ledger entries found for this application ID.');
      }
      const blocksData = await resBlocks.json();
      setBlocks(blocksData);

      // 2. Fetch integrity check
      const resIntegrity = await fetch(`${API_BASE}/audit/${appId.trim()}/verify-integrity`);
      if (resIntegrity.ok) {
        const integrityData = await resIntegrity.json();
        setIntegrity(integrityData);
      }
    } catch (err) {
      addToast(err.message, 'danger');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '48px', padding: '16px 0' }}>

      {/* Hero Section */}
      <section
        className="glass-panel"
        style={{
          padding: '60px 40px',
          textAlign: 'center',
          background: 'radial-gradient(ellipse at center, rgba(37, 99, 235, 0.1) 0%, transparent 70%), var(--bg-card)',
          borderRadius: '24px',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <div style={{ position: 'absolute', top: '-10%', left: '-10%', width: '300px', height: '300px', borderRadius: '50%', background: 'rgba(139, 92, 246, 0.05)', filter: 'blur(80px)' }} />
        <div style={{ position: 'absolute', bottom: '-10%', right: '-10%', width: '300px', height: '300px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.05)', filter: 'blur(80px)' }} />

        <h1 style={{ fontSize: '3rem', marginBottom: '16px', lineHeight: 1.15, fontWeight: 800 }}>
          <span style={{ color: 'var(--color-primary)' }}>e-service Manipur</span> Replica
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.2rem', maxWidth: '800px', margin: '0 auto 32px', lineHeight: 1.6 }}>
          A secure governance framework implementing Manipur's e-Seba certificate issuance protocol. Complete with a cryptographic, hash-chained database ledger protecting against document tampering, unauthorized edits, and backdated approvals.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <button onClick={() => setView('citizen')} className="btn btn-primary">
            Access Citizen Workspace <ChevronRight size={18} />
          </button>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="btn btn-secondary">
            Explore API Documentation
          </a>
        </div>
      </section>

      {/* Feature Grid */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <h2 style={{ fontSize: '1.5rem', textAlign: 'center', marginBottom: '8px' }}>Security & Ledger Mechanism</h2>
        <div className="portal-grid">

          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--color-primary)', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
              <Cpu size={24} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Aadhaar Identity Registry</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5 }}>
              Onboard citizen credentials through simulated UIDAI registry mappings. Freezes primary attributes like name, DOB, and primary address to block identity falsification.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--color-success)', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
              <HardDrive size={24} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Anti-Tamper Sealing</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5 }}>
              Generates a SHA-256 hash fingerprint of all required files. If a file is modified on disk after submission, the inspection checker immediately reports a checksum mismatch.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ background: 'rgba(139, 92, 246, 0.1)', color: 'var(--color-accent)', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
              <Search size={24} />
            </div>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '8px' }}>Public Ledger Audit</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5 }}>
              Any user can trace the complete chain of administrative steps backwards from the SDO's final decision block to the original submission genesis block, ensuring total transparency.
            </p>
          </div>

        </div>
      </section>

      {/* Public Audit Verification System */}
      <section className="glass-panel" style={{ padding: '32px' }}>
        <h2 style={{ fontSize: '1.6rem', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Search color="var(--color-primary)" /> Verify Application Blockchain Ledger
        </h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '24px', maxWidth: '800px', fontSize: '0.95rem' }}>
          Enter a tracking Application ID (e.g. from your Citizen dashboard, or one generated by seeders) to load the blockchain ledger sequence and verify that the data hasn't been edited.
        </p>

        <form onSubmit={handleAudit} style={{ display: 'flex', gap: '12px', marginBottom: '32px', flexWrap: 'wrap' }}>
          <input
            type="text"
            className="form-input"
            placeholder="Enter Application ID (e.g. app-123...)"
            value={appId}
            onChange={(e) => setAppId(e.target.value)}
            style={{ flex: 1, minWidth: '250px' }}
          />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Running Audit...' : 'Audit Ledger'}
          </button>
        </form>

        {loading && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div className="animate-spin-slow" style={{ border: '4px solid rgba(255,255,255,0.1)', borderTopColor: 'var(--color-primary)', borderRadius: '50%', width: '40px', height: '40px', margin: '0 auto 16px' }} />
            <p style={{ color: 'var(--text-muted)' }}>Retrieving ledger sequence blocks and validating hash links...</p>
          </div>
        )}

        {/* Audit Trail Results */}
        {blocks && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

            {/* Integrity Header */}
            {integrity && (
              <div
                className="glass-panel"
                style={{
                  padding: '20px 24px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderLeft: `4px solid ${integrity.is_integrity_intact ? 'var(--color-success)' : 'var(--color-danger)'}`,
                  backgroundColor: integrity.is_integrity_intact ? 'rgba(16, 185, 129, 0.03)' : 'rgba(239, 68, 68, 0.03)'
                }}
              >
                <div>
                  <h4 style={{ fontSize: '1.1rem', color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {integrity.is_integrity_intact ? (
                      <span style={{ color: 'var(--color-success)' }}>LEDGER INTEGRITY SECURE</span>
                    ) : (
                      <span style={{ color: 'var(--color-danger)' }}>WARNING: CHAIN TAMPERED</span>
                    )}
                  </h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {integrity.is_integrity_intact
                      ? 'Chronological block hashes verified sequentially. The document fingerprint, inspection report, and SDO signature are linked securely.'
                      : 'Hash verification failed. The backend detected a block mismatch or manual row modification in the database ledger.'}
                  </p>
                </div>
                <span className={`badge ${integrity.is_integrity_intact ? 'badge-approved' : 'badge-rejected'}`}>
                  {integrity.status}
                </span>
              </div>
            )}

            {/* Blocks List */}
            <h3 style={{ fontSize: '1.2rem', borderBottom: '1px solid var(--border-muted)', paddingBottom: '10px' }}>Ledger Block Sequences</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', position: 'relative', paddingLeft: '24px' }}>
              <div style={{ position: 'absolute', left: '7px', top: '24px', bottom: '24px', width: '2px', backgroundColor: 'var(--border-muted)' }} />

              {blocks.map((block, index) => {
                const isGenesis = block.block_type === 'GENESIS';
                const isVerify = block.block_type === 'VERIFICATION';
                const isApprove = block.block_type === 'APPROVAL';

                return (
                  <div key={block.block_id} className="glass-panel" style={{ padding: '24px', position: 'relative' }}>
                    {/* Bullet Indicator */}
                    <div
                      style={{
                        position: 'absolute',
                        left: '-23px',
                        top: '28px',
                        width: '14px',
                        height: '14px',
                        borderRadius: '50%',
                        backgroundColor: isApprove ? 'var(--color-success)' : isVerify ? 'var(--color-warning)' : 'var(--color-primary)',
                        border: '3px solid var(--bg-base)',
                        boxShadow: isApprove ? '0 0 10px var(--color-success)' : 'none'
                      }}
                    />

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
                      <div>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-gold)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
                          BLOCK #{block.block_index} • {block.block_type}
                        </span>
                        <h4 style={{ fontSize: '1.2rem', marginTop: '2px' }}>
                          {isGenesis && 'Genesis Verification Setup Locked'}
                          {isVerify && 'Field Inspector (Lambu) Signed Verdict'}
                          {isApprove && 'Final SDO Magistrate Issuance Block'}
                        </h4>
                      </div>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {new Date(block.timestamp).toLocaleString()}
                      </span>
                    </div>

                    <div
                      style={{
                        background: 'rgba(0,0,0,0.2)',
                        padding: '16px',
                        borderRadius: '8px',
                        fontSize: '0.85rem',
                        marginBottom: '16px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '10px'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Block Hash:</span>
                        <code className="font-mono" style={{ color: '#ffffff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          {block.block_hash.substring(0, 16)}...{block.block_hash.substring(48)}
                          <button
                            type="button"
                            onClick={() => handleCopy(block.block_hash, `${block.block_id}_hash`)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
                          >
                            {copiedId === `${block.block_id}_hash` ? <Check size={14} color="var(--color-success)" /> : <Copy size={14} />}
                          </button>
                        </code>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Previous Block Hash:</span>
                        <code className="font-mono" style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          {block.prev_block_hash ? (
                            <>
                              {block.prev_block_hash.substring(0, 16)}...{block.prev_block_hash.substring(48)}
                              <button
                                type="button"
                                onClick={() => handleCopy(block.prev_block_hash, `${block.block_id}_prev`)}
                                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
                              >
                                {copiedId === `${block.block_id}_prev` ? <Check size={14} color="var(--color-success)" /> : <Copy size={14} />}
                              </button>
                            </>
                          ) : (
                            'GENESIS (NULL)'
                          )}
                        </code>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Aggregate Data Fingerprint:</span>
                        <code className="font-mono" style={{ color: 'var(--color-gold)' }}>
                          {block.aggregate_data_hash.substring(0, 20)}...
                        </code>
                      </div>
                    </div>

                    {/* Block Specific Data Payload */}
                    <div style={{ fontSize: '0.9rem' }}>
                      {isGenesis && (
                        <p style={{ color: 'var(--text-muted)' }}>
                          Locked all {Object.keys(block.payload || {}).length || 'required'} files. Anchored initial document state fingerprints.
                        </p>
                      )}
                      {isVerify && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          <div>
                            <strong style={{ color: 'var(--text-main)' }}>Inspector Verdict: </strong>
                            <span className={`badge ${block.payload?.verdict === 'VERIFIED' ? 'badge-approved' : 'badge-rejected'}`}>
                              {block.payload?.verdict}
                            </span>
                          </div>
                          <div>
                            <strong style={{ color: 'var(--text-main)' }}>Digital Signature Token: </strong>
                            <code className="font-mono" style={{ color: 'var(--color-primary)' }}>{block.payload?.lambu_signature_token}</code>
                          </div>
                        </div>
                      )}
                      {isApprove && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          <div>
                            <strong style={{ color: 'var(--text-main)' }}>SDO Decision: </strong>
                            <span className="badge badge-approved">{block.payload?.decision}</span>
                          </div>
                          <div>
                            <strong style={{ color: 'var(--text-main)' }}>Authority Signature: </strong>
                            <code className="font-mono" style={{ color: 'var(--color-success)' }}>{block.payload?.sdo_signature_token}</code>
                          </div>
                        </div>
                      )}
                    </div>

                  </div>
                );
              })}

            </div>
          </div>
        )}

      </section>

    </div>
  );
}

export default PortalHome;
