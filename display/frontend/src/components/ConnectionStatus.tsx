import React from 'react';
import { useNetworkStatus } from '../hooks/useNetworkStatus';

const ConnectionStatus: React.FC = () => {
  const { isOnline, connectionLostAt } = useNetworkStatus();

  if (isOnline) {
    return null; // Don't show anything when online
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div style={{
      position: 'fixed',
      bottom: '20px',
      left: '20px',
      background: 'linear-gradient(135deg, #ff6b6b, #ee5a52)',
      color: 'white',
      padding: '12px 20px',
      borderRadius: '12px',
      boxShadow: '0 4px 12px rgba(255, 107, 107, 0.4)',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      fontSize: '14px',
      fontWeight: '500',
      zIndex: 1000,
      border: '1px solid rgba(255, 255, 255, 0.2)',
      backdropFilter: 'blur(10px)',
    }}>
      {/* Warning Icon */}
      <div style={{
        width: '20px',
        height: '20px',
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '12px',
      }}>
        ⚠️
      </div>

      <div>
        <div style={{ fontWeight: '600' }}>
          Conexão Perdida
        </div>
        <div style={{
          fontSize: '12px',
          opacity: 0.9,
          marginTop: '2px'
        }}>
          {connectionLostAt && `Desde ${formatTime(connectionLostAt)}`}
        </div>
      </div>

      {/* Pulsing indicator */}
      <div style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        background: 'rgba(255, 255, 255, 0.8)',
        animation: 'pulse 2s infinite',
      }} />

      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
          }
        `
      }} />
    </div>
  );
};

export default ConnectionStatus;