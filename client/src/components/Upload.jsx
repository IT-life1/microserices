import React, { useState } from "react";
import { uploadVideo } from "../services/api";

const Upload = () => {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [uploading, setUploading] = useState(false);

  const token = localStorage.getItem("token");

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setMessage("Выберите файл");
      return;
    }

    setUploading(true);
    setMessage("");

    try {
      await uploadVideo(file, token);
      setMessage("Видео успешно загружено и отправлено на обработку!");
    } catch (err) {
      setMessage("Ошибка загрузки файла");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="container mt-5">
      <h2>Загрузить видео</h2>
      {message && <div className="alert alert-info">{message}</div>}
      <form onSubmit={handleUpload}>
        <div className="mb-3">
          <input
            type="file"
            accept="video/*"
            className="form-control"
            onChange={(e) => setFile(e.target.files[0])}
          />
        </div>
        <button type="submit" className="btn btn-success" disabled={uploading}>
          {uploading ? "Загрузка..." : "Загрузить"}
        </button>
      </form>
    </div>
  );
};

export default Upload;