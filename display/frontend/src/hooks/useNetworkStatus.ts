import { useState, useEffect } from 'react';

interface NetworkStatus {
  isOnline: boolean;
  lastConnected: Date | null;
  connectionLostAt: Date | null;
}

export const useNetworkStatus = (): NetworkStatus => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [lastConnected, setLastConnected] = useState<Date | null>(null);
  const [connectionLostAt, setConnectionLostAt] = useState<Date | null>(null);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setLastConnected(new Date());
      setConnectionLostAt(null);
    };

    const handleOffline = () => {
      setIsOnline(false);
      setConnectionLostAt(new Date());
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initialize with current status
    if (navigator.onLine) {
      setLastConnected(new Date());
    } else {
      setConnectionLostAt(new Date());
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return {
    isOnline,
    lastConnected,
    connectionLostAt,
  };
};