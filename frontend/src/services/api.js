import axios from 'axios';

export const API_ORIGIN = process.env.REACT_APP_API_ORIGIN ?? 'http://localhost:8001';

const API = axios.create({ baseURL: API_ORIGIN ? `${API_ORIGIN}/api` : '/api' });

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
