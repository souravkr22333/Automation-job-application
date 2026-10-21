import { useContext } from 'react';
import { JobContext } from '../contexts/JobContext';

export const useJobs = () => {
  const context = useContext(JobContext);
  if (!context) {
    throw new Error('useJobs must be used within a JobProvider');
  }
  return context;
};

