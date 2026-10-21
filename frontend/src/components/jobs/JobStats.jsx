// frontend/src/components/jobs/JobStats.jsx
import React from 'react';
import { TrendingUp, Briefcase, BookmarkCheck, CheckCircle, Clock } from 'lucide-react';

const JobStats = ({ stats }) => {
  const statItems = [
    { 
      label: 'Total Jobs', 
      value: stats.total || 0, 
      icon: Briefcase, 
      color: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-50 dark:bg-blue-900/20'
    },
    { 
      label: 'AI Matched', 
      value: stats.matched || 0, 
      icon: TrendingUp, 
      color: 'text-green-600 dark:text-green-400',
      bg: 'bg-green-50 dark:bg-green-900/20'
    },
    { 
      label: 'Saved', 
      value: stats.saved || 0, 
      icon: BookmarkCheck, 
      color: 'text-teal-600 dark:text-teal-400',
      bg: 'bg-teal-50 dark:bg-teal-900/20'
    },
    { 
      label: 'Applied', 
      value: stats.applied || 0, 
      icon: CheckCircle, 
      color: 'text-purple-600 dark:text-purple-400',
      bg: 'bg-purple-50 dark:bg-purple-900/20'
    },
    { 
      label: 'Pending', 
      value: stats.pending || 0, 
      icon: Clock, 
      color: 'text-yellow-600 dark:text-yellow-400',
      bg: 'bg-yellow-50 dark:bg-yellow-900/20'
    }
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {statItems.map((item, index) => (
        <div 
          key={index}
          className="bg-black dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-3 flex items-center gap-3"
        >
          <div className={`p-2 rounded-lg ${item.bg}`}>
            <item.icon className={`w-4 h-4 ${item.color}`} />
          </div>
          <div>
            <p className="text-lg font-bold text-white dark:text-white">
              {item.value.toLocaleString()}
            </p>
            <p className="text-xs text-white dark:text-gray-400">{item.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default JobStats;