import React from 'react';
import type { WeatherData } from '../types';

interface WeatherWidgetProps {
  weather: WeatherData;
}

const WeatherWidget: React.FC<WeatherWidgetProps> = ({ weather }) => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '1.5vw',
      background: 'linear-gradient(135deg, #009FFF, #0B5895)',
      padding: '1.5vh 2vw',
      borderRadius: '15px',
      boxShadow: '0 6px 12px rgba(0,159,255,0.2)',
      color: 'white',
      height: '12vh',
      width: '45vw',
      border: '1px solid rgba(255,255,255,0.1)',
    }}>
      {/* Temperature and Icon Section */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '1.5vw',
        minWidth: '14vw',
      }}>
        <div style={{
          background: 'rgba(255, 255, 255, 0.15)',
          borderRadius: '50%',
          padding: '1vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1px solid rgba(255,255,255,0.2)',
        }}>
          <img
            src={`http://openweathermap.org/img/wn/${weather.icon}@2x.png`}
            alt="Weather"
            style={{
              width: '7vh',
              height: '7vh',
              filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
            }}
          />
        </div>
        <div style={{
          fontSize: '6vh',
          fontWeight: 'bold',
          lineHeight: 1,
          textShadow: '0 2px 4px rgba(0,0,0,0.3)',
          minWidth: '8vw',
          textAlign: 'center',
        }}>
          {weather.temperature}°
        </div>
      </div>

      {/* Weather Details Grid */}
      <div style={{
        borderLeft: '2px solid rgba(255, 255, 255, 0.25)',
        paddingLeft: '1.5vw',
        marginLeft: '0.8vw',
        fontSize: '2.2vh',
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '1.2vh 2vw',
        alignItems: 'center',
        minWidth: '16vw',
      }}>
        <div style={{
          whiteSpace: 'nowrap',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5vw',
        }}>
          <span style={{
            fontSize: '2vh',
            opacity: 0.9,
            minWidth: '1.8vw',
            textAlign: 'center',
          }}>🌡️</span>
          <span style={{ fontSize: '2.1vh', fontWeight: '500' }}>
            Máx: {weather.temp_max}°C
          </span>
        </div>
        <div style={{
          whiteSpace: 'nowrap',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5vw',
        }}>
          <span style={{
            fontSize: '2vh',
            opacity: 0.9,
            minWidth: '1.8vw',
            textAlign: 'center',
          }}>🌧️</span>
          <span style={{ fontSize: '2.1vh', fontWeight: '500' }}>
            Chuva: {weather.rain_chance}%
          </span>
        </div>
        <div style={{
          whiteSpace: 'nowrap',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5vw',
        }}>
          <span style={{
            fontSize: '2vh',
            opacity: 0.9,
            minWidth: '1.8vw',
            textAlign: 'center',
          }}>❄️</span>
          <span style={{ fontSize: '2.1vh', fontWeight: '500' }}>
            Mín: {weather.temp_min}°C
          </span>
        </div>
        <div style={{
          whiteSpace: 'nowrap',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5vw',
        }}>
          <span style={{
            fontSize: '2vh',
            opacity: 0.9,
            minWidth: '1.8vw',
            textAlign: 'center',
          }}>💧</span>
          <span style={{ fontSize: '2.1vh', fontWeight: '500' }}>
            Umidade: {weather.humidity}%
          </span>
        </div>
      </div>

      {/* Weather Description */}
      <div style={{
        borderLeft: '2px solid rgba(255, 255, 255, 0.25)',
        paddingLeft: '2vw',
        marginLeft: '1vw',
        minWidth: '8vw',
        textAlign: 'center',
      }}>
        <div style={{
          fontSize: '1.6vh',
          opacity: 0.9,
          textTransform: 'capitalize',
          lineHeight: 1.2,
          fontWeight: '400',
        }}>
          {weather.weather}
        </div>
        <div style={{
          fontSize: '1.4vh',
          opacity: 0.7,
          marginTop: '0.3vh',
        }}>
          {weather.city}
        </div>
      </div>
    </div>
  );
};

export default WeatherWidget;