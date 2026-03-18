import { projectThemeStyle } from "../lib/projectTheme";

function importanceLabel(level) {
  if (level === "high") return "高关注";
  if (level === "medium") return "持续关注";
  return "低波动";
}

function buildSparklinePoints(values, width, height) {
  const series = Array.isArray(values) && values.length ? values : [0, 0, 0, 0, 0, 0, 0];
  const maxValue = Math.max(...series, 1);
  const step = series.length > 1 ? width / (series.length - 1) : width;

  return series
    .map((value, index) => {
      const x = index * step;
      const y = height - (value / maxValue) * height;
      return `${x},${y}`;
    })
    .join(" ");
}

function Sparkline({ values }) {
  const width = 84;
  const height = 26;
  const points = buildSparklinePoints(values, width, height);

  return (
    <svg className="project-board-sparkline" viewBox={`0 0 ${width} ${height}`} aria-hidden="true" focusable="false">
      <polyline points={points} />
    </svg>
  );
}

export default function ProjectRankBoard({ items }) {
  const boardItems = items || [];

  function handleJump(projectId) {
    if (!projectId) return;
    const target = document.querySelector(`[data-project-id="${projectId}"]`);
    if (target?.scrollIntoView) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  if (!boardItems.length) {
    return <div className="empty-state">当前没有可上榜项目</div>;
  }

  return (
    <div className="project-board-list">
      {boardItems.map((item) => {
        const score = Math.max(0, Math.round((item.board_score || 0) * 100));
        return (
          <button
            key={item.project_id}
            type="button"
            className="project-board-row"
            style={projectThemeStyle(item.project_id)}
            onClick={() => handleJump(item.project_id)}
            aria-label={`查看 ${item.project_name}`}
          >
            <div className="project-board-row__main">
              <div className="project-board-row__title">
                <strong>{item.project_name}</strong>
                <span className={`pill pill--${item.importance || "low"}`}>{importanceLabel(item.importance)}</span>
              </div>
              <span className="project-board-row__time">{item.last_activity_label || "暂无更新"}</span>
            </div>

            <div className="project-board-row__signals">
              <div className="project-board-row__sparkline">
                <span>7天</span>
                <Sparkline values={item.activity_series_7d} />
              </div>
              <span className="project-board-chip">权重 {score}</span>
              <span className="project-board-chip">已读 {item.read_count || 0}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
