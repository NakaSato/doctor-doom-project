import { NavLink } from 'react-router-dom';
import { useUIStore } from '@/stores/uiStore';

const navigation = [
  { name: 'Dashboard', href: '/', icon: '📊' },
  { name: 'Array Map', href: '/map', icon: '🗺️' },
  { name: 'Defect Log', href: '/defects', icon: '⚠️' },
  { name: 'Module Inspector', href: '/modules', icon: '🔍' },
  { name: 'Comparison', href: '/comparison', icon: '📈' },
  { name: 'Reports', href: '/reports', icon: '📄' },
  { name: 'Flight Planner', href: '/flight-planner', icon: '🚁' },
];

function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-80 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-90
          w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700
          transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-0 lg:overflow-hidden'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">☀️</span>
              <span className="font-bold text-lg text-gray-900 dark:text-white">
                Doctor Doom
              </span>
            </div>
            <button
              onClick={toggleSidebar}
              className="lg:hidden text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              ×
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `
                  flex items-center px-4 py-3 text-sm font-medium rounded-lg
                  transition-colors duration-200
                  ${
                    isActive
                      ? 'bg-primary-500 text-white'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `
                }
              >
                <span className="mr-3 text-lg">{item.icon}</span>
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="text-xs text-gray-500 dark:text-gray-400">
              <p>Doctor Doom v1.0.0</p>
              <p className="mt-1">Thermal Panel Inspection</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
