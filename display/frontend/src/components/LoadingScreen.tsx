import React from 'react';

const LoadingScreen: React.FC = () => {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: '#f8f9fa',
      flexDirection: 'column',
    }}>
      <div style={{
        width: '60px',
        height: '60px',
        border: '4px solid #e3e3e3',
        borderTop: '4px solid #009FFF',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        marginBottom: '1rem',
      }}></div>
      <p style={{
        color: '#666',
        fontSize: '1.2rem',
        margin: 0,
      }}>
        Loading display...
      </p>

      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `
      }} />
    </div>
  );
};

export default LoadingScreen;