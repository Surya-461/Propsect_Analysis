import { useState } from 'react';
import { 
  Building, 
  TrendingUp, 
  Award, 
  ShieldAlert, 
  Activity, 
  Briefcase, 
  Zap, 
  Globe, 
  Sparkles, 
  BarChart3, 
  Scale,
  Layers
} from 'lucide-react';

export default function ComparativeMatrixCard({ data }) {
  const [activeParamTab, setActiveParamTab] = useState("Financial Strength");

  if (!data || !data.prospects || data.prospects.length < 2) return null;

  const prospects = data.prospects;
  const metrics = data.metrics || [];
  const breakdown = data.parameter_breakdown || {};
  const execSummary = data.comparative_executive_summary || "";

  const PARAM_LIST = [
    { key: "Financial Strength", label: "Financial Strength", icon: ShieldAlert },
    { key: "Company Scale", label: "Company Scale", icon: Building },
    { key: "Insurance Performance", label: "Insurance Performance", icon: Activity },
    { key: "Business Growth", label: "Business Growth", icon: TrendingUp },
    { key: "Market Position", label: "Market Position", icon: Award },
    { key: "Technology Activity", label: "Technology", icon: Zap },
    { key: "Operational Scale", label: "Operational", icon: Briefcase },
    { key: "Strategic Activity", label: "Strategic", icon: Globe }
  ];

  // Column grid template based on number of carriers (2 or 3)
  const colCount = prospects.length;
  const gridTemplate = `180px repeat(${colCount}, minmax(0, 1fr))`;

  return (
    <div style={{
      background: '#ffffff',
      border: '1px solid #e2e8f0',
      borderRadius: '12px',
      padding: '1.25rem',
      boxShadow: '0 4px 16px rgba(0,0,0,0.04)',
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
      maxWidth: '100%',
      overflowX: 'auto'
    }}>
      {/* 1. Header Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid #f1f5f9',
        paddingBottom: '0.75rem',
        flexWrap: 'wrap',
        gap: '0.5rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{
            background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
            padding: '0.45rem',
            borderRadius: '8px',
            color: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Scale size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Peer Benchmarking Matrix
            </h3>
            <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 500 }}>
              Side-by-Side Underwriting & Disclosures Comparison
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {prospects.map((name, idx) => (
            <span
              key={name}
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                background: idx === 0 ? '#eff6ff' : idx === 1 ? '#f0fdf4' : '#faf5ff',
                color: idx === 0 ? '#1d4ed8' : idx === 1 ? '#15803d' : '#7e22ce',
                border: `1px solid ${idx === 0 ? '#bfdbfe' : idx === 1 ? '#bbf7d0' : '#e9d5ff'}`,
                padding: '0.2rem 0.6rem',
                borderRadius: '9999px'
              }}
            >
              {name}
            </span>
          ))}
        </div>
      </div>

      {/* 2. Executive Comparative Synthesis */}
      {execSummary && (
        <div style={{
          background: '#f8fafc',
          borderLeft: '4px solid #2563eb',
          padding: '0.85rem 1rem',
          borderRadius: '0 8px 8px 0'
        }}>
          <div style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            color: '#2563eb',
            textTransform: 'uppercase',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            marginBottom: '0.3rem',
            letterSpacing: '0.04em'
          }}>
            <Sparkles size={13} /> Comparative Synthesis
          </div>
          <p style={{ margin: 0, fontSize: '0.9rem', color: '#334155', lineHeight: '1.6', whiteSpace: 'pre-line' }}>
            {execSummary}
          </p>
        </div>
      )}

      {/* 3. Side-by-Side Benchmark Metrics Table */}
      <div>
        <h4 style={{
          fontSize: '0.78rem',
          fontWeight: 700,
          color: '#64748b',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          marginBottom: '0.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.35rem'
        }}>
          <BarChart3 size={14} color="#2563eb" /> Core Underwriting Benchmarks
        </h4>

        <div style={{
          border: '1px solid #e2e8f0',
          borderRadius: '8px',
          overflow: 'hidden',
          minWidth: '550px'
        }}>
          {/* Table Header */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: gridTemplate,
            background: '#f8fafc',
            borderBottom: '1px solid #e2e8f0',
            padding: '0.65rem 0.85rem',
            fontWeight: 700,
            fontSize: '0.82rem',
            color: '#475569'
          }}>
            <div>Benchmark Metric</div>
            {prospects.map((name, idx) => (
              <div key={name} style={{
                color: idx === 0 ? '#1d4ed8' : idx === 1 ? '#15803d' : '#7e22ce',
                fontWeight: 800
              }}>
                {name}
              </div>
            ))}
          </div>

          {/* Metric Rows */}
          {[
            { label: "Solvency Ratio", key: "solvency_ratio", highlight: true },
            { label: "Credit / Solvency Rating", key: "credit_rating" },
            { label: "Combined Ratio / RoE", key: "combined_ratio" },
            { label: "AUM / Asset Scale", key: "aum_scale" },
            { label: "Premium Growth (YoY)", key: "premium_growth" },
            { label: "Market Position", key: "market_position" },
            { label: "Digital Maturity", key: "digital_maturity" }
          ].map((row, rIdx) => (
            <div
              key={row.key}
              style={{
                display: 'grid',
                gridTemplateColumns: gridTemplate,
                padding: '0.65rem 0.85rem',
                fontSize: '0.85rem',
                borderBottom: rIdx < 6 ? '1px solid #f1f5f9' : 'none',
                background: rIdx % 2 === 0 ? '#ffffff' : '#fafafa',
                alignItems: 'center'
              }}
            >
              <div style={{ fontWeight: 600, color: '#334155' }}>
                {row.label}
              </div>

              {metrics.map((m, mIdx) => (
                <div key={mIdx} style={{
                  color: row.highlight ? '#1e293b' : '#334155',
                  fontWeight: row.highlight ? 700 : 500
                }}>
                  {row.highlight ? (
                    <span style={{
                      background: mIdx === 0 ? '#eff6ff' : '#f0fdf4',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '4px',
                      color: mIdx === 0 ? '#1d4ed8' : '#15803d',
                      border: `1px solid ${mIdx === 0 ? '#bfdbfe' : '#bbf7d0'}`
                    }}>
                      {m[row.key] || "—"}
                    </span>
                  ) : (
                    m[row.key] || "—"
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* 4. Parameter-by-Parameter Deep Dive Tabs */}
      <div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '0.5rem',
          flexWrap: 'wrap',
          gap: '0.4rem'
        }}>
          <h4 style={{
            fontSize: '0.78rem',
            fontWeight: 700,
            color: '#64748b',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem'
          }}>
            <Layers size={14} color="#2563eb" /> Parameter Deep Dive
          </h4>

          {/* Parameter Pill Selector */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
            {PARAM_LIST.map((tab) => {
              const isSelected = activeParamTab === tab.key;
              const IconComponent = tab.icon;
              return (
                <button
                  key={tab.key}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    fontSize: '0.74rem',
                    padding: '0.25rem 0.55rem',
                    borderRadius: '6px',
                    border: `1px solid ${isSelected ? '#2563eb' : '#e2e8f0'}`,
                    background: isSelected ? '#eff6ff' : '#ffffff',
                    color: isSelected ? '#1d4ed8' : '#64748b',
                    fontWeight: isSelected ? 700 : 500,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                  onClick={() => setActiveParamTab(tab.key)}
                >
                  <IconComponent size={11} color={isSelected ? '#2563eb' : '#94a3b8'} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Side-by-Side Parameter Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${colCount}, minmax(0, 1fr))`,
          gap: '0.75rem',
          marginTop: '0.5rem'
        }}>
          {prospects.map((name, pIdx) => {
            const pInfo = breakdown[activeParamTab]?.[name] || {};
            const keyFacts = pInfo.key_facts || [];

            return (
              <div
                key={name}
                style={{
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  padding: '0.85rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem'
                }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  borderBottom: '1px solid #e2e8f0',
                  paddingBottom: '0.4rem'
                }}>
                  <span style={{
                    fontSize: '0.88rem',
                    fontWeight: 700,
                    color: pIdx === 0 ? '#1d4ed8' : pIdx === 1 ? '#15803d' : '#7e22ce'
                  }}>
                    {name}
                  </span>
                </div>

                <p style={{
                  fontSize: '0.84rem',
                  color: '#334155',
                  lineHeight: '1.5',
                  margin: 0
                }}>
                  {pInfo.summary}
                </p>

                {keyFacts.length > 0 && (
                  <ul style={{
                    margin: '0.2rem 0 0 0',
                    paddingLeft: 0,
                    listStyle: 'none',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.3rem'
                  }}>
                    {keyFacts.map((fact, fIdx) => (
                      <li key={fIdx} style={{
                        fontSize: '0.78rem',
                        color: '#475569',
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '0.35rem',
                        background: '#ffffff',
                        border: '1px solid #f1f5f9',
                        padding: '0.3rem 0.5rem',
                        borderRadius: '4px'
                      }}>
                        <span style={{ color: '#2563eb', fontWeight: 700 }}>•</span>
                        <span style={{ lineHeight: '1.35' }}>{fact}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
