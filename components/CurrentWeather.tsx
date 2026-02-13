import React from 'react';
import { CurrentWeather as CurrentWeatherType } from '../types';
import { WeatherIcon } from './WeatherIcon';
import { Droplets, Wind, Thermometer } from 'lucide-react';

interface Props {
  data: CurrentWeatherType;
  location: string;
}

export const CurrentWeather: React.FC<Props> = ({ data, location }) => {
  return (
    <div className="flex flex-col items-center justify-center p-6 text-white text-center relative z-10">
      <h2 className="text-2xl font-light tracking-wide mb-1">{location}</h2>
      <div className="bg-white/10 backdrop-blur-md rounded-full px-3 py-1 text-sm font-medium text-blue-100 mb-6 border border-white/20">
        Сейчас
      </div>

      <div className="flex flex-col items-center mb-8">
        <WeatherIcon condition={data.condition} className="w-32 h-32 mb-4 animate-pulse-slow text-yellow-300 drop-shadow-lg" />
        <h1 className="text-8xl font-bold tracking-tighter drop-shadow-xl">
          {data.temp}°
        </h1>
        <p className="text-xl font-medium mt-2 capitalize text-blue-100">{data.description}</p>
        
        {/* Funny Feels Like Section */}
        <div className="mt-4 max-w-xs bg-white/5 rounded-xl p-3 backdrop-blur-sm border border-white/5">
            <p className="text-sm font-semibold text-yellow-200 italic">
                "{data.feelsLikePhrase}"
            </p>
            <p className="text-xs text-blue-200 opacity-80 mt-1">
                (Ощущается как {data.feelsLike}°)
            </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 w-full max-w-sm bg-white/10 backdrop-blur-lg rounded-2xl p-4 border border-white/10 shadow-lg">
        <div className="flex flex-col items-center">
          <Wind className="w-5 h-5 mb-1 text-blue-300" />
          <span className="text-lg font-semibold">{data.windSpeed}</span>
          <span className="text-xs text-blue-200">км/ч</span>
        </div>
        <div className="flex flex-col items-center border-l border-r border-white/10">
          <Droplets className="w-5 h-5 mb-1 text-blue-300" />
          <span className="text-lg font-semibold">{data.humidity}%</span>
          <span className="text-xs text-blue-200">Влажн.</span>
        </div>
        <div className="flex flex-col items-center">
          <Thermometer className="w-5 h-5 mb-1 text-blue-300" />
          <span className="text-lg font-semibold">{data.pressure}</span>
          <span className="text-xs text-blue-200">гПа</span>
        </div>
        {/* Wind Description Context */}
        <div className="col-span-3 pt-2 mt-2 border-t border-white/10 text-center">
             <p className="text-xs text-blue-200 italic">"{data.windDescription}"</p>
        </div>
      </div>
    </div>
  );
};