
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import { AuthProvider } from './contexts/AuthContext.jsx';
import { JobProvider } from './contexts/JobContext.jsx';
import { QueueProvider } from './contexts/QueueContext.jsx';

import Layout from './components/common/Layout.jsx';
import Login from './components/auth/Login.jsx';
import Register from './components/auth/Register.jsx';
import ForgotPassword from './components/auth/ForgotPassword.jsx';
import Dashboard from './components/dashboard/Dashboard.jsx';
import JobScout from './components/jobs/JobScout.jsx';
import Applications from './components/applications/Applications.jsx';
import JobDetailPage from './components/jobs/JobDetailPage';
import ProtectedRoute from './components/common/ProtectedRoute.jsx';
import Settings from './components/settings/Settings.jsx';
import Profile from './components/profile/Profile.jsx';
import UploadResume from './components/auth/uploadresume.jsx';


function App() {
  return (
    <Router>
      <AuthProvider>
        <JobProvider>
          <QueueProvider>
          <Routes>
             
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/upload-resume" element= {<UploadResume />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
               
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/jobs" element={<JobScout />} />
                <Route path="/jobs/:jobId" element={<JobDetailPage />} />
                <Route path="/applications" element={<Applications />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/profile" element={<Profile />} />
                
              </Route>
            </Route>
          </Routes>
          </QueueProvider>
        </JobProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;

