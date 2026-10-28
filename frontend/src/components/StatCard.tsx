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
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-soft transition-all hover:border-slate-300"
    >
      <p className="text-xs font-medium uppercase tracking-wider text-slate-500 mb-2">
        {label}
      </p>
      <p className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight leading-none mb-1">
        {value}
      </p>
      {sub && (
        <p className="text-xs text-slate-500 mt-1.5 leading-normal">{sub}</p>
      )}
      {trend && (
        <span
          className={`inline-flex items-center gap-1 mt-2.5 text-xs font-medium px-2 py-0.5 rounded-full border ${
            trendUp
              ? "bg-emerald-50 text-emerald-700 border-emerald-200/60"
              : "bg-slate-100 text-slate-700 border-slate-200"
          }`}
        >
          {trend}
        </span>
      )}
    </motion.div>
  );
}
