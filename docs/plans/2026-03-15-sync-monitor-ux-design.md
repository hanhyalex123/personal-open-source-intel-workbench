Make homepage lead with logs and sync.  
Rejected because it makes “日报” secondary and conflicts with the product emphasis.

### Option C: Split Pages (Selected)
Create a dedicated “同步监控” page for sync radar and logs.  
Keep homepage focused on daily brief and incremental updates.

## Selected Design

### Information Architecture
- Homepage (日报):
  - 日报首页
  - 增量提醒
- 新页面 (同步监控):
  - 同步雷达
  - 日志入口与历史同步

### Navigation
- Add a new sidebar item: `同步监控`
- “立即同步”按钮仅出现在同步监控页

### Sync Monitor Page Layout
Top: status strip with compact, scannable fields
- 阶段
- 当前项目
- 进度
- 失败
- 最后心跳

Middle: three clickable cards
- 新增
- 已分析
- 失败

Right/top: a single “查看日志” entry point

### Log Drawer Behavior
- Default to “本次同步”
- Show model/provider/fallback line in each event
- Failed events get visual emphasis and immediate context

### Homepage Layout
- Remove sync radar block from homepage
- Keep daily brief section
- Keep incremental updates section

## Copy and Empty States

- 新页面标题: `同步监控`
- 日志入口: `查看日志`
- Empty logs: `暂无同步日志，点击“立即同步”开始`

## Testing Scope

- Frontend navigation: `src/test/app.test.jsx`
- Sync status panel: `src/test/sync-status-panel.test.jsx`
- No backend changes required
