import axios from 'axios';

const API = axios.create({ baseURL: 'http://localhost:8000/api' });

export async function analyzeVideo(file, side = 'right', onProgress) {
  const form = new FormData();
  form.append('file', file);
  form.append('side', side);

  const { data } = await API.post('/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
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
