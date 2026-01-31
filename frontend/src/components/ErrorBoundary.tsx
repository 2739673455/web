import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6" style={{ backgroundColor: 'var(--color-bg)' }}>
          <div className="max-w-md w-full border border-mono rounded-lg p-8 shadow-lg" style={{ backgroundColor: 'var(--color-bg)' }}>
            <h1 className="text-2xl font-bold mb-4" style={{ color: 'var(--color-text)' }}>
              出错了
            </h1>
            <p className="mb-6" style={{ color: 'var(--color-text)' }}>
              应用程序遇到了一个错误，请刷新页面重试。
            </p>
            {this.state.error && (
              <details className="mb-6" open>
                <summary className="cursor-pointer text-sm mb-2" style={{ color: 'var(--color-text)' }}>
                  错误详情
                </summary>
                <div className="p-2 border-2 border-red-700 text-red-700 text-sm font-bold overflow-auto">
                  {this.state.error.toString()}
                </div>
              </details>
            )}
            <button
              onClick={() => window.location.reload()}
              className="mx-auto block py-2 px-4 font-medium"
            >
              刷新页面
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}