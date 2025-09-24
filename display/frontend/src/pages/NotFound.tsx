import React from 'react';

const NotFound: React.FC = () => {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: '#f8f9fa',
    }}>
      <div style={{
        textAlign: 'center',
        padding: '2rem',
        background: 'white',
        borderRadius: '10px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      }}>
        <h1 style={{ color: '#dc3545', marginBottom: '1rem' }}>
          404 - Page Not Found
        </h1>
        <p style={{ color: '#666', marginBottom: '1rem' }}>
          The page you're looking for doesn't exist.
        </p>
        <a
          href="/"
          style={{
            color: '#009FFF',
            textDecoration: 'none',
            fontSize: '1.1rem',
          }}
        >
          Return to Display
        </a>
      </div>
    </div>
  );
};

export default NotFound;