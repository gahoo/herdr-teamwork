# 端到端验证路由与交互剧本 (`E2E_PLAYBOOK.md` — Materialized E2E Feature Map)

> **维护铁律**：
> 1. **按需创建与增量维护**：仅在项目启用 `e2e` 角色时由 `Planner` 初始化表头，由 **`E2E Agent` (`e2e`)** 在每次实机走查通过后按 **6 要素结构化字段**增量回写。
> 2. **核心价值**：物化页面路由、稳定选择器与源码入口映射，使 `e2e` 冒烟走查告别从零盲目摸索 DOM 树，并让 `debugger` 在面对模糊 UI 报障或截图时能通过 `entry_point` 与 `dom_selectors` 秒级锁定源码文件。

---

## 1. 全局前置环境与宿主入口 (Global Target & Auth Setup)

- **运行态类型 (`runtime_type`)**：`daemon_port`（如 `http://localhost:3000`） / `push_to_host`（目标宿主站点 `Target Host URL`）
- **通用前置准备 / 登录态注入**：<记录免登录测试账号、LocalStorage/Cookie 预置方式或跳过引导遮罩的通用步骤>

---

## 2. 功能路由与源码映射矩阵 (6-Element Feature Navigation Map)

| `feature_id` (功能唯一标识) | `entry_point` (前端/视图源码入口路径) | `user_route` (访问 URL 或最短前置点击序列) | `dom_selectors` (核心交互控件稳定选择器 / A11y Role) | `keyboard_shortcuts` (关联快捷键/焦点流) | `gotchas` (前置状态依赖、异步等待信号与已知坑点) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`<feature-slug-1>`**<br><功能简述> | `src/<domain>/<Component>.tsx` | 1. 访问 `/route`<br>2. 点击 `[data-testid="open-btn"]` | • 触发按钮：`role=button[name="xxx"]`<br>• 结果容器：`#result-panel` | `Escape` 关闭弹窗；`Tab` 焦点闭环 | 需等待接口 `/api/xxx` 返回后再断言列表渲染 |
