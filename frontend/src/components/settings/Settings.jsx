import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { jobApi } from '../../services/resumeapi';

const Settings = () => {
  const navigate = useNavigate();

  const [settings, setSettings] = useState({
    emailNotifications: true,
    autoApplyEnabled: true,
    dailyDigest: false,
    resumeVersion: 'v2',
    preferredJobTypes: ['full-time', 'remote'],
  });

  
 

  const handleToggle = (key) => {
    setSettings((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Settings</h1>

      <div className="bg-black rounded-xl shadow-md p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Preferences</h2>

        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-gray-800 p-6 rounded-xl">
            <div>
              <p className="font-medium text-white">Email Notifications</p>
              <p className="text-sm text-white">Receive updates about applications</p>
            </div>
            <button
              onClick={() => handleToggle('emailNotifications')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                settings.emailNotifications ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                  settings.emailNotifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between rounded-xl border-b border-gray-800 p-6">
            <div>
              <p className="font-medium text-white">Auto-Apply</p>
              <p className="text-sm text-white">Automatically apply to matching jobs</p>
            </div>
            <button
              onClick={() => handleToggle('autoApplyEnabled')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                settings.autoApplyEnabled ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-black transition ${
                  settings.autoApplyEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

  
    </div>
  );
};

export default Settings;

