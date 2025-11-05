# POLMED Frontend-Backend Integration Guide

## Overview

The new modular backend is fully RESTful and ready for frontend integration. All endpoints follow REST principles and return consistent JSON responses.

---

## Setting Up Frontend API Calls

### Base URL
\`\`\`typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
\`\`\`

### Environment Variables (.env)
\`\`\`env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_JWT_STORAGE_KEY=polmed_jwt_token
\`\`\`

---

## Frontend API Service Example

### Authentication Service

\`\`\`typescript
// services/authService.ts
export const authService = {
  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    if (data.success) {
      localStorage.setItem('token', data.data.token);
    }
    return data;
  },

  async getCurrentUser() {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  },

  async logout() {
    const token = localStorage.getItem('token');
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    localStorage.removeItem('token');
  }
};
\`\`\`

### Patient Service

\`\`\`typescript
// services/patientService.ts
export const patientService = {
  async getPatients(page = 1, search = '') {
    const token = localStorage.getItem('token');
    const response = await fetch(
      `${API_BASE_URL}/patients?page=${page}&search=${search}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    return response.json();
  },

  async createPatient(patientData: any) {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/patients`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(patientData)
    });
    return response.json();
  },

  async getPatient(patientId: number) {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/patients/${patientId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  }
};
\`\`\`

---

## Endpoint Integration Checklist

### Authentication Endpoints
- [ ] Login endpoint integrated
- [ ] Token stored in localStorage/secure storage
- [ ] Token included in all requests
- [ ] Logout functionality implemented
- [ ] Token refresh handling

### Patient Management
- [ ] Patient list page integrated
- [ ] Patient search/filter implemented
- [ ] Patient creation form integrated
- [ ] Patient detail view implemented
- [ ] Patient update functionality

### Clinical Workflow
- [ ] Visit creation form
- [ ] Vital signs input form
- [ ] Clinical notes editor
- [ ] Referral creation form
- [ ] Visit history display

### Inventory Management
- [ ] Asset list page
- [ ] Stock tracking page
- [ ] Inventory alerts display
- [ ] Stock usage recording

### Routes & Appointments
- [ ] Route planning interface
- [ ] Appointment booking form
- [ ] Availability checking
- [ ] Location management

---

## Example Frontend Integration

### Login Page Integration

\`\`\`typescript
// pages/login.tsx
import { useState } from 'react';
import { authService } from '../services/authService';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await authService.login(email, password);
      if (result.success) {
        window.location.href = '/dashboard';
      } else {
        setError(result.error);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input 
        type="email" 
        value={email} 
        onChange={(e) => setEmail(e.target.value)} 
        placeholder="Email"
        required 
      />
      <input 
        type="password" 
        value={password} 
        onChange={(e) => setPassword(e.target.value)} 
        placeholder="Password"
        required 
      />
      {error && <p style={{color: 'red'}}>{error}</p>}
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
\`\`\`

### Patient List Integration

\`\`\`typescript
// pages/patients.tsx
import { useState, useEffect } from 'react';
import { patientService } from '../services/patientService';

export default function PatientsPage() {
  const [patients, setPatients] = useState([]);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPatients();
  }, [page, search]);

  const loadPatients = async () => {
    setLoading(true);
    const result = await patientService.getPatients(page, search);
    if (result.success) {
      setPatients(result.data);
    }
    setLoading(false);
  };

  return (
    <div>
      <h1>Patients</h1>
      <input 
        type="text" 
        placeholder="Search patients..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
      />
      
      {loading ? (
        <p>Loading...</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Phone</th>
              <th>Medical Aid</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((patient: any) => (
              <tr key={patient.id}>
                <td>{patient.first_name} {patient.last_name}</td>
                <td>{patient.phone_number}</td>
                <td>{patient.medical_aid_number}</td>
                <td>
                  <a href={`/patients/${patient.id}`}>View</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
\`\`\`

---

## CORS Configuration

If frontend and backend are on different domains, add CORS support:

\`\`\`python
# In main Flask app
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "https://yourdomain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
\`\`\`

---

## Testing Backend Locally

### Using cURL

\`\`\`bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@polmed.org","password":"password123"}'

# Get patients (replace TOKEN with JWT token)
curl http://localhost:5000/api/patients \
  -H "Authorization: Bearer TOKEN"

# Create patient
curl -X POST http://localhost:5000/api/patients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "first_name":"John",
    "last_name":"Doe",
    "date_of_birth":"1990-01-01",
    "gender":"Male",
    "phone_number":"0791234567"
  }'
\`\`\`

---

## Common Integration Issues

### Token Not Included in Requests
**Solution:** Ensure every API request includes the Authorization header with the JWT token.

### CORS Errors
**Solution:** Add CORS configuration to Flask app or use proxy in development.

### 401 Unauthorized
**Solution:** Token may be expired. Re-login to get a new token.

### 403 Forbidden
**Solution:** User role doesn't have permission. Check user role and endpoint requirements.

---

## Performance Optimization

1. **Pagination:** Always use pagination for list endpoints
2. **Caching:** Cache patient data locally when appropriate
3. **Lazy Loading:** Load clinical notes only when needed
4. **Debouncing:** Debounce search input to reduce API calls

---

## Security Best Practices

1. Store JWT tokens securely (HttpOnly cookies recommended)
2. Always use HTTPS in production
3. Validate input on both frontend and backend
4. Never expose sensitive data in local storage
5. Implement token refresh logic
6. Set appropriate CORS headers
7. Use Content Security Policy headers

---

**Integration Status:** Ready for Development  
**Last Updated:** November 3, 2025
