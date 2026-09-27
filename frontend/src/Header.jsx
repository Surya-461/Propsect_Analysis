import { useState, useRef, useEffect } from 'react';
import { 
  ShieldCheck, 
  History, 
  PanelLeftClose, 
  Menu, 
  LogOut, 
  User as UserIcon, 
  ChevronDown
} from 'lucide-react';
import { useAuth } from './context/AuthContext';

export default function Header({ onOpenHistory, historyCount, dbStatus, onToggleSidebar, isSidebarOpen }) {
  const { user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Close dropdown on click outside or Escape key
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setIsMenuOpen(false);
      }
    };

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsMenuOpen(false);
      }
    };

    if (isMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isMenuOpen]);

  const handleOpenSavedReports = () => {
    setIsMenuOpen(false);
    if (onOpenHistory) onOpenHistory();
  };

  const handleLogout = () => {
    setIsMenuOpen(false);
    if (logout) logout();
  };

  return (
    <header className="navbar">
      <div className="navbar-inner">
        {/* Left: Sidebar Toggle & Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <button 
            className="btn-sidebar-toggle"
            onClick={onToggleSidebar}
            title={isSidebarOpen ? "Collapse sidebar" : "Open sidebar"}
            aria-label="Toggle Sidebar"
          >
            {isSidebarOpen ? <PanelLeftClose size={20} /> : <Menu size={20} />}
          </button>

          <div className="brand-logo">
            <div className="brand-icon">
              <ShieldCheck size={26} color="#ffffff" />
            </div>
            <div>
              <h1 className="brand-title">PROSPECT AI</h1>
              <div className="brand-tagline">B2B Underwriting & Intelligence Platform</div>
            </div>
          </div>
        </div>

        {/* Right: Quick Actions & Profile Menu */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* {onOpenCompare && (
            <button
              onClick={onOpenCompare}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                background: 'rgba(255, 255, 255, 0.12)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '8px',
                padding: '0.45rem 0.85rem',
                color: '#ffffff',
                fontSize: '0.84rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                backdropFilter: 'blur(8px)'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.22)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)'}
              title="Compare 2 or 3 Insurance Prospects Side-by-Side"
            >
              <Sparkles size={14} color="#60a5fa" />
              <span>Compare Peers</span>
            </button>
          )} */}

          <div className="nav-actions" style={{ position: 'relative' }} ref={menuRef}>
          {/* Profile & Menu Button Trigger */}
          <button
            type="button"
            className="profile-menu-trigger"
            onClick={() => setIsMenuOpen(prev => !prev)}
            aria-expanded={isMenuOpen}
            aria-haspopup="true"
            title="User Profile & Quick Actions"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
              background: isMenuOpen ? 'rgba(255, 255, 255, 0.15)' : 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.16)',
              borderRadius: '9999px',
              padding: '0.35rem 0.85rem 0.35rem 0.45rem',
              cursor: 'pointer',
              color: '#ffffff',
              transition: 'all 0.2s ease',
              backdropFilter: 'blur(8px)'
            }}
          >
            {/* User Avatar with Status Dot */}
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {user?.avatar_url ? (
                <img 
                  src={user.avatar_url} 
                  alt={user.name || 'User'}
                  style={{
                    width: '30px',
                    height: '30px',
                    borderRadius: '50%',
                    objectFit: 'cover',
                    border: '1.5px solid #ffffff'
                  }}
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div 
                  style={{ 
                    width: '30px', 
                    height: '30px', 
                    borderRadius: '50%', 
                    background: user?.role === 'admin' ? 'linear-gradient(135deg, #2563eb, #3b82f6)' : 'linear-gradient(135deg, #475569, #64748b)', 
                    color: '#ffffff', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    fontSize: '0.85rem', 
                    fontWeight: 700,
                    border: '1.5px solid #ffffff'
                  }}
                >
                  {user?.name ? user.name.charAt(0).toUpperCase() : <UserIcon size={16} />}
                </div>
              )}
              {/* Online DB Indicator Dot */}
              <span 
                style={{
                  position: 'absolute',
                  bottom: '-1px',
                  right: '-1px',
                  width: '9px',
                  height: '9px',
                  borderRadius: '50%',
                  backgroundColor: dbStatus === 'healthy' ? '#22c55e' : '#f59e0b',
                  border: '2px solid #0f172a'
                }}
              />
            </div>

            {/* User Name & Chevron */}
            {/* <span style={{ fontSize: '0.86rem', fontWeight: 600, color: '#f8fafc', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.name || "Account"}
            </span> */}
            <ChevronDown 
              size={15} 
              style={{ 
                color: '#94a3b8', 
                transition: 'transform 0.2s ease', 
                transform: isMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)' 
              }} 
            />
          </button>

          {/* Floating Dropdown Popover */}
          {isMenuOpen && (
            <div 
              className="profile-dropdown-popover"
              style={{
                position: 'absolute',
                top: 'calc(100% + 10px)',
                right: 0,
                width: '310px',
                background: '#ffffff',
                borderRadius: '16px',
                border: '1px solid #e2e8f0',
                boxShadow: '0 20px 30px -10px rgba(15, 23, 42, 0.2), 0 10px 15px -5px rgba(15, 23, 42, 0.1)',
                padding: '0.75rem',
                zIndex: 100,
                animation: 'dropdownFadeIn 0.18s ease-out'
              }}
            >
              {/* 1. Profile Header Card */}
              <div 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.75rem', 
                  padding: '0.65rem 0.75rem', 
                  background: '#f8fafc', 
                  borderRadius: '12px',
                  border: '1px solid #f1f5f9',
                  marginBottom: '0.5rem'
                }}
              >
                {user?.avatar_url ? (
                  <img 
                    src={user.avatar_url} 
                    alt={user.name || 'User'}
                    style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: '50%',
                      objectFit: 'cover',
                      border: '2px solid #e2e8f0'
                    }}
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <div 
                    style={{ 
                      width: '42px', 
                      height: '42px', 
                      borderRadius: '50%', 
                      background: 'linear-gradient(135deg, #2563eb, #1d4ed8)', 
                      color: '#ffffff', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      fontSize: '1.1rem', 
                      fontWeight: 800 
                    }}
                  >
                    {user?.name ? user.name.charAt(0).toUpperCase() : <UserIcon size={20} />}
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <span style={{ fontSize: '0.92rem', fontWeight: 700, color: '#0f172a', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {user?.name || "Underwriter"}
                    </span>
                    {user?.role === 'admin' && (
                      <span style={{ fontSize: '0.65rem', background: '#dbeafe', color: '#1d4ed8', fontWeight: 800, padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                        ADMIN
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {user?.email || "Signed in"}
                  </span>
                  <div style={{ marginTop: '0.2rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <span style={{ fontSize: '0.68rem', color: '#059669', background: '#ecfdf5', padding: '0.05rem 0.35rem', borderRadius: '4px', fontWeight: 600 }}>
                      {user?.auth_provider === 'google' ? 'Google Auth' : 'Verified User'}
                    </span>
                  </div>
                </div>
              </div>

              {/* 2. Menu Navigation Items */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                {/* Saved Reports Item */}
                <button
                  type="button"
                  onClick={handleOpenSavedReports}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    padding: '0.65rem 0.75rem',
                    borderRadius: '10px',
                    border: 'none',
                    background: 'transparent',
                    cursor: 'pointer',
                    color: '#1e293b',
                    textAlign: 'left',
                    transition: 'background 0.15s ease'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#f1f5f9'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    <div style={{ background: '#eff6ff', padding: '0.45rem', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <History size={17} color="#2563eb" />
                    </div>
                    <div>
                      <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#0f172a' }}>Saved Reports</div>
                      <div style={{ fontSize: '0.72rem', color: '#64748b' }}>Past prospect dossiers</div>
                    </div>
                  </div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 800, background: '#2563eb', color: '#ffffff', padding: '0.2rem 0.55rem', borderRadius: '9999px' }}>
                    {historyCount || 0}
                  </span>
                </button>

                {/* Database Connection Status Item */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.6rem 0.75rem',
                    borderRadius: '10px',
                    color: '#1e293b',
                    background: '#ffffff'
                  }}
                >
                  {/* <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    <div style={{ background: '#ecfdf5', padding: '0.45rem', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Database size={17} color="#059669" />
                    </div>
                    <div>
                      <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#0f172a' }}>Database Status</div>
                      <div style={{ fontSize: '0.72rem', color: '#64748b' }}>PostgreSQL 5432</div>
                    </div>
                  </div>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.3rem', color: dbStatus === 'healthy' ? '#059669' : '#d97706' }}>
                    <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: dbStatus === 'healthy' ? '#22c55e' : '#f59e0b' }} />
                    {dbStatus === 'healthy' ? 'Connected' : 'Checking'}
                  </span> */}
                </div>
              </div>

              {/* 3. Divider */}
              <div style={{ height: '1px', background: '#e2e8f0', margin: '0.45rem 0' }} />

              {/* 4. Logout Action */}
              <button
                type="button"
                onClick={handleLogout}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.65rem',
                  width: '100%',
                  padding: '0.65rem 0.75rem',
                  borderRadius: '10px',
                  border: 'none',
                  background: '#fef2f2',
                  cursor: 'pointer',
                  color: '#dc2626',
                  textAlign: 'left',
                  transition: 'background 0.15s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#fee2e2'}
                onMouseLeave={(e) => e.currentTarget.style.background = '#fef2f2'}
              >
                <div style={{ background: '#ffffff', padding: '0.45rem', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #fecaca' }}>
                  <LogOut size={16} color="#dc2626" />
                </div>
                <div>
                  <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#dc2626' }}>Sign Out</div>
                  <div style={{ fontSize: '0.72rem', color: '#ef4444' }}>End session and lock workspace</div>
                </div>
              </button>
            </div>
          )}
          </div>
        </div>
      </div>
    </header>
  );
}

