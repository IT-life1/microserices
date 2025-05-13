import React, { useState } from "react";
import { downloadMP3 } from "../services/api";

const Downloads = () => {
  const [fid, setFid] = useState("");
  const [error, setError] = useState("");

  const token = localStorage.getItem("token");

  const handleDownload = async (e) => {
    e.preventDefault();
    if (!fid.trim()) {
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-6 border border-gray-200">
        <h2 className="text-2xl font-bold text-center mb-6 text-indigo-700">📥 Скачать MP3</h2>

        {error && (
          <div className="p-3 mb-4 text-sm text-red-700 bg-red-100 rounded-md">
            {error}
          </div>
        )}

        <form onSubmit={handleDownload} className="space-y-5">
          <div className="space-y-2">
            <label htmlFor="fid" className="block text-sm font-medium text-gray-700">
              Введите FID файла
            </label>
            <input
              id="fid"
              type="text"
              placeholder="Например: abcdef123456"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={fid}
              onChange={(e) => setFid(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-md transition-colors duration-200"
          >
            📥 Скачать файл
          </button>
        </form>
      </div>
    </div>
  );
};

export default Downloads;