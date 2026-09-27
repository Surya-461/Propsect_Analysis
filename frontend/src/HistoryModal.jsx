import { X, Trash2, ExternalLink, Calendar } from 'lucide-react';

export default function HistoryModal({ isOpen, onClose, historyList, onLoadReport, onDeleteReport, onOpenProposal }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">Saved Prospect Analyses (PostgreSQL)</div>
          <button 
            onClick={onClose} 
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
          >
            <X size={24} />
          </button>
        </div>

        <div className="modal-body">
          {historyList.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
              <p>No saved analyses found in database yet.</p>
              <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
                Run an analysis from the main dashboard to save prospect intelligence reports automatically.
              </p>
            </div>
          ) : (
            historyList.map((item) => {
              const isProposal = item.analysis_mode === 'PROPOSAL' || Boolean(item.proposal_filename);
              return (
                <div key={item.id} className="history-item">
                  <div className="history-info">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <h4 style={{ margin: 0 }}>{item.company_name}</h4>
                      {isProposal ? (
                        <span 
                          onClick={(e) => {
                            if (onOpenProposal) {
                              e.stopPropagation();
                              onOpenProposal(item);
                            }
                          }}
                          title="Click to open proposal document in a new tab"
                          style={{
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            background: '#eff6ff',
                            color: '#2563eb',
                            border: '1px solid #bfdbfe',
                            padding: '0.15rem 0.5rem',
                            borderRadius: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          📄 Proposal Document ↗
                        </span>
                      ) : (
                        <span style={{
                          fontSize: '0.72rem',
                          fontWeight: 600,
                          background: '#f1f5f9',
                          color: '#64748b',
                          padding: '0.15rem 0.5rem',
                          borderRadius: '4px'
                        }}>
                          General Prospect
                        </span>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.35rem' }}>
                      <span className="history-date" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Calendar size={12} />
                        {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Recent'}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                        • {item.parameter_count || 8} Parameters
                      </span>
                    </div>
                  </div>

                <div className="history-actions">
                  <button className="btn-secondary" onClick={() => onLoadReport(item.id)}>
                    <ExternalLink size={14} /> Open
                  </button>
                  <button 
                    className="btn-secondary" 
                    style={{ color: '#dc2626', borderColor: '#fee2e2' }}
                    onClick={() => onDeleteReport(item.id)}
                    title="Delete saved report"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })
        )}
        </div>
      </div>
    </div>
  );
}
