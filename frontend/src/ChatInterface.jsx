import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Send, 
  Sparkles, 
  ShieldCheck, 
  Building, 
  TrendingUp, 
  Award, 
  ShieldAlert, 
  Activity, 
  Briefcase, 
  Zap, 
  Globe, 
  FileText, 
  Download, 
  ExternalLink,
  BookOpen,
  Calendar,
  CheckCircle2,
  ArrowRight,
  HelpCircle,
  Scale
} from 'lucide-react';
import client from './api/client';
import { exportReportToPDF } from './utils/pdfExport';
import ComparativeMatrixCard from './components/ComparativeMatrixCard';

const generateMsgId = (prefix = 'msg') => `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

const SAMPLE_CARRIER_EXAMPLES = [
  "SBI Life Insurance",
  "Allianz",
  "AXA",
  "ICICI Lombard",
  "HDFC Life",
  "Chubb",
  "State Farm",
  "Zurich Insurance Group"
];

const ANALYSIS_STEPS = [
  { id: 1, label: "Company research", desc: "Harvesting verified corporate filings, IRDAI registries & annual reports" },
  { id: 2, label: "Data collection", desc: "Aggregating statutory disclosures, balance sheets & underwriting data" },
  { id: 3, label: "Parameter analysis", desc: "Analyzing operational scale, solvency, combined ratio & tech activity" },
  { id: 4, label: "Evidence processing", desc: "Structuring empirical observations and grounding source attributions" }
];

export default function ChatInterface({ 
  currentReport, 
  activeCompany, 
  onAnalyze, 
  loading,
  onOpenCompare,
  onOpenProposal,
  pendingComparisonQuery
}) {
  const [inputVal, setInputVal] = useState('');
  const [messages, setMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [selectedParameterFilter, setSelectedParameterFilter] = useState('all');
  const [sessionCompany, setSessionCompany] = useState(currentReport?.company_name || activeCompany || '');
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [, setIsSearching] = useState(false);
  const [activeStep, setActiveStep] = useState(1);
  const [pendingProspect, setPendingProspect] = useState(null);

  const messagesEndRef = useRef(null);
  const searchTimeoutRef = useRef(null);
  const isSendingRef = useRef(false);
  const processedComparisonRef = useRef(null);
  const sendMessageRef = useRef(null);

  // Sync sessionCompany and reset conversation when new chat is started or report cleared
  const [prevReport, setPrevReport] = useState(currentReport);
  const [prevActiveCompany, setPrevActiveCompany] = useState(activeCompany);
  if (currentReport !== prevReport || activeCompany !== prevActiveCompany) {
    setPrevReport(currentReport);
    setPrevActiveCompany(activeCompany);
    if (!currentReport) {
      setMessages([]);
      setPendingProspect(null);
      if (!activeCompany) {
        setSessionCompany('');
      }
      setInputVal('');
      setSelectedParameterFilter('all');
    } else if (currentReport?.company_name) {
      setSessionCompany(currentReport.company_name);
      setPendingProspect(null);
    } else if (activeCompany) {
      setSessionCompany(activeCompany);
    }
  }

  // Live simulation of analysis steps when loading is true
  const [prevLoading, setPrevLoading] = useState(loading);
  if (loading !== prevLoading) {
    setPrevLoading(loading);
    setActiveStep(1);
  }

  useEffect(() => {
    if (!loading) return;
    const interval = setInterval(() => {
      setActiveStep(prev => (prev < 4 ? prev + 1 : prev));
    }, 3500);
    return () => clearInterval(interval);
  }, [loading]);

  // Fetch and restore conversation history via GET /analyses/{analysis_id}/chat-history when a report is loaded or switched
  useEffect(() => {
    if (currentReport) {
      // Safety guard: Prospect ChatInterface must never load a PROPOSAL mode report
      if (currentReport.analysis_mode === 'PROPOSAL') {
        return;
      }

      const reportId = currentReport.id || currentReport.company_name;
      const completedMsg = {
        id: generateMsgId('report-' + reportId),
        sender: 'assistant',
        type: 'analysis_complete',
        companyName: currentReport.company_name,
        reportData: currentReport,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      if (currentReport.id) {
        client.get(`/analyses/${currentReport.id}/chat-history`)
          .then(res => {
            const fetchedMessages = res.data?.messages || res.data?.chat_history || [];
            if (Array.isArray(fetchedMessages) && fetchedMessages.length > 0) {
              const updatedSaved = fetchedMessages.map(m => 
                m.type === 'analysis_complete' ? { ...m, reportData: currentReport } : m
              );
              const hasReportCard = updatedSaved.some(m => m.type === 'analysis_complete');
              setMessages(hasReportCard ? updatedSaved : [completedMsg, ...updatedSaved]);
            } else {
              setMessages([completedMsg]);
            }
          })
          .catch(err => {
            console.warn("Could not fetch chat history via GET:", err);
            const savedHistory = Array.isArray(currentReport.chat_history) ? currentReport.chat_history : [];
            if (savedHistory.length > 0) {
              const hasReportCard = savedHistory.some(m => m.type === 'analysis_complete');
              setMessages(hasReportCard ? savedHistory : [completedMsg, ...savedHistory]);
            } else {
              setMessages([completedMsg]);
            }
          });
      } else {
        const savedHistory = Array.isArray(currentReport.chat_history) ? currentReport.chat_history : [];
        queueMicrotask(() => {
          if (savedHistory.length > 0) {
            const hasReportCard = savedHistory.some(m => m.type === 'analysis_complete');
            setMessages(hasReportCard ? savedHistory : [completedMsg, ...savedHistory]);
          } else {
            setMessages([completedMsg]);
          }
        });
      }
    }
  }, [currentReport]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, chatLoading, pendingProspect]);

  // Autocomplete live search for prospects
  const handleInputChange = (e) => {
    const text = e.target.value;
    setInputVal(text);

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!text.trim() || text.length < 2) {
      setSearchSuggestions([]);
      setIsSearching(false);
      return;
    }

    // Only search prospects if no report is active or if user seems to type a new company
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        setIsSearching(true);
        const res = await client.get('/prospects/search', { params: { q: text.trim(), limit: 6 } });
        setSearchSuggestions(res.data?.results || []);
      } catch (err) {
        console.warn("Prospect search failed:", err);
      } finally {
        setIsSearching(false);
      }
    }, 200);
  };

  // User selects a prospect from suggestions or popular presets
  const handleSelectProspect = (prospect) => {
    setSearchSuggestions([]);
    setInputVal('');
    const prospectName = typeof prospect === 'object' ? prospect.name : prospect;

    const userMsg = {
      id: generateMsgId('user'),
      sender: 'user',
      text: prospectName,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const validationMsg = {
      id: generateMsgId('bot-val'),
      sender: 'assistant',
      type: 'validation_card',
      prospect: prospectName,
      domain: 'Insurance',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setPendingProspect(prospectName);
    setMessages(prev => [...prev, userMsg, validationMsg]);
  };

  // Start analysis trigger
  const handleStartAnalysis = (companyToAnalyze) => {
    const target = companyToAnalyze || pendingProspect || sessionCompany;
    if (!target) return;
    setPendingProspect(null);
    onAnalyze(target, 'Insurance');
  };

  // Parameter Click Handler: View single parameter details
  const handleParameterClick = (paramName, explicitCompany = null) => {
    setInputVal('');
    const targetCompany = explicitCompany || currentReport?.company_name || sessionCompany;

    if (currentReport?.report_data?.[paramName]) {
      const pData = currentReport.report_data[paramName];
      const userMsg = {
        id: generateMsgId('user'),
        sender: 'user',
        text: `Tell me about ${paramName}`,
        companyName: targetCompany,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      const botMsg = {
        id: generateMsgId('bot'),
        sender: 'assistant',
        matchedParameter: paramName,
        parameterData: pData,
        displayMode: 'parameter_card',
        companyName: targetCompany,
        availableParameters: currentReport?.report_data ? Object.keys(currentReport.report_data) : [],
        suggestedFollowups: [
          `What evidence supports ${paramName}?`,
          `Show sources for ${paramName}`
        ],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, userMsg, botMsg]);
      return;
    }

    handleSendMessage(`Tell me about ${paramName}`, paramName, targetCompany);
  };

  // Switch Prospect confirmation handler
  const handleSwitchProspect = async (requestedProspect, pendingQuestion, pendingParameter) => {
    setChatLoading(true);
    try {
      const res = await client.post('/chat', {
        active_prospect_name: sessionCompany,
        switch_confirmed: true,
        switch_to_prospect: requestedProspect,
        pending_question: pendingQuestion,
        pending_parameter: pendingParameter,
        question: pendingQuestion || `Switch to ${requestedProspect}`
      });
      const data = res.data;
      setSessionCompany(requestedProspect);

      if (data.report_data) {
        const botMsg = {
          id: generateMsgId('bot'),
          sender: 'assistant',
          text: data.answer || `Switched to ${requestedProspect}.`,
          matchedParameter: data.matched_parameter,
          parameterData: data.parameter_data,
          displayMode: data.display_mode || 'text_only',
          suggestedFollowups: data.suggested_followups || [],
          availableParameters: data.available_parameters || [],
          companyName: requestedProspect,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, botMsg]);
      } else {
        onAnalyze(requestedProspect, 'Insurance');
      }
    } catch (err) {
      console.error("Error switching prospect:", err);
      onAnalyze(requestedProspect, 'Insurance');
    } finally {
      setChatLoading(false);
    }
  };

  // Stay with active prospect handler
  const handleStayWithProspect = async (activeProspect) => {
    setChatLoading(true);
    try {
      const res = await client.post('/chat', {
        active_prospect_name: activeProspect,
        stay_confirmed: true,
        question: 'Stay with active prospect'
      });
      const data = res.data;
      const botMsg = {
        id: generateMsgId('bot'),
        sender: 'assistant',
        text: data.answer || `No problem. We'll continue with **${activeProspect}**.\n\nWhat would you like to explore?`,
        companyName: activeProspect,
        availableParameters: currentReport?.report_data ? Object.keys(currentReport.report_data) : [],
        suggestedFollowups: data.suggested_followups || ["Company Scale", "Financial Strength", "Market Position"],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, botMsg]);
    } catch {
      setMessages(prev => [
        ...prev,
        {
          id: generateMsgId('bot'),
          sender: 'assistant',
          text: `No problem. We'll continue with **${activeProspect}**.\n\nWhat would you like to explore?`,
          companyName: activeProspect,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  // Main chat submission handler
  const handleSendMessage = useCallback(async (textToSend = null, explicitParam = null, explicitCompany = null) => {
    if (loading || chatLoading || isSendingRef.current) return;

    const text = (textToSend || inputVal).trim();
    if (!text) return;

    isSendingRef.current = true;
    setInputVal('');
    setSearchSuggestions([]);

    // Append User Message
    const userMsgId = generateMsgId('user');
    const newUserMessage = {
      id: userMsgId,
      sender: 'user',
      text: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, newUserMessage]);

    // 1. If NO report is active, NO pending prospect, and NOT a comparative query: Resolve input as prospect
    const isComparative = /\b(compare|comparison|versus|vs|between|who has higher|who is larger|who is growing faster)\b/i.test(text);

    if (!currentReport && !pendingProspect && !isComparative) {
      setChatLoading(true);
      try {
        const res = await client.post('/prospects/resolve', { prospect_name: text });
        const data = res.data;

        if (data.valid && data.prospect_name) {
          const validationMsg = {
            id: generateMsgId('bot-val'),
            sender: 'assistant',
            type: 'validation_card',
            prospect: data.prospect_name,
            domain: data.domain || 'Insurance',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          };
          setPendingProspect(data.prospect_name);
          setMessages(prev => [...prev, validationMsg]);
        } else if (data.candidates && data.candidates.length > 0) {
          // Multiple matches -> disambiguation card
          const disambigMsg = {
            id: generateMsgId('bot-multi'),
            sender: 'assistant',
            type: 'disambiguation_card',
            text: data.message || "Multiple matching prospects found. Please select one:",
            candidates: data.candidates,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          };
          setMessages(prev => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.type === 'disambiguation_card' && JSON.stringify(lastMsg.candidates) === JSON.stringify(data.candidates)) {
              return prev;
            }
            return [...prev, disambigMsg];
          });
        } else {
          // Not found friendly message
          const notFoundMsg = {
            id: generateMsgId('bot-nf'),
            sender: 'assistant',
            text: data.message || "I couldn't find that company in the currently supported insurance prospects. Please select a company from the available prospect list.",
            suggestedFollowups: ["SBI Life Insurance", "Allianz", "HDFC Life", "AXA"],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          };
          setMessages(prev => [...prev, notFoundMsg]);
        }
      } catch (err) {
        console.error("Prospect resolution error:", err);
        const detail = err.response?.data?.detail;
        const errMsg = (typeof detail === 'object' ? detail.message : detail) || "I couldn't find that company in the currently supported insurance prospects. Please select a company from the available prospect list.";
        setMessages(prev => [
          ...prev,
          {
            id: generateMsgId('bot-err'),
            sender: 'assistant',
            text: errMsg,
            suggestedFollowups: ["SBI Life Insurance", "Allianz", "ICICI Lombard", "Chubb"],
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
      } finally {
        setChatLoading(false);
        isSendingRef.current = false;
      }
      return;
    }

    // 2. Report is loaded or comparative query -> Conversational Q&A
    const targetCompany = explicitCompany || currentReport?.company_name || sessionCompany || 'SBI Life Insurance';
    setChatLoading(true);

    try {
      const clientMsgId = newUserMessage.id;
      const res = await client.post('/chat', {
        analysis_id: currentReport?.id || null,
        client_message_id: clientMsgId,
        prospect_name: targetCompany,
        active_prospect_name: targetCompany,
        question: text,
        parameter: explicitParam,
        report_data: currentReport?.report_data || null
      });

      const data = res.data;

      // 1. Handle Prospect Switch Required Gate
      if (data.action === 'PROSPECT_SWITCH_REQUIRED' || data.status === 'prospect_switch_required') {
        const switchMsg = {
          id: generateMsgId('bot-switch'),
          sender: 'assistant',
          type: 'prospect_switch_required',
          activeProspect: data.active_prospect || targetCompany,
          requestedProspect: data.requested_prospect,
          requestedProspectId: data.requested_prospect_id,
          pendingQuestion: data.pending_question || text,
          pendingParameter: data.pending_parameter,
          text: data.answer,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, switchMsg]);
        return;
      }

      // 2. Handle Disambiguation
      if (data.action === 'PROSPECT_DISAMBIGUATION' || (data.candidates && data.candidates.length > 0)) {
        const disambigMsg = {
          id: generateMsgId('bot-multi'),
          sender: 'assistant',
          type: 'disambiguation_card',
          text: data.answer || "Multiple matching prospects found. Please select one:",
          candidates: data.candidates,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.type === 'disambiguation_card' && JSON.stringify(lastMsg.candidates) === JSON.stringify(data.candidates)) {
            return prev;
          }
          return [...prev, disambigMsg];
        });
        return;
      }

      // 3. Handle Multi-Prospect Comparison
      if (data.type === 'prospect_comparison' || data.action === 'PROSPECT_COMPARISON') {
        if (Array.isArray(data.chat_history) && data.chat_history.length > 0) {
          const updatedSaved = data.chat_history.map(m => 
            m.type === 'analysis_complete' ? { ...m, reportData: currentReport } : m
          );
          setMessages(updatedSaved);
          return;
        }

        const compMsg = {
          id: generateMsgId('bot-comp'),
          sender: 'assistant',
          type: 'prospect_comparison',
          text: data.answer || "",
          comparisonMatrix: data.comparison_matrix,
          suggestedFollowups: data.suggested_followups || [
            "Compare solvency ratio",
            "Compare operational footprint",
            "Compare digital maturity"
          ],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, compMsg]);
        return;
      }

      if (Array.isArray(data.chat_history) && data.chat_history.length > 0) {
        const updatedSaved = data.chat_history.map(m => 
          m.type === 'analysis_complete' ? { ...m, reportData: currentReport } : m
        );
        const reportId = data.analysis_id || currentReport?.id || currentReport?.company_name || targetCompany;
        const completedMsg = {
          id: generateMsgId('report-' + reportId),
          sender: 'assistant',
          type: 'analysis_complete',
          companyName: targetCompany,
          reportData: currentReport,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        const hasReportCard = updatedSaved.some(m => m.type === 'analysis_complete');
        setMessages(hasReportCard ? updatedSaved : [completedMsg, ...updatedSaved]);
        return;
      }

      const matchedP = data.matched_parameter;
      const pData = data.parameter_data || null;
      const displayMode = data.display_mode || (pData ? 'parameter_card' : 'text_only');

      const botMsg = {
        id: generateMsgId('bot'),
        sender: 'assistant',
        text: data.answer || "Here is the analyzed intelligence for this prospect.",
        matchedParameter: matchedP,
        parameterData: pData,
        displayMode: displayMode,
        suggestedFollowups: data.suggested_followups || [],
        availableParameters: data.available_parameters || (currentReport?.report_data ? Object.keys(currentReport.report_data) : []),
        companyName: data.company_name || targetCompany,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error("Chat API Error:", err);
      const detail = err.response?.data?.detail;
      const errorText = typeof detail === 'object' && detail !== null
        ? `${detail.message || 'AI service unavailable'}${detail.reason && detail.reason !== detail.message ? ` (${detail.reason})` : ''}`
        : (detail || err.message || "Failed to reach AI assistant. Please try again.");
      setMessages(prev => [
        ...prev,
        {
          id: generateMsgId('bot-err'),
          sender: 'assistant',
          text: errorText,
          companyName: targetCompany,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setChatLoading(false);
      isSendingRef.current = false;
    }
  }, [loading, chatLoading, inputVal, currentReport, pendingProspect, sessionCompany]);

  // Keep sendMessageRef current
  useEffect(() => {
    sendMessageRef.current = handleSendMessage;
  }, [handleSendMessage]);

  // Auto-run comparative query when launched from Compare Modal (guaranteed once per query timestamp)
  useEffect(() => {
    if (pendingComparisonQuery && pendingComparisonQuery.query) {
      const queryKey = `${pendingComparisonQuery.query}-${pendingComparisonQuery.timestamp || ''}`;
      if (processedComparisonRef.current !== queryKey) {
        processedComparisonRef.current = queryKey;
        if (sendMessageRef.current) {
          sendMessageRef.current(pendingComparisonQuery.query);
        }
      }
    }
  }, [pendingComparisonQuery]);

  // Export handlers
  const handleExportMarkdown = (report) => {
    let md = `# Prospect Analysis Report: ${report.company_name}\n\n`;
    md += `## Executive Synthesis\n${report.executive_summary}\n\n---\n\n`;
    Object.entries(report.report_data || {}).forEach(([param, data]) => {
      md += `### ${param}\n**Summary:**\n${data.summary}\n\n**Key Facts:**\n`;
      (data.key_facts || []).forEach(h => md += `- ${h}\n`);
      md += `\n**Sources & Evidence:**\n`;
      (data.sources || []).forEach(s => {
        const dateStr = s.published_date ? ` (Published: ${s.published_date})` : '';
        md += `- [${s.name || s.url}](${s.url})${dateStr} ${s.evidence ? `- "${s.evidence}"` : ''}\n`;
      });
      md += `\n\n`;
    });
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${report.company_name.replace(/\s+/g, '_')}_Prospect_Report.md`;
    link.click();
  };

  const handleExportJSON = (report) => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${report.company_name.replace(/\s+/g, '_')}_Prospect_Report.json`;
    link.click();
  };

  const handleDownloadPDF = (report) => {
    exportReportToPDF(report);
  };

  return (
    <div className="chatgpt-container">
      {/* Messages Scroll Stream */}
      <div className="chatgpt-stream">
        {messages.length === 0 && !loading ? (
          /* Welcome Screen Hero */
          <div className="chatgpt-welcome-hero">
            <div className="chatgpt-hero-icon">
              <Sparkles size={28} color="#ffffff" />
            </div>
            <h2 className="chatgpt-hero-title">
              What prospect would you like to analyze?
            </h2>
            <p className="chatgpt-hero-subtitle">
              Select or search any verified insurance company to run a complete multi-source intelligence analysis across all 8 parameters.
            </p>

            {/* Quick Carrier Preset Chips */}
            <div className="chatgpt-presets-bar">
              <span className="chatgpt-presets-label">Supported Insurance Carriers:</span>
              <div className="chatgpt-presets-list">
                {SAMPLE_CARRIER_EXAMPLES.map((carrier) => (
                  <button
                    key={carrier}
                    className="chatgpt-preset-chip"
                    onClick={() => handleSelectProspect(carrier)}
                  >
                    {carrier}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Message Conversation Stream */
          <div className="chatgpt-messages-list">
            {/* 🏢 BEGINNING OF CHAT: Submitted Prospect Details Card */}
            {(currentReport || activeCompany || pendingProspect) && (
              <div className="submitted-prospect-card" style={{
                background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8b 100%)',
                color: '#ffffff',
                borderRadius: '12px',
                padding: '1.25rem 1.5rem',
                marginBottom: '1.5rem',
                boxShadow: '0 4px 14px rgba(15, 23, 42, 0.18)',
                border: '1px solid #3b82f6'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '1.05rem', fontWeight: 800, color: '#60a5fa' }}>
                    <Building size={20} color="#60a5fa" />
                    <span>SUBMITTED PROSPECT DETAILS</span>
                  </div>
                  <span style={{
                    background: '#2563eb',
                    color: '#ffffff',
                    fontSize: '0.78rem',
                    fontWeight: 800,
                    padding: '0.25rem 0.75rem',
                    borderRadius: '20px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem'
                  }}>
                    📊 General Prospect Mode
                  </span>
                </div>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '1rem',
                  background: 'rgba(255, 255, 255, 0.06)',
                  padding: '0.9rem 1.1rem',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                  <div>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.2rem' }}>Target Prospect</div>
                    <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#ffffff' }}>
                      {currentReport?.company_name || activeCompany || pendingProspect || 'Target Prospect'}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.2rem' }}>Domain</div>
                    <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#cbd5e1' }}>Commercial Insurance</div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.2rem' }}>Underwriting Scope</div>
                    <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#e2e8f0' }}>
                      8 Core Underwriting Parameters
                    </div>
                  </div>
                </div>
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`chatgpt-message-row ${msg.sender}`}>
                <div className="chatgpt-avatar">
                  {msg.sender === 'user' ? 'U' : <ShieldCheck size={18} color="#ffffff" />}
                </div>

                <div className="chatgpt-message-bubble">
                  {/* TYPE 1: Prospect Validation Card */}
                  {msg.type === 'validation_card' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#059669', fontSize: '0.92rem', fontWeight: 700 }}>
                          <CheckCircle2 size={16} /> Prospect validated
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0284c7', fontSize: '0.88rem', fontWeight: 600 }}>
                          <CheckCircle2 size={15} /> Domain: {msg.domain || 'Insurance'}
                        </div>
                      </div>

                      <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#1e293b' }}>
                        Ready to analyze <strong>{msg.prospect}</strong> across all 8 core underwriting parameters.
                      </div>

                      <button
                        className="btn-primary"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.5rem',
                          padding: '0.7rem 1.4rem',
                          fontSize: '0.95rem',
                          fontWeight: 700,
                          borderRadius: '8px',
                          background: '#2563eb',
                          color: '#ffffff',
                          border: 'none',
                          cursor: 'pointer',
                          marginTop: '0.35rem',
                          boxShadow: '0 2px 6px rgba(37, 99, 235, 0.25)'
                        }}
                        onClick={() => handleStartAnalysis(msg.prospect)}
                        disabled={loading}
                      >
                        <Sparkles size={16} /> Start Analysis
                      </button>
                    </div>
                  )}

                  {/* TYPE: Prospect Switch Confirmation Card */}
                  {msg.type === 'prospect_switch_required' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', background: '#fefce8', border: '1px solid #fef08a', padding: '1rem', borderRadius: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#b45309', fontSize: '0.92rem', fontWeight: 700 }}>
                        <HelpCircle size={17} color="#d97706" /> Prospect Context Switch
                      </div>

                      <p style={{ margin: 0, fontSize: '0.94rem', color: '#1e293b', lineHeight: '1.6' }}>
                        I noticed you're asking about <strong>{msg.requestedProspect}</strong>, while we are currently analyzing <strong>{msg.activeProspect}</strong>.
                      </p>
                      <p style={{ margin: 0, fontSize: '0.92rem', fontWeight: 600, color: '#334155' }}>
                        Would you like to switch to <strong>{msg.requestedProspect}</strong> and continue the analysis?
                      </p>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', marginTop: '0.35rem' }}>
                        <button
                          className="btn-primary"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.45rem',
                            padding: '0.6rem 1.15rem',
                            fontSize: '0.88rem',
                            fontWeight: 700,
                            borderRadius: '8px',
                            background: '#2563eb',
                            color: '#ffffff',
                            border: 'none',
                            cursor: 'pointer',
                            boxShadow: '0 2px 4px rgba(37, 99, 235, 0.2)'
                          }}
                          onClick={() => handleSwitchProspect(msg.requestedProspect, msg.pendingQuestion, msg.pendingParameter)}
                          disabled={loading || chatLoading}
                        >
                          <ArrowRight size={14} /> Switch to {msg.requestedProspect}
                        </button>

                        <button
                          className="btn-secondary"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.4rem',
                            padding: '0.6rem 1.15rem',
                            fontSize: '0.88rem',
                            fontWeight: 600,
                            borderRadius: '8px',
                            background: '#ffffff',
                            color: '#334155',
                            border: '1px solid #cbd5e1',
                            cursor: 'pointer'
                          }}
                          onClick={() => handleStayWithProspect(msg.activeProspect)}
                          disabled={loading || chatLoading}
                        >
                          Stay with {msg.activeProspect}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* TYPE: Comparative Peer Benchmarking Matrix */}
                  {msg.type === 'prospect_comparison' && (msg.comparisonMatrix || msg.comparison_matrix) && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                      {msg.text && (
                        <FormattedMessageText text={msg.text} isUser={false} />
                      )}
                      <ComparativeMatrixCard data={msg.comparisonMatrix || msg.comparison_matrix} />
                    </div>
                  )}

                  {/* TYPE 2: Disambiguation Choice Card */}
                  {msg.type === 'disambiguation_card' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                      <p style={{ margin: 0, fontSize: '0.92rem', fontWeight: 600, color: '#1e293b' }}>
                        {msg.text}
                      </p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem', marginTop: '0.25rem' }}>
                        {(msg.candidates || []).map((cand) => (
                          <button
                            key={cand.id || cand.name}
                            className="chatgpt-pill-btn"
                            style={{ background: '#eff6ff', borderColor: '#bfdbfe', color: '#1d4ed8', fontWeight: 600, padding: '0.4rem 0.8rem' }}
                            onClick={() => handleSelectProspect(cand)}
                          >
                            {cand.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* TYPE 3: Analysis Completed Report Summary & Exploration */}
                  {msg.type === 'analysis_complete' && msg.reportData && (
                    <div className="chatgpt-report-wrapper">
                      {/* Analysis Completed Header */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#059669', fontSize: '1rem', fontWeight: 800, marginBottom: '0.75rem' }}>
                        <CheckCircle2 size={20} /> Analysis completed ✓
                      </div>

                      {/* Header Title */}
                      <div className="report-header-card" style={{ marginBottom: '1rem', padding: '1rem' }}>
                        <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ffffff', margin: '0 0 0.25rem 0' }}>
                          {msg.companyName || msg.reportData?.company_name || activeCompany || 'Prospect Intelligence Report'}
                        </h2>
                        <div className="report-meta" style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                          <span>Multi-Source Verified</span>
                          <span>•</span>
                          <span>{msg.reportData?.analysis_mode === 'PROPOSAL' ? 'Proposal-Based Fit Analysis' : '8 Parameters Analyzed'}</span>
                          <span>•</span>
                          <span>Grounded Disclosures</span>
                        </div>
                      </div>

                      {/* Proposal Mode Banner */}
                      {msg.reportData?.analysis_mode === 'PROPOSAL' && (
                        <div style={{
                          background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)',
                          color: '#ffffff',
                          borderRadius: '12px',
                          padding: '1.25rem',
                          marginBottom: '1.25rem',
                          border: '1px solid #3b82f6',
                          boxShadow: '0 4px 12px rgba(37, 99, 235, 0.25)'
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 800, fontSize: '1.05rem', color: '#60a5fa' }}>
                              <FileText size={20} />
                              <span>PROPOSAL-BASED FIT EVALUATION</span>
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                              {msg.reportData.risk_rating && (
                                <span style={{
                                  background: msg.reportData.risk_rating === 'Low' ? '#0284c7' : msg.reportData.risk_rating === 'Critical' ? '#dc2626' : '#d97706',
                                  color: '#ffffff',
                                  fontSize: '0.85rem',
                                  fontWeight: 800,
                                  padding: '0.3rem 0.75rem',
                                  borderRadius: '20px'
                                }}>
                                  {msg.reportData.risk_rating} Risk
                                </span>
                              )}
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
                            {msg.reportData.proposal_filename && (
                              <div style={{ fontSize: '0.85rem', opacity: 0.9, color: '#cbd5e1' }}>
                                📄 Document: <strong>{msg.reportData.proposal_filename}</strong>
                              </div>
                            )}

                            {onOpenProposal && (
                              <button
                                type="button"
                                onClick={() => onOpenProposal(msg.reportData)}
                                style={{
                                  background: '#2563eb',
                                  color: '#ffffff',
                                  border: 'none',
                                  padding: '0.35rem 0.8rem',
                                  borderRadius: '6px',
                                  fontSize: '0.8rem',
                                  fontWeight: 700,
                                  cursor: 'pointer',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '0.35rem',
                                  boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                                }}
                              >
                                <FileText size={13} /> Open Original Document ↗
                              </button>
                            )}
                          </div>

                          {msg.reportData.proposal_details && (
                            <div style={{ background: 'rgba(255, 255, 255, 0.08)', padding: '0.75rem 0.9rem', borderRadius: '8px', fontSize: '0.85rem', color: '#f1f5f9', border: '1px solid rgba(255,255,255,0.1)' }}>
                              <div style={{ fontWeight: 700, marginBottom: '0.3rem', color: '#93c5fd' }}>Parsed Proposal Terms:</div>
                              <div><strong>Coverages:</strong> {Array.isArray(msg.reportData.proposal_details.proposed_coverages) ? msg.reportData.proposal_details.proposed_coverages.join(', ') : 'Commercial Lines'}</div>
                              <div><strong>Sum Insured:</strong> {msg.reportData.proposal_details.total_sum_insured || 'N/A'} | <strong>Premium:</strong> {msg.reportData.proposal_details.proposed_premium || 'N/A'}</div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Executive Summary */}
                      {msg.reportData.executive_summary && (
                        <div className="exec-summary-card" style={{ marginBottom: '1.25rem', padding: '1rem', background: '#f8fafc', borderLeft: '4px solid #2563eb', borderRadius: '0 8px 8px 0' }}>
                          <div className="exec-summary-title" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.82rem', fontWeight: 700, color: '#2563eb', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                            <Sparkles size={14} /> Executive Synthesis
                          </div>
                          <p className="exec-summary-text" style={{ margin: 0, fontSize: '0.92rem', color: '#334155', lineHeight: '1.6' }}>
                            {msg.reportData.executive_summary}
                          </p>
                        </div>
                      )}

                      {/* Export & Actions */}
                      <div className="export-bar" style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                        <button
                          className="btn-primary"
                          style={{
                            padding: '0.4rem 0.85rem',
                            fontSize: '0.8rem',
                            background: '#eff6ff',
                            color: '#1d4ed8',
                            border: '1px solid #bfdbfe',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            cursor: 'pointer',
                            borderRadius: '6px',
                            fontWeight: 700
                          }}
                          onClick={() => onOpenCompare && onOpenCompare(msg.companyName)}
                        >
                          <Scale size={14} color="#2563eb" /> Compare with Peers
                        </button>
                        <button
                          className="btn-secondary"
                          style={{
                            padding: '0.4rem 0.85rem',
                            fontSize: '0.8rem',
                            background: '#eff6ff',
                            color: '#1d4ed8',
                            border: '1px solid #bfdbfe',
                            fontWeight: 700,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.35rem'
                          }}
                          onClick={() => handleDownloadPDF(msg.reportData)}
                        >
                          <Download size={14} color="#2563eb" /> Download PDF (.pdf)
                        </button>
                        <button className="btn-secondary" style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleExportMarkdown(msg.reportData)}>
                          <FileText size={14} /> Export Markdown
                        </button>
                        <button className="btn-secondary" style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }} onClick={() => handleExportJSON(msg.reportData)}>
                          <Download size={14} /> Export JSON
                        </button>
                      </div>

                      {/* What would you like to explore? Title */}
                      <div style={{ marginTop: '1.25rem', marginBottom: '0.65rem' }}>
                        <span style={{ fontSize: '0.92rem', fontWeight: 700, color: '#0f172a' }}>
                          What would you like to explore?
                        </span>
                      </div>

                      {/* Parameter Exploration Buttons */}
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '1.25rem' }}>
                        <button
                          className={`chatgpt-pill-btn ${selectedParameterFilter === 'all' ? 'active-pill' : ''}`}
                          style={{
                            background: selectedParameterFilter === 'all' ? '#2563eb' : '#f1f5f9',
                            color: selectedParameterFilter === 'all' ? '#ffffff' : '#334155',
                            fontWeight: 700,
                            padding: '0.4rem 0.8rem'
                          }}
                          onClick={() => {
                            setSelectedParameterFilter('all');
                          }}
                        >
                          View Full Analysis
                        </button>
                        {Object.keys(msg.reportData.report_data || {}).map(param => (
                          <button
                            key={param}
                            className="chatgpt-pill-btn"
                            style={{
                              background: selectedParameterFilter === param ? '#2563eb' : '#f8fafc',
                              color: selectedParameterFilter === param ? '#ffffff' : '#334155',
                              fontWeight: 600,
                              padding: '0.4rem 0.75rem'
                            }}
                            onClick={() => {
                              setSelectedParameterFilter(param);
                              handleParameterClick(param, msg.companyName);
                            }}
                          >
                            {param}
                          </button>
                        ))}
                      </div>

                      {/* Full Analysis Grid when "All" is active */}
                      {selectedParameterFilter === 'all' && (
                        <div className="parameters-grid" style={{ gridTemplateColumns: '1fr', gap: '1rem' }}>
                          {Object.entries(msg.reportData.report_data || {}).map(([paramName, paramData]) => (
                            <SingleParameterCard key={paramName} paramName={paramName} data={paramData} />
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* TYPE 4: Conversational Text Q&A */}
                  {(!msg.type || msg.type === 'text') && (
                    <div className="chatgpt-text-response">
                      {/* Render text if text exists and parameterData is null (or for user messages) */}
                      {msg.text && (msg.sender === 'user' || !msg.parameterData) && (
                        <FormattedMessageText text={msg.text} isUser={msg.sender === 'user'} />
                      )}

                      {/* Render Structured Parameter Card whenever parameterData is present */}
                      {msg.parameterData && (
                        <div>
                          <SingleParameterCard paramName={msg.matchedParameter || 'Parameter Intelligence'} data={msg.parameterData} />
                        </div>
                      )}

                      {/* Parameter Exploration Pills for Follow-up Inquiries */}
                      {msg.sender === 'assistant' && msg.companyName && (
                        <div className="chatgpt-quick-param-pills" style={{ marginTop: '0.75rem' }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                            Explore Parameters:
                          </span>
                          {(msg.availableParameters && msg.availableParameters.length > 0 
                            ? msg.availableParameters 
                            : (currentReport?.report_data ? Object.keys(currentReport.report_data) : [])
                          ).map((p) => (
                            <button
                              key={p}
                              className="chatgpt-pill-btn"
                              style={{
                                background: msg.matchedParameter === p ? '#eff6ff' : '#f8fafc',
                                borderColor: msg.matchedParameter === p ? '#2563eb' : '#e2e8f0',
                                color: msg.matchedParameter === p ? '#1d4ed8' : '#334155',
                                fontWeight: 600
                              }}
                              onClick={() => handleParameterClick(p, msg.companyName)}
                            >
                              {p}
                            </button>
                          ))}
                        </div>
                      )}

                      {/* Suggested Follow-up Prompts */}
                      {msg.sender === 'assistant' && msg.suggestedFollowups && msg.suggestedFollowups.length > 0 && (
                        <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                            <Sparkles size={12} color="#2563eb" /> Suggested Follow-up Inquiries:
                          </span>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                            {msg.suggestedFollowups.map((chip, idx) => (
                              <button
                                key={idx}
                                className="chatgpt-pill-btn"
                                style={{ background: '#f0f9ff', borderColor: '#bae6fd', color: '#0369a1', fontSize: '0.78rem' }}
                                onClick={() => handleSendMessage(chip, null, msg.companyName)}
                              >
                                {chip}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* LIVE ANALYSIS PROGRESS TRACKER STEPPER */}
            {loading && (
              <div className="chatgpt-message-row assistant">
                <div className="chatgpt-avatar">
                  <ShieldCheck size={18} color="#ffffff" />
                </div>
                <div className="chatgpt-message-bubble" style={{ background: '#ffffff', width: '100%', maxWidth: '600px', border: '1px solid #93c5fd' }}>
                  <div style={{ textAlign: 'center', marginBottom: '1rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.65rem' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#2563eb', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      ───────── Analysis running ─────────
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {ANALYSIS_STEPS.map((step) => {
                      const isComplete = activeStep > step.id;
                      const isCurrent = activeStep === step.id;
                      return (
                        <div key={step.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.65rem' }}>
                          <div style={{ marginTop: '2px' }}>
                            {isComplete ? (
                              <CheckCircle2 size={18} color="#059669" />
                            ) : isCurrent ? (
                              <div className="spin-icon" style={{ width: '16px', height: '16px', border: '2px solid #2563eb', borderTopColor: 'transparent', borderRadius: '50%' }} />
                            ) : (
                              <div style={{ width: '16px', height: '16px', borderRadius: '50%', border: '1.5px solid #cbd5e1' }} />
                            )}
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column' }}>
                            <span style={{ fontSize: '0.9rem', fontWeight: isCurrent ? 700 : 600, color: isComplete ? '#059669' : isCurrent ? '#1e293b' : '#94a3b8' }}>
                              {isComplete ? `✓ ${step.label}` : step.label}
                            </span>
                            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                              {step.desc}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* Chat Q&A Loading Indicator */}
            {chatLoading && !loading && (
              <div className="chatgpt-message-row assistant">
                <div className="chatgpt-avatar">
                  <ShieldCheck size={18} color="#ffffff" />
                </div>
                <div className="chatgpt-message-bubble loading-bubble">
                  <div className="chatgpt-typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
                    Consulting verified underwriting disclosures...
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Floating Bottom Prompt Input Bar with Autocomplete Dropdown */}
      <div className="chatgpt-input-wrapper">
        {/* Autocomplete Dropdown */}
        {searchSuggestions.length > 0 && (
          <div style={{
            position: 'absolute',
            bottom: '100%',
            marginBottom: '6px',
            maxWidth: '820px',
            width: 'calc(100% - 2.5rem)',
            background: '#ffffff',
            borderRadius: '10px',
            boxShadow: '0 -4px 16px rgba(0, 0, 0, 0.12)',
            border: '1px solid #e2e8f0',
            overflow: 'hidden',
            zIndex: 100
          }}>
            <div style={{ padding: '0.45rem 0.85rem', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
              Supported Insurance Prospects:
            </div>
            {searchSuggestions.map((item) => (
              <div
                key={item.id}
                style={{
                  padding: '0.65rem 1rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f1f5f9',
                  transition: 'background 0.15s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#f1f5f9'}
                onMouseLeave={(e) => e.currentTarget.style.background = '#ffffff'}
                onClick={() => handleSelectProspect(item)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Building size={15} color="#2563eb" />
                  <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#1e293b' }}>{item.name}</span>
                </div>
                <span style={{ fontSize: '0.72rem', fontWeight: 500, color: '#64748b', background: '#f1f5f9', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
                  {item.id}
                </span>
              </div>
            ))}
          </div>
        )}

        <form 
          className="chatgpt-input-form"
          onSubmit={(e) => {
            e.preventDefault();
            if (!currentReport && !pendingProspect && inputVal.trim()) {
              const targetCompany = pendingProspect || sessionCompany || inputVal.trim();
              if (targetCompany) {
                onAnalyze(targetCompany, 'Insurance');
                setInputVal('');
                return;
              }
            }
            handleSendMessage();
          }}
        >
          <input
            type="text"
            className="chatgpt-input-field"
            placeholder={
              currentReport 
                ? `Ask about ${currentReport.company_name} (e.g. "Tell me about Financial Strength")...` 
                : "Search prospect name to analyze (e.g. 'SBI Life Insurance')..."
            }
            value={inputVal}
            onChange={handleInputChange}
            disabled={loading || chatLoading}
          />

          <button
            type="submit"
            className="chatgpt-send-btn"
            disabled={loading || chatLoading || !inputVal.trim()}
            title="Send message"
          >
            <Send size={16} />
          </button>
        </form>

        <div className="chatgpt-input-disclaimer">
          Prospect AI • Authoritative 250 Insurance Prospect Directory & Multi-Source Underwriting Intelligence
        </div>
      </div>
    </div>
  );
}

// Formatted Message Text with Markdown Link parsing
function FormattedMessageText({ text, isUser }) {
  if (!text) return null;
  const lines = text.split('\n');
  return (
    <div style={{
      fontSize: '0.94rem',
      lineHeight: '1.65',
      color: isUser ? '#ffffff' : '#1e293b'
    }}>
      {lines.map((line, lIdx) => {
        const parts = [];
        let lastIdx = 0;
        const linkRegex = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
        let match;
        while ((match = linkRegex.exec(line)) !== null) {
          if (match.index > lastIdx) {
            parts.push(line.substring(lastIdx, match.index));
          }
          parts.push(
            <a
              key={match.index}
              href={match[2]}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#2563eb', fontWeight: 600, textDecoration: 'underline' }}
            >
              {match[1]}
            </a>
          );
          lastIdx = match.index + match[0].length;
        }
        if (lastIdx < line.length) {
          parts.push(line.substring(lastIdx));
        }

        return (
          <div key={lIdx} style={{ minHeight: line.trim() === '' ? '0.4rem' : 'auto' }}>
            {parts.length > 0 ? parts : line}
          </div>
        );
      })}
    </div>
  );
}

// Single Parameter Card Component
function SingleParameterCard({ paramName, data }) {
  if (!data) return null;
  const keyFacts = (data.key_facts || []).slice(0, 5);
  const sourcesList = (data.sources || []).slice(0, 5);
  const displaySummary = data.summary || data.explanation || "";

  const getParamIcon = (title) => {
    switch (title) {
      case 'Company Scale': return <Building size={18} color="#2563eb" />;
      case 'Business Growth': return <TrendingUp size={18} color="#059669" />;
      case 'Market Position': return <Award size={18} color="#0284c7" />;
      case 'Financial Strength': return <ShieldAlert size={18} color="#d97706" />;
      case 'Insurance Performance': return <Activity size={18} color="#2563eb" />;
      case 'Operational Scale': return <Briefcase size={18} color="#475569" />;
      case 'Technology Activity': return <Zap size={18} color="#7c3aed" />;
      default: return <Globe size={18} color="#475569" />;
    }
  };

  return (
    <div className="param-card" style={{ background: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', padding: '1.15rem', boxShadow: '0 1px 3px rgba(0,0,0,0.03)', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      {/* Parameter Card Title Bar */}
      <div className="param-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem', margin: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ background: '#f8fafc', padding: '0.3rem', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #e2e8f0' }}>
            {getParamIcon(paramName)}
          </div>
          <span style={{ fontSize: '0.96rem', fontWeight: 700, color: '#1e293b' }}>{paramName}</span>
        </div>
        <span style={{ fontSize: '0.7rem', fontWeight: 600, background: '#eff6ff', color: '#2563eb', padding: '0.15rem 0.5rem', borderRadius: '9999px', border: '1px solid #bfdbfe' }}>
          Verified Disclosures
        </span>
      </div>

      {/* 1. Detailed Summary */}
      {displaySummary && (
        <div style={{ background: '#f8fafc', borderLeft: '3px solid #2563eb', padding: '0.75rem 0.9rem', borderRadius: '0 6px 6px 0' }}>
          <h4 style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', color: '#2563eb', marginBottom: '0.25rem', letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <Sparkles size={12} /> Parameter Summary
          </h4>
          <p className="param-summary" style={{ fontSize: '0.88rem', color: '#334155', lineHeight: '1.55', margin: 0 }}>
            {displaySummary}
          </p>
        </div>
      )}

      {/* 2. Key Empirical Facts (Max 5) */}
      {keyFacts.length > 0 && (
        <div>
          <h4 style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', color: '#64748b', marginBottom: '0.4rem', letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <CheckCircle2 size={12} color="#059669" /> Key Facts & Observations ({keyFacts.length})
          </h4>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', margin: 0, paddingLeft: 0, listStyle: 'none' }}>
            {keyFacts.map((fact, idx) => (
              <li key={idx} style={{ fontSize: '0.84rem', color: '#334155', display: 'flex', alignItems: 'flex-start', gap: '0.45rem', background: '#f8fafc', border: '1px solid #f1f5f9', padding: '0.45rem 0.65rem', borderRadius: '6px' }}>
                <span style={{ color: '#2563eb', fontWeight: 700 }}>•</span>
                <span style={{ lineHeight: '1.4' }}>{fact}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 3. Verified Sources & Evidence Attribution */}
      {sourcesList.length > 0 && (
        <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '0.85rem 1rem' }}>
          <h4 style={{ fontSize: '0.74rem', fontWeight: 800, textTransform: 'uppercase', color: '#1d4ed8', marginBottom: '0.5rem', letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <BookOpen size={13} color="#2563eb" /> Grounded Evidence & Verified Sources ({sourcesList.length})
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
            {sourcesList.map((s, idx) => {
              const name = typeof s === 'object' ? (s.name || s.title) : s;
              const rawUrl = typeof s === 'object' ? s.url : s;
              const url = rawUrl && !rawUrl.startsWith('http') ? `https://${rawUrl}` : rawUrl;
              const evidence = typeof s === 'object' ? s.evidence : null;
              const rawDate = typeof s === 'object' ? s.published_date : null;

              let formattedDate = rawDate;
              if (rawDate && /^\d{4}-\d{2}-\d{2}/.test(String(rawDate).trim())) {
                try {
                  const d = new Date(rawDate);
                  if (!isNaN(d.getTime())) {
                    formattedDate = d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
                  }
                } catch {
                  formattedDate = rawDate;
                }
              }

              return (
                <div key={idx} style={{ fontSize: '0.82rem', background: '#ffffff', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #dbeafe', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
                      {url ? (
                        <a href={url} target="_blank" rel="noopener noreferrer" style={{ fontWeight: 700, color: '#1e3a8a', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                          {name || "Official Public Filing & Disclosure"}
                        </a>
                      ) : (
                        <span style={{ fontWeight: 700, color: '#1e3a8a' }}>{name || "Official Public Filing & Disclosure"}</span>
                      )}
                      {formattedDate && (
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.22rem',
                          fontSize: '0.71rem',
                          color: '#475569',
                          backgroundColor: '#f1f5f9',
                          border: '1px solid #e2e8f0',
                          padding: '0.08rem 0.4rem',
                          borderRadius: '4px',
                          fontWeight: 500
                        }}>
                          <Calendar size={11} color="#64748b" /> {formattedDate}
                        </span>
                      )}
                    </div>
                    {url && (
                      <a href={url} target="_blank" rel="noopener noreferrer" style={{ fontWeight: 700, color: '#2563eb', background: '#dbeafe', padding: '0.2rem 0.55rem', borderRadius: '4px', textDecoration: 'none', fontSize: '0.76rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                        View Source <ExternalLink size={10} />
                      </a>
                    )}
                  </div>
                  {evidence && (
                    <p style={{ fontSize: '0.78rem', color: '#475569', marginTop: '0.25rem', margin: '0.25rem 0 0 0', lineHeight: '1.4' }}>
                      "{evidence}"
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
