import React, { useState, useEffect } from 'react';
import { Cloud, Sun, CloudRain, Wind, Droplets, MapPin, Bell, Settings, Share2, Menu } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const App: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [selectedCity, setSelectedCity] = useState("Волгоград");

  useEffect(() => {
    setTimeout(() => setLoading(false), 1000);
  }, []);

  const cities = ["Волгоград", "Волжский", "Камышин", "Михайловка", "Урюпинск"];

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Header */}
      <header className="flex justify-between items-center mb-12">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-2"
        >
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Cloud className="text-white" size={24} />
          </div>
          <span className="text-xl font-bold tracking-tight">POGODA 34</span>
        </motion.div>

        <div className="flex gap-4">
          <button className="p-2 glass-card hover:bg-white/5 transition-colors">
            <Bell size={20} className="text-slate-400" />
          </button>
          <button className="p-2 glass-card hover:bg-white/5 transition-colors">
            <Menu size={20} className="text-slate-400" />
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Weather Card */}
        <section className="lg:col-span-2 space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-8 relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
              <Sun size={200} className="text-yellow-400" />
            </div>

            <div className="relative z-10">
              <div className="flex items-center gap-2 text-slate-400 mb-4">
                <MapPin size={18} />
                <span className="font-medium">{selectedCity}, Россия</span>
              </div>

              <div className="flex items-end gap-4 mb-8">
                <h1 className="text-8xl font-bold tracking-tighter">+12°</h1>
                <div className="pb-3">
                  <p className="text-2xl text-slate-300 font-medium">Ясно</p>
                  <p className="text-slate-500">Ощущается как +10°</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white/5 rounded-2xl p-4 border border-white/5">
                  <Wind className="text-blue-400 mb-2" size={20} />
                  <p className="text-xs text-slate-500 uppercase">Ветер</p>
                  <p className="font-semibold">4.2 м/с</p>
                </div>
                <div className="bg-white/5 rounded-2xl p-4 border border-white/5">
                  <Droplets className="text-blue-400 mb-2" size={20} />
                  <p className="text-xs text-slate-500 uppercase">Влажность</p>
                  <p className="font-semibold">45%</p>
                </div>
                <div className="bg-white/5 rounded-2xl p-4 border border-white/5">
                  <CloudRain className="text-blue-400 mb-2" size={20} />
                  <p className="text-xs text-slate-500 uppercase">Осадки</p>
                  <p className="font-semibold">0 мм</p>
                </div>
              </div>
            </div>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Bell size={18} className="text-blue-500" />
                Рассылка
              </h3>
              <p className="text-slate-400 text-sm mb-6">Получайте уведомления в 07:00 и 18:00 МСК прямо в Telegram.</p>
              <button className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/20 active:scale-95">
                Настроить уведомления
              </button>
            </div>

            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Share2 size={18} className="text-blue-500" />
                Поделиться
              </h3>
              <p className="text-slate-400 text-sm mb-6">Отправьте бота друзьям, чтобы они тоже были в курсе погоды.</p>
              <button className="w-full py-3 glass-card hover:bg-white/5 text-white rounded-xl font-medium transition-all active:scale-95">
                Копировать ссылку
              </button>
            </div>
          </div>
        </section>

        {/* Sidebar */}
        <aside className="space-y-6">
          <div className="glass-card p-6">
            <h3 className="font-semibold mb-6">Региональные центры</h3>
            <div className="space-y-3">
              {cities.map((city) => (
                <button
                  key={city}
                  onClick={() => setSelectedCity(city)}
                  className={`w-full flex justify-between items-center p-4 rounded-2xl transition-all ${selectedCity === city
                      ? 'bg-blue-600/20 border border-blue-500/30 text-white'
                      : 'hover:bg-white/5 text-slate-400 border border-transparent'
                    }`}
                >
                  <span className="font-medium">{city}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold">+12°</span>
                    <Sun size={16} className={selectedCity === city ? 'text-yellow-400' : 'text-slate-600'} />
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="glass-card p-6 bg-gradient-to-br from-blue-600/10 to-transparent">
            <div className="flex justify-between items-start mb-6">
              <div>
                <p className="text-xs text-blue-400 font-bold uppercase tracking-wider mb-1">Статус бота</p>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <span className="font-semibold">Онлайн 24/7</span>
                </div>
              </div>
              <Settings size={20} className="text-slate-600 cursor-pointer hover:text-white transition-colors" />
            </div>
            <p className="text-sm text-slate-500 leading-relaxed">
              Бот работает в режиме Webhook. Среднее время отклика меньше 0.5с.
            </p>
          </div>
        </aside>
      </main>

      {/* Footer */}
      <footer className="mt-20 py-8 border-t border-white/5 text-center">
        <p className="text-slate-600 text-sm">© 2026 POGODA34. Лучший погодный бот региона.</p>
      </footer>
    </div>
  );
};

export default App;