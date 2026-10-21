
// frontend/src/components/profile/Profile.jsx
import React, { lazy, Suspense } from 'react';
import { Box, Container, Typography, Paper, CircularProgress, Alert, Snackbar } from '@mui/material';
import { useProfile } from '../../hooks/useProfile';
import ProfileHeader from './ProfileHeader';

// Lazy load sections for better performance
const EducationTab = lazy(() => import('./EducationTab'));
const ExperienceTab = lazy(() => import('./ExperienceTab'));
const ProjectsTab = lazy(() => import('./ProjectsTab'));
const CertificationsTab = lazy(() => import('./CertificationsTab'));
const LanguagesTab = lazy(() => import('./LanguagesTab'));

const Profile = () => {
  const {
    profile,
    profileLoading,
    updateProfile,
    isUpdatingProfile,
    educations,
    experiences,
    projects,
    certifications,
    languages,
    successMessage,
    errorMessage,
    clearMessages,
  } = useProfile();

  if (profileLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading profile...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* Profile Header Card */}
      <Paper sx={{ p: 1, bgcolor: 'black' }}>
        <ProfileHeader profile={profile} onUpdate={updateProfile} isUpdating={isUpdatingProfile} />
      </Paper>

      {/* All profile sections on one page (BasicInfo comes from ProfileHeader modal) */}
      <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Suspense
          fallback={
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          }
        >
          <EducationTab educations={educations} />
          <ExperienceTab experiences={experiences} />
          <ProjectsTab projects={projects} />
          <CertificationsTab certifications={certifications} />
          <LanguagesTab languages={languages} />
        </Suspense>
      </Box>

      {/* Success Snackbar */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={4000}
        onClose={clearMessages}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="success" onClose={clearMessages} variant="filled">
          {successMessage}
        </Alert>
      </Snackbar>

      {/* Error Snackbar */}
      <Snackbar
        open={!!errorMessage}
        autoHideDuration={6000}
        onClose={clearMessages}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="error" onClose={clearMessages} variant="filled">
          {errorMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Profile;

