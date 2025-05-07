import React from "react";
import { Link } from "react-router-dom";

const Layout = ({ children }) => {
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