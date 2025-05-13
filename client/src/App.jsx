import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./components/Login";
import Upload from "./components/Upload";
import Downloads from "./components/Downloads";
import Layout from "./components/Layout";
import './index.css'; 

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/download" element={<Downloads />} />
          <Route path="/" element={<Upload />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;