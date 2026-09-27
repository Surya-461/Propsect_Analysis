import { useState } from 'react';
import { ShieldCheck, Mail, Lock, LogIn, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import GoogleAuthButton from './GoogleAuthButton';
import './AuthPage.css';

export default function Login({ onSwitchToSignup }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, authError, setAuthError } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setAuthError('Please enter both email and password.');
      return;
    }

    setIsSubmitting(true);
    await login(email.trim(), password);
    setIsSubmitting(false);
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo-badge">
            <ShieldCheck size={28} color="#ffffff" />
          </div>
          <h2 className="auth-title">Welcome to Prospect AI</h2>
          <p className="auth-subtitle">
            Sign in to access your B2B underwriting intelligence & history
          </p>
        </div>

        {authError && (
          <div className="auth-error-banner">
            <AlertCircle size={16} />
            <span>{authError}</span>
          </div>
        )}

        {/* Google OAuth 2.0 Sign-In */}
        <GoogleAuthButton mode="login" />

        <div className="auth-divider">
          <span className="auth-divider-text">OR</span>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-field-group">
            <label className="auth-label">Email Address</label>
            <div className="auth-input-wrapper">
              <span className="auth-input-icon">
                <Mail size={18} />
              </span>
              <input
                type="email"
                className="auth-input"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
          </div>

          <div className="auth-field-group">
            <label className="auth-label">Password</label>
            <div className="auth-input-wrapper">
              <span className="auth-input-icon">
                <Lock size={18} />
              </span>
              <input
                type="password"
                className="auth-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="auth-btn-submit"
            disabled={isSubmitting}
          >
            <LogIn size={18} />
            <span>{isSubmitting ? 'Signing in...' : 'Sign In'}</span>
          </button>
        </form>

        {/* Quick Admin Helper Button for Instant Evaluation */}


        <div className="auth-footer-text">
          Don't have an account?
          <button
            type="button"
            className="auth-link"
            onClick={onSwitchToSignup}
          >
            Create an Account
          </button>
        </div>
      </div>
    </div>
  );
}
