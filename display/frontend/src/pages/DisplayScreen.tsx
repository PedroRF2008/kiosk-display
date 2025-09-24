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

const DisplayScreen: React.FC = () => {
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
      {/* Header */}
      <div style={{
        height: '16vh',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1.5vh 2vw',
        background: 'white',
        borderRadius: '20px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
        marginBottom: '2vh',
        gap: '1.5vw',
      }}>
        {/* Logo Section */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          minWidth: '15vw',
          flex: '0 0 auto',
        }}>
          <img
            src="/static/display/logo.png"
            alt="Company Logo"
            style={{
              height: '10vh',
              objectFit: 'contain',
            }}
          />
        </div>

        {/* DateTime Section */}
        <div style={{
          flex: '1 1 auto',
          display: 'flex',
          justifyContent: 'center',
          maxWidth: '40vw',
        }}>
          <DateTimeWidget />
        </div>

        {/* Weather Section */}
        <div style={{
          flex: '0 0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
        }}>
          {data?.weather && <WeatherWidget weather={data.weather} />}
        </div>
      </div>

      {/* Main Content */}
      <div style={{
        flex: 1,
        display: 'flex',
        gap: '2vh',
        height: 'calc(82vh - 4vh)',
      }}>
        <div style={{
          flex: 1,
          position: 'relative',
          overflow: 'hidden',
          height: '100%',
        }}>
          <MediaRotator media={data?.media || []} debug={true} />
        </div>

        <div style={{
          width: '25vw',
          background: 'white',
          borderRadius: '20px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          padding: '2vh',
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
        }}>
          <BirthdayPanel birthdays={data?.birthdays || []} />

          <div style={{
            position: 'fixed',
            bottom: 0,
            right: 0,
            fontSize: '14px',
            color: 'rgba(0, 0, 0, 0.3)',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            padding: '6px 10px',
            borderRadius: '4px 0 0 0',
            backdropFilter: 'blur(5px)',
            fontFamily: 'monospace',
            letterSpacing: '0.5px',
            boxShadow: '-2px -2px 4px rgba(0, 0, 0, 0.1)',
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

export default DisplayScreen;