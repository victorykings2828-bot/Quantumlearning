import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { TutorLauncher } from '@/features/tutor/TutorLauncher';
import { useSession } from './session';

const NAV = [
  { to: '/', label: 'Introduction', end: true },
  { to: '/course', label: 'Course' },
  { to: '/lab', label: 'Quantum Lab' },
  { to: '/progress', label: 'Progress' },
];

export function Shell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const session = useSession();

  return (
    <div className="shell">
      <a className="skip-link" href="#main">
        Skip to main content
      </a>
      <header className="site-header">
        <div className="site-header__inner">
          <NavLink to="/" className="wordmark">
            <span className="wordmark__mark" aria-hidden="true">
              Q
            </span>
            <span className="wordmark__text">
              <strong>Quantum Learning Laboratory</strong>
              <span>Verified simulation · learning demo</span>
            </span>
          </NavLink>
          <button
            type="button"
            className="button button--small header-menu-toggle"
            aria-expanded={menuOpen}
            aria-controls="primary-navigation"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? 'Close menu' : 'Menu'}
          </button>
          <nav
            id="primary-navigation"
            className="site-nav"
            aria-label="Primary"
            data-collapsed={!menuOpen}
          >
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main id="main" className="page">
        {session.status === 'error' && session.error && (
          <div className="error-banner" role="alert">
            {session.error}{' '}
            <button type="button" className="button button--small" onClick={session.refresh}>
              Try again
            </button>
          </div>
        )}
        {session.status === 'loading' ? (
          <p className="note" role="status" aria-live="polite">
            Starting your guest session…
          </p>
        ) : (
          <Outlet />
        )}
      </main>

      <TutorLauncher />

      <footer className="site-footer">
        <div className="site-footer__inner">
          <p>
            Experiments run on a quantum simulator executing on a classical computer. Every
            number shown is computed by Qiskit for the exact circuit on screen; values from a
            formula are labelled <strong>analytical prediction</strong>.
          </p>
          <p>
            This demo records progress, assessment results, and evidence-based skill
            demonstration against a guest session held in this browser.
          </p>
        </div>
      </footer>
    </div>
  );
}
