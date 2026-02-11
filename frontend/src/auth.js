/**
 * Frontend authentication utilities for JumpCloud OIDC.
 *
 * When VITE_AUTH_ENABLED is not "true" (default), all auth functions are no-ops
 * and the app works as before with no login required.
 */

export const AUTH_ENABLED = import.meta.env.VITE_AUTH_ENABLED === "true";

const TOKEN_KEY = "contract_ai_token";
const JUMPCLOUD_CLIENT_ID = import.meta.env.VITE_JUMPCLOUD_CLIENT_ID || "";
const JUMPCLOUD_AUTHORIZE_URL = import.meta.env.VITE_JUMPCLOUD_AUTHORIZE_URL || "";
// TODO: Set VITE_JUMPCLOUD_REDIRECT_URI in production
const REDIRECT_URI = import.meta.env.VITE_JUMPCLOUD_REDIRECT_URI || `${window.location.origin}/callback`;

/**
 * Get authorization headers to attach to API requests.
 * Returns empty object when auth is disabled.
 */
export function getAuthHeaders() {
  if (!AUTH_ENABLED) return {};
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

/**
 * Check if user has a valid (non-expired) token.
 */
export function isAuthenticated() {
  if (!AUTH_ENABLED) return true;
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return false;

  // TODO: Decode JWT and check expiration
  // For now, just check token exists
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

/**
 * Redirect to JumpCloud OIDC authorize endpoint.
 */
export function loginRedirect() {
  if (!JUMPCLOUD_AUTHORIZE_URL || !JUMPCLOUD_CLIENT_ID) {
    console.error("JumpCloud OIDC not configured — set VITE_JUMPCLOUD_AUTHORIZE_URL and VITE_JUMPCLOUD_CLIENT_ID");
    return;
  }
  const params = new URLSearchParams({
    response_type: "code",
    client_id: JUMPCLOUD_CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    scope: "openid email profile",
    // TODO: Add state parameter for CSRF protection
  });
  window.location.href = `${JUMPCLOUD_AUTHORIZE_URL}?${params}`;
}

/**
 * Handle the OIDC callback — exchange auth code for token.
 * TODO: Implement token exchange via backend endpoint.
 */
export function handleCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  if (!code) return false;

  // TODO: POST code to backend /api/auth/callback to exchange for token
  // TODO: Store received token in localStorage
  // TODO: Redirect to /
  console.warn("OIDC callback handling not yet implemented");
  return false;
}

/**
 * Clear stored token and redirect to login.
 */
export function logout() {
  localStorage.removeItem(TOKEN_KEY);
  if (AUTH_ENABLED) {
    window.location.href = "/";
  }
}
