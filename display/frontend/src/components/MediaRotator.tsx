import React, { useState, useEffect, useRef, useCallback } from 'react';
import type { MediaItem } from '../types';

interface MediaRotatorProps {
  media: MediaItem[];
  debug?: boolean;
}

const MediaRotator: React.FC<MediaRotatorProps> = ({ media, debug = false }) => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [videoStatus, setVideoStatus] = useState<'loading' | 'playing' | 'ended' | 'error'>('loading');
  const [isInitialized, setIsInitialized] = useState(false);

  const slideTimerRef = useRef<NodeJS.Timeout | null>(null);
  const videoRefs = useRef<Map<number, HTMLVideoElement>>(new Map());
  const transitionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Debug logging function
  const log = useCallback((message: string, level: 'info' | 'warn' | 'error' = 'info') => {
    const timestamp = new Date().toISOString().substr(11, 8);
    if (level === 'error') {
      console.error(`[MediaRotator ${timestamp}] ${message}`);
    } else if (level === 'warn') {
      console.warn(`[MediaRotator ${timestamp}] ${message}`);
    } else if (debug) {
      console.log(`[MediaRotator ${timestamp}] ${message}`);
    }
  }, [debug]);

  const clearTimer = useCallback(() => {
    if (slideTimerRef.current) {
      clearTimeout(slideTimerRef.current);
      slideTimerRef.current = null;
    }
  }, []);

  const clearTransitionTimeout = useCallback(() => {
    if (transitionTimeoutRef.current) {
      clearTimeout(transitionTimeoutRef.current);
      transitionTimeoutRef.current = null;
    }
  }, []);

  const nextSlide = useCallback(() => {
    if (media.length <= 1 || isTransitioning) return;

    const nextIndex = (currentSlide + 1) % media.length;
    log(`Moving from slide ${currentSlide} to ${nextIndex}`);

    setIsTransitioning(true);
    clearTimer();
    clearTransitionTimeout();

    // Stop current video if playing
    const currentVideo = videoRefs.current.get(currentSlide);
    if (currentVideo && !currentVideo.paused) {
      currentVideo.pause();
      currentVideo.currentTime = 0;
    }

    setCurrentSlide(nextIndex);
    setVideoStatus('loading');

    // Reset transition state
    transitionTimeoutRef.current = setTimeout(() => {
      setIsTransitioning(false);
    }, 300);
  }, [currentSlide, media.length, isTransitioning, clearTimer, clearTransitionTimeout, log]);

  // Video ref management
  const setVideoRef = useCallback((index: number) => (el: HTMLVideoElement | null) => {
    if (el) {
      videoRefs.current.set(index, el);
    } else {
      videoRefs.current.delete(index);
    }
  }, []);

  // Video event handlers
  const handleVideoCanPlay = useCallback((index: number) => {
    if (index !== currentSlide) return;

    log(`Video can play for slide ${index}`);
    const video = videoRefs.current.get(index);
    if (video && video.paused) {
      video.play().catch((error) => {
        log(`Video play failed for slide ${index}: ${error.message}`, 'error');
        setVideoStatus('error');
        setTimeout(() => nextSlide(), 2000);
      });
    }
  }, [currentSlide, log, nextSlide]);

  const handleVideoPlay = useCallback((index: number) => {
    if (index !== currentSlide) return;

    log(`Video started playing for slide ${index}`);
    setVideoStatus('playing');

    clearTimer();
    const video = videoRefs.current.get(index);
    if (video && video.duration && isFinite(video.duration)) {
      const duration = Math.ceil(video.duration * 1000) + 500; // Add 500ms buffer
      slideTimerRef.current = setTimeout(() => {
        log(`Video duration timer expired for slide ${index}`);
        nextSlide();
      }, duration);
    }
  }, [currentSlide, log, clearTimer, nextSlide]);

  const handleVideoEnd = useCallback((index: number) => {
    if (index !== currentSlide) return;

    log(`Video ended for slide ${index}`);
    setVideoStatus('ended');
    clearTimer();

    setTimeout(() => {
      if (!isTransitioning) {
        nextSlide();
      }
    }, 100);
  }, [currentSlide, log, clearTimer, nextSlide, isTransitioning]);

  const handleVideoError = useCallback((index: number, error: any) => {
    if (index !== currentSlide) return;

    log(`Video error for slide ${index}: ${error?.message || 'Unknown error'}`, 'error');
    setVideoStatus('error');
    clearTimer();

    setTimeout(() => nextSlide(), 2000);
  }, [currentSlide, log, clearTimer, nextSlide]);

  // Main effect for handling slide changes
  useEffect(() => {
    if (media.length === 0 || !isInitialized) return;

    const currentMedia = media[currentSlide];
    if (!currentMedia) return;

    clearTimer();

    if (currentMedia.is_video) {
      log(`Setting up video for slide ${currentSlide}`);
      setVideoStatus('loading');

      // Force video to load and play after a small delay to ensure DOM is ready
      setTimeout(() => {
        const video = videoRefs.current.get(currentSlide);
        if (video) {
          log(`Forcing video load for slide ${currentSlide}`);
          // Reset video state
          video.currentTime = 0;
          // Force load
          video.load();

          // If video is already ready, try to play immediately
          if (video.readyState >= 3) {
            log(`Video ${currentSlide} already ready, playing immediately`);
            video.play().catch((error) => {
              log(`Video immediate play failed for slide ${currentSlide}: ${error.message}`, 'error');
              setVideoStatus('error');
              setTimeout(() => nextSlide(), 2000);
            });
          }
        } else {
          log(`No video element found for slide ${currentSlide}`, 'error');
          setTimeout(() => nextSlide(), 1000);
        }
      }, 100);
    } else {
      // Image timing
      const duration = Math.max(currentMedia.duration, 3000); // Minimum 3 seconds
      log(`Setting image timer for ${duration}ms on slide ${currentSlide}`);

      slideTimerRef.current = setTimeout(() => {
        nextSlide();
      }, duration);
    }

    return () => {
      clearTimer();
    };
  }, [currentSlide, media, isInitialized, clearTimer, nextSlide, log]);

  // Initialize slideshow
  useEffect(() => {
    if (media.length > 0 && !isInitialized) {
      log(`Initializing slideshow with ${media.length} slides`);
      setCurrentSlide(0);
      setVideoStatus('loading');

      setTimeout(() => {
        setIsInitialized(true);
      }, 100);
    }
  }, [media, isInitialized, log]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimer();
      clearTransitionTimeout();
      videoRefs.current.clear();
    };
  }, [clearTimer, clearTransitionTimeout]);

  if (media.length === 0) {
    return (
      <div style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'white',
        borderRadius: '20px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        fontSize: '2rem',
        color: '#666',
      }}>
        Nenhuma mídia disponível
      </div>
    );
  }

  if (!isInitialized) {
    return (
      <div style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: '#000',
        borderRadius: '20px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        color: 'white',
        fontSize: '1.5rem',
      }}>
        Inicializando...
      </div>
    );
  }

  return (
    <div style={{
      position: 'relative',
      width: '100%',
      height: '100%',
      overflow: 'hidden',
      background: '#000',
      borderRadius: '20px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
    }}>
      {media.map((item, index) => {
        const isActive = index === currentSlide;
        const isPerfectSize = item.width === 1920 && item.height === 1080;

        return (
          <div
            key={`${item.id}-${index}`}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              opacity: isActive ? 1 : 0,
              transition: 'opacity 0.8s ease-in-out',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              zIndex: isActive ? 10 : 1,
              background: '#000',
            }}
          >
            {item.is_video ? (
              <>
                <video
                  ref={setVideoRef(index)}
                  src={item.local_path}
                  preload="auto"
                  muted
                  playsInline
                  onCanPlay={() => handleVideoCanPlay(index)}
                  onPlay={() => handleVideoPlay(index)}
                  onEnded={() => handleVideoEnd(index)}
                  onError={(e) => handleVideoError(index, e.currentTarget.error)}
                  style={{
                    width: isPerfectSize ? '100%' : 'auto',
                    height: isPerfectSize ? '100%' : 'auto',
                    maxWidth: '100%',
                    maxHeight: '100%',
                    objectFit: isPerfectSize ? 'cover' : 'contain',
                    borderRadius: '20px',
                  }}
                />
                {/* Loading indicator */}
                {isActive && videoStatus === 'loading' && (
                  <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    color: 'white',
                    fontSize: '1.2rem',
                    background: 'rgba(0,0,0,0.7)',
                    padding: '10px 20px',
                    borderRadius: '10px',
                    zIndex: 15,
                  }}>
                    Carregando vídeo...
                  </div>
                )}
                {/* Error indicator */}
                {isActive && videoStatus === 'error' && (
                  <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    color: '#ff6b6b',
                    fontSize: '1.2rem',
                    background: 'rgba(0,0,0,0.7)',
                    padding: '10px 20px',
                    borderRadius: '10px',
                    zIndex: 15,
                  }}>
                    Erro ao carregar vídeo
                  </div>
                )}
              </>
            ) : (
              <img
                src={item.local_path}
                alt="Display Content"
                loading="lazy"
                style={{
                  width: isPerfectSize ? '100%' : 'auto',
                  height: isPerfectSize ? '100%' : 'auto',
                  maxWidth: '100%',
                  maxHeight: '100%',
                  objectFit: isPerfectSize ? 'cover' : 'contain',
                  borderRadius: '20px',
                }}
              />
            )}
          </div>
        );
      })}

      {/* Slide indicators */}
      {media.length > 1 && (
        <div style={{
          position: 'absolute',
          bottom: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex',
          gap: '8px',
          zIndex: 20,
          background: 'rgba(0,0,0,0.3)',
          padding: '8px 12px',
          borderRadius: '20px',
        }}>
          {media.map((_, index) => (
            <div
              key={index}
              style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                background: index === currentSlide
                  ? 'rgba(255, 255, 255, 0.9)'
                  : 'rgba(255, 255, 255, 0.4)',
                transition: 'all 0.3s ease',
                border: '1px solid rgba(255, 255, 255, 0.2)',
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default MediaRotator;