import { useState } from 'react';
import { ChevronDown, Plus, Trash2, ShieldCheck } from 'lucide-react';
import './Sidebar.css';

export default function Sidebar({ 
  historyList = [], 
  onNewChat, 
  onLoadChat, 
  onDeleteChat, 
  onOpenProposal,
  currentChatId,
  isOpen = true,
  onToggle 
}) {
  const [expandedSections, setExpandedSections] = useState({
    recent: true,
    pinned: true
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const recentChats = historyList
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 20);

  const formatDate = (dateString) => {
    if (!dateString) return 'Recent';
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <>
      {/* Mobile overlay backdrop */}
      {isOpen && <div className="sidebar-overlay" onClick={onToggle} />}
      
      <aside className={`sidebar ${isOpen ? 'open' : 'collapsed'}`}>
        {/* Sidebar Header */}
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="sidebar-logo-badge">
              <ShieldCheck size={18} color="#ffffff" />
            </div>
            <span className="sidebar-title">Prospect AI</span>
          </div>
          {/* <button 
            className="sidebar-collapse-btn"
            onClick={onToggle}
            title="Collapse sidebar"
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose size={18} />
          </button> */}
        </div>

        {/* New Chat Button */}
        <button className="btn-new-chat" onClick={onNewChat} title="Start a new prospect analysis">
          <Plus size={18} />
          <span>New Analysis</span>
        </button>

        {/* Sidebar Scroll Container */}
        <div className="sidebar-content">
          <div className="sidebar-section">
            <button 
              className="section-header"
              onClick={() => toggleSection('recent')}
            >
              <ChevronDown 
                size={16}
                style={{
                  transform: expandedSections.recent ? 'rotate(0deg)' : 'rotate(-90deg)',
                  transition: 'transform 0.2s ease'
                }}
              />
              <span>Recent Analyses</span>
              <span className="section-badge">{recentChats.length}</span>
            </button>

            {expandedSections.recent && (
              <div className="section-items">
                {recentChats.length === 0 ? (
                  <div className="empty-state">
                    <p>No saved analyses yet</p>
                    <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Search any carrier name to begin</p>
                  </div>
                ) : (
                  recentChats.map(chat => (
                    <ChatItem
                      key={chat.id}
                      chat={chat}
                      isActive={currentChatId === chat.id}
                      onLoad={() => onLoadChat(chat.id)}
                      onDelete={() => onDeleteChat(chat.id)}
                      onOpenProposal={onOpenProposal}
                      formatDate={formatDate}
                    />
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="sidebar-footer">
          <div className="footer-info">
            <p style={{ fontSize: '0.78rem', color: '#64748b', margin: 0 }}>
              Total Saved: <strong style={{ color: '#0f172a' }}>{historyList.length}</strong>
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}

// Individual Chat Item Component
function ChatItem({ chat, isActive, onLoad, onDelete, onOpenProposal, formatDate }) {
  const [hovering, setHovering] = useState(false);
  const isProposal = chat.analysis_mode === 'PROPOSAL' || Boolean(chat.proposal_filename);

  return (
    <div
      className={`chat-item ${isActive ? 'active' : ''}`}
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
    >
      <button
        className="chat-item-content"
        onClick={onLoad}
        title={chat.company_name}
      >
        <div className="chat-item-text" style={{ width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.4rem', width: '100%' }}>
            <div className="chat-item-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {chat.company_name}
            </div>
            {isProposal ? (
              <span 
                onClick={(e) => {
                  if (onOpenProposal) {
                    e.stopPropagation();
                    onOpenProposal(chat);
                  }
                }}
                title="Click to open proposal document in a new tab"
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  background: '#eff6ff',
                  color: '#2563eb',
                  border: '1px solid #bfdbfe',
                  padding: '0.1rem 0.4rem',
                  borderRadius: '4px',
                  whiteSpace: 'nowrap',
                  flexShrink: 0,
                  cursor: 'pointer'
                }}
              >
                📄 Proposal ↗
              </span>
            ) : (
              <span style={{
                fontSize: '0.65rem',
                fontWeight: 600,
                background: '#f1f5f9',
                color: '#64748b',
                padding: '0.1rem 0.4rem',
                borderRadius: '4px',
                whiteSpace: 'nowrap',
                flexShrink: 0
              }}>
                General
              </span>
            )}
          </div>
          <div className="chat-item-meta">
            <span>{formatDate(chat.created_at)}</span>
          </div>
        </div>
      </button>

      {hovering && (
        <button
          className="chat-item-delete"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          title="Delete report"
          aria-label="Delete report"
        >
          <Trash2 size={13} />
        </button>
      )}
    </div>
  );
}
