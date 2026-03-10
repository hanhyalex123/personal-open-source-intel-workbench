import InsightCard from "./InsightCard";

export default function SourceSection({ group }) {
  return (
    <section className="source-section" id={`source-${group.id.replace(/[^a-zA-Z0-9-_]/g, "-")}`}>
      <div className="source-section__header">
        <div>
          <p className="section-kicker">监控源</p>
          <h2>{group.title}</h2>
        </div>
        <div className="source-section__aside">
          <p className="source-section__kind">{group.kind === "docs" ? "文档 / 博客源" : "项目源"}</p>
          <p className="source-section__count">{group.items.length} 条结论</p>
        </div>
      </div>
      <div className="source-section__grid">
        {group.items.map((item) => (
          <InsightCard key={item.id} item={item} />
        ))}
      </div>
    </section>
  );
}
