/**
 * SSO Login page stub — dark-themed to match fintech UI.
 * Redirects to JumpCloud OIDC authorize URL on click.
 */

import { loginRedirect } from "../auth";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-50">
      <div className="w-full max-w-sm">
        <div className="overflow-hidden rounded-2xl border border-surface-400 bg-surface-200 shadow-card">
          {/* Top accent */}
          <div className="h-1 bg-gradient-to-r from-brand-700 via-brand-500 to-brand-700" />

          <div className="px-8 py-10">
            {/* Logo */}
            <div className="mb-8 flex flex-col items-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-brand-600 shadow-glow">
                <span className="text-2xl font-bold text-white">C</span>
              </div>
              <h1 className="text-lg font-semibold text-white">Contract Precedent AI</h1>
              <p className="mt-1 text-xs text-surface-800">Clause Intelligence Platform</p>
            </div>

            {/* SSO Button */}
            <button
              type="button"
              onClick={loginRedirect}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition-all hover:bg-brand-500 hover:shadow-glow"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z"
                />
              </svg>
              Sign in with JumpCloud
            </button>

            {/* Footer */}
            <p className="mt-6 text-center text-[10px] text-surface-700">
              Access requires company VPN connection
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
