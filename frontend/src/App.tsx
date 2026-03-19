import { Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import Layout from '@/components/layout/Layout';
import Dashboard from '@/views/dashboard/Dashboard';
import ArrayMap from '@/views/array-map/ArrayMap';
import DefectLog from '@/views/defect-log/DefectLog';
import ModuleInspector from '@/views/module-inspector/ModuleInspector';
import ComparisonView from '@/views/comparison/ComparisonView';
import ReportBuilder from '@/views/report-builder/ReportBuilder';
import FlightPlanner from '@/views/flight-planner/FlightPlanner';
import Login from '@/views/auth/Login';
import SolarThermalInspector from '@/views/dashboard/SolarThermalInspector';

function App() {
  const { fetchUser, isAuthenticated } = useAuthStore();

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // DEMO MODE: Allow access without authentication
  // Remove this condition for production
  const isDemoMode = true;

  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={isAuthenticated && !isDemoMode ? <Navigate to="/" /> : <Login />}
      />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          (isAuthenticated || isDemoMode) ? (
            <Layout />
          ) : (
            <Navigate to="/login" />
          )
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="map" element={<ArrayMap />} />
        <Route path="defects" element={<DefectLog />} />
        <Route path="modules/:moduleId" element={<ModuleInspector />} />
        <Route path="comparison" element={<ComparisonView />} />
        <Route path="reports" element={<ReportBuilder />} />
        <Route path="flight-planner" element={<FlightPlanner />} />
        <Route path="inspector" element={<SolarThermalInspector />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
