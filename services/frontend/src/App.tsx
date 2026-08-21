import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Routes, Route, Navigate, useNavigate, useLocation, Outlet } from 'react-router-dom'
import { useAuthStore, type Persona } from './store/authStore'
import DemandPlannerView from './views/DemandPlanner/index'
import ExecutiveView from './views/Executive/index'
import DistributorView from './views/Distributor/index'
import CreditAdminView from './views/CreditAdmin/index'

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 5 * 60 * 1000 } } })

const PERSONA_ROUTES: Record<Persona, string> = {
  planner: '/planner',
  executive: '/executive',
  distributor: '/distributor',
  credit_admin: '/credit',
}

const PERSONA_LABELS: Record<Persona, string> = {
  planner: 'Demand Planner',
  executive: 'Sales / Executive',
  distributor: 'Distributor Portal',
  credit_admin: 'Credit Admin',
}

function TopNav() {
  const { persona, logout } = useAuthStore()
  const navigate = useNavigate()
  return (
    <nav className="bg-blue-700 text-white px-6 py-3 flex items-center justify-between shadow-md">
      <div className="flex items-center gap-3">
        <span className="text-xl font-bold tracking-tight">CRS Demo</span>
        <span className="bg-blue-500 px-3 py-0.5 rounded-full text-sm font-medium">
          {persona ? PERSONA_LABELS[persona] : ''}
        </span>
      </div>
      <button
        onClick={() => { logout(); navigate('/login') }}
        className="px-3 py-1.5 text-sm rounded hover:bg-blue-600 transition-colors"
      >
        Logout
      </button>
    </nav>
  )
}

function RequireAuth() {
  const { token } = useAuthStore()
  const location = useLocation()
  if (!token) return <Navigate to="/login" state={{ from: location }} replace />
  return (
    <>
      <TopNav />
      <main className="min-h-[calc(100vh-52px)]">
        <Outlet />
      </main>
    </>
  )
}

function LoginPage() {
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/planner'

  const login = (persona: Persona) => {
    setAuth(`demo-${persona}`, persona)
    navigate(PERSONA_ROUTES[persona])
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center p-6">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-2xl p-8 space-y-6">
        <div className="text-center">
          <div className="inline-block bg-blue-700 text-white text-xs font-semibold px-3 py-1 rounded-full mb-3">
            FMCG Beverages · Australia
          </div>
          <h1 className="text-3xl font-bold text-gray-900">CRS Demo</h1>
          <p className="mt-1 text-gray-500 text-sm">Autonomous Continuous Replenishment System</p>
          <p className="mt-3 text-xs text-gray-400 max-w-xs mx-auto">
            Vendor-Managed Inventory · OR-Tools MILP · Temporal.io Saga · TFT Forecasting
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {([
            ['planner', 'Demand Planner', 'Exception triage · Forecast bands · TFT attention'],
            ['executive', 'Sales / Executive', 'S&OP simulator · Network DOS health'],
            ['distributor', 'Distributor Portal', 'In-transit tracking · DOS projection'],
            ['credit_admin', 'Credit Admin', 'Credit utilization · OR-Tools output'],
          ] as const).map(([persona, label, desc]) => (
            <button key={persona} onClick={() => login(persona)}
              className="p-4 border-2 border-gray-200 rounded-xl text-left hover:border-blue-500 hover:bg-blue-50 transition-all group">
              <div className="font-semibold text-gray-800 group-hover:text-blue-700 text-sm">{label}</div>
              <div className="text-xs text-gray-400 mt-1 leading-snug">{desc}</div>
            </button>
          ))}
        </div>

        <p className="text-center text-xs text-gray-400">
          5 AU distributors · 30 beverage SKUs · 52 weeks synthetic history
        </p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route element={<RequireAuth />}>
          <Route path="/planner" element={<DemandPlannerView />} />
          <Route path="/executive" element={<ExecutiveView />} />
          <Route path="/distributor" element={<DistributorView />} />
          <Route path="/credit" element={<CreditAdminView />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </QueryClientProvider>
  )
}
