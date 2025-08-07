import { forwardRef, useImperativeHandle, useRef, useState, useEffect } from 'react';

export interface VideoPlayerProps {
  src?: string;
  presignedUrl?: string;
  poster?: string;
  width?: number | string;
  height?: number | string;
  controls?: boolean;
  autoPlay?: boolean;
  muted?: boolean;
  loop?: boolean;
  preload?: 'none' | 'metadata' | 'auto';
  onVideoError?: (error: string) => void;
  onAnnotationsChange?: (annotations: Record<string, BoundingBox[]>) => void;
}

export interface VideoPlayerRef {
  seekTo: (seconds: number) => void;
  pause: () => void;
  play: () => void;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label?: string;
  confidence?: number;
}

const VideoPlayer = forwardRef<VideoPlayerRef, VideoPlayerProps>(({
  src,
  presignedUrl,
  poster,
  width = '100%',
  height = 600,
  controls = true,
  autoPlay = false,
  muted = false,
  loop = false,
  preload = 'metadata',
  onVideoError,
  onAnnotationsChange,
  ...props
}, ref) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [browserInfo, setBrowserInfo] = useState<{name: string, version: string} | null>(null);

  // Determine video source - prioritize src over presignedUrl
  const videoSrc = src || presignedUrl;

  // Detect browser and version
  useEffect(() => {
    const detectBrowser = () => {
      const userAgent = navigator.userAgent;
      let browserName = 'Unknown';
      let browserVersion = 'Unknown';

      if (userAgent.includes('Chrome')) {
        browserName = 'Chrome';
        browserVersion = userAgent.match(/Chrome\/(\d+)/)?.[1] || 'Unknown';
      } else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) {
        browserName = 'Safari';
        browserVersion = userAgent.match(/Version\/(\d+)/)?.[1] || 'Unknown';
      } else if (userAgent.includes('Firefox')) {
        browserName = 'Firefox';
        browserVersion = userAgent.match(/Firefox\/(\d+)/)?.[1] || 'Unknown';
      } else if (userAgent.includes('Edge')) {
        browserName = 'Edge';
        browserVersion = userAgent.match(/Edge\/(\d+)/)?.[1] || 'Unknown';
      }

      setBrowserInfo({ name: browserName, version: browserVersion });
      console.log(`🎬 Browser detected: ${browserName} ${browserVersion}`);
    };

    detectBrowser();
  }, []);

  // Debug logging
  console.log('🎬 VideoPlayer props:', { src, presignedUrl, videoSrc });
  console.log('🎬 Using video source:', videoSrc ? 'src' : 'presignedUrl');

  useImperativeHandle(ref, () => ({
    seekTo: (seconds: number) => {
      if (videoRef.current) {
        videoRef.current.currentTime = seconds;
      }
    },
    pause: () => {
      if (videoRef.current) {
        videoRef.current.pause();
      }
    },
    play: () => {
      if (videoRef.current) {
        videoRef.current.play();
      }
    }
  }));

  const handleError = (e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    console.log('🎬 Video error:', e);
    const videoElement = e.currentTarget;
    const error = videoElement.error;
    let errorMessage = 'Video playback error';
    
    if (error) {
      switch (error.code) {
        case MediaError.MEDIA_ERR_ABORTED:
          errorMessage = 'Video loading was aborted';
          break;
        case MediaError.MEDIA_ERR_NETWORK:
          errorMessage = 'Network error while loading video';
          break;
        case MediaError.MEDIA_ERR_DECODE:
          errorMessage = 'Video decoding error - this may be a codec compatibility issue';
          break;
        case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
          errorMessage = 'Video format not supported by this browser';
          break;
        default:
          errorMessage = `Video error: ${error.message || 'Unknown error'}`;
      }
    }
    
    console.log('🎬 Error details:', errorMessage);
    setError(errorMessage);
    onVideoError?.(errorMessage);
  };

  const handleLoadStart = () => {
    console.log('🎬 Video loading started');
    setIsLoading(true);
    setError(null);
  };

  const handleLoadedMetadata = () => {
    console.log('🎬 Video metadata loaded');
    setIsLoading(false);
  };

  const handleCanPlay = () => {
    console.log('🎬 Video can play');
    setIsLoading(false);
  };

  const getBrowserSpecificMessage = () => {
    if (!browserInfo) return '';
    
    if (browserInfo.name === 'Chrome') {
      return 'Chrome has stricter video codec requirements. Try opening this video in Safari or contact support to re-encode the video.';
    } else if (browserInfo.name === 'Safari') {
      return 'Safari supports more video formats than Chrome. This video may not work in Chrome.';
    }
    
    return 'This video may not be compatible with your browser.';
  };

  if (!videoSrc) {
    return <div>No video source provided</div>;
  }

  return (
    <div style={{ width, height }}>
      {isLoading && (
        <div style={{ 
          position: 'absolute', 
          top: '50%', 
          left: '50%', 
          transform: 'translate(-50%, -50%)',
          backgroundColor: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '10px',
          borderRadius: '4px',
          zIndex: 10
        }}>
          Loading video...
        </div>
      )}
      
      {error && (
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100%',
          backgroundColor: '#f5f5f5',
          border: '1px solid #ddd',
          borderRadius: '4px',
          color: '#666',
          padding: '20px',
          textAlign: 'center'
        }}>
          <div>
            <h4 style={{ margin: '0 0 10px 0', color: '#d32f2f' }}>Video Playback Error</h4>
            <p style={{ margin: '0 0 10px 0' }}>{error}</p>
            <p style={{ margin: '0 0 15px 0', fontSize: '14px' }}>
              {getBrowserSpecificMessage()}
            </p>
            <div style={{ fontSize: '12px', color: '#888' }}>
              <p><strong>Browser:</strong> {browserInfo?.name} {browserInfo?.version}</p>
              <p><strong>Video URL:</strong> {videoSrc.substring(0, 50)}...</p>
            </div>
            <div style={{ marginTop: '15px' }}>
              <button 
                onClick={() => window.open(videoSrc, '_blank')}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#1976d2',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  marginRight: '10px'
                }}
              >
                Open in New Tab
              </button>
              <button 
                onClick={() => window.open(videoSrc, '_blank', 'download')}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#388e3c',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Download Video
              </button>
            </div>
          </div>
        </div>
      )}
      
      <video
        ref={videoRef}
        src={videoSrc}
        width="100%"
        height="100%"
        controls={controls}
        autoPlay={autoPlay}
        muted={muted}
        loop={loop}
        preload={preload}
        poster={poster}
        style={{ 
          display: error ? 'none' : 'block',
          maxWidth: '100%',
          height: 'auto'
        }}
        onLoadStart={handleLoadStart}
        onLoadedMetadata={handleLoadedMetadata}
        onCanPlay={handleCanPlay}
        onError={handleError}
        {...props}
      >
        <source src={videoSrc} type="video/mp4" />
        <source src={videoSrc.replace('.mp4', '.webm')} type="video/webm" />
        Your browser does not support the video tag.
      </video>
    </div>
  );
});

VideoPlayer.displayName = 'VideoPlayer';

export default VideoPlayer; 