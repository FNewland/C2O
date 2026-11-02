import { Component, type ReactNode } from 'react'
import i18n from '../i18n'
import { fs } from '../theme/tokens'

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
          padding: '2rem', textAlign: 'center', color: 'var(--text)',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          height: '100%', gap: '1rem',
        }}>
          <div className="t-20 c-alarm w-600">
            {i18n.t('{{name}} encountered an error', { name: i18n.t(this.props.phaseName || 'Component') })}
          </div>
          <div style={{ fontSize: fs.label, color: 'var(--text-2)', maxWidth: '500px' }}>
            {this.state.error?.message || i18n.t('An unexpected error occurred.')}
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              padding: '0.4rem 1.2rem', borderRadius: '6px', cursor: 'pointer',
              background: 'var(--interactive)', color: 'white', border: 'none',
              fontSize: fs.body, fontWeight: 500,
            }}
          >
            {i18n.t('Retry')}
          </button>
          <div style={{ fontSize: fs.label, color: 'var(--text-3)', fontFamily: 'monospace', maxWidth: '600px', overflow: 'auto', maxHeight: '200px', textAlign: 'left', whiteSpace: 'pre-wrap' }}>
            {this.state.error?.stack}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
