# ai-web-app-builder

> 一个用于**从零构建可演示全栈 AI Web 应用**的标准工作流 Skill。
> 触发场景：用户要做一个「AI + X」的 Web 应用 / 原型 / 轻量产品（前端界面 + 后端 API + 接一个 AI 模型）。

本 Skill 把一次真实落地（**AI 微服务架构审查员**）中验证过的脚手架、双模式设计、启发式扫描、暗色 Bento 主题，以及 Windows 高频坑固化下来，让同类 AI Web 应用任务直接复用，不再从零踩坑。

- 仓库地址：<https://github.com/Leterhong/ai-web-app-builder>
- 完整指令（给智能体读）：见 [`SKILL.md`](./SKILL.md)

---

## 核心原则

1. **原型优先** —— 保持轻量原型级别，不做企业级生产平台的过度设计。
2. **双模式** —— 无 Key 走内置固定结果（默认模式），有 Key 走真实 OpenAI 兼容模型（实时模式）。
3. **所有按钮都必须有真实逻辑** —— 拒绝假按钮、假数据。
4. **3 分钟能讲完** —— 结构清晰，可演示、可复述。

---

## 目录结构

```
ai-web-app-builder/
  SKILL.md                              # 完整工作流指令（给智能体读）
  README.md                             # 本文件（给人类读的项目说明）
  .gitignore
  references/                           # 深度参考文档
    tech_stack.md                       # 技术栈选型 / 手写脚手架 / 暗色 Bento 主题
    dual_mode_design.md                 # 双模式判定 / 固定数据红线 / 启发式扫描规则
    windows_pitfalls.md                 # Windows 高频坑速查 + 端到端验证清单
  scripts/                              # 可复用脚本
    scaffold.py                         # 一键生成标准目录骨架
    verify_app.py                       # 端到端校验（36 项断言）
  assets/                               # 可直接复制的模板
    frontend/                           # Next.js 手写配置模板
    backend/                            # FastAPI 入口与依赖模板
```

---

## 适用与不适用

**适用**

- 做一个「AI + X」的 Web 应用 / 原型 / 轻量产品（如 AI 代码审查、AI 文档分析、AI SQL 优化器）。
- 需要前端界面 + 后端 API + 接一个 AI 模型。
- 强调「可演示」「真实」「不要假按钮」「3 分钟讲完」。

**不适用**

- 纯静态页、纯后端 CLI。
- 要扩展成企业级生产平台（保持轻量原型级别，别过度设计）。

---

## 标准技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Next.js 14（App Router）+ TypeScript + Tailwind CSS + React Flow + Monaco Editor |
| 后端 | FastAPI + SQLAlchemy + SQLite |
| AI | OpenAI 兼容 `/v1/chat/completions`（不引 SDK，用 `requests` 直连） |
| 主题 | 暗色 Bento（深空黑 / 银 / 蓝 / 绿 / 红，**严禁紫色**） |

---

## 双模式设计（要点）

| 模式 | 触发条件 | 行为 |
| --- | --- | --- |
| **默认模式** | 无 active 且 `api_key` 非空的模型配置 | 返回通用、合法、固定的内置结果；徽标显示 `● 默认` |
| **实时模式** | 存在 active 且 `api_key` 非空 | 调用用户配置的真实模型；徽标显示模型名（如 `● Kimi K3`） |

**红线**：默认模式结果必须通用合法、不得署名任何厂商真实输出；仅当用户填入自己的 Key 才进入实时模式并如实署名该用户模型。

详见 [`references/dual_mode_design.md`](./references/dual_mode_design.md)。

---

## 快速使用

### 1. 生成项目骨架

```bash
python scripts/scaffold.py
```

在当前目录生成标准 `frontend/`（含手写配置模板）与 `backend/`（含 `main.py`、相对导入骨架、`requirements.txt`）。

### 2. 安装并启动后端（Windows 注意）

```bash
# 用 managed Python 建独立 venv（Windows 可执行文件在 Scripts/ 而非 bin/）
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt

# 从项目根目录以包形式启动（main.py 用相对导入）
PYTHONPATH=. .venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 3. 安装并启动前端

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com   # 国内网络切镜像
npm run dev
```

### 4. 端到端验证

```bash
python scripts/verify_app.py
```

覆盖双模式、启发式扫描、AI chat、错误路径、前后端契约等 36 项断言。

更多 Windows 坑（端口占用、npm ECONNRESET、安全删除拦截等）见 [`references/windows_pitfalls.md`](./references/windows_pitfalls.md)。

---

## 参考实现

**AI 微服务架构审查员**（`F:/lanyun/ai-arch-auditor/`）是本项目验证过的完整落地：

- 后端：完整路由、双模式、启发式扫描、跨服务依赖分片匹配。
- 前端：React Flow 架构图、Monaco 源码查看、暗色 Bento 仪表盘。
- 测试：`_test/deep_test.py` 端到端测试（36 项）。

复刻同类应用时，改 `ai/preset_data.py` 固定剧本与 `analyzer` 扫描规则即可。

---

## License

本项目用于教学与原型复用，遵循仓库默认协议。
