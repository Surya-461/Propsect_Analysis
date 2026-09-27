import { useState, useRef } from 'react';
import { Scale, X, Sparkles, Search, Loader2, AlertCircle } from 'lucide-react';
import client from '../api/client';

const SAMPLE_PRESETS = [
  ["SBI Life Insurance", "HDFC Life", "ICICI Prudential Life"],
  ["Allianz", "AXA", "Zurich Insurance Group"],
  ["SBI Life Insurance", "Allianz"],
  ["ICICI Lombard", "Chubb", "State Farm"]
];

export default function CompareModal({ isOpen, onClose, onLaunchComparison, activeProspect, loading = false }) {
  const [selectedProspects, setSelectedProspects] = useState([]);
  const [inputVal, setInputVal] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState('');
  const searchTimeoutRef = useRef(null);

  const [prevOpen, setPrevOpen] = useState(isOpen);
  if (isOpen !== prevOpen) {
    setPrevOpen(isOpen);
    if (isOpen) {
      setSelectedProspects(activeProspect ? [activeProspect] : ["SBI Life Insurance", "Allianz"]);
      setInputVal('');
      setSuggestions([]);
      setSearchError('');
    }
  }

  if (!isOpen) return null;

  const handleSearch = (val) => {
    setInputVal(val);
    setSearchError('');

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!val || val.trim().length < 1) {
      setSuggestions([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const res = await client.get('/prospects/search', {
          params: { q: val.trim(), limit: 8 }
        });
        
        // Correctly handle {"results": [...], "count": ...} or direct array
        const list = Array.isArray(res.data)
          ? res.data
          : (res.data?.results || res.data?.prospects || []);
        
        setSuggestions(list);
        if (list.length === 0 && val.trim().length >= 2) {
          setSearchError(`No carriers matching "${val}" found in 234+ directory`);
        }
      } catch (err) {
        console.warn("Prospect search failed:", err);
        setSuggestions([]);
      } finally {
        setIsSearching(false);
      }
    }, 150);
  };

  const handleAddProspect = (name) => {
    if (!name) return;
    const cleanName = name.trim();
    if (selectedProspects.includes(cleanName)) {
      setInputVal('');
      setSuggestions([]);
      return;
    }
    if (selectedProspects.length >= 3) {
      alert("You can compare a maximum of 3 prospects simultaneously.");
      return;
    }
    setSelectedProspects(prev => [...prev, cleanName]);
    setInputVal('');
    setSuggestions([]);
    setSearchError('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (suggestions.length > 0) {
        handleAddProspect(suggestions[0].name);
      }
    }
  };

  const handleRemoveProspect = (name) => {
    setSelectedProspects(prev => prev.filter(p => p !== name));
  };

  const handleSelectPreset = (preset) => {
    setSelectedProspects(preset);
    setInputVal('');
    setSuggestions([]);
    setSearchError('');
  };

  const handleRunComparison = () => {
    if (selectedProspects.length < 2) {
      alert("Please select at least 2 prospects to compare.");
      return;
    }
    onLaunchComparison(selectedProspects);
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(15, 23, 42, 0.65)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '1rem'
    }}>
      <div style={{
        background: '#ffffff',
        borderRadius: '16px',
        maxWidth: '560px',
        width: '100%',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        border: '1px solid #e2e8f0'
      }}>
        {/* Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#f8fafc'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div style={{
              background: '#2563eb',
              color: '#ffffff',
              padding: '0.45rem',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Scale size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                Compare Insurance Peers
              </h3>
              <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '0.15rem 0 0 0' }}>
                Side-by-side benchmarking across solvency, scale, and 8 parameters
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: '#64748b',
              padding: '0.4rem',
              borderRadius: '6px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Selected Prospects Badges */}
          <div>
            <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Selected Prospects ({selectedProspects.length}/3)
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.4rem', minHeight: '40px', alignItems: 'center' }}>
              {selectedProspects.map((name, idx) => (
                <div
                  key={name}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    background: idx === 0 ? '#eff6ff' : idx === 1 ? '#f0fdf4' : '#faf5ff',
                    border: `1px solid ${idx === 0 ? '#bfdbfe' : idx === 1 ? '#bbf7d0' : '#e9d5ff'}`,
                    color: idx === 0 ? '#1d4ed8' : idx === 1 ? '#15803d' : '#7e22ce',
                    padding: '0.35rem 0.75rem',
                    borderRadius: '9999px',
                    fontSize: '0.85rem',
                    fontWeight: 700
                  }}
                >
                  <span>{name}</span>
                  <button
                    onClick={() => handleRemoveProspect(name)}
                    style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'inherit', padding: 0 }}
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}

              {selectedProspects.length === 0 && (
                <span style={{ fontSize: '0.84rem', color: '#94a3b8', fontStyle: 'italic' }}>
                  No prospects selected. Add at least 2 to compare.
                </span>
              )}
            </div>
          </div>

          {/* Add Prospect Input */}
          {selectedProspects.length < 3 && (
            <div style={{ position: 'relative' }}>
              <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Add Prospect from 234+ Directory
              </label>
              <div style={{ position: 'relative', marginTop: '0.35rem' }}>
                <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text"
                  placeholder="Search carrier (e.g. HDFC Life, AXA, Zurich, State Farm)..."
                  value={inputVal}
                  onChange={(e) => handleSearch(e.target.value)}
                  onKeyDown={handleKeyDown}
                  style={{
                    width: '100%',
                    padding: '0.65rem 2.2rem 0.65rem 2.4rem',
                    border: '1px solid #cbd5e1',
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    boxSizing: 'border-box',
                    outline: 'none'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#2563eb'}
                  onBlur={(e) => e.target.style.borderColor = '#cbd5e1'}
                />
                {isSearching && (
                  <Loader2 size={16} color="#2563eb" className="animate-spin" style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
                )}
              </div>

              {/* Search Error / Not Found */}
              {searchError && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.35rem', color: '#64748b', fontSize: '0.78rem' }}>
                  <AlertCircle size={13} color="#94a3b8" />
                  <span>{searchError}</span>
                </div>
              )}

              {/* Suggestions Dropdown */}
              {suggestions.length > 0 && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  background: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                  zIndex: 10,
                  marginTop: '0.25rem',
                  overflow: 'hidden',
                  maxHeight: '220px',
                  overflowY: 'auto'
                }}>
                  {suggestions.map((s) => (
                    <div
                      key={s.id || s.name}
                      onClick={() => handleAddProspect(s.name)}
                      style={{
                        padding: '0.6rem 0.85rem',
                        fontSize: '0.86rem',
                        color: '#1e293b',
                        cursor: 'pointer',
                        borderBottom: '1px solid #f1f5f9',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                      onMouseLeave={(e) => e.currentTarget.style.background = '#ffffff'}
                    >
                      <span style={{ fontWeight: 600 }}>{s.name}</span>
                      <span style={{ fontSize: '0.72rem', color: '#64748b' }}>{s.region || "Insurance Carrier"}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Quick Comparison Presets */}
          <div>
            <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Popular Peer Presets
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.35rem' }}>
              {SAMPLE_PRESETS.map((preset, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectPreset(preset)}
                  style={{
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    padding: '0.35rem 0.65rem',
                    borderRadius: '6px',
                    fontSize: '0.76rem',
                    fontWeight: 600,
                    color: '#334155',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.3rem'
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = '#eff6ff'; e.currentTarget.style.borderColor = '#bfdbfe'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = '#f8fafc'; e.currentTarget.style.borderColor = '#e2e8f0'; }}
                >
                  <Sparkles size={11} color="#2563eb" /> {preset.join(' vs. ')}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '1rem 1.5rem',
          borderTop: '1px solid #e2e8f0',
          background: '#f8fafc',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '0.75rem'
        }}>
          <button
            onClick={onClose}
            style={{
              padding: '0.6rem 1.1rem',
              borderRadius: '8px',
              border: '1px solid #cbd5e1',
              background: '#ffffff',
              color: '#475569',
              fontWeight: 600,
              fontSize: '0.88rem',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleRunComparison}
            disabled={selectedProspects.length < 2 || loading}
            style={{
              padding: '0.6rem 1.35rem',
              borderRadius: '8px',
              border: 'none',
              background: selectedProspects.length >= 2 ? '#2563eb' : '#94a3b8',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '0.88rem',
              cursor: selectedProspects.length >= 2 ? 'pointer' : 'not-allowed',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              boxShadow: selectedProspects.length >= 2 ? '0 2px 6px rgba(37, 99, 235, 0.25)' : 'none'
            }}
          >
            <Scale size={15} /> Compare {selectedProspects.length} Prospects
          </button>
        </div>
      </div>
    </div>
  );
}
