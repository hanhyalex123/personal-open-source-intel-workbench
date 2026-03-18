import HelpTip from "./HelpTip";
import { projectThemeStyle } from "../lib/projectTheme";

function importanceLabel(level) {
  if (level === "high") return "高关注";
  if (level === "medium") return "持续关注";
  return "低波动";
}

function normalizeSeries(values) {
  if (Array.isArray(values) && values.length) return values;
  return Array.from({ length: 30 }, () => 0);
}

function buildSparklinePoints(values, width, height) {
  const series = normalizeSeries(values);
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
  const width = 116;
  const height = 30;
  const points = buildSparklinePoints(values, width, height);

  return (
    <svg className="project-board-sparkline" viewBox={`0 0 ${width} ${height}`} aria-hidden="true" focusable="false">
      <polyline points={points} />
    </svg>
  );
}

function buildExplanation(item) {
  if (item.board_explanation) return item.board_explanation;
  const breakdown = item.activity_breakdown_30d || {};
  return `30天内 ${breakdown.total || item.updates_30d || 0} 条变化，release ${breakdown.release || 0} 条，docs ${breakdown.docs || 0} 条。`;
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
        const explanation = buildExplanation(item);
        const breakdown = item.activity_breakdown_30d || {};
        const model = item.llm?.model ? `本次分析：${item.llm.model}` : "";
        const tooltipText = [explanation, model].filter(Boolean).join(" ");

        return (
          <article
            key={item.project_id}
            className="project-board-row"
            style={projectThemeStyle(item.project_id)}
          >
            <div className="project-board-row__main">
              <div className="project-board-row__title">
                <div className="project-board-row__meta">
                  <button
                    type="button"
                    className="project-board-row__jump"
                    onClick={() => handleJump(item.project_id)}
                    aria-label={`查看 ${item.project_name}`}
                  >
                    {item.project_name}
                  </button>
                  <HelpTip label={`${item.project_name} 说明`} text={tooltipText} />
                </div>
                <div className={`pill pill--${item.importance || "low"}`}>{importanceLabel(item.importance)}</div>
              </div>
              <span className="project-board-row__time">{item.last_activity_label || "暂无更新"}</span>
            </div>

            <div className="project-board-row__signals">
              <div className="project-board-row__sparkline">
                <span>30天</span>
                <Sparkline values={item.activity_series_30d} />
              </div>
              <span className="project-board-chip">变化 {breakdown.total || item.updates_30d || 0}</span>
              <span className="project-board-chip">权重 {score}</span>
              <span className="project-board-chip">已读 {item.read_count || 0}</span>
            </div>

            <p className="project-board-row__hint">
              {breakdown.release || 0} 条 release，{breakdown.docs || 0} 条 docs
            </p>
          </article>
        );
      })}
    </div>
  );
}
