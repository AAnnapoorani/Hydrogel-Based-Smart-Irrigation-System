"use client";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from "recharts";
import { api } from "@/lib/api";
import dynamic from "next/dynamic";

const FieldMap = dynamic(() => import("@/components/FieldMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-48 rounded-xl bg-green-50 border border-green-100 flex items-center justify-center">
      <p className="text-xs text-green-400">Loading map…</p>
    </div>
  ),
});

const weekData = [
  { day: "Mon", value: 16 }, { day: "Tue", value: 14 },
  { day: "Wed", value: 19 }, { day: "Thu", value: 17 },
  { day: "Fri", value: 15 }, { day: "Sat", value: 18 },
  { day: "Sun", value: 14 },
];

const stats = [
  { label: "Soil Fertility",     value: "72%",      sub: "Medium-High",     trend: "+4%",  up: true  },
  { label: "Irrigation Req.",    value: "18 L/m²",  sub: "Today's estimate",trend: "−6%",  up: false },
  { label: "Water Saved",        value: "31%",      sub: "vs traditional",  trend: "+3%",  up: true  },
  { label: "Soil Moisture",      value: "58%",      sub: "Target: 60–75%",  trend: "Low",  up: false },
];

export default function DashboardPage() {
  const now = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

  return (
    <main className="max-w-6xl mx-auto px-6 py-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <h1 className="text-3xl font-serif font-bold text-green-950 mb-1">Farm Dashboard</h1>
        <p className="text-green-700 text-sm mb-8">Erumaiyur Village · Last updated: {now}</p>

        {/* Stat cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              className="bg-white rounded-2xl border border-green-100 p-5 shadow-sm"
            >
              <p className="text-xs font-semibold uppercase tracking-widest text-green-500 mb-2">{s.label}</p>
              <p className="text-3xl font-semibold text-green-900">{s.value}</p>
              <p className="text-xs text-green-600 mt-1">{s.sub}</p>
              <span className={`inline-block mt-2 text-xs font-semibold px-2 py-0.5 rounded-full ${s.up ? "bg-green-50 text-green-700" : "bg-teal-50 text-teal-700"}`}>
                {s.trend}
              </span>
            </motion.div>
          ))}
        </div>

        {/* Chart + Weather */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="md:col-span-2 bg-white rounded-2xl border border-green-100 p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-green-900 mb-4">Weekly Irrigation Trend <span className="text-green-500 font-normal">L/m² per day</span></h2>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={weekData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f4ea" />
                <XAxis dataKey="day" tick={{ fontSize: 12, fill: "#7a9a5a" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#7a9a5a" }} axisLine={false} tickLine={false} domain={[10, 22]} />
                <Tooltip contentStyle={{ background: "#fff", border: "1px solid #d1e7c0", borderRadius: 8, fontSize: 13 }} />
                <Line type="monotone" dataKey="value" stroke="#3b6d11" strokeWidth={2.5} dot={{ fill: "#3b6d11", r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-white rounded-2xl border border-green-100 p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-green-900 mb-4">Weather · Tambaram</h2>
            <div className="flex items-center gap-4 mb-5 pb-5 border-b border-green-50">
              <span className="text-5xl font-light text-green-950">34°</span>
              <div>
                <p className="font-semibold text-green-800">Partly Cloudy</p>
                <p className="text-xs text-green-600">Humidity: 72%</p>
                <p className="text-xs text-green-400">Erumaiyur, Tamil Nadu</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              {[["🌡️","34°C","Temp"],["💧","72%","Humidity"],["🌬️","18 km/h","Wind"]].map(([icon,val,lbl]) => (
                <div key={lbl}>
                  <div className="text-2xl">{icon}</div>
                  <div className="font-semibold text-green-800 text-sm">{val}</div>
                  <div className="text-xs text-green-500">{lbl}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Crop + Map */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl border border-green-100 p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-green-900 mb-4">Recommended Crop</h2>
            <div className="flex items-center gap-4 bg-green-50 rounded-xl p-4 border border-green-100">
              <span className="text-4xl">🌾</span>
              <div className="flex-1">
                <p className="font-bold text-green-900">Samba Rice</p>
                <p className="text-xs text-green-600">Season: Kharif · Sowing: Jun–Jul</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-green-600">92</p>
                <p className="text-xs text-green-500">Match Score</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 mt-4">
              {[["Sugarcane","84","green"],["Black Gram","78","blue"],["Groundnut","71","amber"]].map(([crop,score,color]) => (
                <span key={crop} className={`text-xs font-semibold px-3 py-1.5 rounded-full bg-${color}-50 text-${color}-700`}>{crop} {score}</span>
              ))}
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-green-100 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-green-900">Field Location</h2>
              <span className="text-xs text-green-500 bg-green-50 px-2 py-1 rounded-lg border border-green-100">
                12.9298° N, 80.0629° E
              </span>
            </div>
            <FieldMap />
            <p className="text-xs text-green-500 mt-2 text-center">
              📍 Erumaiyur Village, Tambaram · Tamil Nadu
            </p>
          </div>
        </div>
      </motion.div>
    </main>
  );
}
