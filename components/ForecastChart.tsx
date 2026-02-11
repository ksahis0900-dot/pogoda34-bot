import React, { useMemo } from 'react';
import { DayForecast } from '../types';

interface Props {
  forecast: DayForecast[];
}

export const ForecastChart: React.FC<Props> = ({ forecast }) => {
  // Вычисляем данные для SVG
  const { points, areaPath, linePath, minTemp, maxTemp } = useMemo(() => {
    if (!forecast.length) return { points: [], areaPath: '', linePath: '', minTemp: 0, maxTemp: 0 };

    const temps = forecast.map(d => d.tempHigh);
    const min = Math.min(...temps) - 2; // Добавляем отступ снизу
    const max = Math.max(...temps) + 2; // Добавляем отступ сверху
    const range = max - min;
    
    // Размеры SVG координатной сетки (не пиксели, а единицы viewBox)
    const width = 100;
    const height = 50;
    
    const calculatedPoints = forecast.map((day, index) => {
      const x = (index / (forecast.length - 1)) * width;
      // Инвертируем Y, так как в SVG 0 сверху
      const y = height - ((day.tempHigh - min) / range) * height;
      return { x, y, temp: day.tempHigh, day: day.day };
    });

    // Генерация пути линии (L = Line to)
    const linePathCmd = calculatedPoints.map((p, i) => 
      `${i === 0 ? 'M' : 'L'} ${p.x},${p.y}`
    ).join(' ');

    // Генерация пути области (для градиента)
    const areaPathCmd = `
      ${linePathCmd} 
      L ${width},${height} 
      L 0,${height} 
      Z
    `;

    return { 
      points: calculatedPoints, 
      linePath: linePathCmd, 
      areaPath: areaPathCmd,
      minTemp: min,
      maxTemp: max
    };
  }, [forecast]);

  return (
    <div className="w-full bg-white/5 backdrop-blur-sm rounded-3xl p-4 my-6 border border-white/10 shadow-inner flex flex-col relative overflow-hidden">
      <h3 className="text-lg font-semibold mb-6 px-2 flex items-center gap-2 relative z-10">
        <span className="w-2 h-2 rounded-full bg-yellow-400"></span>
        График температур
      </h3>

      <div className="relative w-full h-40">
        <svg 
          viewBox="0 0 100 65" 
          preserveAspectRatio="none" 
          className="w-full h-full overflow-visible"
        >
          <defs>
            <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#fbbf24" stopOpacity="0" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="1" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          {/* Область под графиком */}
          <path 
            d={areaPath} 
            fill="url(#chartGradient)" 
            className="opacity-50"
          />

          {/* Линия графика */}
          <path 
            d={linePath} 
            fill="none" 
            stroke="#fbbf24" 
            strokeWidth="1.5" 
            strokeLinecap="round" 
            strokeLinejoin="round"
            filter="url(#glow)"
            className="drop-shadow-lg"
          />

          {/* Точки и подписи */}
          {points.map((p, i) => (
            <g key={i}>
              {/* Линия к точке (опционально, для стиля) */}
              <line 
                x1={p.x} y1={p.y} 
                x2={p.x} y2={65} 
                stroke="white" 
                strokeOpacity="0.1" 
                strokeDasharray="1 1" 
                strokeWidth="0.5"
              />

              {/* Точка */}
              <circle 
                cx={p.x} 
                cy={p.y} 
                r="1.5" 
                fill="#fbbf24" 
                stroke="#fff" 
                strokeWidth="0.5"
              />

              {/* Текст температуры */}
              <text 
                x={p.x} 
                y={p.y - 4} 
                textAnchor="middle" 
                fill="white" 
                fontSize="4" 
                fontWeight="bold"
                className="drop-shadow-md"
              >
                {p.temp}°
              </text>

              {/* День недели (внизу) */}
              <text 
                x={p.x} 
                y="65" 
                textAnchor="middle" 
                fill="#94a3b8" 
                fontSize="3.5"
              >
                {p.day}
              </text>
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
};