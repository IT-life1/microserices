import axios from 'axios';

const API_URL = "http://gateway:8080"; // заменить на ваш хост при деплое

const apiClient = axios.create({
  baseURL: API_URL,
});

export const login = async (username, password) => {
  const response = await apiClient.post("/login", { username, password });
  return response.data;
};

export const uploadVideo = async (file, token) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post("/upload", formData, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    onUploadProgress: progressEvent => {
      const percent = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      console.log(`Upload Progress: ${percent}%`);
    }
  });

  return response.data;
};

export const downloadMP3 = async (fid, token) => {
  const response = await apiClient.get("/download", {
    params: { fid },
    headers: {
      Authorization: `Bearer ${token}`,
    },
    responseType: 'blob'
  });

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${fid}.mp3`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};