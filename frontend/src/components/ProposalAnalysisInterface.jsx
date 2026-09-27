import { useState, useEffect, useRef } from 'react';
import { 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  AlertTriangle, 
  Sparkles, 
  Building, 
  Upload, 
  Search, 
  Download, 
  X, 
  RefreshCw, 
  Layers, 
  Target, 
  TrendingUp, 
  Zap, 
  HelpCircle, 
  Check, 
  ExternalLink
} from 'lucide-react';
import client from '../api/client';

const SAMPLE_PROSPECTS = [
  "Allianz",
  "AXA",
  "Zurich Insurance Group",
  "Chubb",
  "SBI Life Insurance",
  "HDFC ERGO",
  "ICICI Lombard",
  "State Farm"
];

const DEFAULT_PROPOSAL_PARAMETERS = [
  {
    id: "business_alignment",
    name: "Business Alignment",
    category: "Prospect Fit",
    description: "How closely the prospect's overall business model, commercial lines, and target markets align with the proposal."
  },
  {
    id: "insurance_product_alignment",
    name: "Insurance Product Alignment",
    category: "Domain Fit",
    description: "Alignment between the proposal's product scope (property, casualty, life, cyber, health) and the prospect's existing product offerings."
  },
  {
    id: "underwriting_relevance",
    name: "Underwriting Relevance",
    category: "Business Need",
    description: "Relevance of the proposal to the prospect's underwriting operations, appetite, pricing discipline, and risk intake."
  },
  {
    id: "claims_relevance",
    name: "Claims Relevance",
    category: "Operations",
    description: "Relevance of the proposal to claims processing, adjudication speed, fraud detection, and settlement operations."
  },
  {
    id: "ai_ml_adoption",
    name: "AI / ML Adoption",
    category: "Technology",
    description: "Evidence of AI/ML adoption, predictive analytics, intelligent automation, or strategic investments in cognitive technologies."
  },
  {
    id: "digital_transformation",
    name: "Digital Transformation",
    category: "Technology",
    description: "Evidence of digital transformation programs, cloud migrations, modern portal rollouts, and customer journey digitization."
  },
  {
    id: "technology_modernization",
    name: "Technology Modernization",
    category: "Technology",
    description: "Evidence of core IT modernization, legacy platform replacement, API-first architecture, and modern core system adoption."
  },
  {
    id: "data_analytics",
    name: "Data & Analytics",
    category: "Technology",
    description: "Relevance and maturity of enterprise data lakes, actuarial analytics, telemetry, and portfolio business intelligence."
  },
  {
    id: "strategic_initiative",
    name: "Strategic Initiative",
    category: "Strategy",
    description: "Evidence that the proposal directly supports corporate strategic priorities, executive goals, or announced multi-year roadmaps."
  },
  {
    id: "financial_capacity",
    name: "Financial Capacity",
    category: "Financial",
    description: "Prospect's financial scale, balance sheet health, capital surplus, solvency margin, and capability to fund multi-million investments."
  },
  {
    id: "growth_expansion",
    name: "Growth / Expansion",
    category: "Business Signals",
    description: "Commercial growth signals, gross written premium (GWP) expansion, regional diversification, and active market share acquisition."
  },
  {
    id: "implementation_fit",
    name: "Implementation Fit",
    category: "Solution Fit",
    description: "Operational feasibility, organizational readiness, partner integration ecosystem, and delivery timeline alignment for the proposed solution."
  },
  {
    id: "opportunity_timing",
    name: "Opportunity Timing",
    category: "Buying Signal",
    description: "Evidence indicating potential timing, procurement cycles, executive leadership turnover, technology obsolescence, or urgent business triggers."
  },
  {
    id: "regulatory_compliance",
    name: "Regulatory / Compliance Fit",
    category: "Risk",
    description: "Relevance of insurance regulatory compliance (IRDAI, Solvency II, NAIC, EIOPA), statutory reporting, data privacy, and governance requirements."
  },
  {
    id: "competitive_landscape",
    name: "Competitive Landscape",
    category: "Market",
    description: "Market positioning, competitive moat, peer group benchmarking, and defensive or offensive pressures relevant to the proposed solution."
  }
];

const stripMarkdown = (text) => {
  if (!text || typeof text !== 'string') return '';
  return text
    // Strip bracketed scores e.g. (85/100), (61/100), (85%), [85/100]
    .replace(/(?:\(|\[)\s*(?:Score:\s*)?\d+(?:\.\d+)?\s*\/\s*100\s*(?:\)|\])/gi, '')
    .replace(/(?:\(|\[)\s*\d+(?:\.\d+)?%\s*(?:\)|\])/g, '')
    .replace(/(?:\(|\[)\s*Score:\s*\d+\s*(?:\)|\])/gi, '')
    // Strip standalone score terminology
    .replace(/\b(?:an?\s+)?(?:overall\s+)?(?:high|moderate|medium|low|very high)?\s*fit\s+score\s+(?:of\s+)?\d+(?:\.\d+)?(?:\s*\/\s*100)?\b/gi, 'strong overall alignment')
    .replace(/\b(?:an?\s+)?(?:overall\s+)?score\s+(?:of\s+)?\d+(?:\.\d+)?(?:\s*\/\s*100)?\b/gi, '')
    .replace(/\b\d+(?:\.\d+)?\s*\/\s*100\b/g, '')
    .replace(/\b(?:High|Moderate|Low|Very High)\s+Fit\s+score\b/gi, 'alignment')
    .replace(/\bFit\s+score\b/gi, 'alignment')
    .replace(/\bConfidence\s+Score:\s*\d+\b/gi, '')
    .replace(/\bFit\s+Score:\s*\d+\b/gi, '')
    .replace(/\bOverall\s+Score:\s*\d+\b/gi, '')
    .replace(/^#+\s+/gm, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/---+/g, '')
    .replace(/:\s*:/g, ':')
    .replace(/\s{2,}/g, ' ')
    .trim();
};

const normalizeProposalReport = (data) => {
  if (!data) return null;

  let paramAnalysis = data.parameter_analysis;
  if ((!paramAnalysis || paramAnalysis.length === 0) && data.report_data && typeof data.report_data === 'object') {
    paramAnalysis = Object.entries(data.report_data)
      .filter(([key]) => key !== '_summary_synthesis')
      .map(([name, val]) => {
        if (!val || typeof val !== 'object') return null;
        return {
          parameter: name,
          parameter_id: val.parameter_id || name.toLowerCase().replace(/\s+/g, '_'),
          fit_level: val.fit_level || 'Moderate',
          confidence: val.confidence || 'High',
          finding: stripMarkdown(val.finding || val.summary || ''),
          reasoning: stripMarkdown(val.reasoning || val.why_it_matters || (Array.isArray(val.key_facts) ? val.key_facts.join(' ') : '')),
          evidence: val.evidence || val.sources || [],
          gaps: Array.isArray(val.gaps) ? val.gaps.map(stripMarkdown) : [],
          category: val.category || 'General'
        };
      })
      .filter(Boolean);
  }

  const synthesis = data.report_data?._summary_synthesis 
    || data.proposal_details?.summary_synthesis 
    || {};

  const companyName = data.prospect?.name || data.company_name || 'Target Prospect';
  const proposalTitle = data.proposal?.title 
    || data.proposal_details?.proposal_title 
    || data.proposal_filename 
    || 'Commercial Insurance Proposal';

  const strengths = (Array.isArray(data.strengths) && data.strengths.length > 0)
    ? data.strengths.map(stripMarkdown)
    : (synthesis.strongest_alignment || synthesis.strengths || (paramAnalysis ? paramAnalysis.filter(p => p.fit_level === 'High' || p.fit_level === 'Very High').map(p => `${p.parameter}: Strong operational alignment`) : [])).map(stripMarkdown);

  const gaps = (Array.isArray(data.gaps) && data.gaps.length > 0)
    ? data.gaps.map(stripMarkdown)
    : (synthesis.key_gaps || synthesis.gaps || (paramAnalysis ? paramAnalysis.filter(p => p.fit_level === 'Low').map(p => `${p.parameter}: Lower alignment`) : [])).map(stripMarkdown);

  const risks = (Array.isArray(data.risks) && data.risks.length > 0)
    ? data.risks.map(stripMarkdown)
    : (synthesis.risks_and_unknowns || synthesis.risks || ["Standard commercial underwriting warranties apply.", "Verification of claim reserves recommended."]).map(stripMarkdown);

  const opps = (Array.isArray(data.opportunity_signals) && data.opportunity_signals.length > 0)
    ? data.opportunity_signals.map(stripMarkdown)
    : (synthesis.opportunity_signals || [`Favorable underwriting appetite detected for ${companyName} in core target lines.`]).map(stripMarkdown);

  const rawOverall = data.overall_assessment || synthesis.overall_assessment || data.summary || data.executive_summary || 'Comprehensive proposal fit analysis evaluated across all selected underwriting parameters.';
  const cleanSummary = stripMarkdown(rawOverall);

  return {
    ...data,
    id: data.id,
    analysis_id: data.analysis_id || `PA-${data.id}`,
    prospect: {
      id: data.prospect?.id || 'INS-1',
      name: companyName
    },
    proposal: {
      id: data.proposal?.id || data.proposal_details?.proposal_id,
      title: proposalTitle,
      domain: data.proposal?.domain || data.proposal_details?.domain || 'Commercial Insurance',
      filename: data.proposal?.filename || data.proposal_filename || 'proposal.pdf'
    },
    parameter_analysis: paramAnalysis || [],
    strengths,
    gaps,
    risks,
    opportunity_signals: opps,
    recommended_contact_angle: stripMarkdown(data.recommended_contact_angle || synthesis.recommended_contact_angle || 'Engage executive underwriting sponsors with focus on proposal-aligned commercial coverage strengths.'),
    recommended_next_action: stripMarkdown(data.recommended_next_action || synthesis.recommended_next_action || 'Schedule formal underwriting alignment session to review policy terms and coverage limits.'),
    overall_assessment: cleanSummary,
    summary: cleanSummary,
    executive_summary: cleanSummary
  };
};

export default function ProposalAnalysisInterface({ savedReport, onAnalysisComplete, onReset }) {
  // Wizard State: 'setup' | 'analyzing' | 'results'
  const [stage, setStage] = useState(() => (
    (savedReport && (savedReport.analysis_mode === 'PROPOSAL' || savedReport.proposal_filename || savedReport.parameter_analysis))
      ? 'results'
      : 'setup'
  ));

  // Step 1: Prospect Selection
  const [selectedProspect, setSelectedProspect] = useState(null); // { id, name }
  const [prospectSearchInput, setProspectSearchInput] = useState('');
  const [prospectSuggestions, setProspectSuggestions] = useState([]);

  // Step 2: Proposal PDF Upload & Extraction
  const [proposalFile, setProposalFile] = useState(null);
  const [proposalProfile, setProposalProfile] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState('');

  // Step 3: Parameters Catalog & Selection (Default 15 canonical parameters, 0 selected initially)
  const [parameterCatalog, setParameterCatalog] = useState(DEFAULT_PROPOSAL_PARAMETERS);
  const [selectedParamIds, setSelectedParamIds] = useState(new Set());
  const [recommendedParamIds, setRecommendedParamIds] = useState(new Set());
  const [paramEvaluations, setParamEvaluations] = useState([]);

  // Step 4: Streaming & Progressive Concurrency State
  const [streamingParams, setStreamingParams] = useState({}); // { [paramId]: { parameter_id, parameter, category, status, result, error } }
  const [streamingSummary, setStreamingSummary] = useState(null);
  const [isStreamingComplete, setIsStreamingComplete] = useState(false);
  const [totalStreamParams, setTotalStreamParams] = useState(0);

  // Step 5: Results Data
  const [analysisResult, setAnalysisResult] = useState(() => (
    (savedReport && (savedReport.analysis_mode === 'PROPOSAL' || savedReport.proposal_filename || savedReport.parameter_analysis))
      ? normalizeProposalReport(savedReport)
      : null
  ));
  const [activeParamDetail, setActiveParamDetail] = useState(null);
  const [generalError, setGeneralError] = useState('');

  const fileInputRef = useRef(null);
  const searchTimeoutRef = useRef(null);

  // Sync state when savedReport prop changes
  const [prevSavedReport, setPrevSavedReport] = useState(savedReport);
  if (savedReport !== prevSavedReport) {
    setPrevSavedReport(savedReport);
    if (savedReport && (savedReport.analysis_mode === 'PROPOSAL' || savedReport.proposal_filename || savedReport.parameter_analysis)) {
      const normalized = normalizeProposalReport(savedReport);
      setAnalysisResult(normalized);
      setStage('results');
    } else if (!savedReport) {
      setAnalysisResult(null);
      setStage('setup');
      setSelectedProspect(null);
      setProposalFile(null);
      setProposalProfile(null);
      setSelectedParamIds(new Set());
      setRecommendedParamIds(new Set());
      setParamEvaluations([]);
      setStreamingParams({});
      setStreamingSummary(null);
      setIsStreamingComplete(false);
      setTotalStreamParams(0);
      setActiveParamDetail(null);
      setGeneralError('');
      setExtractionError('');
    }
  }

  // Load parameter catalog from backend (keeps DEFAULT_PROPOSAL_PARAMETERS as fallback)
  useEffect(() => {
    let ignore = false;
    async function loadCatalog() {
      try {
        const res = await client.get('/api/proposal/parameters');
        if (!ignore && res.data?.parameters && Array.isArray(res.data.parameters) && res.data.parameters.length > 0) {
          setParameterCatalog(res.data.parameters);
        }
      } catch (err) {
        console.warn("Could not load proposal parameter catalog, using default catalog:", err);
      }
    }
    loadCatalog();
    return () => {
      ignore = true;
    };
  }, []);

  // Autocomplete Prospect Search
  const handleProspectSearchChange = (e) => {
    const val = e.target.value;
    setProspectSearchInput(val);
    setGeneralError('');

    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    if (!val.trim() || val.length < 2) {
      setProspectSuggestions([]);
      return;
    }

    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const res = await client.get('/prospects/search', { params: { q: val.trim(), limit: 6 } });
        setProspectSuggestions(res.data?.results || []);
      } catch (err) {
        console.warn("Prospect search failed:", err);
      }
    }, 200);
  };

  const handleSelectProspect = (prospect) => {
    const pObj = typeof prospect === 'string' ? { name: prospect, id: null } : prospect;
    setSelectedProspect(pObj);
    setProspectSearchInput('');
    setProspectSuggestions([]);
    // Step 9: Changing prospect does NOT reset or alter RFP-selected parameters!
  };

  // PDF / DOCX File Selection & Extraction
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleProcessSelectedFile(file);
    }
  };

  const handleProcessSelectedFile = (file) => {
    setExtractionError('');
    if (!file) return;
    const isAllowed = /\.(pdf|docx|doc|txt)$/i.test(file.name);
    if (!isAllowed) {
      setExtractionError("Unable to process this file. Please upload a valid PDF or DOCX proposal/RFP.");
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      setExtractionError("File size exceeds 15 MB limit. Please upload a smaller document.");
      return;
    }
    // STEP 8: Reset all previous proposal state immediately when a new RFP is uploaded
    setProposalFile(file);
    setProposalProfile(null);
    setSelectedParamIds(new Set());
    setRecommendedParamIds(new Set());
    setParamEvaluations([]);
    setAnalysisResult(null);

    // Automatically trigger extraction and dynamic parameter recommendations immediately on upload
    handleExtractProposal(file);
  };

  const handleExtractProposal = async (fileOverride = null) => {
    const fileToProcess = fileOverride || proposalFile;
    if (!fileToProcess) return;
    setIsExtracting(true);
    setExtractionError('');
    // Step 1: Ensure parameters selection is empty while extracting
    setSelectedParamIds(new Set());
    setRecommendedParamIds(new Set());
    setParamEvaluations([]);

    try {
      const formData = new FormData();
      formData.append('file', fileToProcess);
      const res = await client.post('/api/proposal/extract', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const profile = res.data;
      setProposalProfile(profile);

      // Fetch proposal-specific recommendations tailored dynamically to this RFP
      try {
        const recRes = await client.post('/api/proposal/recommend-parameters', {
          proposal_profile: profile
        });
        const recs = recRes.data?.recommended_parameters || [];
        const evals = recRes.data?.parameter_evaluations || [];
        setParamEvaluations(evals);
        if (recs.length > 0) {
          setRecommendedParamIds(new Set(recs));
          setSelectedParamIds(new Set(recs)); // Dynamically check recommended parameters for this RFP
        }

        // Backfill parameterCatalog if it is ever empty or missing
        setParameterCatalog(prev => {
          if (prev && prev.length > 0) return prev;
          if (evals && evals.length > 0) {
            return evals.map(e => {
              const fallback = DEFAULT_PROPOSAL_PARAMETERS.find(p => p.id === e.parameter_id);
              return {
                id: e.parameter_id,
                name: e.parameter || fallback?.name || e.parameter_id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
                category: fallback?.category || 'General',
                description: fallback?.description || ''
              };
            });
          }
          return DEFAULT_PROPOSAL_PARAMETERS;
        });
      } catch (recErr) {
        console.warn("AI recommendation calculation failed:", recErr);
        const errMsg = recErr.response?.data?.detail || "AI parameter recommendation temporarily unavailable. You can manually select parameters from the catalog below.";
        setGeneralError(errMsg);
      }
    } catch (err) {
      console.error("Proposal extraction failed:", err);
      const msg = err.response?.data?.detail || "Unable to extract proposal. Please ensure the document has readable text.";
      setExtractionError(msg);
    } finally {
      setIsExtracting(false);
    }
  };

  // Parameter Selection Controls
  const toggleParameter = (paramId) => {
    setSelectedParamIds(prev => {
      const next = new Set(prev);
      if (next.has(paramId)) {
        next.delete(paramId);
      } else {
        next.add(paramId);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    setSelectedParamIds(new Set(parameterCatalog.map(p => p.id)));
  };

  const handleClearAll = () => {
    setSelectedParamIds(new Set());
  };

  const handleSelectRecommended = () => {
    setSelectedParamIds(new Set(recommendedParamIds));
  };

  // Execution: Progressive Concurrent Streaming
  const handleStartAnalysis = async () => {
    setGeneralError('');
    if (!selectedProspect) {
      setGeneralError("Please select a prospect before starting analysis.");
      return;
    }
    if (!proposalProfile) {
      setGeneralError("Please upload and extract a proposal PDF before starting analysis.");
      return;
    }
    if (selectedParamIds.size === 0) {
      setGeneralError("Please select at least one analysis parameter.");
      return;
    }

    const selectedIdsList = Array.from(selectedParamIds);
    setTotalStreamParams(selectedIdsList.length);
    setIsStreamingComplete(false);
    setStreamingSummary(null);
    setAnalysisResult(null);

    // Initialize all selected parameter cards immediately in 'processing' state
    const initialMap = {};
    selectedIdsList.forEach(pid => {
      const pMeta = parameterCatalog.find(p => p.id === pid) || {
        name: pid.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        category: 'General',
        description: ''
      };
      initialMap[pid] = {
        parameter_id: pid,
        parameter: pMeta.name,
        category: pMeta.category,
        description: pMeta.description,
        status: 'processing',
        result: null,
        error: null
      };
    });
    setStreamingParams(initialMap);
    setStage('analyzing');

    try {
      const token = localStorage.getItem('prospect_ai_token');
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

      const payload = {
        prospect_id: selectedProspect.id || null,
        prospect_name: selectedProspect.name,
        proposal_id: proposalProfile.proposal_id || null,
        proposal_profile: proposalProfile,
        selected_parameters: selectedIdsList,
        mock_mode: false
      };

      const response = await fetch(`${API_BASE}/api/proposal/analyze/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        let errDetail = "Streaming analysis failed.";
        try {
          const errJson = await response.json();
          errDetail = errJson.detail || errDetail;
        } catch {
          // ignore parse failure
        }
        throw new Error(errDetail);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (!part.trim()) continue;
          const lines = part.split('\n');
          let eventType = 'message';
          let dataStr = '';

          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.substring(6).trim();
            } else if (line.startsWith('data:')) {
              dataStr += (dataStr ? '\n' : '') + line.substring(5).trim();
            }
          }

          if (dataStr) {
            try {
              const data = JSON.parse(dataStr);

              if (eventType === 'init') {
                if (data.total_parameters) {
                  setTotalStreamParams(data.total_parameters);
                }
              } else if (eventType === 'param_started') {
                setStreamingParams(prev => ({
                  ...prev,
                  [data.parameter_id]: {
                    ...(prev[data.parameter_id] || {}),
                    parameter_id: data.parameter_id,
                    status: 'processing'
                  }
                }));
              } else if (eventType === 'param_completed') {
                const cleanResult = {
                  ...data,
                  finding: stripMarkdown(data.finding || data.summary || ''),
                  summary: stripMarkdown(data.summary || data.finding || ''),
                  reasoning: stripMarkdown(data.reasoning || data.why_it_matters || ''),
                  gaps: Array.isArray(data.gaps) ? data.gaps.map(stripMarkdown) : []
                };
                setStreamingParams(prev => ({
                  ...prev,
                  [data.parameter_id]: {
                    ...(prev[data.parameter_id] || {}),
                    parameter_id: data.parameter_id,
                    parameter: data.parameter || prev[data.parameter_id]?.parameter,
                    category: data.category || prev[data.parameter_id]?.category,
                    status: 'completed',
                    result: cleanResult,
                    error: null
                  }
                }));
              } else if (eventType === 'param_failed') {
                setStreamingParams(prev => ({
                  ...prev,
                  [data.parameter_id]: {
                    ...(prev[data.parameter_id] || {}),
                    parameter_id: data.parameter_id,
                    status: 'failed',
                    error: data.error || 'Parameter evaluation failed'
                  }
                }));
              } else if (eventType === 'summary_ready') {
                setStreamingSummary({
                  overall_assessment: stripMarkdown(data.overall_assessment || data.executive_summary || ''),
                  summary: stripMarkdown(data.executive_summary || data.overall_assessment || ''),
                  strengths: (data.strengths || []).map(stripMarkdown),
                  gaps: (data.gaps || []).map(stripMarkdown),
                  risks: (data.risks || []).map(stripMarkdown),
                  opportunity_signals: (data.opportunity_signals || []).map(stripMarkdown),
                  recommended_contact_angle: stripMarkdown(data.recommended_contact_angle || ''),
                  recommended_next_action: stripMarkdown(data.recommended_next_action || '')
                });
              } else if (eventType === 'complete') {
                const normalized = normalizeProposalReport(data);
                setAnalysisResult(normalized);
                setIsStreamingComplete(true);
                if (onAnalysisComplete) {
                  onAnalysisComplete(normalized);
                }
              } else if (eventType === 'error') {
                console.error("SSE error event:", data);
                setGeneralError(data.error || "Analysis encountered an error.");
              }
            } catch (jsonErr) {
              console.warn("Failed to parse SSE JSON payload:", dataStr, jsonErr);
            }
          }
        }
      }
    } catch (err) {
      console.error("Proposal stream analysis error:", err);
      setGeneralError(err.message || "Proposal analysis failed. Please try again.");
    }
  };

  const handleReset = () => {
    setStage('setup');
    setProposalFile(null);
    setProposalProfile(null);
    setSelectedProspect(null);
    setAnalysisResult(null);
    setActiveParamDetail(null);
    setStreamingParams({});
    setStreamingSummary(null);
    setIsStreamingComplete(false);
    setTotalStreamParams(0);
    setSelectedParamIds(new Set());
    setRecommendedParamIds(new Set());
    setParamEvaluations([]);
    setGeneralError('');
    setExtractionError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (onReset) {
      onReset();
    }
  };

  // Score styling helper
  const getFitBadgeStyle = (fitLevel) => {
    const lower = (fitLevel || '').toLowerCase();
    if (lower.includes('very high')) return { background: '#059669', color: '#ffffff', label: 'VERY HIGH FIT' };
    if (lower.includes('high')) return { background: '#2563eb', color: '#ffffff', label: 'HIGH FIT' };
    if (lower.includes('moderate')) return { background: '#d97706', color: '#ffffff', label: 'MODERATE FIT' };
    if (lower.includes('low')) return { background: '#dc2626', color: '#ffffff', label: 'LOW FIT' };
    return { background: '#64748b', color: '#ffffff', label: 'EVALUATED' };
  };

  return (
    <div className="proposal-analysis-container" style={{ padding: '1.5rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      {/* Top Breadcrumb & Return Option */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{ background: '#2563eb', color: '#ffffff', padding: '0.4rem', borderRadius: '8px', display: 'flex' }}>
            <FileText size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Proposal-Based Prospect Analysis
            </h2>
            <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
              Evaluate how well any carrier fits an uploaded RFP across custom selected parameters.
            </p>
          </div>
        </div>

        {stage === 'results' && (
          <button 
            className="btn-secondary" 
            onClick={handleReset}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.5rem 1rem', fontSize: '0.85rem', fontWeight: 700, borderRadius: '8px', cursor: 'pointer' }}
          >
            <RefreshCw size={14} /> New Proposal Analysis
          </button>
        )}
      </div>

      {generalError && (
        <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', color: '#991b1b', padding: '0.85rem 1.25rem', borderRadius: '10px', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.92rem', fontWeight: 600 }}>
          <AlertCircle size={18} color="#dc2626" />
          <span>{generalError}</span>
        </div>
      )}

      {/* ======================================================== */}
      {/* STAGE 1: SETUP WIZARD (PROSPECT + PROPOSAL + PARAMETERS) */}
      {/* ======================================================== */}
      {stage === 'setup' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* STEP 1: PROSPECT SELECTION */}
          <div className="proposal-card" style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.4rem', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ background: '#eff6ff', color: '#2563eb', padding: '0.35rem', borderRadius: '6px' }}>
                  <Building size={18} />
                </div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1e293b', margin: 0 }}>
                  1. Select Target Prospect
                </h3>
              </div>
              {selectedProspect && (
                <span style={{ fontSize: '0.78rem', color: '#059669', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.3rem', background: '#ecfdf5', padding: '0.2rem 0.6rem', borderRadius: '20px' }}>
                  <Check size={13} /> Selected
                </span>
              )}
            </div>

            {selectedProspect ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#f8fafc', border: '1px solid #cbd5e1', padding: '0.85rem 1.15rem', borderRadius: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <Building size={20} color="#2563eb" />
                  <div>
                    <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>{selectedProspect.name}</div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                      {selectedProspect.id ? `Catalog ID: ${selectedProspect.id}` : 'Verified Insurance Prospect'}
                    </div>
                  </div>
                </div>
                <button 
                  type="button" 
                  onClick={() => setSelectedProspect(null)} 
                  style={{ background: '#ffffff', border: '1px solid #cbd5e1', padding: '0.4rem 0.8rem', borderRadius: '6px', fontSize: '0.82rem', fontWeight: 600, color: '#475569', cursor: 'pointer' }}
                >
                  Change Prospect
                </button>
              </div>
            ) : (
              <div>
                <div style={{ position: 'relative', marginBottom: '0.85rem' }}>
                  <input
                    type="text"
                    placeholder="Type to search supported insurance prospects (e.g. Allianz, AXA, Chubb)..."
                    value={prospectSearchInput}
                    onChange={handleProspectSearchChange}
                    style={{
                      width: '100%',
                      padding: '0.85rem 1rem 0.85rem 2.6rem',
                      borderRadius: '10px',
                      border: '1.5px solid #cbd5e1',
                      fontSize: '0.95rem'
                    }}
                  />
                  <Search size={18} color="#94a3b8" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />

                  {/* Autocomplete dropdown */}
                  {prospectSuggestions.length > 0 && (
                    <div style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      background: '#ffffff',
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      boxShadow: '0 6px 16px rgba(0,0,0,0.1)',
                      zIndex: 50,
                      marginTop: '4px',
                      overflow: 'hidden'
                    }}>
                      {prospectSuggestions.map(p => (
                        <div
                          key={p.id || p.name}
                          onClick={() => handleSelectProspect(p)}
                          style={{ padding: '0.65rem 1rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9' }}
                          onMouseEnter={(e) => e.currentTarget.style.background = '#f1f5f9'}
                          onMouseLeave={(e) => e.currentTarget.style.background = '#ffffff'}
                        >
                          <span style={{ fontWeight: 600, color: '#1e293b', fontSize: '0.92rem' }}>{p.name}</span>
                          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{p.id}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Preset Chips */}
                <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.45rem' }}>
                  <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b', marginRight: '0.3rem' }}>Quick select:</span>
                  {SAMPLE_PROSPECTS.map(name => (
                    <button
                      key={name}
                      type="button"
                      onClick={() => handleSelectProspect(name)}
                      style={{
                        background: '#eff6ff',
                        border: '1px solid #bfdbfe',
                        color: '#1d4ed8',
                        padding: '0.3rem 0.7rem',
                        borderRadius: '16px',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      {name}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* STEP 2: PROPOSAL / RFP UPLOAD */}
          <div className="proposal-card" style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.4rem', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ background: '#eff6ff', color: '#2563eb', padding: '0.35rem', borderRadius: '6px' }}>
                  <Upload size={18} />
                </div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1e293b', margin: 0 }}>
                  2. Upload Proposal / RFP Document (PDF / DOCX)
                </h3>
              </div>
              {proposalProfile && (
                <span style={{ fontSize: '0.78rem', color: '#059669', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.3rem', background: '#ecfdf5', padding: '0.2rem 0.6rem', borderRadius: '20px' }}>
                  <Check size={13} /> Extracted
                </span>
              )}
            </div>

            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              accept=".pdf,.docx,.doc,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword,text/plain"
              onChange={handleFileChange}
            />

            {!proposalProfile ? (
              <div>
                <div 
                  onClick={() => !isExtracting && fileInputRef.current?.click()}
                  onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const droppedFile = e.dataTransfer.files?.[0];
                    if (droppedFile) handleProcessSelectedFile(droppedFile);
                  }}
                  style={{
                    border: '2px dashed #93c5fd',
                    background: isExtracting ? '#f0f9ff' : '#f8fafc',
                    padding: '1.75rem',
                    borderRadius: '10px',
                    textAlign: 'center',
                    cursor: isExtracting ? 'wait' : 'pointer',
                    transition: 'border 0.2s'
                  }}
                  onMouseEnter={(e) => { if (!isExtracting) e.currentTarget.style.borderColor = '#2563eb'; }}
                  onMouseLeave={(e) => { if (!isExtracting) e.currentTarget.style.borderColor = '#93c5fd'; }}
                >
                  {isExtracting ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0' }}>
                      <RefreshCw size={32} className="spinner" color="#2563eb" style={{ animation: 'spin 1.2s linear infinite' }} />
                      <div style={{ fontSize: '1rem', fontWeight: 800, color: '#1e293b' }}>
                        Analyzing RFP &amp; Extracting Requirements...
                      </div>
                      <div style={{ fontSize: '0.82rem', color: '#64748b' }}>
                        Evaluating proposal scope and dynamically recommending tailored parameters
                      </div>
                    </div>
                  ) : (
                    <>
                      <Upload size={32} color="#2563eb" style={{ margin: '0 auto 0.5rem auto' }} />
                      <div style={{ fontSize: '0.98rem', fontWeight: 700, color: '#1e293b', marginBottom: '0.25rem' }}>
                        {proposalFile ? proposalFile.name : 'Click to select or drag & drop Proposal/RFP (PDF or DOCX)'}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                        Commercial Insurance Proposals or RFPs in PDF or DOCX format (Max 15 MB)
                      </div>
                      {proposalFile && (
                        <div style={{ marginTop: '0.5rem', fontSize: '0.82rem', fontWeight: 700, color: '#059669' }}>
                          ✓ File selected: {proposalFile.name} ({(proposalFile.size / 1024).toFixed(1)} KB)
                        </div>
                      )}
                    </>
                  )}
                </div>

                {extractionError && (
                  <div style={{ marginTop: '0.75rem', color: '#dc2626', fontSize: '0.85rem', fontWeight: 600 }}>
                    {extractionError}
                  </div>
                )}
              </div>
            ) : (
              /* Extracted Profile Preview Card */
              <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '1.25rem' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 700 }}>
                      Extracted Proposal / RFP Profile
                    </div>
                    <h4 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', margin: '0.2rem 0' }}>
                      {proposalProfile.proposal_title}
                    </h4>
                    <span style={{ fontSize: '0.76rem', background: '#dbeafe', color: '#1e40af', padding: '0.15rem 0.55rem', borderRadius: '12px', fontWeight: 700 }}>
                      {proposalProfile.domain || 'Commercial Insurance'}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setProposalProfile(null);
                      setProposalFile(null);
                      setSelectedParamIds(new Set());
                      setRecommendedParamIds(new Set());
                      setParamEvaluations([]);
                      if (fileInputRef.current) fileInputRef.current.value = '';
                    }}
                    style={{ background: '#ffffff', border: '1px solid #cbd5e1', padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.78rem', fontWeight: 600, color: '#475569', cursor: 'pointer' }}
                  >
                    Replace Document
                  </button>
                </div>

                <p style={{ fontSize: '0.88rem', color: '#334155', lineHeight: '1.5', margin: '0.5rem 0 0.85rem 0' }}>
                  {proposalProfile.summary}
                </p>

                {/* Requirements Chips */}
                {proposalProfile.requirements && proposalProfile.requirements.length > 0 && (
                  <div style={{ marginBottom: '0.75rem' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
                      Core Requirements Identified ({proposalProfile.requirements.length}):
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                      {proposalProfile.requirements.slice(0, 5).map((req, idx) => (
                        <div key={idx} style={{ fontSize: '0.82rem', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <CheckCircle2 size={13} color="#2563eb" />
                          <span>{req}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Capabilities Badges */}
                {proposalProfile.capabilities && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                    {proposalProfile.capabilities.map((cap, idx) => (
                      <span key={idx} style={{ fontSize: '0.74rem', background: '#eff6ff', border: '1px solid #bfdbfe', color: '#1d4ed8', padding: '0.15rem 0.5rem', borderRadius: '6px', fontWeight: 600 }}>
                        {cap}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* STEP 3: DYNAMIC PARAMETER CHECKLIST */}
          <div className="proposal-card" style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '1.4rem', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ background: '#eff6ff', color: '#2563eb', padding: '0.35rem', borderRadius: '6px' }}>
                  <Layers size={18} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1e293b', margin: 0 }}>
                    3. Analysis Parameters Checklist
                  </h3>
                  <div style={{ fontSize: '0.78rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <span>{selectedParamIds.size} of {parameterCatalog.length} parameters selected for evaluation</span>
                    {proposalProfile && (
                      <span style={{ fontSize: '0.72rem', background: '#ecfdf5', color: '#065f46', border: '1px solid #a7f3d0', padding: '0.1rem 0.5rem', borderRadius: '12px', fontWeight: 700 }}>
                        ✓ Dynamically tailored to RFP
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Selection Tool Bar */}
              <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                <button
                  type="button"
                  onClick={handleSelectAll}
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '0.35rem 0.65rem', borderRadius: '6px', fontSize: '0.78rem', fontWeight: 700, color: '#334155', cursor: 'pointer' }}
                >
                  Select All
                </button>
                <button
                  type="button"
                  onClick={handleClearAll}
                  style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', padding: '0.35rem 0.65rem', borderRadius: '6px', fontSize: '0.78rem', fontWeight: 700, color: '#334155', cursor: 'pointer' }}
                >
                  Clear All
                </button>
                {recommendedParamIds.size > 0 && (
                  <button
                    type="button"
                    onClick={handleSelectRecommended}
                    style={{ background: '#eff6ff', border: '1px solid #bfdbfe', padding: '0.35rem 0.65rem', borderRadius: '6px', fontSize: '0.78rem', fontWeight: 700, color: '#1d4ed8', cursor: 'pointer' }}
                  >
                    Select Recommended ({recommendedParamIds.size})
                  </button>
                )}
              </div>
            </div>

            {/* Render Parameter Checklist: Split into Recommended & Not Recommended when RFP extracted, or Empty Catalog when not */}
            {!proposalProfile ? (
              <div>
                <div style={{ background: '#f8fafc', border: '1px dashed #cbd5e1', borderRadius: '8px', padding: '0.85rem 1rem', marginBottom: '1rem', color: '#64748b', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <HelpCircle size={16} color="#3b82f6" />
                  <span>Upload and extract a proposal/RFP (PDF or DOCX) above. The system will dynamically evaluate the proposal and recommend relevant parameters. Currently 0 parameters are selected.</span>
                </div>
                <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.04em', marginBottom: '0.6rem' }}>
                  Analysis Parameters Catalog (Empty Selection)
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '0.6rem' }}>
                  {parameterCatalog.map(param => (
                    <div
                      key={param.id}
                      onClick={() => toggleParameter(param.id)}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '0.6rem',
                        padding: '0.75rem',
                        borderRadius: '8px',
                        border: selectedParamIds.has(param.id) ? '1.5px solid #2563eb' : '1px solid #e2e8f0',
                        background: selectedParamIds.has(param.id) ? '#eff6ff' : '#ffffff',
                        cursor: 'pointer'
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={selectedParamIds.has(param.id)}
                        onChange={() => {}}
                        style={{ marginTop: '0.2rem', cursor: 'pointer', accentColor: '#2563eb' }}
                      />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#1e293b' }}>{param.name}</div>
                        <div style={{ fontSize: '0.74rem', color: '#64748b', margin: '0.15rem 0' }}>{param.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* When Proposal IS Extracted: Group into Recommended and Not Recommended with Reasons */
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {/* SECTION A: RECOMMENDED PARAMETERS */}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.65rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', color: '#047857', letterSpacing: '0.04em' }}>
                        ✓ Recommended Parameters ({parameterCatalog.filter(p => recommendedParamIds.has(p.id)).length})
                      </span>
                      <span style={{ fontSize: '0.72rem', background: '#ecfdf5', color: '#047857', border: '1px solid #a7f3d0', padding: '0.1rem 0.45rem', borderRadius: '12px', fontWeight: 700 }}>
                        Derived from RFP Scope
                      </span>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '0.75rem' }}>
                    {parameterCatalog.filter(p => recommendedParamIds.has(p.id)).map(param => {
                      const isSelected = selectedParamIds.has(param.id);
                      const evalData = paramEvaluations.find(e => e.parameter_id === param.id);
                      return (
                        <div
                          key={param.id}
                          onClick={() => toggleParameter(param.id)}
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.45rem',
                            padding: '0.85rem',
                            borderRadius: '10px',
                            border: isSelected ? '2px solid #059669' : '1px solid #cbd5e1',
                            background: isSelected ? '#f0fdf4' : '#ffffff',
                            cursor: 'pointer',
                            transition: 'all 0.15s',
                            boxShadow: isSelected ? '0 2px 6px rgba(5,150,105,0.1)' : 'none'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem' }}>
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => {}}
                              style={{ marginTop: '0.2rem', cursor: 'pointer', accentColor: '#059669', width: '16px', height: '16px' }}
                            />
                            <div style={{ flex: 1 }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.3rem' }}>
                                <span style={{ fontSize: '0.92rem', fontWeight: 800, color: '#0f172a' }}>
                                  {param.name}
                                </span>
                                {evalData?.recommendation === 'recommended' && (
                                  <span style={{ fontSize: '0.7rem', background: '#dcfce7', color: '#15803d', fontWeight: 800, padding: '0.1rem 0.45rem', borderRadius: '10px' }}>
                                    Recommended
                                  </span>
                                )}
                              </div>
                              <p style={{ fontSize: '0.76rem', color: '#475569', margin: '0.2rem 0 0 0', lineHeight: '1.35' }}>
                                {param.description}
                              </p>
                            </div>
                          </div>

                          {/* Reason & Evidence Box */}
                          {evalData && (
                            <div style={{ background: '#ffffff', border: '1px solid #bbf7d0', borderRadius: '6px', padding: '0.45rem 0.6rem', marginTop: '0.2rem' }}>
                              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#166534', marginBottom: evalData.rfp_evidence?.length > 0 ? '0.25rem' : '0' }}>
                                💡 Reason: {evalData.reason}
                              </div>
                              {evalData.rfp_evidence && evalData.rfp_evidence.length > 0 && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem' }}>
                                  {evalData.rfp_evidence.slice(0, 2).map((ev, idx) => (
                                    <div key={idx} style={{ fontSize: '0.71rem', color: '#334155', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                      <span style={{ color: '#059669', fontWeight: 800 }}>•</span>
                                      <span>"{ev}"</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* SECTION B: NOT RECOMMENDED PARAMETERS */}
                {parameterCatalog.filter(p => !recommendedParamIds.has(p.id)).length > 0 && (
                  <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.65rem' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 800, textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.04em' }}>
                        Not Recommended ({parameterCatalog.filter(p => !recommendedParamIds.has(p.id)).length})
                      </span>
                      <span style={{ fontSize: '0.72rem', background: '#f1f5f9', color: '#64748b', border: '1px solid #e2e8f0', padding: '0.1rem 0.45rem', borderRadius: '12px' }}>
                        Low / No Match in RFP Scope (Optional)
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '0.75rem' }}>
                      {parameterCatalog.filter(p => !recommendedParamIds.has(p.id)).map(param => {
                        const isSelected = selectedParamIds.has(param.id);
                        const evalData = paramEvaluations.find(e => e.parameter_id === param.id);
                        return (
                          <div
                            key={param.id}
                            onClick={() => toggleParameter(param.id)}
                            style={{
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.4rem',
                              padding: '0.75rem',
                              borderRadius: '8px',
                              border: isSelected ? '1.5px solid #2563eb' : '1px solid #e2e8f0',
                              background: isSelected ? '#eff6ff' : '#f8fafc',
                              cursor: 'pointer',
                              opacity: isSelected ? 1 : 0.85,
                              transition: 'all 0.15s'
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.6rem' }}>
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => {}}
                                style={{ marginTop: '0.2rem', cursor: 'pointer', accentColor: '#2563eb' }}
                              />
                              <div style={{ flex: 1 }}>
                                <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#334155' }}>
                                  {param.name}
                                </div>
                                <p style={{ fontSize: '0.74rem', color: '#64748b', margin: '0.15rem 0 0 0', lineHeight: '1.3' }}>
                                  {param.description}
                                </p>
                              </div>
                            </div>

                            {evalData?.reason && (
                              <div style={{ fontSize: '0.72rem', color: '#64748b', fontStyle: 'italic', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '0.3rem 0.5rem' }}>
                                ℹ️ {evalData.reason}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* STEP 4: START ANALYSIS BUTTON */}
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '0.5rem' }}>
            <button
              type="button"
              className="btn-primary"
              onClick={handleStartAnalysis}
              disabled={!selectedProspect || !proposalProfile || selectedParamIds.size === 0}
              style={{
                padding: '0.9rem 2.5rem',
                fontSize: '1.05rem',
                fontWeight: 800,
                borderRadius: '10px',
                background: (!selectedProspect || !proposalProfile || selectedParamIds.size === 0) ? '#94a3b8' : '#2563eb',
                color: '#ffffff',
                border: 'none',
                cursor: (!selectedProspect || !proposalProfile || selectedParamIds.size === 0) ? 'not-allowed' : 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.6rem',
                boxShadow: '0 4px 14px rgba(37, 99, 235, 0.3)'
              }}
            >
              <Sparkles size={18} />
              <span>Start Proposal Analysis</span>
            </button>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* STAGE 2: PROGRESSIVE CONCURRENT STREAMING UI             */}
      {/* ======================================================== */}
      {stage === 'analyzing' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Progress Header & Counter */}
          <div style={{
            background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)',
            color: '#ffffff',
            borderRadius: '14px',
            padding: '1.75rem',
            boxShadow: '0 6px 20px rgba(15, 23, 42, 0.25)',
            border: '1px solid #3b82f6'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
              <div>
                <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: '#93c5fd', fontWeight: 800, letterSpacing: '0.05em' }}>
                  CONCURRENT PROPOSAL ANALYSIS IN PROGRESS
                </div>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#ffffff', margin: '0.35rem 0' }}>
                  {selectedProspect?.name || 'Target Prospect'}
                </h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.92rem', color: '#cbd5e1' }}>
                  <FileText size={16} />
                  <span>Proposal: <strong>{proposalProfile?.proposal_title || 'Uploaded Proposal'}</strong></span>
                </div>
              </div>

              {/* Status Badge */}
              <div>
                {isStreamingComplete ? (
                  <span style={{ background: '#059669', color: '#ffffff', padding: '0.45rem 1rem', borderRadius: '20px', fontSize: '0.85rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                    <CheckCircle2 size={16} /> Analysis Complete &amp; Saved
                  </span>
                ) : (
                  <span style={{ background: 'rgba(37, 99, 235, 0.4)', border: '1px solid #60a5fa', color: '#ffffff', padding: '0.45rem 1rem', borderRadius: '20px', fontSize: '0.85rem', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.45rem' }}>
                    <RefreshCw size={14} className="spinner" /> Evaluating Parameters Concurrently
                  </span>
                )}
              </div>
            </div>

            {/* Live Counter & Progress Bar */}
            <div>
              {(() => {
                const paramsList = Object.values(streamingParams);
                const completedCount = paramsList.filter(p => p.status === 'completed' || p.status === 'failed').length;
                const totalCount = totalStreamParams || paramsList.length || selectedParamIds.size;
                const progressPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
                return (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.88rem', fontWeight: 700, marginBottom: '0.45rem', color: '#e2e8f0' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <Layers size={16} color="#60a5fa" />
                        <strong>{completedCount} / {totalCount} Parameters Completed</strong>
                      </span>
                      <span>{progressPct}%</span>
                    </div>

                    <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.2)', borderRadius: '9999px', overflow: 'hidden' }}>
                      <div style={{
                        width: `${progressPct}%`,
                        height: '100%',
                        background: progressPct === 100 ? '#10b981' : '#38bdf8',
                        borderRadius: '9999px',
                        transition: 'width 0.4s ease-in-out'
                      }} />
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>

          {/* PROGRESSIVE PARAMETER CARDS GRID */}
          <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.4rem', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Layers size={18} color="#2563eb" />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                  Selected Parameters ({Object.values(streamingParams).length})
                </h3>
              </div>
              <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                Results appear immediately as each parameter finishes analysis
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '0.85rem' }}>
              {Object.values(streamingParams).map((param) => {
                const isCompleted = param.status === 'completed';
                const isFailed = param.status === 'failed';
                const isProcessing = param.status === 'processing';
                const fitBadge = isCompleted ? getFitBadgeStyle(param.result?.fit_level) : null;

                return (
                  <div
                    key={param.parameter_id}
                    onClick={() => isCompleted && param.result && setActiveParamDetail(param.result)}
                    style={{
                      background: isCompleted ? '#ffffff' : (isFailed ? '#fef2f2' : '#f8fafc'),
                      border: isCompleted ? '1.5px solid #cbd5e1' : (isFailed ? '1.5px solid #fca5a5' : '1.5px solid #bfdbfe'),
                      borderRadius: '10px',
                      padding: '1rem',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      boxShadow: isCompleted ? '0 2px 6px rgba(0,0,0,0.04)' : 'none',
                      cursor: isCompleted ? 'pointer' : 'default',
                      transition: 'all 0.2s ease-in-out'
                    }}
                    onMouseEnter={(e) => { if (isCompleted) e.currentTarget.style.borderColor = '#2563eb'; }}
                    onMouseLeave={(e) => { if (isCompleted) e.currentTarget.style.borderColor = '#cbd5e1'; }}
                  >
                    <div>
                      {/* Card Header */}
                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.5rem', marginBottom: '0.5rem' }}>
                        <div>
                          <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 700 }}>
                            {param.category || 'General'}
                          </span>
                          <h4 style={{ fontSize: '0.98rem', fontWeight: 800, color: '#0f172a', margin: '0.1rem 0' }}>
                            {param.parameter}
                          </h4>
                        </div>

                        {/* Status / Fit Badge */}
                        <div>
                          {isProcessing && (
                            <span style={{
                              background: '#eff6ff',
                              border: '1px solid #bfdbfe',
                              color: '#2563eb',
                              padding: '0.2rem 0.55rem',
                              borderRadius: '12px',
                              fontSize: '0.72rem',
                              fontWeight: 700,
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.3rem'
                            }}>
                              <RefreshCw size={11} className="spinner" /> Processing...
                            </span>
                          )}

                          {isCompleted && fitBadge && (
                            <span style={{
                              background: fitBadge.background,
                              color: '#ffffff',
                              padding: '0.2rem 0.55rem',
                              borderRadius: '12px',
                              fontSize: '0.72rem',
                              fontWeight: 700
                            }}>
                              {param.result?.fit_level || 'COMPLETED'}
                            </span>
                          )}

                          {isFailed && (
                            <span style={{
                              background: '#dc2626',
                              color: '#ffffff',
                              padding: '0.2rem 0.55rem',
                              borderRadius: '12px',
                              fontSize: '0.72rem',
                              fontWeight: 700,
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.25rem'
                            }}>
                              <AlertCircle size={11} /> Failed
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Card Body */}
                      {isProcessing && (
                        <div style={{ background: '#f0f9ff', borderRadius: '6px', padding: '0.65rem', marginTop: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <RefreshCw size={14} className="spinner" color="#2563eb" />
                          <span style={{ fontSize: '0.8rem', color: '#1e40af', fontWeight: 500 }}>
                            Researching empirical sources &amp; evaluating RFP fit...
                          </span>
                        </div>
                      )}

                      {isCompleted && (
                        <div>
                          <p style={{ fontSize: '0.84rem', color: '#334155', lineHeight: '1.45', margin: '0.35rem 0' }}>
                            {param.result?.summary || param.result?.finding}
                          </p>

                          {param.result?.reasoning && (
                            <div style={{ fontSize: '0.76rem', color: '#64748b', fontStyle: 'italic', marginTop: '0.25rem' }}>
                              💡 {param.result.reasoning}
                            </div>
                          )}
                        </div>
                      )}

                      {isFailed && (
                        <div style={{ color: '#991b1b', fontSize: '0.8rem', marginTop: '0.35rem' }}>
                          {param.error}
                        </div>
                      )}
                    </div>

                    {/* Card Footer for Completed Params */}
                    {isCompleted && (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #f1f5f9', paddingTop: '0.5rem', marginTop: '0.65rem' }}>
                        <span style={{ fontSize: '0.74rem', color: '#059669', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                          <CheckCircle2 size={12} color="#059669" />
                          {param.result?.sources?.length ? `${param.result.sources.length} Grounded Sources` : 'Evaluated'}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (param.result) setActiveParamDetail(param.result);
                          }}
                          style={{ background: '#eff6ff', border: 'none', color: '#2563eb', padding: '0.25rem 0.6rem', borderRadius: '4px', fontSize: '0.74rem', fontWeight: 700, cursor: 'pointer' }}
                        >
                          Inspect Details ↗
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* FINAL EXECUTIVE ANALYSIS SUMMARY */}
          {(streamingSummary || analysisResult) && (
            <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.75rem' }}>
                <Sparkles size={20} color="#2563eb" />
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                  Final Consolidated Executive Analysis
                </h3>
              </div>

              {/* 1. Overall Assessment */}
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#2563eb', marginBottom: '0.35rem' }}>
                  Overall Assessment
                </div>
                <p style={{ fontSize: '0.95rem', color: '#1e293b', lineHeight: '1.6', margin: 0 }}>
                  {(streamingSummary || analysisResult)?.overall_assessment || (streamingSummary || analysisResult)?.summary}
                </p>
              </div>

              {/* 2. Strongest Alignment */}
              {(streamingSummary || analysisResult)?.strengths?.length > 0 && (
                <div style={{ marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#059669', marginBottom: '0.45rem' }}>
                    Strongest Alignment Areas
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem' }}>
                    {(streamingSummary || analysisResult).strengths.map((str, idx) => (
                      <span key={idx} style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#065f46', padding: '0.3rem 0.75rem', borderRadius: '20px', fontSize: '0.84rem', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                        <CheckCircle2 size={13} color="#059669" />
                        {str}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 3. Key Gaps */}
              {(streamingSummary || analysisResult)?.gaps?.length > 0 && (
                <div style={{ background: '#fefce8', border: '1px solid #fef08a', padding: '1rem', borderRadius: '10px', marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#854d0e', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <AlertTriangle size={15} color="#b45309" /> Key Gaps &amp; Missing Evidence
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    {(streamingSummary || analysisResult).gaps.map((g, idx) => (
                      <div key={idx} style={{ fontSize: '0.88rem', color: '#713f12', lineHeight: '1.45' }}>
                        • {g}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 4. Opportunity Signals */}
              {(streamingSummary || analysisResult)?.opportunity_signals?.length > 0 && (
                <div style={{ marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#2563eb', marginBottom: '0.35rem' }}>
                    Opportunity Signals
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    {(streamingSummary || analysisResult).opportunity_signals.map((sig, idx) => (
                      <div key={idx} style={{ fontSize: '0.88rem', color: '#334155', display: 'flex', alignItems: 'flex-start', gap: '0.4rem', lineHeight: '1.45' }}>
                        <TrendingUp size={15} color="#2563eb" style={{ flexShrink: 0, marginTop: '2px' }} />
                        <span>{sig}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 5. Risks & Unknowns */}
              {(streamingSummary || analysisResult)?.risks?.length > 0 && (
                <div style={{ marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#64748b', marginBottom: '0.35rem' }}>
                    Risks &amp; Unknowns
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    {(streamingSummary || analysisResult).risks.map((r, idx) => (
                      <div key={idx} style={{ fontSize: '0.88rem', color: '#475569', lineHeight: '1.45' }}>
                        • {r}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 6. Recommended Contact Angle */}
              {(streamingSummary || analysisResult)?.recommended_contact_angle && (
                <div style={{ background: '#eff6ff', borderLeft: '4px solid #2563eb', padding: '1rem', borderRadius: '0 8px 8px 0', marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#1d4ed8', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Target size={15} /> Recommended Contact Angle
                  </div>
                  <p style={{ fontSize: '0.92rem', color: '#1e3a8a', lineHeight: '1.6', margin: 0 }}>
                    {(streamingSummary || analysisResult).recommended_contact_angle}
                  </p>
                </div>
              )}

              {/* 7. Recommended Next Action */}
              {(streamingSummary || analysisResult)?.recommended_next_action && (
                <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', padding: '1rem', borderRadius: '10px' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#0f172a', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <Zap size={15} color="#d97706" /> Recommended Next Action
                  </div>
                  <p style={{ fontSize: '0.92rem', color: '#334155', lineHeight: '1.6', margin: 0 }}>
                    {(streamingSummary || analysisResult).recommended_next_action}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Action / Export Bar */}
          {isStreamingComplete && (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleReset}
                style={{ padding: '0.6rem 1.25rem', fontSize: '0.88rem', fontWeight: 700, borderRadius: '8px', cursor: 'pointer' }}
              >
                ← Analyze Another Proposal / Prospect
              </button>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    const reportToExport = analysisResult || {
                      prospect: selectedProspect,
                      proposal: proposalProfile,
                      parameter_analysis: Object.values(streamingParams).map(p => p.result).filter(Boolean),
                      summary_synthesis: streamingSummary
                    };
                    const blob = new Blob([JSON.stringify(reportToExport, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${selectedProspect?.name || 'Prospect'}_Proposal_Analysis.json`;
                    a.click();
                  }}
                  style={{ padding: '0.55rem 1rem', fontSize: '0.85rem', fontWeight: 700, borderRadius: '8px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
                >
                  <Download size={14} /> Export JSON
                </button>
              </div>
            </div>
          )}
        </div>
      )}


      {/* ======================================================== */}
      {/* STAGE 3: RESULTS VIEW                                    */}
      {/* ======================================================== */}
      {stage === 'results' && analysisResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Main Hero Fit Banner */}
          <div style={{
            background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)',
            color: '#ffffff',
            borderRadius: '14px',
            padding: '1.75rem',
            boxShadow: '0 6px 20px rgba(15, 23, 42, 0.25)',
            border: '1px solid #3b82f6'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: '#93c5fd', fontWeight: 800, letterSpacing: '0.05em' }}>
                  PROPOSAL-BASED PROSPECT ANALYSIS
                </div>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#ffffff', margin: '0.35rem 0' }}>
                  {analysisResult.prospect?.name || 'Target Prospect'}
                </h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.92rem', color: '#cbd5e1' }}>
                  <FileText size={16} />
                  <span>Proposal: <strong>{analysisResult.proposal?.title}</strong></span>
                </div>
              </div>
            </div>
          </div>

          {/* PARAMETER ANALYSIS TABLE */}
          <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.4rem', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Layers size={18} color="#2563eb" />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                  Parameter Analysis ({analysisResult.parameter_analysis?.length || 0})
                </h3>
              </div>
              <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                Click any parameter to inspect evidence, reasoning, and identified gaps
              </div>
            </div>

            {/* Table */}
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '1.5px solid #e2e8f0', fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    <th style={{ padding: '0.75rem 1rem' }}>Parameter</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Category</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Fit Level</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Confidence</th>
                    <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {(analysisResult.parameter_analysis || []).map((param) => {
                    const fitBadge = getFitBadgeStyle(param.fit_level);
                    return (
                      <tr 
                        key={param.parameter_id || param.parameter}
                        onClick={() => setActiveParamDetail(param)}
                        style={{
                          borderBottom: '1px solid #f1f5f9',
                          cursor: 'pointer',
                          transition: 'background 0.15s'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                        onMouseLeave={(e) => e.currentTarget.style.background = '#ffffff'}
                      >
                        <td style={{ padding: '0.9rem 1rem', fontWeight: 700, color: '#1e293b', fontSize: '0.92rem' }}>
                          {param.parameter}
                        </td>
                        <td style={{ padding: '0.9rem 1rem', color: '#64748b', fontSize: '0.84rem' }}>
                          {param.category}
                        </td>
                        <td style={{ padding: '0.9rem 1rem' }}>
                          <span style={{
                            background: fitBadge.background,
                            color: '#ffffff',
                            padding: '0.2rem 0.55rem',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                            fontWeight: 700
                          }}>
                            {param.fit_level}
                          </span>
                        </td>
                        <td style={{ padding: '0.9rem 1rem' }}>
                          <span style={{
                            background: param.confidence === 'High' ? '#ecfdf5' : '#fefce8',
                            color: param.confidence === 'High' ? '#065f46' : '#854d0e',
                            border: `1px solid ${param.confidence === 'High' ? '#a7f3d0' : '#fef08a'}`,
                            padding: '0.15rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.76rem',
                            fontWeight: 600
                          }}>
                            {param.confidence}
                          </span>
                        </td>
                        <td style={{ padding: '0.9rem 1rem', textAlign: 'right' }}>
                          <button
                            type="button"
                            style={{ background: '#eff6ff', border: 'none', color: '#2563eb', padding: '0.35rem 0.7rem', borderRadius: '6px', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer' }}
                          >
                            Inspect ↗
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* PARAMETER DETAIL MODAL / DRAWER */}
          {activeParamDetail && (
            <div style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
              padding: '1rem'
            }}>
              <div style={{
                background: '#ffffff',
                borderRadius: '12px',
                width: '100%',
                maxWidth: '650px',
                maxHeight: '90vh',
                overflowY: 'auto',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)',
                padding: '1.75rem'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
                  <div>
                    <span style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: '#64748b', fontWeight: 700 }}>
                      {activeParamDetail.category} Parameter
                    </span>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', margin: '0.2rem 0' }}>
                      {activeParamDetail.parameter}
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => setActiveParamDetail(null)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
                  >
                    <X size={20} />
                  </button>
                </div>

                {/* Status Header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', background: '#f8fafc', padding: '0.85rem 1rem', borderRadius: '8px', marginBottom: '1rem' }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.25rem' }}>Fit Level</div>
                    <span style={{
                      ...getFitBadgeStyle(activeParamDetail.fit_level),
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px',
                      fontSize: '0.85rem',
                      fontWeight: 700
                    }}>
                      {activeParamDetail.fit_level}
                    </span>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.25rem' }}>Confidence</div>
                    <span style={{
                      background: activeParamDetail.confidence === 'High' ? '#ecfdf5' : '#fefce8',
                      color: activeParamDetail.confidence === 'High' ? '#065f46' : '#854d0e',
                      border: `1px solid ${activeParamDetail.confidence === 'High' ? '#a7f3d0' : '#fef08a'}`,
                      padding: '0.2rem 0.6rem',
                      borderRadius: '4px',
                      fontSize: '0.82rem',
                      fontWeight: 700
                    }}>
                      {activeParamDetail.confidence}
                    </span>
                  </div>
                </div>

                {/* Summary */}
                <div style={{ marginBottom: '1rem' }}>
                  <h4 style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: '#2563eb', fontWeight: 800, marginBottom: '0.35rem' }}>
                    Summary
                  </h4>
                  <p style={{ fontSize: '0.92rem', color: '#1e293b', lineHeight: '1.5', margin: 0 }}>
                    {activeParamDetail.summary || activeParamDetail.finding}
                  </p>
                </div>

                {/* Why it Matters (Reasoning) */}
                <div style={{ marginBottom: '1rem' }}>
                  <h4 style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: '#475569', fontWeight: 800, marginBottom: '0.35rem' }}>
                    Why It Matters
                  </h4>
                  <p style={{ fontSize: '0.88rem', color: '#475569', lineHeight: '1.5', margin: 0 }}>
                    {activeParamDetail.reasoning}
                  </p>
                </div>

                {/* Evidence List */}
                <div style={{ marginBottom: '1rem' }}>
                  <h4 style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: '#475569', fontWeight: 800, marginBottom: '0.35rem' }}>
                    Grounded Public Evidence ({activeParamDetail.evidence?.length || 0})
                  </h4>
                  {activeParamDetail.evidence && activeParamDetail.evidence.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                      {activeParamDetail.evidence.map((ev, idx) => (
                        <div key={idx} style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '6px', padding: '0.65rem 0.85rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem', marginBottom: '0.2rem' }}>
                            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e3a8a' }}>{ev.source}</span>
                            {ev.url && (
                              <a href={ev.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.75rem', color: '#2563eb', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                                View Source <ExternalLink size={10} />
                              </a>
                            )}
                          </div>
                          <p style={{ fontSize: '0.8rem', color: '#334155', margin: 0, lineHeight: '1.4' }}>
                            "{ev.summary}"
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.85rem', color: '#94a3b8', fontStyle: 'italic' }}>
                      No public citations available for this dimension.
                    </div>
                  )}
                </div>

                {/* Gaps */}
                {activeParamDetail.gaps && activeParamDetail.gaps.length > 0 && (
                  <div style={{ background: '#fefce8', border: '1px solid #fef08a', borderRadius: '8px', padding: '0.85rem', marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.76rem', fontWeight: 800, color: '#854d0e', textTransform: 'uppercase', marginBottom: '0.3rem' }}>
                      Potential Gaps & Unconfirmed Areas
                    </div>
                    {activeParamDetail.gaps.map((g, idx) => (
                      <div key={idx} style={{ fontSize: '0.84rem', color: '#713f12', lineHeight: '1.4' }}>
                        • {g}
                      </div>
                    ))}
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.25rem' }}>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setActiveParamDetail(null)}
                    style={{ padding: '0.45rem 1rem', fontSize: '0.85rem', fontWeight: 700, borderRadius: '6px', cursor: 'pointer' }}
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* FINAL ANALYSIS EXECUTIVE SUMMARY (MANDATORY SECTION 16) */}
          <div style={{ background: '#ffffff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.75rem' }}>
              <Sparkles size={20} color="#2563eb" />
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                Executive Analysis Summary
              </h3>
            </div>

            {/* 1. Overall Assessment */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#2563eb', marginBottom: '0.35rem' }}>
                Overall Assessment
              </div>
              <p style={{ fontSize: '0.95rem', color: '#1e293b', lineHeight: '1.6', margin: 0 }}>
                {analysisResult.overall_assessment || analysisResult.summary}
              </p>
            </div>

            {/* 2. Strongest Alignment */}
            {analysisResult.strengths && analysisResult.strengths.length > 0 && (
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#059669', marginBottom: '0.45rem' }}>
                  Strongest Alignment Areas
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem' }}>
                  {analysisResult.strengths.map((str, idx) => (
                    <span key={idx} style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', color: '#065f46', padding: '0.3rem 0.75rem', borderRadius: '20px', fontSize: '0.84rem', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                      <CheckCircle2 size={13} color="#059669" />
                      {str}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 3. Key Gaps */}
            {analysisResult.gaps && analysisResult.gaps.length > 0 && (
              <div style={{ background: '#fefce8', border: '1px solid #fef08a', padding: '1rem', borderRadius: '10px', marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#854d0e', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <AlertTriangle size={15} color="#b45309" /> Key Gaps & Missing Evidence
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  {analysisResult.gaps.map((g, idx) => (
                    <div key={idx} style={{ fontSize: '0.88rem', color: '#713f12', lineHeight: '1.45' }}>
                      • {g}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. Opportunity Signals */}
            {analysisResult.opportunity_signals && analysisResult.opportunity_signals.length > 0 && (
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#2563eb', marginBottom: '0.35rem' }}>
                  Opportunity Signals
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  {analysisResult.opportunity_signals.map((sig, idx) => (
                    <div key={idx} style={{ fontSize: '0.88rem', color: '#334155', display: 'flex', alignItems: 'flex-start', gap: '0.4rem', lineHeight: '1.45' }}>
                      <TrendingUp size={15} color="#2563eb" style={{ flexShrink: 0, marginTop: '2px' }} />
                      <span>{sig}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 5. Risks & Unknowns */}
            {analysisResult.risks && analysisResult.risks.length > 0 && (
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#64748b', marginBottom: '0.35rem' }}>
                  Risks & Unknowns
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  {analysisResult.risks.map((r, idx) => (
                    <div key={idx} style={{ fontSize: '0.88rem', color: '#475569', lineHeight: '1.45' }}>
                      • {r}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 6. Recommended Contact Angle */}
            {analysisResult.recommended_contact_angle && (
              <div style={{ background: '#eff6ff', borderLeft: '4px solid #2563eb', padding: '1rem', borderRadius: '0 8px 8px 0', marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#1d4ed8', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Target size={15} /> Recommended Contact Angle
                </div>
                <p style={{ fontSize: '0.92rem', color: '#1e3a8a', lineHeight: '1.6', margin: 0 }}>
                  {analysisResult.recommended_contact_angle}
                </p>
              </div>
            )}

            {/* 7. Recommended Next Action */}
            {analysisResult.recommended_next_action && (
              <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', padding: '1rem', borderRadius: '10px' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: 800, textTransform: 'uppercase', color: '#0f172a', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Zap size={15} color="#d97706" /> Recommended Next Action
                </div>
                <p style={{ fontSize: '0.92rem', color: '#334155', lineHeight: '1.6', margin: 0 }}>
                  {analysisResult.recommended_next_action}
                </p>
              </div>
            )}
          </div>

          {/* Action / Export Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleReset}
              style={{ padding: '0.6rem 1.25rem', fontSize: '0.88rem', fontWeight: 700, borderRadius: '8px', cursor: 'pointer' }}
            >
              ← Analyze Another Proposal / Prospect
            </button>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => {
                  const blob = new Blob([JSON.stringify(analysisResult, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${analysisResult.prospect?.name}_Proposal_Analysis.json`;
                  a.click();
                }}
                style={{ padding: '0.55rem 1rem', fontSize: '0.85rem', fontWeight: 700, borderRadius: '8px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
              >
                <Download size={14} /> Export JSON
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

