import React, { useEffect, useState } from 'react';
import { fetchWeatherForecast } from './services/weatherService';
import { WeatherData } from './types';
import { CurrentWeather } from './components/CurrentWeather';
import { WeeklyList } from './components/WeeklyList';
import { HourlyForecast } from './components/HourlyForecast';
import { Loader2, RefreshCw, MapPin, Clock } from 'lucide-react';

const CITIES = [
  'Волгоград',
  'Волжский',
  'Камышин',
  'Михайловка',
  'Урюпинск',
  'Фролово',
  'Калач-на-Дону',
  'Котово',
  'Городище',
  'Суровикино'
];

const REFRESH_INTERVAL_MS = 15 * 60 * 1000; // 15 minutes

const App: React.FC = () => {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);
  const [selectedCity, setSelectedCity] = useState<string>('Волгоград');
  
  // Timer states
  const [nextUpdate, setNextUpdate] = useState<number>(Date.now() + REFRESH_INTERVAL_MS);
  const [timeLeftStr, setTimeLeftStr] = useState<string>("15:00");

  const loadData = async (isBackgroundRefresh = false) => {
    if (!isBackgroundRefresh) setLoading(true);
    setError(false);
    try {
      const data = await fetchWeatherForecast(selectedCity);
      setWeather(data);
      // Reset timer on successful load
      setNextUpdate(Date.now() + REFRESH_INTERVAL_MS);
    } catch (e) {
      console.error(e);
      if (!isBackgroundRefresh) setError(true);
    } finally {
      if (!isBackgroundRefresh) setLoading(false);
    }
  };

  useEffect(() => {
    // Initial load
    loadData();
  }, [selectedCity]); // Re-load when city changes

  // Countdown Timer Logic
  useEffect(() => {
    const timerId = setInterval(() => {
      const now = Date.now();
      const diff = nextUpdate - now;

      if (diff <= 0) {
        // Time to refresh
        loadData(true);
        setNextUpdate(Date.now() + REFRESH_INTERVAL_MS);
      } else {
        // Update display string
        const minutes = Math.floor(diff / 60000);
        const seconds = Math.floor((diff % 60000) / 1000);
        setTimeLeftStr(`${minutes}:${seconds < 10 ? '0' : ''}${seconds}`);
      }
    }, 1000);

    return () => clearInterval(timerId);
  }, [nextUpdate, selectedCity]); // Dependency ensures timer doesn't break on updates

  // Dynamic background based on weather condition
  const getBackgroundClass = (condition?: string) => {
    const c = condition?.toLowerCase() || '';
    if (c.includes('дождь') || c.includes('гроза')) return 'bg-gradient-to-br from-slate-900 via-slate-800 to-blue-900';
    if (c.includes('ясно') || c.includes('солн')) return 'bg-gradient-to-br from-blue-500 via-blue-400 to-blue-300';
    if (c.includes('облач')) return 'bg-gradient-to-br from-slate-600 via-slate-500 to-blue-400';
    return 'bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900';
  };

  return (
    <div className={`min-h-screen w-full transition-colors duration-700 ease-in-out ${getBackgroundClass(weather?.current.condition)}`}>
      <div className="max-w-md mx-auto min-h-screen flex flex-col relative overflow-hidden">
        
        {/* Decorative Background Elements */}
        <div className="absolute top-[-10%] left-[-10%] w-64 h-64 bg-white/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-[20%] right-[-10%] w-80 h-80 bg-blue-500/20 rounded-full blur-3xl pointer-events-none"></div>

        {/* Header Actions */}
        <div className="flex justify-between items-start p-4 z-20">
            <div className="flex items-center gap-2 bg-white/10 rounded-full px-3 py-1.5 backdrop-blur-md border border-white/10 shadow-lg">
              <MapPin className="w-4 h-4 text-white/80" />
              <select 
                value={selectedCity}
                onChange={(e) => setSelectedCity(e.target.value)}
                className="bg-transparent text-white text-sm font-medium outline-none appearance-none cursor-pointer w-24"
                disabled={loading}
              >
                {CITIES.map(city => (
                  <option key={city} value={city} className="text-black">{city}</option>
                ))}
              </select>
            </div>

            <div className="flex flex-col items-end gap-1">
                <button 
                    onClick={() => loadData(false)} 
                    className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-all backdrop-blur-md active:scale-95 border border-white/10 shadow-lg group"
                    disabled={loading}
                >
                    <RefreshCw className={`w-5 h-5 text-white ${loading ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`} />
                </button>
                {/* Countdown Timer */}
                {!loading && !error && (
                  <div className="flex items-center gap-1 text-[10px] text-blue-100 bg-black/30 px-2 py-0.5 rounded-full backdrop-blur-md border border-white/5">
                    <Clock className="w-3 h-3" />
                    <span>Обновление: {timeLeftStr}</span>
                  </div>
                )}
            </div>
        </div>

        {loading && !weather ? (
          <div className="flex-1 flex flex-col items-center justify-center text-white space-y-4">
            <Loader2 className="w-12 h-12 animate-spin text-blue-200" />
            <p className="animate-pulse">Прогноз для {selectedCity}...</p>
          </div>
        ) : error ? (
            <div className="flex-1 flex flex-col items-center justify-center text-white p-6 text-center">
                <p className="text-xl mb-4">😔</p>
                <p>Не удалось получить данные для города {selectedCity}.</p>
                <button onClick={() => loadData(false)} className="mt-4 px-6 py-2 bg-white/20 rounded-lg">Попробовать снова</button>
            </div>
        ) : weather ? (
          <div className="flex-1 overflow-y-auto pb-10 custom-scrollbar z-10">
            {/* Main Current Weather Card */}
            <CurrentWeather data={weather.current} location={weather.location} />

            <div className="px-4 mt-2">
                {/* Hourly Forecast */}
                <HourlyForecast hourly={weather.hourly} />

                {/* Weekly List */}
                <h3 className="text-lg font-semibold mb-3 px-2 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                    Прогноз на 7 дней
                </h3>
                <div className="bg-black/20 backdrop-blur-md rounded-3xl p-4 border border-white/5 shadow-lg mb-6">
                    <WeeklyList forecast={weather.forecast} />
                </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default App;