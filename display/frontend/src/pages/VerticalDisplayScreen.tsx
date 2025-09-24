import React from 'react';
import { useDisplayData } from '../hooks/useDisplayData';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import WeatherWidget from '../components/WeatherWidget';
import BirthdayPanel from '../components/BirthdayPanel';
import MediaRotator from '../components/MediaRotator';
import DateTimeWidget from '../components/DateTimeWidget';
import LoadingScreen from '../components/LoadingScreen';
import ErrorScreen from '../components/ErrorScreen';
import ConnectionStatus from '../components/ConnectionStatus';

const VerticalDisplayScreen: React.FC = () => {
  const { data, isLoading, error } = useDisplayData();
  const { isOnline } = useNetworkStatus();

  if (isLoading) {
    return <LoadingScreen />;
  }

  // Handle offline mode gracefully - only show error screen if no cached data AND online
  if (error || !data?.configured) {
    // If we're offline and have no data at all, show offline message
    if (!isOnline && !data) {
      return (
        <div style={{
          height: '100vh',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          background: '#000',
          color: '#fff',
          fontFamily: 'system-ui',
          flexDirection: 'column',
          gap: '20px'
        }}>
          <div style={{ fontSize: '3rem' }}>📡</div>
          <div style={{ fontSize: '1.5rem', textAlign: 'center' }}>
            Sem conexão com internet
          </div>
          <div style={{ fontSize: '1rem', opacity: 0.7, textAlign: 'center' }}>
            Aguardando reconexão para carregar o conteúdo...
          </div>
          <ConnectionStatus />
        </div>
      );
    }

    // If we're online or have cached data that's not configured, show normal error
    if (isOnline && (error || !data?.configured)) {
      const errorMessage = data?.error || (error as any)?.message || 'Device not configured';
      const errorDetails = error ? `API Error: ${(error as any)?.message}` : data?.error;

      return (
        <ErrorScreen
          message={errorMessage}
          details={errorDetails}
        />
      );
    }

    // If we're offline but have cached data, continue with cached data
    // (fall through to normal display)
  }

  return (
    <div style={{
      height: '100vh',
      background: '#f8f9fa',
      padding: '2vh',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Compact Header for Vertical Layout */}
      <div style={{
        height: '14vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'white',
        borderRadius: '16px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        marginBottom: '2vh',
        padding: '1vh 2vh',
        gap: '1vh',
      }}>
        {/* Top Row: Logo and DateTime */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          height: '6vh',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
          }}>
            <img
              src="/static/display/logo.png"
              alt="Company Logo"
              style={{
                height: '5vh',
                objectFit: 'contain',
              }}
            />
          </div>
          <div style={{
            flex: '1',
            display: 'flex',
            justifyContent: 'center',
          }}>
            <DateTimeWidget />
          </div>
        </div>

        {/* Bottom Row: Weather (Centered) */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '6vh',
        }}>
          {data?.weather && <WeatherWidget weather={data.weather} />}
        </div>
      </div>

      {/* Main Content - Vertical Stack */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        gap: '2vh',
        height: 'calc(84vh - 4vh)',
      }}>
        {/* Media Rotator - Takes up 60% of remaining space */}
        <div style={{
          flex: '0 0 60%',
          position: 'relative',
          overflow: 'hidden',
          minHeight: '40vh',
        }}>
          <MediaRotator media={data?.media || []} debug={true} />
        </div>

        {/* Birthday Panel - Takes up 40% of remaining space */}
        <div style={{
          flex: '0 0 40%',
          background: 'white',
          borderRadius: '16px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          padding: '2vh',
          display: 'flex',
          flexDirection: 'column',
          minHeight: '25vh',
          position: 'relative',
        }}>
          <BirthdayPanel birthdays={data?.birthdays || []} />

          {/* Version indicator */}
          <div style={{
            position: 'absolute',
            bottom: '1vh',
            right: '2vh',
            fontSize: '12px',
            color: 'rgba(0, 0, 0, 0.3)',
            fontFamily: 'monospace',
            letterSpacing: '0.5px',
          }}>
            v{data?.version || 'unknown'}
          </div>
        </div>
      </div>

      {/* Connection Status Indicator */}
      <ConnectionStatus />
    </div>
  );
};

export default VerticalDisplayScreen;