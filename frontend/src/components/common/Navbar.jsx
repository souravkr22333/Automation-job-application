import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  BellIcon, 
  UserCircleIcon, 
  MagnifyingGlassIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const Navbar = ({ onMenuClick }) => {
  const { user } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const notifications = [
    { id: 1, message: 'New application submitted to Stripe', time: '5 min ago' },
    { id: 2, message: 'Interview scheduled with Google', time: '1 hour ago' },
    { id: 3, message: 'Resume tailored for Vercel position', time: '3 hours ago' },
  ];

  return (
    <nav className="bg-black border-b border-gray-800 px-4 py-3 text-white">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-800 transition"
          >
            <Bars3Icon className="h-6 w-6 text-gray-300" />
          </button>
          <div className="hidden lg:block relative ml-4">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search jobs, companies..."
              className="pl-10 pr-4 py-2 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-black text-white w-64"
            />
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 rounded-lg hover:bg-gray-100 transition relative"
            >
              <BellIcon className="h-6 w-6 text-gray-700" />
              <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full"></span>
            </button>
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-black rounded-xl shadow-lg border border-gray-800 z-50">
                <div className="p-4 border-b border-gray-200">
                  <h4 className="font-semibold text-gray-800">Notifications</h4>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {notifications.map((notif) => (
                    <div key={notif.id} className="p-3 hover:bg-gray-50 transition border-b border-gray-100">
                      <p className="text-sm text-gray-800">{notif.message}</p>
                      <p className="text-xs text-gray-500 mt-1">{notif.time}</p>
                    </div>
                  ))}
                </div>
                <div className="p-3 text-center">
                  <button className="text-sm text-blue-600 hover:text-blue-800">
                    View all notifications
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition"
            >
              <UserCircleIcon className="h-8 w-8 text-gray-700" />
              <span className="hidden md:block text-sm font-medium text-gray-700">
                {user?.name || 'User'}
              </span>
            </button>
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-black rounded-xl shadow-lg border border-gray-800 z-50">
                <div className="p-3 border-b border-gray-800">
                  <p className="text-sm font-medium text-white">{user?.name}</p>
                  <p className="text-xs text-gray-400">{user?.email}</p>
                </div>
                <div className="p-2">
                  <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition">
                    Profile Settings
                  </button>
                  <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition">
                    Resume
                  </button>
                  <button className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition">
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;