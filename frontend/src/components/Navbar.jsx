import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Film, Heart, Sparkles, LogOut, User as UserIcon } from 'lucide-react';

export const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="p-2 bg-gradient-to-tr from-sky-500 to-indigo-600 rounded-xl shadow-lg shadow-sky-500/20 group-hover:scale-105 transition-transform">
              <Film className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              Instant<span className="text-sky-400">Movies</span>
            </span>
          </Link>

          {/* Navigation Links */}
          {isAuthenticated && (
            <nav className="hidden md:flex items-center space-x-1">
              <Link
                to="/"
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/')
                    ? 'bg-slate-800 text-sky-400'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Film className="w-4 h-4" />
                <span>Catálogo</span>
              </Link>

              <Link
                to="/likes"
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/likes')
                    ? 'bg-slate-800 text-rose-400'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Heart className="w-4 h-4" />
                <span>Mis Favoritas</span>
              </Link>

              <Link
                to="/recommendations"
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/recommendations')
                    ? 'bg-slate-800 text-amber-400'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <Sparkles className="w-4 h-4" />
                <span>Recomendaciones AI</span>
              </Link>
            </nav>
          )}

          {/* User Profile / Auth Actions */}
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700/50">
                  <UserIcon className="w-4 h-4 text-sky-400" />
                  <span className="text-xs font-semibold text-slate-200">{user?.username}</span>
                </div>
                <button
                  onClick={handleLogout}
                  title="Cerrar sesión"
                  className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
                >
                  Iniciar sesión
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-sm font-medium bg-sky-500 hover:bg-sky-400 text-white rounded-lg shadow-md shadow-sky-500/20 transition-colors"
                >
                  Registrarse
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
