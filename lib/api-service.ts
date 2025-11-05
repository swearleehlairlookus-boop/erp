// --- Asset Maintenance Types ---
export interface AssetMaintenance {
  id: number;
  asset_id: number;
  maintenance_type: string;
  description?: string;
  performed_by?: string;
  performed_at?: string;
  next_due?: string;
  cost?: number;
  created_at?: string;
  updated_at?: string;
}


// --- API Response Wrapper ---
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// --- Auth Types ---
export interface LoginCredentials {
  username: string;
  password: string;
}

// --- User Types ---
export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  [key: string]: any;
}

// --- Patient Types ---
export interface Patient {
  id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  [key: string]: any;
}

// --- Visit Types ---
export interface Visit {
  id: number;
  patient_id: number;
  visit_date: string;
  [key: string]: any;
}

// --- Route Types ---
export interface Route {
  id: number;
  route_name: string;
  [key: string]: any;
}

// --- Asset Types ---
export interface Asset {
  id: number;
  asset_tag: string;
  asset_name: string;
  serial_number: string;
  status: string;
  [key: string]: any;
}

// --- Consumable Types ---
export interface Consumable {
  id: number;
  item_code: string;
  item_name: string;
  category_name?: string;
  total_in_stock?: number;
  total_received?: number;
  total_used?: number;
  next_expiry?: string;
  [key: string]: any;
}

// --- Supplier Types ---
export interface Supplier {
  id: number;
  supplier_name: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  address?: string;
  tax_number?: string;
  is_active?: boolean;
  [key: string]: any;
}

// --- Inventory Stock Receipt ---
export interface StockReceiptRequest {
  consumable_id: number;
  batch_number: string;
  quantity_received: number;
  unit_cost?: number;
  supplier_id?: number;
  received_date?: string;
  expiry_date?: string;
  [key: string]: any;
}

// --- Inventory Usage ---
export interface InventoryUsageRequest {
  consumable_id: number;
  stock_id?: number;
  quantity_used: number;
  usage_reason: string;
  notes?: string;
  used_by?: number;
  usage_date?: string;
  [key: string]: any;
}

const DEFAULT_API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api"

class ApiService {
  // ==================== ASSET MAINTENANCE ====================
  async getAssetMaintenance(assetId: number): Promise<ApiResponse<AssetMaintenance[]>> {
    return this.request<AssetMaintenance[]>(`/inventory/assets/${assetId}/maintenance`)
  }

  async createAssetMaintenance(assetId: number, data: {
    maintenance_type: string;
    description?: string;
    performed_by?: string;
    performed_at?: string;
    next_due?: string;
    cost?: number;
  }): Promise<ApiResponse<AssetMaintenance>> {
    return this.request<AssetMaintenance>(`/inventory/assets/${assetId}/maintenance`, {
      method: "POST",
      body: JSON.stringify(data),
    })
  }
  async updateAssetMaintenance(id: number, maintenance: { last_maintenance_date?: string; next_maintenance_date?: string; maintenance_notes?: string }): Promise<ApiResponse<any>> {
    return this.request<any>(`/inventory/assets/${id}/maintenance`, {
      method: "PUT",
      body: JSON.stringify(maintenance),
    })
  }
  private baseUrl: string
  private token: string | null = null

  constructor() {
    this.baseUrl = DEFAULT_API_BASE_URL.replace(/\/$/, "")
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("token")
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    // Refresh token before each request
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("token")
    }

    const url = `${this.baseUrl}${endpoint}`
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`
    }

    console.log(`[v0] API Request: ${options.method || "GET"} ${url}`)

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      let data: any
      try {
        data = await response.json()
      } catch (e) {
        data = { message: response.statusText }
      }

      console.log(`[v0] API Response: ${response.status}`, data)

      if (!response.ok) {
        return {
          success: false,
          error: data?.error || data?.message || `HTTP ${response.status}`,
        }
      }

      return {
        success: true,
        data: data.data || data,
        message: data.message,
      }
    } catch (error) {
      console.error("[v0] API Error:", error)
      return {
        success: false,
        error: error instanceof Error ? error.message : "Network error",
      }
    }
  }

  // ==================== AUTHENTICATION ====================
  async login(credentials: LoginCredentials): Promise<ApiResponse<{ token: string; user: User }>> {
    const response = await this.request<{ token: string; user: User }>("/auth/login", {
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
  async getPatients(): Promise<ApiResponse<Patient[]>> {
    return this.request<Patient[]>("/patients")
  }

  async getPatient(id: number): Promise<ApiResponse<Patient>> {
    return this.request<Patient>(`/patients/${id}`)
  }

  async createPatient(patient: Partial<Patient>): Promise<ApiResponse<Patient>> {
    return this.request<Patient>("/patients", {
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

  async searchMember(medicalAidNumber: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/patients/search-member/${medicalAidNumber}`)
  }

  // ==================== VISITS ====================
  async createVisit(patientId: number, payload: any): Promise<ApiResponse<Visit>> {
    return this.request<Visit>(`/patients/${patientId}/visits`, {
      method: "POST",
      body: JSON.stringify(payload),
    })
  }

  async getVisit(visitId: number): Promise<ApiResponse<Visit>> {
    return this.request<Visit>(`/visits/${visitId}`)
  }

  async addVitalSigns(visitId: number, vitals: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/visits/${visitId}/vital-signs`, {
      method: "POST",
      body: JSON.stringify(vitals),
    })
  }

  async getVisitVitals(visitId: number): Promise<ApiResponse<any>> {
    return this.request<any>(`/visits/${visitId}/vital-signs`)
  }

  // ==================== ROUTES ====================
  async getRoutes(): Promise<ApiResponse<Route[]>> {
    return this.request<Route[]>("/routes")
  }

  async getRoute(id: number): Promise<ApiResponse<Route>> {
    return this.request<Route>(`/routes/${id}`)
  }

  async createRoute(route: Partial<Route>): Promise<ApiResponse<Route>> {
    return this.request<Route>("/routes", {
      method: "POST",
      body: JSON.stringify(route),
    })
  }

  async updateRoute(id: number, route: Partial<Route>): Promise<ApiResponse<Route>> {
    return this.request<Route>(`/routes/${id}`, {
      method: "PUT",
      body: JSON.stringify(route),
    })
  }

  async deleteRoute(id: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/routes/${id}`, {
      method: "DELETE",
    })
  }

  // ==================== APPOINTMENTS ====================
  async getAppointments(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>("/appointments")
  }

  async bookAppointment(payload: any): Promise<ApiResponse<any>> {
    return this.request<any>("/appointments", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  }

  async getAvailableAppointments(params?: any): Promise<ApiResponse<any[]>> {
    const qs = params ? `?${new URLSearchParams(params).toString()}` : ""
    return this.request<any[]>(`/appointments/available${qs}`)
  }

  async updateAppointment(id: number, payload: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/appointments/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    })
  }

  async cancelAppointment(id: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/appointments/${id}/cancel`, {
      method: "POST",
    })
  }

  // ==================== INVENTORY MANAGEMENT ====================
  async getAssets(): Promise<ApiResponse<Asset[]>> {
    return this.request<Asset[]>("/inventory/assets")
  }

  async createAsset(asset: Partial<Asset>): Promise<ApiResponse<Asset>> {
    return this.request<Asset>("/inventory/assets", {
      method: "POST",
      body: JSON.stringify(asset),
    })
  }


  async updateAsset(id: number, asset: Partial<Asset>): Promise<ApiResponse<Asset>> {
    return this.request<Asset>(`/inventory/assets/${id}`, {
      method: "PUT",
      body: JSON.stringify(asset),
    })
  }

  async updateAssetStatus(id: number, statusPayload: { status: string; notes?: string }): Promise<ApiResponse<any>> {
    return this.request<any>(`/inventory/assets/${id}/status`, {
      method: "PUT",
      body: JSON.stringify(statusPayload),
    })
  }

  async getAssetCategories(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>("/inventory/asset-categories")
  }

  async getConsumables(): Promise<ApiResponse<Consumable[]>> {
    const response: any = await this.request<any>("/inventory/consumables")
    if (response && response.success && Array.isArray(response["consumables"])) {
      return { ...response, data: response["consumables"] }
    }
    return response
  }

  async createConsumable(consumable: Partial<Consumable>): Promise<ApiResponse<Consumable>> {
    return this.request<Consumable>("/inventory/consumables", {
      method: "POST",
      body: JSON.stringify(consumable),
    })
  }

  async updateConsumable(id: number, consumable: Partial<Consumable>): Promise<ApiResponse<Consumable>> {
    return this.request<Consumable>(`/inventory/consumables/${id}`, {
      method: "PUT",
      body: JSON.stringify(consumable),
    })
  }

  async getConsumableCategories(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>("/inventory/consumable-categories")
  }

  async getSuppliers(params?: Record<string, string | number | boolean>): Promise<ApiResponse<Supplier[]>> {
    const query = params
      ? `?${new URLSearchParams(
          Object.entries(params).reduce<Record<string, string>>((acc, [key, value]) => {
            acc[key] = String(value)
            return acc
          }, {})
        ).toString()}`
      : ""

    return this.request<Supplier[]>(`/inventory/suppliers${query}`)
  }

  async createSupplier(supplier: {
    supplier_name: string
    contact_person?: string
    phone?: string
    email?: string
    address?: string
    tax_number?: string
    is_active?: boolean
  }): Promise<ApiResponse<any>> {
    const payload = {
      name: supplier.supplier_name,
      contact_person: supplier.contact_person,
      phone: supplier.phone,
      email: supplier.email,
      address: supplier.address,
      tax_number: supplier.tax_number,
      is_active: supplier.is_active ?? true,
    }

    return this.request<any>("/inventory/suppliers", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  }

  async receiveInventoryStock(payload: StockReceiptRequest): Promise<ApiResponse<any>> {
    return this.request<any>("/inventory/stock/receive", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  }

  async adjustInventoryStock(stockId: number, payload: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/inventory/stock/${stockId}/adjust`, {
      method: "POST",
      body: JSON.stringify(payload),
    })
  }

  async getExpiryAlerts(daysAhead = 90): Promise<ApiResponse<any[]>> {
    return this.request<any[]>(`/inventory/alerts/expiry?days_ahead=${daysAhead}`)
  }

  async getStockAlerts(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>("/inventory/alerts/stock")
  }

  async recordInventoryUsage(payload: InventoryUsageRequest): Promise<ApiResponse<any>> {
    return this.request<any>("/inventory/stock/usage", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  }

  // ==================== CLINICAL WORKFLOW ====================
  async getWorkflowStatus(visitId: number): Promise<ApiResponse<any>> {
    return this.request<any>(`/visits/${visitId}/workflow/status`)
  }

  async getClinicalNotes(visitId: number): Promise<ApiResponse<any[]>> {
    return this.request<any[]>(`/visits/${visitId}/clinical-notes`)
  }

  async createClinicalNote(visitId: number, payload: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/visits/${visitId}/clinical-notes`, {
      method: "POST",
      body: JSON.stringify(payload),
    })
  }

  async createReferral(patientId: number, payload: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/patients/${patientId}/referrals`, {
      method: "POST",
      body: JSON.stringify(payload),
    })
  }

  async getReferrals(patientId: number): Promise<ApiResponse<any[]>> {
    return this.request<any[]>(`/patients/${patientId}/referrals`)
  }

  // ==================== DASHBOARD & ANALYTICS ====================
  async getDashboardStats(): Promise<ApiResponse<any>> {
    return this.request<any>("/dashboard/stats")
  }

  // ==================== USER MANAGEMENT ====================
  async getUsers(): Promise<ApiResponse<User[]>> {
    return this.request<User[]>("/users")
  }

  async createUser(user: Partial<User>): Promise<ApiResponse<User>> {
    return this.request<User>("/users", {
      method: "POST",
      body: JSON.stringify(user),
    })
  }

  async updateUser(id: number, user: Partial<User>): Promise<ApiResponse<User>> {
    return this.request<User>(`/users/${id}`, {
      method: "PUT",
      body: JSON.stringify(user),
    })
  }

  async deleteUser(id: number): Promise<ApiResponse<void>> {
    return this.request<void>(`/users/${id}`, {
      method: "DELETE",
    })
  }

  // ==================== HEALTH CHECK ====================
  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.request<{ status: string }>("/health")
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
