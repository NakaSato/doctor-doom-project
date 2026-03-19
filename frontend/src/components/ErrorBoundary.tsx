/**
 * Error Boundary Component
 * 
 * Catches React errors and displays fallback UI
 */

import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  name?: string;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`ErrorBoundary [${this.props.name || 'unnamed'}] caught:`, error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div style={{
          padding: 24,
          textAlign: 'center',
          background: 'rgba(255,59,48,0.1)',
          border: '1px solid rgba(255,59,48,0.3)',
          borderRadius: 12,
          color: '#FF3B30',
          maxWidth: 600,
          margin: '40px auto',
        }}>
          <div style={{ fontSize: 32, marginBottom: 16 }}>⚠️</div>
          <h2 style={{ fontSize: 18, fontWeight: 800, marginBottom: 8, color: '#FF3B30' }}>
            Something went wrong
          </h2>
          <p style={{ fontSize: 12, color: '#888', marginBottom: 16 }}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false })}
            style={{
              padding: '10px 20px',
              background: 'linear-gradient(135deg, #00F0FF 0%, #0080FF 100%)',
              border: 'none',
              borderRadius: 8,
              color: '#000',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: 12,
              fontFamily: 'inherit',
            }}
          >
            🔄 Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Error Boundary Hook
 * 
 * Functional component wrapper for error boundaries
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  name: string
) {
  return function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundary name={name}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}
