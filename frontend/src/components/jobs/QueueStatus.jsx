// frontend/src/components/jobs/QueueStatus.jsx
import React from 'react';
import { Clock, CheckCircle, Loader2 } from 'lucide-react';

const QueueStatus = ({ progress, queued, applied }) => {
  const getStatusColor = (progress) => {
    if (progress >= 80) return 'bg-green-500';
    if (progress >= 50) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  return (
    <div className="bg-black dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
            <span className="text-sm font-medium text-white dark:text-white">
              Queue Progress
            </span>
          </div>
          <span className="text-sm font-bold text-teal-600 dark:text-teal-400">
            {progress}%
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs text-white dark:text-gray-400">
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {queued || 0} Queued
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle className="w-3.5 h-3.5 text-green-500" />
            {applied || 0} Applied
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all duration-500 ease-out ${getStatusColor(progress)}`}
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>

      {/* Status labels */}
      <div className="flex justify-between mt-1 text-[10px] text-gray-400 dark:text-gray-500">
        <span>Pending</span>
        <span>Processing</span>
        <span>Complete</span>
      </div>
    </div>
  );
};

export default QueueStatus;