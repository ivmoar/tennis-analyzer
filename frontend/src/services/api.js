import axios from 'axios';

// En producción (Docker) debe quedar vacío para usar URLs relativas que Nginx proxea.
// En desarrollo local, el proxy de CRA (package.json) hace lo mismo.
// Setear REACT_APP_API_ORIGIN sólo si el backend es accesible desde el browser directamente.
export const API_ORIGIN = process.env.REACT_APP_API_ORIGIN || '';

const BASE_PATH = process.env.PUBLIC_URL || '';
const API = axios.create({ baseURL: API_ORIGIN ? `${API_ORIGIN}/api` : `${BASE_PATH}/api` });

export async function analyzeVideo(file, side = 'right', onProgress) {
  const form = new FormData();
  form.append('file', file);
  form.append('side', side);

  const { data } = await API.post('/analyze', form, {
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    },
  });
  return data;
}

export async function checkHealth() {
  const { data } = await API.get('/health');
  return data;
}
