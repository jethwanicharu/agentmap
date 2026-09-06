"use client";
import { useEffect, useRef, useState } from "react";

function useCountUp(target: number, duration = 900) {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    const startTime = performance.now();
    cancelAnimationFrame(rafRef.current!);

    function tick(now: number) {
      const t = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(Math.round(target * eased));
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current!);
  }, [target]);

  return display;
}                                         

function StatCard({ label, value, loading }: { label: string; value: number; loading: boolean }) {
  const animated = useCountUp(value);
  return (
    <div className="stat-card">
      {loading ? (
        <div className="stat-value skeleton" />
      ) : (
        <div className="stat-value">{animated}</div>
      )}
      <div className="stat-label">{label}</div>
    </div>
  );
}                                         

export interface StatsCardsProps {
  filesIndexed: number;
  chunksCreated: number;
  questionsAsked: number;
  loading?: boolean;
}

export default function StatsCards({
  filesIndexed,
  chunksCreated,
  questionsAsked,
  loading = false,
}: StatsCardsProps) {
  const stats = [
    { label: "Files indexed", value: filesIndexed },
    { label: "Chunks created", value: chunksCreated },
    { label: "Questions asked", value: questionsAsked },
  ];

  return (
    <div className="stats-grid">
      {stats.map((stat) => (
        <StatCard key={stat.label} label={stat.label} value={stat.value} loading={loading} />
      ))}
    </div>
  );
}