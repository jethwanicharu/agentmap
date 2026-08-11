export interface StatsCardsProps {
  filesIndexed: number;
  chunksCreated: number;
  questionsAsked: number;
  /** true while a repo is being indexed and counts aren't known yet */
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
        <div className="stat-card" key={stat.label}>
          {loading ? (
            <div className="stat-value skeleton" />
          ) : (
            <div className="stat-value">{stat.value}</div>
          )}
          <div className="stat-label">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}