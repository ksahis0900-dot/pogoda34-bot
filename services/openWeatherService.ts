import axios from 'axios';

interface OpenWeatherCurrent {
  temp: number;
  feels_like: number;
  pressure: number;
  humidity: number;
  wind_speed: number;
  wind_deg: number;
  weather: [{
    main: string;
    description: string;
    icon: string;
  }];
}

interface OpenWeatherHourly {
  dt: number;
  temp: number;
  weather: [{
    main: string;
    description: string;
    icon: string;
  }];
}

interface OpenWeatherDaily {
  dt: number;
  temp: {
    day: number;
    min: number;
    max: number;
  };
  weather: [{
    main: string;
    description: string;
    icon: string;
  }];
}

interface OpenWeatherResponse {
  current: OpenWeatherCurrent;
  hourly: OpenWeatherHourly[];
  daily: OpenWeatherDaily[];
}

interface WeatherData {
  current: {
    temp: number;
    feels_like: number;
    pressure: number;
    humidity: number;
    wind_speed: number;
    wind_deg: number;
    condition: string;
    icon: string;
  };
  location: {
    name: string;
    country: string;
  };
  hourly: Array<{
    time: string;
    temp: number;
    condition: string;
    icon: string;
  }>;
  forecast: Array<{
    date: string;
    temp_max: number;
    temp_min: number;
    condition: string;
    icon: string;
  }>;
}

// API key - hardcoded for Netlify compatibility
const API_KEY = 'bafd7faf0a523d40f16892a82b062065';
const BASE_URL = 'https://api.openweathermap.org/data/2.5';

const getRussianCityName = (cityName: string): string => {
  const cityMap: Record<string, string> = {
    'Волгоград': 'Volgograd',
    'Волжский': 'Volzhskiy',
    'Камышин': 'Kamyshin',
    'Михайловка': 'Mikhaylovka',
    'Урюпинск': 'Uryupinsk',
    'Фролово': 'Frolovo',
    'Калач-на-Дону': 'Kalach-na-Donu',
    'Котово': 'Kotovo',
    'Городище': 'Gorodishche',
    'Суровикино': 'Surovikino'
  };
  return cityMap[cityName] || cityName;
};

const formatTime = (timestamp: number): string => {
  return new Date(timestamp * 1000).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

const formatDate = (timestamp: number): string => {
  return new Date(timestamp * 1000).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short'
  });
};

const getWeatherIcon = (iconCode: string): string => {
  const iconMap: Record<string, string> = {
    '01d': 'sun',
    '01n': 'moon',
    '02d': 'cloud-sun',
    '02n': 'cloud-moon',
    '03d': 'cloud',
    '03n': 'cloud',
    '04d': 'cloud',
    '04n': 'cloud',
    '09d': 'cloud-rain',
    '09n': 'cloud-rain',
    '10d': 'cloud-rain',
    '10n': 'cloud-rain',
    '11d': 'zap',
    '11n': 'zap',
    '13d': 'snowflake',
    '13n': 'snowflake',
    '50d': 'wind',
    '50n': 'wind'
  };
  return iconMap[iconCode] || 'sun';
};

export const fetchOpenWeatherForecast = async (cityName: string): Promise<WeatherData> => {
  try {
    const englishCityName = getRussianCityName(cityName);
    
    // First get coordinates for the city
    const geoResponse = await axios.get(`${BASE_URL}/weather`, {
      params: {
        q: englishCityName,
        appid: API_KEY,
        units: 'metric',
        lang: 'ru'
      }
    });

    const geoData = geoResponse.data;
    const lat = geoData.coord.lat;
    const lon = geoData.coord.lon;

    // Use One Call API for more comprehensive weather data
    const oneCallResponse = await axios.get(`${BASE_URL}/onecall`, {
      params: {
        lat: lat,
        lon: lon,
        appid: API_KEY,
        units: 'metric',
        lang: 'ru',
        exclude: 'minutely,alerts' // Exclude minutely forecast and alerts
      }
    });

    const oneCallData = oneCallResponse.data;

    // Process current weather
    const current = oneCallData.current;
    
    // Process hourly forecast (next 24 hours)
    const hourly = oneCallData.hourly.slice(0, 24).map((item: any) => ({
      time: formatTime(item.dt),
      temp: Math.round(item.temp),
      condition: item.weather[0].description,
      icon: getWeatherIcon(item.weather[0].icon)
    }));

    // Process daily forecast (next 5 days)
    const forecast = oneCallData.daily.slice(0, 5).map((item: any) => ({
      date: formatDate(item.dt),
      temp_max: Math.round(item.temp.max),
      temp_min: Math.round(item.temp.min),
      condition: item.weather[0].description,
      icon: getWeatherIcon(item.weather[0].icon)
    }));

    return {
      current: {
        temp: Math.round(current.temp),
        feels_like: Math.round(current.feels_like),
        pressure: current.pressure,
        humidity: current.humidity,
        wind_speed: Math.round(current.wind_speed * 10) / 10,
        wind_deg: current.wind_deg,
        condition: current.weather[0].description,
        icon: getWeatherIcon(current.weather[0].icon)
      },
      location: {
        name: geoData.name,
        country: geoData.sys.country
      },
      hourly,
      forecast
    };
  } catch (error) {
    console.error('OpenWeather API Error:', error);
    
    // Fallback to basic weather data if One Call API fails
    try {
      const englishCityName = getRussianCityName(cityName);
      const response = await axios.get(`${BASE_URL}/weather`, {
        params: {
          q: englishCityName,
          appid: API_KEY,
          units: 'metric',
          lang: 'ru'
        }
      });

      const data = response.data;

      return {
        current: {
          temp: Math.round(data.main.temp),
          feels_like: Math.round(data.main.feels_like),
          pressure: data.main.pressure,
          humidity: data.main.humidity,
          wind_speed: Math.round(data.wind.speed * 10) / 10,
          wind_deg: data.wind.deg,
          condition: data.weather[0].description,
          icon: getWeatherIcon(data.weather[0].icon)
        },
        location: {
          name: data.name,
          country: data.sys.country
        },
        hourly: [],
        forecast: []
      };
    } catch (fallbackError) {
      console.error('Fallback API Error:', fallbackError);
      throw new Error(`Не удалось получить данные о погоде для города ${cityName}`);
    }
  }
};