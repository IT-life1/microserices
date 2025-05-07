import React, { useState } from "react";
import { downloadMP3 } from "../services/api";

const Downloads = () => {
  const [fid, setFid] = useState("");
  const [error, setError] = useState("");

  const token = localStorage.getItem("token");

  const handleDownload = async (e) => {
    e.preventDefault();
    if (!fid) {
      setError("Введите FID");
      return;
    }

    try {
      await downloadMP3(fid, token);
    } catch (err) {
      setError("Файл не найден или ошибка доступа");
    }
  };

  return (
    <div className="container mt-5">
      <h2>Скачать MP3</h2>
      {error && <div className="alert alert-danger">{error}</div>}
      <form onSubmit={handleDownload}>
        <div className="mb-3">
          <label>FID файла</label>
          <input
            type="text"
            className="form-control"
            value={fid}
            onChange={(e) => setFid(e.target.value)}
          />
        </div>
        <button type="submit" className="btn btn-primary">Скачать</button>
      </form>
    </div>
  );
};

export default Downloads;