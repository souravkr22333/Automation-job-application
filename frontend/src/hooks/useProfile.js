// frontend/src/hooks/useProfile.js
import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { profileService } from '../services/userdata';

export const useProfile = () => {
  const queryClient = useQueryClient();
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Single combined query for profile data
  const {
    data: profileData,
    isLoading: profileLoading,
    refetch: refetchProfile,
  } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const response = await profileService.getCompleteProfile();
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: true,
  });

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: profileService.updateProfile,
    onSuccess: (data) => {
      queryClient.setQueryData(['profile'], data);
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      setSuccessMessage('Profile updated successfully');
    },
    onError: (error) => {
      const payload = error?.response?.data;
      console.error('updateProfile failed:', payload);
      const msg =
        payload?.message ||
        payload?.errors?.[0] ||
        payload?.errors ||
        'Failed to update profile';
      setErrorMessage(
        typeof msg === 'string' ? msg : JSON.stringify(msg)
      );
    },
  });

  // Clear messages
  const clearMessages = useCallback(() => {
    setSuccessMessage('');
    setErrorMessage('');
  }, []);

  const completeProfileResponse = profileData?.data;

  // Backend returns: { status: 'success', data: <user payload>, ... }
  // But since we call axios.get and return response.data from the service,
  // profileData?.data here is already the top-level response.
  // CompleteProfileView wraps the serializer under `data`, so we handle:
  // - wrapped: { status, data: { user fields + educations/... } }
  // - unwrapped: { educations: [...], experiences: [...], ... } (if you ever change backend)
  const completeProfile = completeProfileResponse?.data ?? completeProfileResponse;

  const profile = completeProfile ?? {};


  const sectionLoading = profileLoading;

  // For now, the section components expect CRUD handlers and per-section loading flags.
  // Implement lightweight CRUD mutations that update the backend and then invalidate/refetch
  // the single `['profile']` query so all sections refresh from the complete payload.
  const createEducationMutation = useMutation({
    mutationFn: (payload) => profileService.createEducation(payload),
    onSuccess: async () => {
      // Force immediate refetch so UI updates right after the edit
      await queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.refetchQueries({ queryKey: ['profile'] });
    },
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to create education'),
  });

  const updateEducationMutation = useMutation({
    mutationFn: ({ id, data }) => profileService.updateEducation(id, data),
    onSuccess: () => {
      // refresh complete userdata after any section update
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to update education'),
  });

  const deleteEducationMutation = useMutation({
    mutationFn: (id) => profileService.deleteEducation(id),
    onSuccess: () => {
      // refresh complete userdata after any section update
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to delete education'),
  });

  const createExperienceMutation = useMutation({
    mutationFn: (payload) => profileService.createExperience(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to create experience'),
  });

  const updateExperienceMutation = useMutation({
    mutationFn: ({ id, data }) => profileService.updateExperience(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to update experience'),
  });

  const deleteExperienceMutation = useMutation({
    mutationFn: (id) => profileService.deleteExperience(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to delete experience'),
  });

  const createProjectMutation = useMutation({
    mutationFn: (payload) => profileService.createProject(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to create project'),
  });

  const updateProjectMutation = useMutation({
    mutationFn: ({ id, data }) => profileService.updateProject(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to update project'),
  });

  const deleteProjectMutation = useMutation({
    mutationFn: (id) => profileService.deleteProject(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to delete project'),
  });

  const createCertificationMutation = useMutation({
    mutationFn: (payload) => profileService.createCertification(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to create certification'),
  });

  const updateCertificationMutation = useMutation({
    mutationFn: ({ id, data }) => profileService.updateCertification(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to update certification'),
  });

  const deleteCertificationMutation = useMutation({
    mutationFn: (id) => profileService.deleteCertification(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to delete certification'),
  });

  const createLanguageMutation = useMutation({
    mutationFn: (payload) => profileService.createLanguage(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to create language'),
  });

  const updateLanguageMutation = useMutation({
    mutationFn: ({ id, data }) => profileService.updateLanguage(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to update language'),
  });

  const deleteLanguageMutation = useMutation({
    mutationFn: (id) => profileService.deleteLanguage(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
    onError: (error) => setErrorMessage(error.response?.data?.message || 'Failed to delete language'),
  });

  return {
    // Personal/basic info
    profile,

    // Section data (all derived from the single complete-profile request)
    educations: completeProfile?.educations ?? [],
    experiences: completeProfile?.experiences ?? [],
    projects: completeProfile?.projects ?? [],
    certifications: completeProfile?.certifications ?? [],
    languages: completeProfile?.languages ?? [],

    // Loading/refetch
    profileLoading,
    refetchProfile,

    // Sections loading flags expected by tabs
    educationsLoading: sectionLoading,
    experiencesLoading: sectionLoading,
    projectsLoading: sectionLoading,
    certificationsLoading: sectionLoading,
    languagesLoading: sectionLoading,

  // Education CRUD
    createEducation: (payload) => createEducationMutation.mutate(payload),
    updateEducation: ({ id, data }) => updateEducationMutation.mutate({ id, data }),
    deleteEducation: (id) => deleteEducationMutation.mutate(id),

    // Promise-based variants (so UI can wait for refetch after success)
    createEducationAsync: (payload) => createEducationMutation.mutateAsync(payload),
    updateEducationAsync: ({ id, data }) => updateEducationMutation.mutateAsync({ id, data }),
    deleteEducationAsync: (id) => deleteEducationMutation.mutateAsync(id),

    isCreatingEducation: createEducationMutation.isPending,
    isUpdatingEducation: updateEducationMutation.isPending,
    isDeletingEducation: deleteEducationMutation.isPending,


    // Experience CRUD
    createExperience: (payload) => createExperienceMutation.mutate(payload),
    updateExperience: ({ id, data }) => updateExperienceMutation.mutate({ id, data }),
    deleteExperience: (id) => deleteExperienceMutation.mutate(id),
    isCreatingExperience: createExperienceMutation.isPending,
    isUpdatingExperience: updateExperienceMutation.isPending,
    isDeletingExperience: deleteExperienceMutation.isPending,

    // Project CRUD
    createProject: (payload) => createProjectMutation.mutate(payload),
    updateProject: ({ id, data }) => updateProjectMutation.mutate({ id, data }),
    deleteProject: (id) => deleteProjectMutation.mutate(id),
    isCreatingProject: createProjectMutation.isPending,
    isUpdatingProject: updateProjectMutation.isPending,
    isDeletingProject: deleteProjectMutation.isPending,

    // Certification CRUD
    createCertification: (payload) => createCertificationMutation.mutate(payload),
    updateCertification: ({ id, data }) => updateCertificationMutation.mutate({ id, data }),
    deleteCertification: (id) => deleteCertificationMutation.mutate(id),
    isCreatingCertification: createCertificationMutation.isPending,
    isUpdatingCertification: updateCertificationMutation.isPending,
    isDeletingCertification: deleteCertificationMutation.isPending,

    // Language CRUD
    createLanguage: (payload) => createLanguageMutation.mutate(payload),
    updateLanguage: ({ id, data }) => updateLanguageMutation.mutate({ id, data }),
    deleteLanguage: (id) => deleteLanguageMutation.mutate(id),
    isCreatingLanguage: createLanguageMutation.isPending,
    isUpdatingLanguage: updateLanguageMutation.isPending,
    isDeletingLanguage: deleteLanguageMutation.isPending,

    // Update profile mutation
    updateProfile: updateProfileMutation.mutate,
    isUpdatingProfile: updateProfileMutation.isPending,

    // Messages
    successMessage,
    errorMessage,
    clearMessages,

};
};