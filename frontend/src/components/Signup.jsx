import { useState } from 'react';
import {
  ShieldCheck,
  User,
  Mail,
  Lock,
  UserPlus,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import GoogleAuthButton from './GoogleAuthButton';
import './AuthPage.css';

export default function Signup({ onSwitchToLogin }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { signup, authError, setAuthError } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!name.trim() || !email.trim() || !password.trim()) {
      setAuthError('Please fill in all required fields.');
      return;
    }

    if (password.length < 6) {
      setAuthError('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setAuthError('Passwords do not match.');
      return;
    }

    setIsSubmitting(true);

    try {
      await signup(
        name.trim(),
        email.trim(),
        password
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">

        <div className="auth-header">
          <div className="auth-logo-badge">
            <ShieldCheck size={28} color="#ffffff" />
          </div>

          <h2 className="auth-title">
            Create an Account
          </h2>

          <p className="auth-subtitle">
            Join Prospect AI to begin B2B underwriting intelligence
          </p>
        </div>

        {authError && (
          <div className="auth-error-banner">
            <AlertCircle size={16} />
            <span>{authError}</span>
          </div>
        )}

        {/* Google OAuth 2.0 Sign-Up */}
        <GoogleAuthButton mode="signup" />

        <div className="auth-divider">
          <span className="auth-divider-text">OR</span>
        </div>

        <form
          className="auth-form"
          onSubmit={handleSubmit}
          autoComplete="off"
        >

          {/* Full Name */}
          <div className="auth-field-group">
            <label
              className="auth-label"
              htmlFor="signup-full-name"
            >
              Full Name
            </label>

            <div className="auth-input-wrapper">
              <span className="auth-input-icon">
                <User size={18} />
              </span>

              <input
                id="signup-full-name"
                name="signup-full-name"
                type="text"
                className="auth-input"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoFocus
                autoComplete="off"
                autoCapitalize="words"
                spellCheck="false"
              />
            </div>
          </div>

          {/* Email */}
          <div className="auth-field-group">
            <label
              className="auth-label"
              htmlFor="signup-email"
            >
              Email Address
            </label>

            <div className="auth-input-wrapper">
              <span className="auth-input-icon">
                <Mail size={18} />
              </span>

              <input
                id="signup-email"
                name="signup-email"
                type="email"
                className="auth-input"
                placeholder="john@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="off"
                spellCheck="false"
              />
            </div>
          </div>

          {/* Password */}
          <div className="auth-field-group">
            <label
              className="auth-label"
              htmlFor="signup-password"
            >
              Password
            </label>

            <div className="auth-input-wrapper">
              <span className="auth-input-icon">
                <Lock size={18} />
              </span>

              <input
                id="signup-password"
                name="signup-password"
                type="password"
                className="auth-input"
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete="new-password"
              />
            </div>
          </div>

          {/* Confirm Password */}
          <div className="auth-field-group">
            <label
              className="auth-label"
              htmlFor="signup-confirm-password"
            >
              Confirm Password
            </label>

            <div className="auth-input-wrapper">
              <span className="auth-input-icon">
                <Lock size={18} />
              </span>

              <input
                id="signup-confirm-password"
                name="signup-confirm-password"
                type="password"
                className="auth-input"
                placeholder="Repeat password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="auth-btn-submit"
            disabled={isSubmitting}
          >
            <UserPlus size={18} />

            <span>
              {isSubmitting
                ? 'Creating account...'
                : 'Create Account'}
            </span>
          </button>
        </form>

        <div className="auth-footer-text">
          Already have an account?

          <button
            type="button"
            className="auth-link"
            onClick={onSwitchToLogin}
          >
            Sign In
          </button>
        </div>

      </div>
    </div>
  );
}