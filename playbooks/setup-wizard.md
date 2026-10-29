# Playbook: 人类专属配置交互式向导脚本生成 (`setup-wizard`)

> **设计溯源**：融合自 Matt Pocock 的 `wizard` 技能与 Lauren Tan (`pstack`) 的 `build-the-lever` 原则。

---

## 1. 适用场景与触发条件 (When to Use)

当 `ops` 在执行环境启动（`OPS_BOOT`）或部署准备时，发现遇到**只有人类才有权限或凭证完成的操作**而导致流水线受阻时，**全自动触发**本剧本。典型场景包括：
1. **缺失外部服务凭证**：`.env` 中缺少真实的第三方 API Key、支付密钥、Webhook Secret 或云厂商 AK/SK。
2. **第三方控制台配置**：需要人类去 GitHub / Google Cloud / Stripe / 飞书后台创建 OAuth 应用、配置回调地址或开启权限。
3. **本地特权或证书准备**：需要人类输入 `sudo` 密码信任本地 HTTPS 根证书、登录 Docker Registry 或授权系统权限。
4. **单向数据库割接 / 生产发布确认**：需要人类亲自核对参数并按回车确认的高危一次性操作。

---

## 2. 角色分工链路 (Role Handoff Chain)

```
[ops] 在 OPS_BOOT 检测出缺失人类专属配置
        │ (全自动触发，无需事先请示)
        ▼
[ops] 编写幂等、带连通性自检的交互式向导脚本 scripts/setup-wizard.sh
        │ (写入 OPS_BLOCKED，指明运行脚本命令)
        ▼
[dispatcher / planner] 在 Window 1 提示人类运行 `bash scripts/setup-wizard.sh`
        │
        ▼
[Human] 跟随终端向导一步步填入密钥/完成操作，脚本自动校验连通性并落盘 .env
        │
        ▼
[dispatcher] 重新唤醒 [ops] 执行 OPS_BOOT ➔ 环境就绪 (OPS_READY)
```

---

## 3. `ops` 编写向导脚本的 5 条铁律 (Step-by-Step for `ops`)

> ⚠️ **严禁 `ops` 仅仅在 `pipeline.jsonl` 里甩一句“缺少 XXX_API_KEY，请人类自己去配 `.env`”就撂挑子！** 把配置过程写成交互式脚本，能让人类少花 80% 的翻文档排错时间。

当触发本剧本时，`ops` 必须立即在项目 `scripts/setup-wizard.sh`（或针对特定功能的 `scripts/wizard-<topic>.sh`）生成交互式 Bash 脚本，并遵守以下 5 条规范：

1. **脚本头部幂等预检（Idempotent Pre-flight Check）**：
   * 脚本一启动先检查哪些配置**已经存在且有效**，已经配好的项直接显示 `✅ [已就绪] XXX_KEY` 并自动跳过，只引导人类填写缺失或失效的项！
2. **在终端里直接给出精准的「去哪拿」指引（Zero-Search Guidance）**：
   * 在 `read` 提示人类输入之前，先用清晰的 `echo` 告诉人类：
     * 具体点开哪个网址（如 `https://dashboard.stripe.com/apikeys`）；
     * 在页面哪个菜单下点击什么按钮；
     * 期望粘贴的字符串格式长什么样（如 `以 sk_test_ 开头的密钥`）。
3. **敏感输入隐藏与安全写入（Secret Safety）**：
   * 读取密钥/密码时使用 `read -r -s -p`（不回显明文或仅打印长度校验）；
   * 自动确保目标配置文件（如 `.env` 或 `.env.local`）已被列入 `.gitignore`，绝不让人类误提交真实密钥。
4. **填完一项，立即实测连通性（Validate Immediately）**：
   * 人类每填完一个 Key 或配置项，脚本必须**当场发起一次轻量级真实探测**（例如用 `curl -s -f` 调一下该服务的健康检查/鉴权接口，或用 CLI 测试数据库连接）。
   * 若鉴权失败，当场打印明确原因并允许人类重新输入，绝不把错误的 Key 留到后面启动服务时才爆栈！
5. **在 `OPS_BLOCKED` 事件中给出零思考执行指令**：
   * 脚本生成并 `chmod +x` 后，`ops` 向 `changes/pipeline.jsonl` 写入：
     ```json
     {"ts":"...","feat":"<feat>","node":3,"role":"ops","status":"OPS_BLOCKED","summary":"缺失第三方服务凭证，已生成交互式配置向导。请人类在终端运行 `bash scripts/setup-wizard.sh` 按提示完成配置并自动校验"}
     ```
