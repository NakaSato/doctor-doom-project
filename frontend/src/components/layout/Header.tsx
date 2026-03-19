import { useAuthStore } from '@/stores/authStore';
import { useUIStore } from '@/stores/uiStore';

function Header() {
  const { user, logout } = useAuthStore();
  const { toggleSidebar, toggleDarkMode, darkMode } = useUIStore();

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4">
      {/* Left side */}
      <div className="flex items-center space-x-4">
        <button
          onClick={toggleSidebar}
          className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 lg:hidden"
        >
          ☰
        </button>

        {/* Search */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search sites, modules, defects..."
            className="w-64 lg:w-96 px-4 py-2 pl-10 bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 dark:text-white"
          />
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            🔍
          </span>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center space-x-4">
        {/* Dark mode toggle */}
        <button
          onClick={toggleDarkMode}
          className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          title="Toggle dark mode"
        >
          {darkMode ? '☀️' : '🌙'}
        </button>

        {/* Notifications */}
        <button className="relative p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
          🔔
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* User menu */}
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-white font-medium">
            {user?.full_name.charAt(0).toUpperCase()}
          </div>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300 hidden md:block">
            {user?.full_name}
          </span>
          <button
            onClick={logout}
            className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;
