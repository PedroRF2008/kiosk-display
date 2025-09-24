import React from 'react';

interface ErrorScreenProps {
  message: string;
  details?: string;
}

const ErrorScreen: React.FC<ErrorScreenProps> = ({ message, details }) => {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      margin: 0,
      background: '#000',
      color: '#fff',
      fontFamily: 'sans-serif',
    }}>
      <div style={{
        textAlign: 'center',
        padding: '2rem',
        maxWidth: '600px',
      }}>
        <h1 style={{
          fontSize: '2.5rem',
          marginBottom: '1rem',
          color: '#ff6b6b',
        }}>
          Erro de Conexão
        </h1>
        <p style={{
          fontSize: '1.2rem',
          marginBottom: '1rem',
          color: '#ccc',
        }}>
          {message || 'Não foi possível conectar ao servidor.'}
        </p>
        {details && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.1)',
            padding: '1rem',
            borderRadius: '8px',
            marginTop: '1rem',
            fontSize: '0.9rem',
            color: '#ffeb3b',
            textAlign: 'left',
          }}>
            <strong>Detalhes:</strong><br/>
            {details}
          </div>
        )}
        <div style={{
          marginTop: '2rem',
          fontSize: '0.9rem',
          color: '#999',
        }}>
          <p>Verifique se:</p>
          <ul style={{ textAlign: 'left', display: 'inline-block' }}>
            <li>O servidor Flask está rodando (porta 5000)</li>
            <li>A configuração do Firebase está correta</li>
            <li>O dispositivo está registrado no sistema</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ErrorScreen;