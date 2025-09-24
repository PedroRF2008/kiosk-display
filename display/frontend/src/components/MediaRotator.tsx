import React, { useState, useEffect, useRef, useCallback } from 'react';
import type { MediaItem } from '../types';

interface MediaRotatorProps {
  media: MediaItem[];
  debug?: boolean;
}

const MediaRotator: React.FC<MediaRotatorProps> = ({ media, debug = false }) => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const slideTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Debug logging function - simplified
  const log = useCallback((message: string) => {
    if (debug) {
      const timestamp = new Date().toISOString().substr(11, 8);
      console.log(`[${timestamp}] ${message}`);
    }
  }, [debug]);

  const clearTimer = useCallback(() => {
    if (slideTimerRef.current) {
      clearTimeout(slideTimerRef.current);
      slideTimerRef.current = null;
    }
  }, []);

  const nextSlide = useCallback(() => {
    if (media.length <= 1 || isTransitioning) return;

    log(`nextSlide called. Old currentSlide: ${currentSlide}. isTransitioning: ${isTransitioning}`);
    if (isTransitioning) {
      log('Transition already in progress, ignoring nextSlide call');
      return;
    }

    setIsTransitioning(true);
    const nextIndex = (currentSlide + 1) % media.length;
    log(`nextSlide: New currentSlide calculated: ${nextIndex}. Total slides: ${media.length}`);

    setCurrentSlide(nextIndex);

    // Reset transition state after fade animation
    setTimeout(() => {
      setIsTransitioning(false);
    }, 1000);
  }, [currentSlide, media.length, isTransitioning, log]);

  // Main effect for handling slide changes - simplified like legacy version
  useEffect(() => {
    if (media.length === 0) return;

    const currentMedia = media[currentSlide];
    if (!currentMedia) return;

    clearTimer();

    if (currentMedia.is_video) {
      log(`Setting up video for slide ${currentSlide}`);
      // No complex video state management - let browser handle it
    } else {
      // Image timing - simplified
      const duration = Math.max(currentMedia.duration - 1000, 1000); // Subtract 1s for transition like legacy
      log(`Image slide ${currentSlide} timer set for ${duration}ms`);

      slideTimerRef.current = setTimeout(() => {
        nextSlide();
      }, duration);
    }

    return () => {
      clearTimer();
    };
  }, [currentSlide, media, clearTimer, nextSlide, log]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimer();
    };
  }, [clearTimer]);

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

        // Simple video event handlers matching legacy logic
        const handleVideoEnd = () => {
          log(`Video ended for slide ${index}`);
          if (isActive && !isTransitioning) {
            nextSlide();
          }
        };

        const handleVideoError = () => {
          log(`Video error for slide ${index}`);
          if (isActive) {
            setTimeout(() => nextSlide(), 2000);
          }
        };

        const handleVideoLoadedMetadata = (e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
          const video = e.currentTarget;
          log(`Video metadata loaded for slide ${index}. Duration: ${video.duration}`);

          if (isActive && isFinite(video.duration) && video.duration > 0) {
            // Set safety timeout like legacy version
            const durationMs = video.duration * 1000;
            slideTimerRef.current = setTimeout(() => {
              log(`Video duration timer expired for slide ${index}`);
              if (!isTransitioning) {
                nextSlide();
              }
            }, durationMs + 500); // Add 500ms buffer
          }
        };

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
              transition: 'opacity 1s ease-in-out',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              zIndex: isActive ? 10 : 1,
              background: '#000',
            }}
          >
            {item.is_video ? (
              <video
                src={item.local_path}
                autoPlay={isActive}
                muted
                playsInline
                preload="auto"
                onEnded={handleVideoEnd}
                onError={handleVideoError}
                onLoadedMetadata={handleVideoLoadedMetadata}
                style={{
                  width: isPerfectSize ? '100%' : 'auto',
                  height: isPerfectSize ? '100%' : 'auto',
                  maxWidth: '100%',
                  maxHeight: '100%',
                  objectFit: isPerfectSize ? 'cover' : 'contain',
                  borderRadius: '20px',
                }}
              />
            ) : (
              <img
                src={item.local_path}
                alt="Display Content"
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