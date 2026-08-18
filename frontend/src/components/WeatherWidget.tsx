"use client";
import { useQuery } from "@tanstack/react-query";

// In production: fetch from Open-Meteo free API (no key needed)
// https://api.open-meteo.com/v1/forecast?latitude=12.93&longitude=80.06&current_weather=true&hourly=relativehumidity_2m
async function fetchWeather() {
  const res = await fetch(
    "https://api.open-meteo.com/v1/forecast?latitude=12.9298&longitude=80.0629&current_weather=true&hourly=relativehumidity_2m,windspeed_10m&timezone=Asia%2FKolkata&forecast_days=1"
  );
  if (!res.ok) throw new Error("Weather fetch failed");
  return res.json();
}

const MOCK = {
  temperature: 34,
  humidity:    72,
  windspeed:   18,
  description: "Partly Cloudy",
};

export default function WeatherWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["weather"],
    queryFn: fetchWeather,
    staleTime: 1000 * 60 * 15, // 15 min cache
    retry: 1,
  });

  const temp      = data?.current_weather?.temperature     ?? MOCK.temperature;
  const wind      = Math.round(data?.current_weather?.windspeed ?? MOCK.windspeed);
  const humidity  = data?.hourly?.relativehumidity_2m?.[new Date().getHours()] ?? MOCK.humidity;
  const desc      = isError || isLoading ? MOCK.description : "Current Conditions";

  return (
    <div className="bg-white rounded-2xl border border-green-100 p-6 shadow-sm h-full">
      <h2 className="text-sm font-semibold text-green-900 mb-4">
        Weather <span className="font-normal text-green-400">· Tambaram</span>
      </h2>

      <div className="flex items-center gap-4 mb-5 pb-5 border-b border-green-50">
        <p className="text-5xl font-light text-green-950">{Math.round(temp)}°</p>
        <div>
          <p className="font-semibold text-green-800 text-base">{desc}</p>
          <p className="text-xs text-green-500">Humidity: {humidity}%</p>
          <p className="text-xs text-green-400">Erumaiyur, Tamil Nadu</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        {[
          { icon: "🌡️", val: `${Math.round(temp)}°C`, lbl: "Temp"     },
          { icon: "💧", val: `${humidity}%`,           lbl: "Humidity" },
          { icon: "🌬️", val: `${wind} km/h`,           lbl: "Wind"     },
        ].map(({ icon, val, lbl }) => (
          <div key={lbl}>
            <div className="text-2xl mb-1">{icon}</div>
            <p className="font-semibold text-green-800 text-sm">{val}</p>
            <p className="text-xs text-green-400">{lbl}</p>
          </div>
        ))}
      </div>

      {isLoading && (
        <p className="text-xs text-green-400 mt-3 text-center">Fetching live weather…</p>
      )}
    </div>
  );
}
