import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FaSignInAlt, FaSignOutAlt, FaMoon, FaSun } from "react-icons/fa";

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem("token");
  const [darkMode, setDarkMode] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  const toggleTheme = () => {
    setDarkMode(!darkMode);
  };

  return (
    <div className={darkMode ? "bg-gray-900 text-white min-h-screen" : "bg-gray-50 text-gray-900 min-h-screen flex flex-col"}>
      <nav className={`${
        darkMode ? "bg-gray-800" : "bg-indigo-600"
      } text-white shadow-lg`}>
        <div className="container mx-auto px-4 py-3">
          <div className="flex justify-between items-center">
            <Link to="/" className="text-xl font-bold">🔐 Media Converter</Link>

            {/* Навигация */}
            <div className="hidden md:flex space-x-6">
              <Link to="/upload" className="hover:underline hover:text-blue-300 transition duration-200">
                📁 Загрузить
              </Link>
              <Link to="/download" className="hover:underline hover:text-blue-300 transition duration-200">
                📥 Скачать
              </Link>
            </div>

            {/* Правая часть: Авторизация + Тема */}
            <div className="flex items-center gap-4">
              {!isAuthenticated ? (
                <Link to="/login" className="hover:text-blue-300 flex items-center gap-1">
                  <FaSignInAlt /> Войти
                </Link>
              ) : (
                <button onClick={handleLogout} className="hover:text-red-300 flex items-center gap-1 bg-transparent border-none cursor-pointer">
                  <FaSignOutAlt /> Выйти
                </button>
              )}

              {/* Кнопка переключения темы */}
              <button onClick={toggleTheme} className="ml-3 p-1 rounded-full">
                {darkMode ? <FaSun /> : <FaMoon />}
              </button>
            </div>
          </div>
        </div>

        {/* Мобильное меню */}
        <div className="md:hidden bg-opacity-70 bg-black px-4 py-2">
          <ul className="flex flex-col space-y-2">
            <li>
              <Link to="/upload" className="block py-2 hover:text-blue-300">📁 Загрузить</Link>
            </li>
            <li>
              <Link to="/download" className="block py-2 hover:text-blue-300">📥 Скачать</Link>
            </li>
          </ul>
        </div>
      </nav>

      {/* Основной контент */}
      <main className="container mx-auto px-4 py-6 flex-grow">
        {children}
      </main>

      {/* Футер */}
      <footer className={`mt-auto py-4 text-center ${
        darkMode ? "text-gray-400" : "text-gray-600"
      }`}>
        <small>&copy; 2025 Media Converter | DevOps</small>
      </footer>
    </div>
  );
};

export default Layout;