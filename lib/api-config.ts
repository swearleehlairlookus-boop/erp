// API Configuration and constants for new backend v2.0

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000/api"

export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: "/auth/login",
    LOGOUT: "/auth/logout",
    ME: "/auth/me",
    REFRESH: "/auth/refresh",
  },

  // Patients
  PATIENTS: {
    LIST: "/patients",
    CREATE: "/patients",
    GET: (id: number) => `/patients/${id}`,
    UPDATE: (id: number) => `/patients/${id}`,
    DELETE: (id: number) => `/patients/${id}`,
    SEARCH_MEMBER: (medicalAidNumber: string) => `/patients/search-member/${medicalAidNumber}`,
  },

  // Visits
  VISITS: {
    CREATE: (patientId: number) => `/patients/${patientId}/visits`,
    GET: (id: number) => `/visits/${id}`,
    VITALS: (visitId: number) => `/visits/${visitId}/vital-signs`,
    WORKFLOW: (visitId: number) => `/visits/${visitId}/workflow/status`,
    NOTES: (visitId: number) => `/visits/${visitId}/clinical-notes`,
  },

  // Routes
  ROUTES: {
    LIST: "/routes",
    CREATE: "/routes",
    GET: (id: number) => `/routes/${id}`,
    UPDATE: (id: number) => `/routes/${id}`,
    DELETE: (id: number) => `/routes/${id}`,
  },

  // Appointments
  APPOINTMENTS: {
    LIST: "/appointments",
    CREATE: "/appointments",
    GET: (id: number) => `/appointments/${id}`,
    UPDATE: (id: number) => `/appointments/${id}`,
    CANCEL: (id: number) => `/appointments/${id}/cancel`,
    AVAILABLE: "/appointments/available",
  },

  // Inventory
  INVENTORY: {
    ASSETS: {
      LIST: "/inventory/assets",
      CREATE: "/inventory/assets",
      GET: (id: number) => `/inventory/assets/${id}`,
      UPDATE: (id: number) => `/inventory/assets/${id}`,
      CATEGORIES: "/inventory/asset-categories",
    },
    CONSUMABLES: {
      LIST: "/inventory/consumables",
      CREATE: "/inventory/consumables",
      GET: (id: number) => `/inventory/consumables/${id}`,
      UPDATE: (id: number) => `/inventory/consumables/${id}`,
      CATEGORIES: "/inventory/consumable-categories",
    },
    SUPPLIERS: {
      LIST: "/inventory/suppliers",
      CREATE: "/inventory/suppliers",
      GET: (id: number) => `/inventory/suppliers/${id}`,
      UPDATE: (id: number) => `/inventory/suppliers/${id}`,
    },
    STOCK: {
      RECEIVE: "/inventory/stock/receive",
      ADJUST: (stockId: number) => `/inventory/stock/${stockId}/adjust`,
      ALERTS: "/inventory/alerts/stock",
      EXPIRY: "/inventory/alerts/expiry",
    },
  },

  // Clinical
  CLINICAL: {
    NOTES: (visitId: number) => `/visits/${visitId}/clinical-notes`,
    REFERRALS: (patientId: number) => `/patients/${patientId}/referrals`,
  },

  // Dashboard
  DASHBOARD: {
    STATS: "/dashboard/stats",
  },

  // Users
  USERS: {
    LIST: "/users",
    CREATE: "/users",
    GET: (id: number) => `/users/${id}`,
    UPDATE: (id: number) => `/users/${id}`,
    DELETE: (id: number) => `/users/${id}`,
  },

  // Health
  HEALTH: "/health",
}

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE: 422,
  SERVER_ERROR: 500,
}
