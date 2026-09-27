import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { AlertCircle } from 'lucide-react';

export default function GoogleAuthButton({ mode = 'signup' }) {
  const { loginWithGoogle, setAuthError } = useAuth();
  const [loading, setLoading] = useState(false);
  const [infoMessage, setInfoMessage] = useState('');

  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '951782072564-f128l81shrtel5p4m3oh2p425um1gtuf.apps.googleusercontent.com';

  const handleGoogleClick = async () => {
    setAuthError('');
    setInfoMessage('');

    if (!clientId) {
      setInfoMessage(
        'Google OAuth requires VITE_GOOGLE_CLIENT_ID in frontend .env. To enable live Google Sign-In, add your Google Cloud OAuth Client ID.'
      );
      return;
    }

    if (!window.google || !window.google.accounts || !window.google.accounts.oauth2) {
      setAuthError('Google Identity Services is still loading. Please check your connection and try again.');
      return;
    }

    setLoading(true);

    try {
      const tokenClient = window.google.accounts.oauth2.initTokenClient({
        client_id: clientId,
        scope: 'openid email profile',
        callback: async (response) => {
          if (response.error) {
            setLoading(false);
            if (response.error !== 'popup_closed_by_user') {
              setAuthError(`Google authentication error: ${response.error_description || response.error}`);
            }
            return;
          }
          if (response.access_token) {
            const res = await loginWithGoogle({ access_token: response.access_token });
            setLoading(false);
            if (!res.success && res.message) {
              setAuthError(res.message);
            }
          }
        },
        error_callback: () => {
          setLoading(false);
          setAuthError('Google authentication popup could not be opened.');
        }
      });

      tokenClient.requestAccessToken({ prompt: 'consent' });
    } catch (err) {
      setLoading(false);
      setAuthError(`Failed to initialize Google Sign-In: ${err.message || err}`);
    }
  };

  return (
    <div style={{ width: '100%' }}>
      {infoMessage && (
        <div className="auth-info-banner">
          <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
          <span>{infoMessage}</span>
        </div>
      )}

      <button
        type="button"
        className="auth-btn-google"
        onClick={handleGoogleClick}
        disabled={loading}
        title={mode === 'signup' ? 'Sign up using your Google account' : 'Sign in using your Google account'}
      >
        {loading ? (
          <span>Connecting to Google...</span>
        ) : (
          <>
            <svg className="google-icon" viewBox="0 0 24 24" width="18" height="18">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
            </svg>
            <span>{mode === 'signup' ? 'Sign up with Google' : 'Sign in with Google'}</span>
          </>
        )}
      </button>
    </div>
  );
}
