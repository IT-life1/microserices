import React from "react";
import { Link, useNavigate } from "react-router-dom";

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const isAuthenticated = !!localStorage.getItem("token");

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <div>
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
        <div className="container-fluid">
          <Link className="navbar-brand" to="/">Media Converter</Link>
          <div className="collapse navbar-collapse">
            <ul className="navbar-nav me-auto">
              <li className="nav-item">
                <Link className="nav-link" to="/upload">Загрузить</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/download">Скачать</Link>
              </li>
            </ul>

            <ul className="navbar-nav ms-auto">
              {!isAuthenticated ? (
                <li className="nav-item">
                  <Link className="nav-link" to="/login">Войти</Link>
                </li>
              ) : (
                <li className="nav-item">
                  <button className="btn btn-link nav-link" onClick={handleLogout}>
                    Выйти
                  </button>
                </li>
              )}
            </ul>
          </div>
        </div>
      </nav>

      <div className="container">
        {children}
      </div>
    </div>
  );
};

export default Layout;