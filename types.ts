export interface DayForecast {
  day: string; // e.g., "Monday"
  date: string; // e.g., "12 Oct"
  tempHigh: number;
  tempLow: number;
  condition: string; // e.g., "Sunny", "Cloudy"
  precipitationChance: number;
}

export interface HourlyForecast {
  time: string; // e.g. "14:00"
  temp: number;
  condition: string;
}

export interface CurrentWeather {
  temp: number;
  condition: string;
  feels_like: number;
  humidity: number;
  wind_speed: number;
  wind_deg: number;
  pressure: number;
  description: string;
}

export interface Location {
  name: string;
  country: string;
}

export interface WeatherData {
  location: Location;
  current: CurrentWeather;
  forecast: DayForecast[];
  hourly: HourlyForecast[];
}