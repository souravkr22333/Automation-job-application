import React, { useMemo, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  BriefcaseIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { Icon } from 'lucide-react';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';

const Sidebar = () => {
  const { logout } = useAuth();
  const [expanded, setExpanded] = useState(false);

  const navigation = useMemo(
    () => [
      { name: 'Dashboard', to: '/dashboard', icon: HomeIcon },
      { name: 'Job Scout', to: '/jobs', icon: BriefcaseIcon },
      { name: 'Applications', to: '/applications', icon: DocumentTextIcon },
      { name: 'Profile', to: '/profile', icon: UserCircleIcon },
      { name: 'Settings', to: '/settings', icon: Cog6ToothIcon },
    ],
    []
  );

  return (
    <div className="hidden md:flex h-screen">
      <aside
        className={
          expanded
            ? 'flex flex-col w-64 bg-black border-r border-gray-800 transition-[width] duration-200'
            : 'flex flex-col w-16 bg-black border-r border-gray-800 transition-[width] duration-200 items-center'
        }
      >
        {/* Top bar */}
        <div className="flex items-center h-18 px-4 border-b border-gray-800 w-full">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="text-white/80 hover:text-white"
            aria-label={expanded ? 'Collapse sidebar' : 'Expand sidebar'}
            title={expanded ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {/* simple arrow */}
            <span className="text-lg font-bold p-2">{expanded ? '‹' : '›'}</span>
          </button>

          {expanded && (
            <span className="ml-3 text-xl font-bold text-blue-600 truncate">AutoApply AI</span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 w-full px-2 py-4">
          <div className={expanded ? 'space-y-1' : 'space-y-1 flex flex-col items-center'}>
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center ${
                    expanded ? 'px-4' : 'justify-center px-2'
                  } py-3 text-sm rounded-lg transition ${
                    isActive ? 'bg-blue-900/40 text-white' : 'text-gray-300 hover:bg-gray-800'
                  }`
                }
              >
                <item.icon className="h-5 w-5 text-white" />
                {expanded && <span className="ml-3 truncate">{item.name}</span>}
              </NavLink>
            ))}
          </div>
        </nav>

        {/* Logout */}
        <div className={expanded ? 'p-4 border-t border-gray-800' : 'p-4 border-t border-gray-800 w-full flex justify-center'}>
          <button
            onClick={logout}
            className={
              expanded
                ? 'flex items-center w-full px-4 py-3 text-sm text-gray-300 rounded-lg hover:bg-gray-800 transition'
                : 'flex items-center justify-center w-10 h-10 text-gray-300 rounded-lg hover:bg-gray-800 transition'
            }
          >
            <div className="h-5 w-5 flex justify-center  items-center" />
            {expanded ? <span className="ml-3 text-red-600 mr-1">Sign Out < ExitToAppIcon style={{color:"red"}}/></span> : <span className='p-1'> < ExitToAppIcon style={{color:"red"}}/></span>}
          </button>
        </div>
      </aside>
    </div>
  );
};

export default Sidebar;

