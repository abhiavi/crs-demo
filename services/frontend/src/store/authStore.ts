import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Persona = 'planner' | 'executive' | 'distributor' | 'credit_admin'

interface AuthState {
  token: string | null
  persona: Persona | null
  tenantId: string | null
  setAuth: (token: string, persona: Persona, tenantId?: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      persona: null,
      tenantId: null,
      setAuth: (token, persona, tenantId = 'DIST-AU-SYD') =>
        set({ token, persona, tenantId }),
      logout: () => set({ token: null, persona: null, tenantId: null }),
    }),
    { name: 'crs-auth' }
  )
)
