import { useEffect, useState } from 'react'

interface ToastProps {
  message: string
  type?: 'info' | 'error' | 'success'
  duration?: number
  onClose?: () => void
}

export default function Toast({ message, type = 'info', duration = 3000, onClose }: ToastProps) {
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false)
      setTimeout(() => onClose?.(), 300)
    }, duration)

    return () => clearTimeout(timer)
  }, [duration, onClose])

  if (!isVisible) return null

  const bgColor = {
    info: 'bg-mono-800',
    error: 'bg-red-600',
    success: 'bg-green-600',
  }[type]

  return (
    <div
      className={`fixed top-4 left-1/2 transform -translate-x-1/2 ${bgColor} text-white px-6 py-3 rounded shadow-lg z-50 transition-all duration-300`}
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translate(-50%, 0)' : 'translate(-50%, -20px)',
      }}
    >
      {message}
    </div>
  )
}

// Global toast container
let toastContainer: HTMLDivElement | null = null

function getToastContainer() {
  if (!toastContainer) {
    toastContainer = document.createElement('div')
    toastContainer.id = 'toast-container'
    document.body.appendChild(toastContainer)
  }
  return toastContainer
}

export function showToast(message: string, type: 'info' | 'error' | 'success' = 'info', duration = 3000) {
  const container = getToastContainer()
  const toastElement = document.createElement('div')
  container.appendChild(toastElement)

  const bgColor = {
    info: 'background-color: var(--color-text)',
    error: 'background-color: #dc2626',
    success: 'background-color: #16a34a',
  }[type]

  toastElement.style.cssText = `
    ${bgColor};
    color: var(--color-bg);
    padding: 12px 24px;
    border-radius: 8px;
    margin-bottom: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    position: fixed;
    top: 16px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    font-family: var(--font-sans);
    max-width: 80vw;
    text-align: center;
  `

  toastElement.textContent = message

  setTimeout(() => {
    toastElement.style.opacity = '0'
    toastElement.style.transform = 'translate(-50%, -20px)'
    setTimeout(() => {
      if (container.contains(toastElement)) {
        container.removeChild(toastElement)
      }
    }, 300)
  }, duration)
}