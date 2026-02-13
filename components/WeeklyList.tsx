import React from 'react';
import { DayForecast } from '../types';
import { WeatherIcon } from './WeatherIcon';

interface Props {
  forecast: DayForecast[];
}

export const WeeklyList: React.FC<Props> = ({ forecast }) => {
  // Find global min/max for the progress bar calculation
  const minTemp = Math.min(...forecast.map(d => d.tempLow));
  const maxTemp = Math.max(...forecast.map(d => d.tempHigh));
  const range = maxTemp - minTemp || 1; // Avoid division by zero

  return (
    <div className="flex flex-col gap-3 pb-8">
      {forecast.map((day, idx) => {
        // Calculate relative positions for the temperature bar
        const leftPercent = ((day.tempLow - minTemp) / range) * 100;
        const widthPercent = ((day.tempHigh - day.tempLow) / range) * 100;

        return (
          <div key={idx} className="grid grid-cols-[2.5rem_3rem_1fr] items-center gap-3 p-3 rounded-xl hover:bg-white/5 transition-colors">
            {/* Column 1: Day Name (Short) */}
            <div className="font-semibold text-lg text-white/90">
              {day.day}
            </div>
            
            {/* Column 2: Icon and Precip Chance */}
            <div className="flex flex-col items-center justify-center relative">
               <WeatherIcon condition={day.condition} className="w-8 h-8 text-blue-200 drop-shadow-sm" />
               {day.precipitationChance > 20 && (
                   <span className="absolute -bottom-1 -right-2 bg-blue-500/90 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full backdrop-blur-sm border border-white/10 shadow-sm">
                     {day.precipitationChance}%
                   </span>
               )}
            </div>

            {/* Column 3: Temperature Bar */}
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-400 w-8 text-right font-mono">{day.tempLow}°</span>
              
              <div className="flex-1 h-2 bg-gray-700/50 rounded-full relative overflow-hidden">
                <div 
                    className="absolute h-full rounded-full bg-gradient-to-r from-blue-400 to-yellow-400 opacity-90 shadow-[0_0_10px_rgba(250,204,21,0.5)]"
                    style={{
                        left: `${leftPercent}%`,
                        width: `${widthPercent}%`,
                        minWidth: '6px' // Visual anchor for equal temps
                    }}
                />
              </div>

              <span className="text-sm text-white w-8 text-left font-mono">{day.tempHigh}°</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};