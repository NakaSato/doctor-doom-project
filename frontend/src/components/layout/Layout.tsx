import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import { useUIStore } from '@/stores/uiStore';

function Layout() {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900 overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content area */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          sidebarOpen ? 'ml-64' : 'ml-0'
        }`}
      >
        {/* Header */}
        <Header />

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>

      {/* Toast notifications */}
      <ToastContainer />
    </div>
  );
}

function ToastContainer() {
  const { toasts, removeToast } = useUIStore();

  return (
    <div className="fixed bottom-4 right-4 z-100 space-y-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`
            card p-4 min-w-80 shadow-lg animate-slide-up
            ${
              toast.type === 'success'
                ? 'border-l-4 border-green-500'
                : toast.type === 'error'
                ? 'border-l-4 border-red-500'
                : toast.type === 'warning'
                ? 'border-l-4 border-yellow-500'
                : 'border-l-4 border-blue-500'
            }
          `}
        >
          <div className="flex justify-between items-start">
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white">
                {toast.title}
              </h4>
              {toast.message && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {toast.message}
                </p>
              )}
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default Layout;
