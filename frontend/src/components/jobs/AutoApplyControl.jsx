// frontend/src/components/jobs/AutoApplyControl.jsx
import React, { useState } from 'react';
import { Play, Pause, RefreshCw, Settings } from 'lucide-react';

const AutoApplyControl = ({ onStart, onStop, isRunning }) => {
  const [isHovering, setIsHovering] = useState(false);

  return (
    <div className="bg-black dark:bg-gray-800 rounded-lg border border-gray-700 dark:border-gray-700 p-2">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-medium text-white dark:text-white">Auto-Apply</h4>
          <p className="text-xs text-white dark:text-gray-400">
            {isRunning ? 'Running' : 'Paused'}
          </p>
        </div>
        <button
          onClick={isRunning ? onStop : onStart}
          className={`
            p-2 rounded-lg transition-colors
            ${isRunning 
              ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 hover:bg-yellow-200' 
              : 'bg-teal-600 hover:bg-teal-700 text-white'
            }
          `}
          title={isRunning ? 'Pause' : 'Start'}
        >
          {isRunning ? (
            <Pause className="w-5 h-5" />
          ) : (
            <Play className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Status indicator */}
      <div className="mt-2 flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
        <span className="text-xs text-white dark:text-gray-400">
          {isRunning ? 'Applying jobs automatically...' : 'Ready to start'}
        </span>
      </div>

      {/* Quick actions */}
      <div className="mt-3 flex gap-2">
        <button className="flex-1 text-xs px-2 py-1 bg-teal-600 hover:bg-teal-700 text-white rounded-2xl transition-colors">
          Settings
        </button>
        <button className="flex-1 text-xs px-2 py-1 rounded-2xl bg-teal-600 hover:bg-teal-700 text-white transition-colors">
          <RefreshCw className="w-3 h-3 inline mr-1" />
          Queue
        </button>
      </div>
    </div>
  );
};

export default AutoApplyControl;