import React from 'react';

const Login: React.FC = () => {
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
        <h1 style={{ color: '#0B5895', marginBottom: '1rem' }}>
          Login
        </h1>
        <p style={{ color: '#666', marginBottom: '1rem' }}>
          React login interface coming soon...
        </p>
        <a
          href="/login"
          style={{
            color: '#009FFF',
            textDecoration: 'none',
            fontSize: '1.1rem',
          }}
        >
          Use Legacy Login
        </a>
      </div>
    </div>
  );
};

export default Login;