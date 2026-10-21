// frontend/src/components/jobs/JobList.jsx
import React from 'react';
import { Briefcase, Loader2 } from 'lucide-react';
import JobCard from './JobCard';

const JobList = ({ 
  jobs, 
  loading, 
  viewMode, 
  onApply, 
  onSave, 
  applying, 
  selectedJob,
  onSelectJob,
  queueJobIds = [],
  onToggleQueueJob
}) => {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-teal-600 animate-spin" />
        <p className="mt-4 text-gray-500 dark:text-gray-400">Loading jobs...</p>
      </div>
    );
  }

  if (!jobs || jobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <Briefcase className="w-16 h-16 text-gray-300 dark:text-gray-600" />
        <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">No jobs found</h3>
        <p className="mt-2 text-gray-500 dark:text-gray-400">
          Try adjusting your filters or discover new jobs
        </p>
        <button 
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-medium"
        >
          Refresh
        </button>
      </div>
    );
  }

  return (
    <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : 'space-y-4'}>
      {jobs.map((job) => (
        <JobCard
          key={job.id}
          job={job}
          onApply={onApply}
          onSave={onSave}
          applying={applying[job.id]}
          selected={selectedJob === job.id}
          onSelect={onSelectJob}
          viewMode={viewMode}
          queueIds={queueJobIds}
          onToggleQueue={onToggleQueueJob}
        />
      ))}
    </div>
  );
};

export default JobList;