import React from 'react';
import { HourlyForecast as HourlyForecastType } from '../types';
import { WeatherIcon } from './WeatherIcon';

interface Props {
  hourly: HourlyForecastType[];
}

export const HourlyForecast: React.FC<Props> = ({ hourly }) => {
  if (!hourly || hourly.length === 0) return null;

  return (
    <div className="w-full mb-6">
      <h3 className="text-lg font-semibold mb-3 px-2 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-blue-300"></span>
        Почасовой прогноз
      </h3>
      <div className="flex overflow-x-auto pb-4 gap-3 px-2 custom-scrollbar snap-x">
        {hourly.map((hour, idx) => (
          <div 
            key={idx} 
            className="flex flex-col items-center justify-between min-w-[70px] p-3 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/5 snap-center hover:bg-white/10 transition-colors"
          >
            <span className="text-sm text-gray-300 font-medium">{hour.time}</span>
            <WeatherIcon condition={hour.condition} className="w-8 h-8 my-3 text-white drop-shadow-md" />
            <span className="text-xl font-bold">{hour.temp}°</span>
          </div>
        ))}
      </div>
    </div>
  );
};
