import { useEffect, useState } from 'react';
import { ShieldCheck, Cpu, Zap, Lock, Activity } from 'lucide-react';
import './ProspectAISplashLoader.css';

export default function ProspectAISplashLoader({ onFinish }) {
  const [progress, setProgress] = useState(0);
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [loadingStep, setLoadingStep] = useState('Booting Prospect AI Core...');

  useEffect(() => {
    // Ultra-fast 1-second progress timeline
    const startTime = Date.now();
    const duration = 800; // Fill progress in 800ms

    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const pct = Math.min(100, Math.floor((elapsed / duration) * 100));
      setProgress(pct);

      if (pct < 40) {
        setLoadingStep('Connecting Statutory Data Streams...');
      } else if (pct < 80) {
        setLoadingStep('Mounting Underwriting Models...');
      } else {
        setLoadingStep('Prospect AI Live ✓');
      }

      if (pct >= 100) {
        clearInterval(interval);
      }
    }, 20);

    // Fade out at 850ms and complete at exactly 1000ms
    const fadeTimer = setTimeout(() => {
      setIsFadingOut(true);
    }, 820);

    const finishTimer = setTimeout(() => {
      if (onFinish) onFinish();
    }, 1000);

    return () => {
      clearInterval(interval);
      clearTimeout(fadeTimer);
      clearTimeout(finishTimer);
    };
  }, [onFinish]);

  return (
    <div className={`prospect-splash-overlay ${isFadingOut ? 'fade-out' : ''}`}>
      {/* Cyber Grid Pattern Backdrop */}
      <div className="prospect-grid-backdrop" />
      <div className="prospect-glow-spotlight" />

      <div className="prospect-splash-content">
        
        {/* Holographic Shield Container with Laser Scan Beam */}
        <div className="prospect-logo-wrapper">
          <div className="prospect-laser-scanner" />
          <div className="prospect-orbit-ring" />
          <div className="prospect-orbit-ring-outer" />
          <div className="prospect-logo-circle">
            <ShieldCheck size={44} color="#ffffff" className="prospect-shield-icon" />
          </div>
        </div>

        {/* Brand Header */}
        <div className="prospect-title-group">
          <div className="prospect-top-tag">
            <span className="live-dot" />
            <span>AI UNDERWRITING PLATFORM</span>
          </div>
          <h1 className="prospect-brand-title">PROSPECT AI</h1>
          <p className="prospect-brand-tagline">
            ENTERPRISE PROSPECT INTELLIGENCE & AUDIT
          </p>
        </div>

        {/* Fast Precision Progress Line */}
        <div className="prospect-progress-container">
          <div className="prospect-progress-track">
            <div 
              className="prospect-progress-fill" 
              style={{ width: `${progress}%` }}
            />
            <div className="prospect-progress-glow-head" style={{ left: `${progress}%` }} />
          </div>
          <div className="prospect-progress-label">
            <span className="step-text"><Activity size={12} className="pulse-icon" color="#38bdf8" /> {loadingStep}</span>
            <span className="prospect-percent">{progress}%</span>
          </div>
        </div>

        {/* Real-time System Telemetry Badges */}
        <div className="prospect-splash-badges">
          <div className="splash-badge-item">
            <Zap size={12} color="#60a5fa" />
            <span>1.0s Speed Launch</span>
          </div>
          <div className="splash-badge-item">
            <Cpu size={12} color="#34d399" />
            <span>Dual-LLM Active</span>
          </div>
          <div className="splash-badge-item">
            <Lock size={12} color="#38bdf8" />
            <span>250+ Disclosures</span>
          </div>
        </div>

      </div>
    </div>
  );
}
