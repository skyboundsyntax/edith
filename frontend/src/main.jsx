import React, { StrictMode, Component } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('EDITH Global Error Boundary Caught:', error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          backgroundColor: '#070b14',
          color: '#f8fafc',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem',
          fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
        }}>
          <div style={{
            maxWidth: '640px',
            width: '100%',
            background: 'rgba(19, 31, 56, 0.85)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: '16px',
            padding: '2rem',
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <span style={{ fontSize: '1.5rem' }}>⚠️</span>
              <h1 style={{ fontSize: '1.25rem', margin: 0, color: '#f87171' }}>
                Application Runtime Notice
              </h1>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '1.25rem', lineHeight: 1.5 }}>
              EDITH caught an unhandled client error during render:
            </p>
            <div style={{
              background: 'rgba(0, 0, 0, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '8px',
              padding: '0.85rem',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '0.8rem',
              color: '#fca5a5',
              overflowX: 'auto',
              marginBottom: '1.5rem',
              whiteSpace: 'pre-wrap'
            }}>
              {this.state.error?.toString()}
            </div>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: 'linear-gradient(135deg, #f59e0b, #ea580c)',
                color: '#fff',
                border: 'none',
                padding: '0.65rem 1.25rem',
                borderRadius: '8px',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(245, 158, 11, 0.3)'
              }}
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
