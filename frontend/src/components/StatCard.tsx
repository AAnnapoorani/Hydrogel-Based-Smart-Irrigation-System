import { motion } from "framer-motion";

interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  trend?: string;
  trendUp?: boolean;
  delay?: number;
}

export default function StatCard({ label, value, sub, trend, trendUp = true, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.35 }}
      className="bg-white rounded-2xl border border-green-100 p-5 shadow-sm"
    >
      <p className="text-xs font-semibold uppercase tracking-widest text-green-400 mb-2">
        {label}
      </p>
      <p className="text-3xl font-semibold text-green-900 leading-none mb-1">
        {value}
      </p>
      {sub && (
        <p className="text-xs text-green-500 mt-1">{sub}</p>
      )}
      {trend && (
        <span
          className={`inline-block mt-2 text-xs font-semibold px-2.5 py-0.5 rounded-full ${
            trendUp ? "bg-green-50 text-green-700" : "bg-teal-50 text-teal-700"
          }`}
        >
          {trend}
        </span>
      )}
    </motion.div>
  );
}
