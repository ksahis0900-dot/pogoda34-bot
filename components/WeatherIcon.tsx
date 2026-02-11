import React from 'react';
import { 
  Sun, 
  Cloud, 
  CloudRain, 
  CloudSnow, 
  CloudLightning, 
  Wind, 
  CloudDrizzle, 
  CloudFog,
  Moon
} from 'lucide-react';

interface WeatherIconProps {
  condition: string;
  className?: string;
  isNight?: boolean;
}

export const WeatherIcon: React.FC<WeatherIconProps> = ({ condition, className, isNight = false }) => {
  const lowerCondition = condition.toLowerCase();

  if (lowerCondition.includes('ясно') || lowerCondition.includes('солн')) {
    return isNight ? <Moon className={className} /> : <Sun className={className} />;
  }
  if (lowerCondition.includes('гроза')) {
    return <CloudLightning className={className} />;
  }
  if (lowerCondition.includes('дождь') || lowerCondition.includes('ливень')) {
    return <CloudRain className={className} />;
  }
  if (lowerCondition.includes('снег')) {
    return <CloudSnow className={className} />;
  }
  if (lowerCondition.includes('морос')) {
    return <CloudDrizzle className={className} />;
  }
  if (lowerCondition.includes('туман') || lowerCondition.includes('мгла')) {
    return <CloudFog className={className} />;
  }
  if (lowerCondition.includes('ветер')) {
    return <Wind className={className} />;
  }
  
  return <Cloud className={className} />;
};
