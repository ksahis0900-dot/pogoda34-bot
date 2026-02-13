import { fetchOpenWeatherForecast } from './openWeatherService';
import { WeatherData, Location } from "../types";

export const fetchWeatherForecast = async (city: string = "Волгоград"): Promise<WeatherData> => {
  try {
    // Use OpenWeather API as primary (works without VPN)
    const data = await fetchOpenWeatherForecast(city);

    // Background ping to Render bot to keep it alive
    fetch('https://pogoda34-bot.onrender.com/').catch(() => { });

    return data;
  } catch (error) {
    console.error("Failed to fetch weather data:", error);
    // Return fallback data if API fails
    return {
      location: { name: `${city} (Ошибка)`, country: "RU" },
      current: {
        temp: 0,
        condition: "Ошибка",
        feels_like: 0,
        humidity: 0,
        wind_speed: 0,
        wind_deg: 0,
        pressure: 0,
        description: "Не удалось загрузить данные."
      },
      hourly: [],
      forecast: []
    };
  }
};