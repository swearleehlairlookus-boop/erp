// Maintains all existing interfaces but optimizes for the new database schema

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  pagination?: {
    page: number
    per_page: number
    total: number
    pages: number
  }
}

interface LoginCredentials {
  username: string
  password: string
}

interface User {
  id: number
  name: string
  email: string
}

interface Patient {
  id: number
  name: string
  age: number
}

interface CreatePatientRequest {
  name: string
  age: number
}

interface VitalSignsRequest {
  temperature: string
  heart_rate: string
  blood_pressure: string
}

interface Route {
  id: number
  name: string
}

interface Consumable {
  id: number
  name: string
}

const DEFAULT_REMOTE_API_BASE_URL =
  "https://app-polmed-backend-fmamhma6g4gngfey.southafricanorth-01.azurewebsites.net/api"

class ApiService {
  private token: string | null = null
  private baseUrl: string = DEFAULT_REMOTE_API_BASE_URL

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    // ALWAYS refresh token from localStorage before each request
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("token")
    }

    const url = `${this.baseUrl}${endpoint}`
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    }

    if (options.headers) {
      if (options.headers instanceof Headers) {
        options.headers.forEach((value, key) => {
          headers[key] = value
        })
      } else if (Array.isArray(options.headers)) {
        options.headers.forEach(([key, value]) => {
          headers[key] = value
        })
      } else {
        Object.assign(headers, options.headers as Record<string, string>)
      }
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    console.log(`🚀 API Request: ${options.method || "GET"} ${url}`)

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      let data
      try {
        data = await response.json()
        console.log(`📨 API Response: ${response.status}`, data)
      } catch (e) {
        console.error("❌ Failed to parse JSON response:", e)
        data = { message: response.statusText }
      }

      if (!response.ok) {
        const errorMessage = (data && (data.error || data.message)) || `HTTP ${response.status}: ${response.statusText}`
        console.error(`❌ API Error: ${errorMessage}`)
        return {
          success: false,
          error: errorMessage,
        }
      }

      return {
        success: true,
        data: data.data,
        message: data.message,
        pagination: data.pagination,
      }
    } catch (error) {
      console.error("💥 API Request Error:", error)
      return {
        success: false,
        error: error instanceof Error ? error.message : "Network error occurred",
      }
    }
  }

  // ==================== AUTHENTICATION ====================
  async login(credentials: LoginCredentials): Promise<ApiResponse<{ token: string; user: any }>> {
    const response = await this.request<{ token: string; user: any }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    })

    if (response.success && response.data?.token) {
      this.token = response.data.token
      if (typeof window !== "undefined") {
        localStorage.setItem("token", response.data.token)
        localStorage.setItem("user", JSON.stringify(response.data.user))
      }
    }

    return response
  }

  async logout(): Promise<void> {
    this.token = null
    if (typeof window !== "undefined") {
      localStorage.removeItem("token")
      localStorage.removeItem("user")
    }
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    return this.request<User>("/auth/me")
  }

  // ==================== PATIENT MANAGEMENT ====================
  async getPatients(params?: Record<string, string>): Promise<ApiResponse<Patient[]>> {
    const queryString = params ? `?${new URLSearchParams(params)}` : ""
    return this.request<Patient[]>(`/patients${queryString}`)
  }

  async getPatient(id: number): Promise<ApiResponse<Patient>> {
    return this.request<Patient>(`/patients/${id}`)
  }

  async createPatient(patient: CreatePatientRequest): Promise<ApiResponse<any>> {
    return this.request<any>("/patients", {
      method: "POST",
      body: JSON.stringify(patient),
    })
  }

  async updatePatient(id: number, patient: Partial<Patient>): Promise<ApiResponse<Patient>> {
    return this.request<Patient>(`/patients/${id}`, {
      method: "PUT",
      body: JSON.stringify(patient),
    })
  }

  // ==================== VISITS ====================
  async createVisit(
    patientId: number,
    payload: {
      visit_date?: string
      visit_time?: string
      visit_type?: string
      route_id?: number
      location_id?: number
      location_name?: string
      chief_complaint?: string
    } = {},
  ): Promise<ApiResponse<{ visit_id: number }>> {
    return this.request<{ visit_id: number }>(`/patients/${patientId}/visits`, {
      method: "POST",
      body: JSON.stringify(payload),
    })
  }

  async addVitalSigns(visitId: number, payload: VitalSignsRequest): Promise<ApiResponse<any>> {
    const cleanPayload: Record<string, any> = {}

    for (const [key, value] of Object.entries(payload)) {
      if (value === "" || value === null) {
        cleanPayload[key] = undefined
      } else if (typeof value === "string" && !isNaN(Number(value)) && key !== "nursing_notes") {
        cleanPayload[key] = Number(value)
      } else {
        cleanPayload[key] = value
      }
    }

    return this.request<any>(`/visits/${visitId}/vital-signs`, {
      method: "POST",
      body: JSON.stringify(cleanPayload),
    })
  }

  // ==================== ROUTES ====================
  async getRoutes(params?: Record<string, string>): Promise<ApiResponse<Route[]>> {
    const queryString = params ? `?${new URLSearchParams(params)}` : ""
    return this.request<Route[]>(`/routes${queryString}`)
  }

  async getRoute(id: number): Promise<ApiResponse<Route>> {
    return this.request<Route>(`/routes/${id}`)
  }

  // ==================== DASHBOARD ====================
  async getDashboardStats(): Promise<ApiResponse<any>> {
    return this.request<any>("/dashboard/stats")
  }

  // ==================== HEALTH CHECK ====================
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.request<{ status: string; timestamp: string }>("/health")
  }

  // ==================== UTILITY METHODS ====================
  setToken(token: string): void {
    this.token = token
    if (typeof window !== "undefined") {
      localStorage.setItem("token", token)
    }
  }

  getToken(): string | null {
    return this.token
  }

  clearToken(): void {
    this.token = null
    if (typeof window !== "undefined") {
      localStorage.removeItem("token")
      localStorage.removeItem("user")
    }
  }

  isAuthenticated(): boolean {
    return !!this.token
  }

  getStoredUser(): User | null {
    if (typeof window !== "undefined") {
      const userStr = localStorage.getItem("user")
      return userStr ? JSON.parse(userStr) : null
    }
    return null
  }
}

export const apiService = new ApiService()
