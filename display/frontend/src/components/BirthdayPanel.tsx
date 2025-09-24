import React from 'react';
import type { Birthday } from '../types';

interface BirthdayPanelProps {
  birthdays: Birthday[];
}

const BirthdayPanel: React.FC<BirthdayPanelProps> = ({ birthdays }) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}`;
  };

  return (
    <>
      <div style={{
        fontSize: '2.8vh',
        color: '#0B5895',
        marginBottom: '1.5vh',
        paddingBottom: '0.8vh',
        borderBottom: '3px solid #009FFF',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
      }}>
        🎂 Próximos Aniversários
      </div>

      <div style={{
        flex: 1,
        overflowY: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: '1vh',
      }}>
        {birthdays.length === 0 ? (
          <div style={{
            textAlign: 'center',
            color: '#666',
            fontSize: '2vh',
            padding: '2vh',
          }}>
            Nenhum aniversário próximo
          </div>
        ) : (
          birthdays.slice(0, 5).map((birthday) => (
            <div
              key={`${birthday.name}-${birthday.date}`}
              style={{
                background: birthday.is_today
                  ? 'linear-gradient(to right, rgba(255, 215, 0, 0.1), #f0f3f5 80%)'
                  : '#f0f3f5',
                padding: '1.2vh',
                borderRadius: '10px',
                borderLeft: `4px solid ${birthday.is_today ? '#FFD700' : '#009FFF'}`,
                position: 'relative',
                height: 'calc((100% - 4vh) / 5)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                animation: birthday.is_today ? 'pulse 2s ease-in-out infinite' : 'none',
              }}
            >
              <div style={{
                fontSize: '2.2vh',
                fontWeight: 'bold',
                color: birthday.is_today ? '#FFD700' : '#0B5895',
                marginBottom: '0.3vh',
              }}>
                {birthday.name}
              </div>
              <div style={{
                fontSize: '1.8vh',
                color: '#3A3A3A',
              }}>
                {birthday.is_today ? 'Hoje! 🎂' : formatDate(birthday.date)}
              </div>
              <div style={{
                fontSize: '1.6vh',
                color: '#3A3A3A',
                fontStyle: 'italic',
              }}>
                {birthday.sector}
              </div>
              {birthday.is_today && (
                <div style={{
                  position: 'absolute',
                  right: '1.5vh',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  fontSize: '2.5vh',
                  animation: 'celebrate 1s ease infinite',
                }}>
                  🎉
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes celebrate {
            0% { transform: translateY(-50%) rotate(0deg); }
            25% { transform: translateY(-50%) rotate(15deg); }
            75% { transform: translateY(-50%) rotate(-15deg); }
            100% { transform: translateY(-50%) rotate(0deg); }
          }

          @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(255, 215, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0); }
          }
        `
      }} />
    </>
  );
};

export default BirthdayPanel;