import axios from 'axios';

const API_URL = "http://158.160.64.194:30159/api";

// Создаем клиент без базового хоста — будем использовать полный URL
const apiClient = axios.create();

/**
 * Функция для создания строки Basic Auth
 */
function getBasicAuthHeader(username, password) {
  const credentials = `${username}:${password}`;
  const base64Credentials = btoa(credentials); // браузерная функция
  return `Basic ${base64Credentials}`;
}

/**
 * Логин через Basic Auth
 */
export const login = async (username, password) => {
  const authHeader = getBasicAuthHeader(username, password);

  try {
    const response = await apiClient.post(
      `${API_URL}/login`,
      {}, // тело не нужно
      {
        headers: {
          Authorization: authHeader,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("Login error:", error.response?.data || error.message);
    throw error;
  }
};

export const uploadVideo = async (file, token) => {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await apiClient.post(
      `${API_URL}/upload`, // Теперь будет http://<VM_IP>:30159/api/upload
      formData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        onUploadProgress: progressEvent => {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          console.log(`Upload Progress: ${percent}%`);
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error("Upload error:", error.response?.data || error.message);
    throw error;
  }
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