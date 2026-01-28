import api from './api'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserInfo {
  username: string
  email: string
  groups: string[]
}

export interface UpdateUsernameRequest {
  username: string
}

export interface UpdateEmailRequest {
  email: string
}

export interface UpdatePasswordRequest {
  password: string
}

// User registration
export const register = async (data: RegisterRequest): Promise<TokenResponse> => {
  const response = await api.post<TokenResponse>('/api/v1/user/register', data)
  return response.data
}

// User login
export const login = async (data: LoginRequest): Promise<TokenResponse> => {
  const response = await api.post<TokenResponse>('/api/v1/user/login', data)
  return response.data
}

// Token refresh is handled automatically by the interceptor in api.ts

// Get current user information
export const getCurrentUser = async (): Promise<UserInfo> => {
  const response = await api.get<UserInfo>('/api/v1/user/me')
  return response.data
}

// Update username
export const updateUsername = async (data: UpdateUsernameRequest): Promise<void> => {
  await api.post('/api/v1/user/me/username', data)
}

// Update email
export const updateEmail = async (data: UpdateEmailRequest): Promise<TokenResponse> => {
  const response = await api.post<TokenResponse>('/api/v1/user/me/email', data)
  return response.data
}

// Update password
export const updatePassword = async (data: UpdatePasswordRequest): Promise<TokenResponse> => {
  const response = await api.post<TokenResponse>('/api/v1/user/me/password', data)
  return response.data
}

// User logout
export const logout = async (): Promise<void> => {
  await api.post('/api/v1/user/logout')
}