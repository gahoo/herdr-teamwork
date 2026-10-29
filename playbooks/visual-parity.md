# Playbook: 像素级视觉等价同屏比对 (`visual-parity`)

> **设计溯源**：融合自 Lauren Tan (`pstack`) 的 `visual-parity` Playbook 与 `prove-it-works` 原则。

---

## 1. 适用场景与触发条件 (When to Use)

当任务要求实现与参考基准**视觉呈现高度一致（Pixel-Exact / Visual Equivalence）**时触发本剧本：
1. **UI 重构与技术栈迁移**：例如将旧版页面迁移到新组件库、将 CSS 重构为 Tailwind，要求重构前后视觉零退化。
2. **还原设计稿或参考截图**：`changes/<feat>/spec.md` 中明确附带了目标参考截图、Figma 标注图或竞品对照图。
3. **修复微妙的样式偏移 Bug**：如特定状态下的行高抖动、间距不齐、暗黑模式错色或响应式折行异常。

---

## 2. 角色分工链路 (Role Handoff Chain)

```
[planner] 在 spec.md 中标注 [VISUAL_PARITY] 并指明基准参考图路径/旧版对照 URL
        │
        ▼
[coding] 实现样式与结构后流转至审查与验收节点
        │
        ▼
[reviewer-ux / e2e] 在完全一致的视口尺寸与状态下截取实机画面，执行逐项像素级比对
        │ (若存在肉眼可见偏差 ➔ 附 Before/After 截图与具体 CSS 差异打回 coding)
        ▼
[e2e] 验证全断点视觉等价后，将实机对比截图归档至 result.md 并签发 E2E_PASS
```

---

## 3. 分角色执行规程 (Step-by-Step by Role)

### 阶段一：`planner` 锁定对照基准
在 `changes/<feat>/spec.md` 中明确声明 `[VISUAL_PARITY]`，并固定以下比对参数：
* **参考基准源（Reference Source）**：本地参考图片路径，或旧版运行的对照路由 URL。
* **标准视口断点（Viewports）**：默认至少包含桌面端（如 `1440×900`）与移动端（如 `390×844`）。
* **特定交互状态（States）**：如默认态、Hover/Focus 态、空数据态、超长文本截断态、暗黑模式（Dark Mode）。

### 阶段二：`reviewer-ux` 与 `e2e` 同屏对账规程（核心执行者）
**严禁仅凭阅读 JSX/CSS 源码就主观断定“样式看起来一样”！** 必须启动真实浏览器渲染并执行以下 4 步对账：

1. **对齐环境与假数据（Normalize Fixtures）**：
   * 确保新实现页面填充的数据（文本长度、头像尺寸、列表条数）与参考图尽量一致，固定随机时间/动画，并在完全相同的视口宽高（`resize_page`）下渲染。
2. **截取实机画面并读取计算样式（Screenshot & Computed Styles）**：
   * 调用截图工具截取当前渲染结果，同时通过 `getComputedStyle` 读取关键容器与文本节点的实际计算属性（`padding`、`margin`、`gap`、`fontSize`、`lineHeight`、`fontWeight`、`color`、`borderRadius`）。
3. **六维视觉逐项核查（The 6-Axis Visual Diff）**：
   将参考图与实机截图并排对比，逐一核查：
   * **盒子间距与节奏（Spacing & Rhythm）**：内外边距、列表行高、图标与文字的间距是否相差超过 `1~2px`？
   * **对齐基线（Alignment）**：图标与相邻文本是否垂直居中对齐？左右两侧边缘是否在同一垂直基准线上？
   * **排版层级（Typography）**：字号、字重（如 `500` vs `600`）、行高、字间距及浅色辅助文本的对比度是否一致？
   * **边框、圆角与阴影（Borders & Elevation）**：`1px` 分割线颜色深浅、圆角弧度、卡片阴影扩散范围是否吻合？
   * **溢出与弹性边界（Overflow & Flex/Grid）**：当文本变长或窗口缩窄时，是优雅省略（`text-overflow: ellipsis`）还是把按钮挤出容器？
   * **状态反馈一致性**：选中态、禁用态、加载态的视觉反馈是否与基准一致？
4. **打回或放行裁决**：
   * ❌ **发现偏差**：严禁含糊地说“间距有点不对”。必须在 `result.md` 中明确列出：**具体元素选择器 + 参考图表现 vs 当前实机表现 + 建议调整的 CSS 属性值**，直接打回 `coding`。
   * ✅ **完全对齐**：在 `result.md` 中记录各断点与状态下的实机验证通过结论。
