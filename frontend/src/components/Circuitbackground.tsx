"use client";

function CircuitCluster({
  className,
  paths,
  duration = 7,
}: {
  className: string;
  paths: { d: string; nodes: { cx: number; cy: number; r?: number; delay: number }[]; delay?: number }[];
  duration?: number;
}) {
  return (
    <svg className={`circuit-cluster ${className}`} viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">
      {paths.map((p, i) => (
        <g key={i}>
          <path d={p.d} fill="none" stroke="#8b7cf6" strokeWidth="1" opacity="0.5" />
          {p.nodes.map((n, j) => (
            <circle
              key={j}
              cx={n.cx}
              cy={n.cy}
              r={n.r ?? 2.2}
              className="circuit-node"
              style={{ animationDelay: `${n.delay}s`, animationDuration: `${duration}s` }}
            />
          ))}
          <circle r="2.6" className="circuit-pulse">
            <animateMotion
              dur={`${duration}s`}
              begin={`${p.delay ?? 0}s`}
              repeatCount="indefinite"
              path={p.d}
            />
          </circle>
        </g>
      ))}
    </svg>
  );
}

export default function CircuitBackground() {
  return (
    <div className="circuit-bg" aria-hidden="true">
      <CircuitCluster
        className="circuit-tr"
        paths={[
          {
            d: "M0,40 H60 V90 H140 V40 H240",
            nodes: [
              { cx: 60, cy: 40, delay: 0.9 },
              { cx: 140, cy: 90, delay: 2.6 },
            ],
            delay: 0,
          },
          {
            d: "M180,0 V60 H120 V120 H200 V240",
            nodes: [
              { cx: 180, cy: 60, delay: 1.4 },
              { cx: 120, cy: 120, r: 2.4, delay: 3.4 },
              { cx: 200, cy: 120, delay: 5 },
            ],
            delay: 1.2,
          },
          {
            d: "M140,40 V0",
            nodes: [{ cx: 140, cy: 40, delay: 0.9 }],
            delay: 2.4,
          },
        ]}
        duration={7}
      />

      <CircuitCluster
        className="circuit-bl"
        paths={[
          {
            d: "M0,150 H40 V190 H100 V230",
            nodes: [
              { cx: 40, cy: 150, delay: 1 },
              { cx: 100, cy: 190, r: 2.4, delay: 2.8 },
            ],
            delay: 0.3,
          },
          {
            d: "M60,90 V180 H0",
            nodes: [{ cx: 60, cy: 90, delay: 0.8 }],
            delay: 1.8,
          },
        ]}
        duration={6.5}
      />
    </div>
  );
}