"use client";

import dynamic from "next/dynamic";
import React from "react";

// Dynamically import factory and plotly.js-dist-min with SSR disabled
const Plot = dynamic<any>(
  async () => {
    const [factoryMod, plotlyMod] = await Promise.all([
      import("react-plotly.js/factory"),
      import("plotly.js-dist-min"),
    ]);
    const createPlotlyComponent = (factoryMod as any).default || factoryMod;
    const Plotly = (plotlyMod as any).default || plotlyMod;
    return createPlotlyComponent(Plotly);
  },
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-80 rounded-xl bg-slate-50 border border-slate-200/80 flex flex-col items-center justify-center p-6 text-slate-400 animate-pulse">
        <div className="w-7 h-7 rounded-full border-2 border-slate-200 border-t-emerald-600 animate-spin mb-2.5"></div>
        <p className="text-xs font-medium text-slate-500">Rendering interactive Plotly visualization…</p>
      </div>
    ),
  }
);

export interface PlotlyChartProps {
  data: any[];
  layout?: Record<string, any>;
  config?: Record<string, any>;
  style?: React.CSSProperties;
  className?: string;
}

export default function PlotlyChart({
  data,
  layout = {},
  config = {},
  style = { width: "100%", height: "100%", minHeight: "340px" },
  className = "",
}: PlotlyChartProps) {
  const mergedLayout = {
    autosize: true,
    margin: { l: 55, r: 25, t: 45, b: 55, pad: 4 },
    font: { family: "system-ui, -apple-system, sans-serif", color: "#334155", size: 12 },
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    hoverlabel: { bgcolor: "#0f172a", font: { color: "#ffffff", size: 11 } },
    ...layout,
  };

  const mergedConfig = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d"],
    toImageButtonOptions: {
      format: "png",
      filename: "irrigatewise_model_evaluation",
      height: 600,
      width: 900,
      scale: 2,
    },
    ...config,
  };

  return (
    <div className={`w-full overflow-hidden ${className}`}>
      <Plot
        data={data}
        layout={mergedLayout}
        config={mergedConfig}
        style={style}
        useResizeHandler={true}
      />
    </div>
  );
}
