import { X, FileText, Shield, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function ProposalViewerModal({ isOpen, onClose, proposalDetails, filename, companyName }) {
  if (!isOpen) return null;

  const details = proposalDetails || {};
  const coverages = details.proposed_coverages || ["Commercial Property", "Cyber Risk", "Liability"];
  const conditions = details.underwriting_conditions || [];
  const exclusions = details.key_exclusions || [];

  const fileUrl = details.file_url || 'http://localhost:8000/uploads/proposals/Commercial_Insurance_Proposal_HDFC_ERGO.pdf';

  const handleOpenOriginalFile = () => {
    window.open(fileUrl, '_blank');
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(5px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 99999,
      padding: '1.25rem'
    }} onClick={onClose}>
      <div style={{
        background: '#ffffff',
        borderRadius: '16px',
        maxWidth: '680px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'hidden',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        display: 'flex',
        flexDirection: 'column',
        border: '1px solid #cbd5e1'
      }} onClick={(e) => e.stopPropagation()}>
        
        {/* Modal Header */}
        <div style={{
          background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)',
          color: '#ffffff',
          padding: '1.25rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #3b82f6'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div style={{ background: '#2563eb', padding: '0.5rem', borderRadius: '8px', display: 'flex' }}>
              <FileText size={20} color="#ffffff" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0, color: '#ffffff' }}>
                {details.proposal_title || "Commercial Insurance Proposal"}
              </h3>
              <div style={{ fontSize: '0.78rem', color: '#93c5fd', marginTop: '0.15rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span 
                  onClick={handleOpenOriginalFile}
                  style={{ textDecoration: 'underline', cursor: 'pointer', fontWeight: 700 }}
                  title="Click to view/download original document"
                >
                  📄 {filename || "Commercial_Insurance_Proposal_HDFC_ERGO.pdf"} ↗
                </span>
                <span>•</span>
                <span>Insured: {companyName || "Target Prospect"}</span>
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: 'none',
              cursor: 'pointer',
              color: '#ffffff',
              padding: '0.4rem',
              borderRadius: '6px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div style={{ padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Direct File Banner */}
          <div style={{
            background: '#f0f9ff',
            border: '1px solid #bae6fd',
            borderRadius: '10px',
            padding: '0.85rem 1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '0.5rem'
          }}>
            <div style={{ fontSize: '0.85rem', color: '#0369a1', fontWeight: 600 }}>
              📄 Original Source File: <strong>{filename || "Commercial_Insurance_Proposal_HDFC_ERGO.pdf"}</strong>
            </div>
            <button
              onClick={handleOpenOriginalFile}
              style={{
                background: '#0284c7',
                color: '#ffffff',
                border: 'none',
                padding: '0.35rem 0.85rem',
                borderRadius: '6px',
                fontSize: '0.8rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.3rem',
                flexShrink: 0
              }}
            >
              Open Original PDF ↗
            </button>
          </div>

          {/* Key Proposal Financial Summary Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '0.85rem'
          }}>
            <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '10px', padding: '0.85rem' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#2563eb', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                Total Sum Insured / Limit
              </div>
              <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#1e3a8a' }}>
                {details.total_sum_insured || "USD $50,000,000"}
              </div>
            </div>

            <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '10px', padding: '0.85rem' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#16a34a', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                Proposed Premium
              </div>
              <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#14532d' }}>
                {details.proposed_premium || "USD $245,000 / Annual"}
              </div>
            </div>

            <div style={{ background: '#fefce8', border: '1px solid #fef08a', borderRadius: '10px', padding: '0.85rem' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 800, color: '#ca8a04', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                Policy Deductible / Retention
              </div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#713f12' }}>
                {details.deductibles_and_retentions || "USD $50,000 per claim"}
              </div>
            </div>
          </div>

          {/* 1. Proposed Coverages */}
          <div>
            <h4 style={{ fontSize: '0.82rem', fontWeight: 800, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <Shield size={15} color="#2563eb" /> Proposed Coverages & Scope ({coverages.length})
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem' }}>
              {Array.isArray(coverages) && coverages.map((cov, idx) => (
                <span key={idx} style={{
                  background: '#f1f5f9',
                  border: '1px solid #cbd5e1',
                  color: '#0f172a',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                  padding: '0.35rem 0.75rem',
                  borderRadius: '6px'
                }}>
                  ✓ {cov}
                </span>
              ))}
            </div>
          </div>

          {/* 2. Mandatory Underwriting Conditions */}
          <div>
            <h4 style={{ fontSize: '0.82rem', fontWeight: 800, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <CheckCircle2 size={15} color="#16a34a" /> Mandatory Underwriting Conditions
            </h4>
            {conditions.length > 0 ? (
              <ul style={{ margin: 0, paddingLeft: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {conditions.map((cond, idx) => (
                  <li key={idx} style={{ fontSize: '0.86rem', color: '#334155', background: '#f8fafc', border: '1px solid #e2e8f0', padding: '0.5rem 0.75rem', borderRadius: '6px', display: 'flex', alignItems: 'flex-start', gap: '0.4rem' }}>
                    <span style={{ color: '#16a34a', fontWeight: 800 }}>•</span>
                    <span>{cond}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b', fontStyle: 'italic' }}>
                Standard commercial underwriting warranties apply (SOC 2 audit compliance, quarterly filings).
              </p>
            )}
          </div>

          {/* 3. Key Policy Exclusions */}
          <div>
            <h4 style={{ fontSize: '0.82rem', fontWeight: 800, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <AlertTriangle size={15} color="#dc2626" /> Key Policy Exclusions
            </h4>
            {exclusions.length > 0 ? (
              <ul style={{ margin: 0, paddingLeft: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {exclusions.map((ex, idx) => (
                  <li key={idx} style={{ fontSize: '0.86rem', color: '#7f1d1d', background: '#fef2f2', border: '1px solid #fecaca', padding: '0.5rem 0.75rem', borderRadius: '6px', display: 'flex', alignItems: 'flex-start', gap: '0.4rem' }}>
                    <span style={{ color: '#dc2626', fontWeight: 800 }}>•</span>
                    <span>{ex}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b', fontStyle: 'italic' }}>
                Standard exclusions apply (war risks, prior unstated acts, unencrypted media).
              </p>
            )}
          </div>

          {/* Raw Excerpt snippet */}
          {details.raw_snippet && (
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '0.75rem', borderRadius: '6px' }}>
              <div style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', color: '#64748b', marginBottom: '0.25rem' }}>
                Document Excerpt
              </div>
              <p style={{ fontSize: '0.8rem', color: '#475569', margin: 0, fontFamily: 'monospace', lineHeight: '1.4' }}>
                "{details.raw_snippet}"
              </p>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div style={{
          padding: '0.85rem 1.5rem',
          background: '#f8fafc',
          borderTop: '1px solid #e2e8f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <button
            onClick={handleOpenOriginalFile}
            style={{
              padding: '0.55rem 1.1rem',
              borderRadius: '8px',
              border: '1px solid #2563eb',
              background: '#eff6ff',
              color: '#1d4ed8',
              fontWeight: 700,
              fontSize: '0.88rem',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem'
            }}
          >
            📄 Open Original Document File ↗
          </button>

          <button
            onClick={onClose}
            style={{
              padding: '0.55rem 1.25rem',
              borderRadius: '8px',
              border: 'none',
              background: '#2563eb',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '0.88rem',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(37, 99, 235, 0.2)'
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
