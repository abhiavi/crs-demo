import { create } from 'zustand';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import DemandPlannerView from './views/DemandPlanner/index';
import ExecutiveView from './views/Executive/index';
import DistributorView from './views/Distributor/index';
import CreditAdminView from './views/CreditAdmin/index';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route
            path="/planner"
            element={
              <RequireAuth persona="Demand Planner">
                <DemandPlannerView />
              </RequireAuth>
            }
          />
          <Route
            path="/executive"
            element={
              <RequireAuth persona="Sales / Executive">
                <ExecutiveView />
              </RequireAuth>
            }
          />
          <Route
            path="/distributor"
            element={
              <RequireAuth persona="Distributor Portal">
                <DistributorView />
              </RequireAuth>
            }
          />
          <Route
            path="/credit"
            element={
              <RequireAuth persona="Credit Admin">
                <CreditAdminView />
              </RequireAuth>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function RequireAuth({ children, persona }: { children: React.ReactNode; persona: string }) {
  const { persona: currentPersona } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  if (!currentPersona) {
    navigate('/login', { replace: true, state: { from: location } });
    return null;
  }

  if (currentPersona !== persona) {
    navigate('/login', { replace: true });
    return null;
  }

  return children;
}

function LoginPage() {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  const handleLogin = (token: string, persona: string) => {
    setAuth(token, persona);
    navigate(from, { replace: true });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-blue-700">CRS Demo</h1>
          <p className="mt-2 text-lg text-gray-600">
            Autonomous Continuous Replenishment System
          </p>
          <p className="mt-1 text-sm text-gray-500">
            FMCG beverages VMI demo
          </p>
        </div>
        <div className="space-y-4">
          <button
            onClick={() => handleLogin('demo-planner', 'Demand Planner')}
            className="w-full px-4 py-3 bg-blue-700 text-white font-medium rounded-lg hover:bg-blue-800 transition-colors"
          >
            Demand Planner
          </button>
          <button
            onClick={() => handleLogin('demo-executive', 'Sales / Executive')}
            className="w-full px-4 py-3 bg-blue-700 text-white font-medium rounded-lg hover:bg-blue-800 transition-colors"
          >
            Sales / Executive
          </button>
          <button
            onClick={() => handleLogin('demo-distributor', 'Distributor Portal')}
            className="w-full px-4 py-3 bg-blue-700 text-white font-medium rounded-lg hover:bg-blue-800 transition-colors"
          >
            Distributor Portal
          </button>
          <button
            onClick={() => handleLogin('demo-credit_admin', 'Credit Admin')}
            className="w-full px-4 py-3 bg-blue-700 text-white font-medium rounded-lg hover:bg-blue-800 transition-colors"
          >
            Credit Admin
          </button>
        </div>
      </div>
    </div>
  );
}

function TopNav() {
  const { persona, logout } = useAuthStore();
  const navigate = useNavigate();

  return (
    <nav className="bg-blue-700 text-white px-4 py-3 flex items-center justify-between shadow-md">
      <div className="flex items-center space-x-3">
        <span className="text-xl font-bold">CRS Demo</span>
        <span className="bg-blue-600 px-2 py-1 rounded text-sm">{persona}</span>
      </div>
      <button
        onClick={() => {
          logout();
          navigate('/login');
        }}
        className="hover:bg-blue-600 transition-colors px-3 py-1 rounded"
      >
        Logout
      </button>
    </nav>
  );
}

function AppWithNav() {
  const { persona } = useAuthStore();
  return (
    <>
      {persona && <TopNav />}
      <main className="min-h-[calc(100vh-64px)] p-4">
        <Outlet />
      </main>
    </>
  );
}

// Update Routes to use AppWithNav for protected routes
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route
            element={
              <RequireAuth>
                <AppWithNav />
              </RequireAuth>
            }
          >
            <Route path="/planner" element={<DemandPlannerView />} />
            <Route path="/executive" element={<ExecutiveView />} />
            <Route path="/distributor" element={<DistributorView />} />
            <Route path="/credit" element={<CreditAdminView />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;