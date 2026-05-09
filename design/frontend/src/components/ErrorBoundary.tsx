import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  phaseName?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error(`ErrorBoundary [${this.props.phaseName || 'unknown'}]:`, error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '2rem', textAlign: 'center', color: '#d1d5db',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          height: '100%', gap: '1rem',
        }}>
          <div style={{ fontSize: '1.2rem', color: '#ef4444', fontWeight: 600 }}>
            {this.props.phaseName || 'Component'} encountered an error
          </div>
          <div style={{ fontSize: '0.78rem', color: '#9ca3af', maxWidth: '500px' }}>
            {this.state.error?.message || 'An unexpected error occurred.'}
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              padding: '0.4rem 1.2rem', borderRadius: '6px', cursor: 'pointer',
              background: '#3b82f6', color: 'white', border: 'none',
              fontSize: '0.82rem', fontWeight: 500,
            }}
          >
            Retry
          </button>
          <div style={{ fontSize: '0.65rem', color: '#6b7280', fontFamily: 'monospace', maxWidth: '600px', overflow: 'auto', maxHeight: '200px', textAlign: 'left', whiteSpace: 'pre-wrap' }}>
            {this.state.error?.stack}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
