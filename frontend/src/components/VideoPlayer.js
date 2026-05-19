import React, { forwardRef } from 'react';
import { API_ORIGIN } from '../services/api';

const VideoPlayer = forwardRef(({ url, onTimeUpdate, onLoadedMetadata }, ref) => {
  if (!url) return null;

  const fullUrl = url.startsWith('http') ? url : `${API_ORIGIN}${url}`;

  return (
    <video
      ref={ref}
      src={fullUrl}
      controls
      onTimeUpdate={onTimeUpdate}
      onLoadedMetadata={onLoadedMetadata}
      style={{
        width: '100%',
        borderRadius: '8px',
        background: '#000',
        maxHeight: '360px',
        objectFit: 'contain',
      }}
    />
  );
});

export default VideoPlayer;
