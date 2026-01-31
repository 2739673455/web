import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '../stores/authStore'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/**
 * API client class
 * Manages HTTP requests, response interceptors, and automatic token refresh
 */
class ApiClient {
  private client: AxiosInstance
  private isRefreshing = false
  private refreshSubscribers: Array<(token: string) => void> = []

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000, // 30 second timeout
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Allow sending cookies
    })

    this.setupInterceptors()
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors() {
    // Request interceptor: automatically add Authorization header
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = useAuthStore.getState().accessToken
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error),
    )

    // Response interceptor: handle 401 errors and automatic token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & {
          _retry?: boolean
        }

        // 401 error, try to refresh token (exclude login and refresh endpoints)
        if (
          error.response?.status === 401 &&
          !originalRequest._retry &&
          !originalRequest.url?.includes('/login') &&
          !originalRequest.url?.includes('/refresh')
        ) {
          if (this.isRefreshing) {
            // If refreshing, add request to waiting queue
            return new Promise((resolve) => {
              this.subscribeTokenRefresh((token: string) => {
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${token}`
                }
                resolve(this.client(originalRequest))
              })
            })
          }

          originalRequest._retry = true
          this.isRefreshing = true

          try {
            // Try to refresh token
            const authStore = useAuthStore.getState()
            
            // Check if refresh token exists
            if (!authStore.refreshToken) {
              throw new Error('No refresh token available')
            }
            
            const result = await this.refreshToken()
            authStore.setTokens(result.access_token, result.refresh_token)

            // Notify all waiting requests to use new token
            this.onRefreshed(result.access_token)
            this.refreshSubscribers = []
            this.isRefreshing = false

            // 重试原始请求
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${result.access_token}`
            }
            return this.client(originalRequest)
          } catch (refreshError) {
            // 刷新失败，清除认证状态并跳转到主页
            this.isRefreshing = false
            this.refreshSubscribers = []
            useAuthStore.getState().logout()
            window.location.href = '/'
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      },
    )
  }

  /**
   * 订阅 token 刷新完成事件
   */
  private subscribeTokenRefresh(callback: (token: string) => void) {
    this.refreshSubscribers.push(callback)
  }

  /**
   * 通知所有订阅者 token 已刷新
   */
  private onRefreshed(token: string) {
    this.refreshSubscribers.forEach((callback) => callback(token))
  }

  /**
   * 刷新 access token
   */
  private async refreshToken() {
    const response = await axios.post(
      '/api/api/v1/user/refresh',
      {},
      {
        withCredentials: true, // 让浏览器自动发送所有 cookie，包括 refresh_token
      },
    )
    return response.data
  }

  /**
   * 获取 Axios 实例
   */
  getClient(): AxiosInstance {
    return this.client
  }

  /**
   * 生成 WebSocket 连接 URL
   * @param path WebSocket 路径
   * @returns 完整的 WebSocket URL
   */
  getWebSocketUrl(path: string): string {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = import.meta.env.VITE_WS_HOST || window.location.host
    const token = useAuthStore.getState().accessToken
    return `${wsProtocol}//${wsHost}${path}?token=${token}`
  }
}

export const apiClient = new ApiClient()
export default apiClient.getClient()