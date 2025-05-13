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
      setMessage("Пожалуйста, выберите файл");
      return;
    }

    setUploading(true);
    setMessage("");

    try {
      await uploadVideo(file, token);
      setMessage("Видео успешно загружено и отправлено на обработку!");
    } catch (err) {
      setMessage("Ошибка загрузки видео.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-white rounded-xl shadow-xl p-6">
        <h2 className="text-2xl font-bold text-center mb-6 text-indigo-700">
          📥 Загрузить видео
        </h2>

        {message && (
          <div className={`p-3 mb-4 text-sm rounded-md ${message.includes('успешно') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            {message}
          </div>
        )}

        <form onSubmit={handleUpload} className="space-y-6">
          <div className="border-2 border-dashed border-indigo-300 rounded-lg p-6 text-center hover:border-indigo-500 transition-all duration-300">
            <label className="cursor-pointer">
              <input
                type="file"
                accept="video/*"
                onChange={(e) => setFile(e.target.files[0])}
                className="hidden"
              />
              <span className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors">
                🔍 Выберите видео
              </span>
            </label>
            {file && <p className="mt-2 text-gray-600">{file.name}</p>}
          </div>

          <button
            type="submit"
            disabled={uploading}
            className={`w-full py-3 rounded-md font-semibold text-white ${
              uploading ? "bg-indigo-300" : "bg-indigo-600 hover:bg-indigo-700"
            } transition-colors`}
          >
            {uploading ? "🔄 Загрузка..." : "📤 Загрузить"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Upload;