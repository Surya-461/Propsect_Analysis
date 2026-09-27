import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import client from './api/client';
import Header from './Header';
import ChatInterface from './ChatInterface';
import HistoryModal from './HistoryModal';
import CompareModal from './components/CompareModal';
import ProposalViewerModal from './components/ProposalViewerModal';
import Sidebar from './Sidebar';
import Login from './components/Login';
import Signup from './components/Signup';
import ProspectAISplashLoader from './components/ProspectAISplashLoader';
import ProposalAnalysisInterface from './components/ProposalAnalysisInterface';

function DashboardContent() {
  const { user } = useAuth();
  const [analysisMode, setAnalysisMode] = useState('prospect'); // 'prospect' (Prospect Analysis) or 'proposal' (Proposal-Based Prospect Analysis)
  const [loading, setLoading] = useState(false);
  const [activeProspectCompany, setActiveProspectCompany] = useState('');
  const [activeProposalCompany, setActiveProposalCompany] = useState('');
  const [prospectReport, setProspectReport] = useState(null);
  const [proposalReport, setProposalReport] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isCompareOpen, setIsCompareOpen] = useState(false);
  const [proposalModalData, setProposalModalData] = useState(null);
  const [dbStatus, setDbStatus] = useState('checking');
  const [errorMessage, setErrorMessage] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [pendingComparisonQuery, setPendingComparisonQuery] = useState(null);
  const [newSessionKey, setNewSessionKey] = useState(() => Date.now());

  const fetchHistory = async () => {
    try {
      const res = await client.get('/analyses');
      setHistoryList(res.data || []);
    } catch (e) {
      console.warn("Could not fetch history list from backend:", e);
    }
  };

  // Fetch initial status & saved analyses from PostgreSQL for this user
  useEffect(() => {
    let ignore = false;
    const initData = async () => {
      try {
        const res = await client.get('/health');
        if (!ignore) {
          setDbStatus(res.data && res.data.status === 'healthy' ? 'healthy' : 'warning');
        }
      } catch {
        if (!ignore) setDbStatus('error');
      }

      try {
        const res = await client.get('/analyses');
        if (!ignore) {
          setHistoryList(res.data || []);
        }
      } catch (e) {
        console.warn("Could not fetch history list from backend:", e);
      }
    };

    initData();
    return () => {
      ignore = true;
    };
  }, [user]);

  const [clarificationData, setClarificationData] = useState(null);

  const startAnalysis = async (companyName, domain = 'Insurance') => {
    setLoading(true);
    setErrorMessage('');
    setClarificationData(null);

    try {
      setActiveProspectCompany(companyName);
      const res = await client.post('/analyze', {
        prospect_name: companyName,
        company_name: companyName,
        domain: domain || 'Insurance'
      });

      // Prospect analysis gave result -> DISABLE Proposal Analysis Result
      setProspectReport(res.data);
      setActiveProspectCompany(companyName);
      setProposalReport(null);
      setActiveProposalCompany('');
      setAnalysisMode('prospect');

      if (res.data && res.data.id) {
        setCurrentChatId(res.data.id);
      }
      fetchHistory(); // Refresh history list
    } catch (e) {
      console.error("Analysis Error:", e);
      setProspectReport(null);
      const detail = e.response?.data?.detail;
      if (detail && typeof detail === 'object') {
        if (detail.clarification) {
          setClarificationData(detail.clarification);
        }
        const mainMsg = detail.message || "Please enter a valid prospect name for analysis.";
        const subReason = (detail.reason && detail.reason !== mainMsg) ? ` (${detail.reason})` : '';
        setErrorMessage(`${mainMsg}${subReason}`);
      } else {
        setErrorMessage(
          detail || "Please enter a valid prospect name for analysis."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const loadSavedReport = async (analysisId) => {
    try {
      const res = await client.get(`/analyses/${analysisId}`);
      setCurrentChatId(analysisId);
      setIsHistoryOpen(false);
      if (res.data?.analysis_mode === 'PROPOSAL') {
        // Proposal analysis loaded -> DISABLE Prospect Analysis Result
        setProposalReport(res.data);
        setActiveProposalCompany(res.data.company_name);
        setProspectReport(null);
        setActiveProspectCompany('');
        setAnalysisMode('proposal');
      } else {
        // Prospect analysis loaded -> DISABLE Proposal Analysis Result
        setProspectReport(res.data);
        setActiveProspectCompany(res.data.company_name);
        setProposalReport(null);
        setActiveProposalCompany('');
        setAnalysisMode('prospect');
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch {
      alert("Error loading saved analysis report.");
    }
  };

  const deleteSavedReport = async (analysisId) => {
    try {
      await client.delete(`/analyses/${analysisId}`);
      fetchHistory();
      if (prospectReport && prospectReport.id === analysisId) {
        setProspectReport(null);
        setActiveProspectCompany('');
      }
      if (proposalReport && proposalReport.id === analysisId) {
        setProposalReport(null);
        setActiveProposalCompany('');
      }
      if (currentChatId === analysisId) {
        setCurrentChatId(null);
      }
    } catch {
      alert("Error deleting report.");
    }
  };

  const handleNewChat = () => {
    setProspectReport(null);
    setProposalReport(null);
    setActiveProspectCompany('');
    setActiveProposalCompany('');
    setCurrentChatId(null);
    setErrorMessage('');
    setClarificationData(null);
    setPendingComparisonQuery(null);
    setNewSessionKey(Date.now());
  };

  const handleSelectMode = (mode) => {
    setAnalysisMode(mode);
    setErrorMessage('');
    setClarificationData(null);
    if (mode === 'prospect') {
      setCurrentChatId(prospectReport?.id || null);
    } else {
      setCurrentChatId(proposalReport?.id || null);
    }
  };

  const handleToggleSidebar = () => {
    setSidebarOpen(prev => !prev);
  };

  const handleOpenProposal = (item) => {
    if (!item) return;

    // Resolve direct proposal document URL
    let targetUrl = item.proposal_file_url 
      || item.file_url 
      || item.proposal_details?.file_url;

    if (!targetUrl && item.id) {
      targetUrl = `http://localhost:8000/analyses/${item.id}/document`;
    }

    if (!targetUrl && (item.proposal_filename || item.filename)) {
      const fname = item.proposal_filename || item.filename;
      targetUrl = `http://localhost:8000/uploads/proposals/${fname}`;
    }

    if (!targetUrl) {
      targetUrl = 'http://localhost:8000/uploads/proposals/Commercial_Insurance_Proposal_HDFC_ERGO.pdf';
    }

    // Directly open document file in a new browser tab
    window.open(targetUrl, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="app-wrapper">
      {/* Collapsible Left Sidebar with User's Isolated Search History */}
      <Sidebar 
        historyList={historyList}
        onNewChat={handleNewChat}
        onLoadChat={loadSavedReport}
        onDeleteChat={deleteSavedReport}
        onOpenProposal={handleOpenProposal}
        currentChatId={currentChatId}
        isOpen={sidebarOpen}
        onToggle={handleToggleSidebar}
      />

      {/* Main Content Area */}
      <div className={`app-container ${sidebarOpen ? 'with-sidebar' : 'full-width'}`}>
        <Header 
          onOpenHistory={() => setIsHistoryOpen(true)} 
          historyCount={historyList.length}
          dbStatus={dbStatus}
          onToggleSidebar={handleToggleSidebar}
          isSidebarOpen={sidebarOpen}
          onOpenCompare={() => setIsCompareOpen(true)}
        />

        {/* Analysis Type Mode Selector */}
        <div className="analysis-mode-bar" style={{
          background: '#ffffff',
          borderBottom: '1px solid #e2e8f0',
          padding: '0.65rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          flexShrink: 0
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.04em' }}>
              Analysis Type:
            </span>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <button
                type="button"
                onClick={() => handleSelectMode('prospect')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  padding: '0.4rem 0.95rem',
                  borderRadius: '20px',
                  fontSize: '0.84rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  border: analysisMode === 'prospect' ? '1.5px solid #2563eb' : '1px solid #cbd5e1',
                  background: analysisMode === 'prospect' ? '#eff6ff' : '#ffffff',
                  color: analysisMode === 'prospect' ? '#1d4ed8' : '#475569',
                  boxShadow: analysisMode === 'prospect' ? '0 1px 3px rgba(37, 99, 235, 0.15)' : 'none',
                  transition: 'all 0.15s'
                }}
              >
                <span style={{
                  width: '9px',
                  height: '9px',
                  borderRadius: '50%',
                  background: analysisMode === 'prospect' ? '#2563eb' : '#cbd5e1'
                }} />
                <span>Prospect Analysis</span>
                {prospectReport && (
                  <span style={{
                    fontSize: '0.7rem',
                    background: '#dcfce7',
                    color: '#15803d',
                    padding: '0.1rem 0.45rem',
                    borderRadius: '10px',
                    fontWeight: 700
                  }}>
                    Active Result
                  </span>
                )}
              </button>

              <button
                type="button"
                onClick={() => handleSelectMode('proposal')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  padding: '0.4rem 0.95rem',
                  borderRadius: '20px',
                  fontSize: '0.84rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  border: analysisMode === 'proposal' ? '1.5px solid #2563eb' : '1px solid #cbd5e1',
                  background: analysisMode === 'proposal' ? '#eff6ff' : '#ffffff',
                  color: analysisMode === 'proposal' ? '#1d4ed8' : '#475569',
                  boxShadow: analysisMode === 'proposal' ? '0 1px 3px rgba(37, 99, 235, 0.15)' : 'none',
                  transition: 'all 0.15s'
                }}
              >
                <span style={{
                  width: '9px',
                  height: '9px',
                  borderRadius: '50%',
                  background: analysisMode === 'proposal' ? '#2563eb' : '#cbd5e1'
                }} />
                <span>Proposal-Based Analysis</span>
                {proposalReport && (
                  <span style={{
                    fontSize: '0.7rem',
                    background: '#dcfce7',
                    color: '#15803d',
                    padding: '0.1rem 0.45rem',
                    borderRadius: '10px',
                    fontWeight: 700
                  }}>
                    Active Result
                  </span>
                )}
              </button>
            </div>
          </div>

          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600 }}>
            {analysisMode === 'prospect' 
              ? (prospectReport ? `Viewing Prospect Dossier: ${prospectReport.company_name}` : 'Standard Multi-Source Dossier') 
              : (proposalReport ? `Viewing Proposal Fit: ${proposalReport.prospect?.name || proposalReport.company_name}` : 'Dynamic Carrier vs RFP Matching')}
          </div>
        </div>

        <main className="main-content-chatgpt" style={{ overflowY: 'auto' }}>
          {analysisMode === 'proposal' ? (
            <ProposalAnalysisInterface
              key={proposalReport?.id ? `proposal-${proposalReport.id}` : `proposal-new-${newSessionKey}`}
              onBackToProspectAnalysis={() => handleSelectMode('prospect')}
              savedReport={proposalReport}
              onAnalysisComplete={(data) => {
                // Proposal analysis gave result -> DISABLE Prospect Analysis Result!
                setProposalReport(data);
                setActiveProposalCompany(data?.company_name || data?.prospect?.name || '');
                setProspectReport(null);
                setActiveProspectCompany('');
                if (data?.id) setCurrentChatId(data.id);
                fetchHistory();
              }}
              onReset={() => {
                setProposalReport(null);
                setCurrentChatId(null);
                setActiveProposalCompany('');
              }}
            />
          ) : (
            <>
              {errorMessage && (
                <div style={{
                  background: clarificationData ? '#eff6ff' : '#fef2f2',
                  border: `1px solid ${clarificationData ? '#93c5fd' : '#fca5a5'}`,
                  color: clarificationData ? '#1e3a8a' : '#991b1b',
                  padding: '1.25rem 1.5rem',
                  borderRadius: '12px',
                  margin: '1.25rem auto 0 auto',
                  maxWidth: '900px',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '1.05rem', fontWeight: 800, color: clarificationData ? '#2563eb' : '#dc2626', marginBottom: '0.4rem' }}>
                    {clarificationData ? 'ℹ️ SELECT A SUPPORTED PROSPECT' : 'ℹ️ PROSPECT NOTICE'}
                  </div>
                  <p style={{ margin: '0.4rem 0', color: clarificationData ? '#1e40af' : '#7f1d1d', fontSize: '0.92rem', fontWeight: 500 }}>
                    {errorMessage}
                  </p>

                  {clarificationData && clarificationData.options && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.85rem' }}>
                      {clarificationData.options.map((opt, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            setErrorMessage('');
                            setClarificationData(null);
                            startAnalysis(opt);
                          }}
                          style={{
                            background: '#2563eb',
                            border: 'none',
                            color: '#ffffff',
                            fontSize: '0.85rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                            padding: '0.5rem 1rem',
                            borderRadius: '8px',
                            boxShadow: '0 2px 4px rgba(37, 99, 235, 0.2)'
                          }}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  )}

                  {!clarificationData && (
                    <button 
                      onClick={() => {
                        setErrorMessage('');
                        setActiveProspectCompany('');
                      }}
                      style={{
                        background: '#dc2626',
                        border: 'none',
                        color: '#ffffff',
                        fontSize: '0.85rem',
                        fontWeight: 700,
                        cursor: 'pointer',
                        padding: '0.45rem 1rem',
                        borderRadius: '6px',
                        marginTop: '0.5rem',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                      }}
                    >
                      Try Again
                    </button>
                  )}
                </div>
              )}

              {/* Prospect Analysis: ChatGPT Interface */}
              <ChatInterface 
                key={prospectReport?.id ? `chat-${prospectReport.id}` : `new-prospect-${newSessionKey}`}
                currentReport={prospectReport}
                activeCompany={activeProspectCompany}
                onAnalyze={startAnalysis}
                loading={loading}
                onNewChat={handleNewChat}
                onOpenProposal={handleOpenProposal}
                pendingComparisonQuery={pendingComparisonQuery}
                onOpenCompare={(company) => {
                  if (company) setActiveProspectCompany(company);
                  setIsCompareOpen(true);
                }}
              />
            </>
          )}
        </main>

        <HistoryModal 
          isOpen={isHistoryOpen}
          onClose={() => setIsHistoryOpen(false)}
          historyList={historyList}
          onLoadReport={loadSavedReport}
          onDeleteReport={deleteSavedReport}
          onOpenProposal={handleOpenProposal}
        />

        <CompareModal
          isOpen={isCompareOpen}
          onClose={() => setIsCompareOpen(false)}
          activeProspect={activeProspectCompany || activeProposalCompany}
          loading={loading}
          onLaunchComparison={(prospects) => {
            const query = `Compare ${prospects.join(' and ')}`;
            setActiveProspectCompany(prospects[0]);
            setPendingComparisonQuery({ query, prospects, timestamp: Date.now() });
            setAnalysisMode('prospect');
          }}
        />

        <ProposalViewerModal
          isOpen={Boolean(proposalModalData)}
          onClose={() => setProposalModalData(null)}
          proposalDetails={proposalModalData?.details}
          filename={proposalModalData?.filename}
          companyName={proposalModalData?.companyName}
        />
      </div>
    </div>
  );
}

function MainApp() {
  const { isAuthenticated, loading } = useAuth();
  const [authView, setAuthView] = useState('login'); // 'login' or 'signup'
  const [showSplash, setShowSplash] = useState(true);

  if (showSplash || loading) {
    return <ProspectAISplashLoader onFinish={() => setShowSplash(false)} />;
  }

  if (!isAuthenticated) {
    if (authView === 'signup') {
      return <Signup onSwitchToLogin={() => setAuthView('login')} />;
    }
    return <Login onSwitchToSignup={() => setAuthView('signup')} />;
  }

  return <DashboardContent />;
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}