import React, { useState, useEffect } from 'react';

const DateTimeWidget: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '1.5vw',
      background: '#f0f3f5',
      padding: '1.5vh 2vw',
      borderRadius: '15px',
      boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.05)',
      height: '12vh',
      minWidth: '24vw',
      maxWidth: '32vw',
    }}>
      <div style={{
        fontSize: '8vh',
        fontWeight: '900',
        color: '#0B5895',
        lineHeight: 1,
        letterSpacing: '-2px',
        minWidth: '12vw',
        textAlign: 'center',
        fontFamily: 'monospace',
      }}>
        {currentTime.toLocaleTimeString('pt-BR', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        })}
      </div>
      <div style={{
        borderLeft: '2px solid #C4CCD1',
        paddingLeft: '1.5vw',
        height: '8vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
      }}>
        <div style={{
          fontSize: '2.8vh',
          color: '#3A3A3A',
          lineHeight: 1.1,
          fontWeight: '500',
          textTransform: 'capitalize',
        }}>
          {currentTime.toLocaleDateString('pt-BR', { weekday: 'long' })}
        </div>
        <div style={{
          fontSize: '2.4vh',
          color: '#666',
          lineHeight: 1.1,
          marginTop: '0.3vh',
        }}>
          {currentTime.toLocaleDateString('pt-BR', {
            day: 'numeric',
            month: 'long'
          })}
        </div>
      </div>
    </div>
  );
};

export default DateTimeWidget;