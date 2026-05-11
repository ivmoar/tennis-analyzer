import React from 'react';

export default function VideoPlayer({ url }) {
  if (!url) return null;

  const fullUrl = url.startsWith('http') ? url : `http://localhost:8000${url}`;

  return (
    <video
      src={fullUrl}
      controls
      style={{
        width: '100%',
        borderRadius: '8px',
        background: '#000',
        maxHeight: '360px',
        objectFit: 'contain',
      }}
    />
  );
}
