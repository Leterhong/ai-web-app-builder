---
name: ai-web-app-builder
description: |
  从零构建一个可演示的全栈 AI Web 应用（Next.js 前端 + FastAPI 后端 + SQLite）的标准工作流 skill。当用户要求"做一个 AI 工具 / 产品 / 原型 / Web 应用"，且任务涉及前端界面 + 后端 API + AI 模型调用时触发。覆盖：项目脚手架、默认模式与实时模式双模式（无 Key 走内置固定结果，有 Key 走真实 OpenAI 兼容模型）、启发式项目扫描、架构图（React Flow）、源码查看（Monaco Editor）、暗色 Bento 主题，以及 Windows 环境下 venv 布局 / 包启动方式 / npm 镜像 / 安全删除等高频坑。典型参考实现：AI 微服务架构审查员。不要用于纯前端静态页、纯后端脚本，或企业级生产平台（保持轻量原型级别）。
agent_created: true
---

# 全栈 AI Web 应用构建工作流

> 本 skill 把一次真实落地（AI 微服务架构审查员）中验证过的脚手架、双模式设计、启发式扫描、暗色 Bento 主题，以及 Windows 高频坑固化下来，让同类 AI Web 应用任务直接复用，不再从零踩坑。
>
> 核心原则：**原型优先、双模式、所有按钮都必须有真实逻辑、3 分钟能讲完。**

## 一、什么时候用

- 用户要做一个"AI + X"的 Web 应用 / 原型 / 轻量产品（如 AI 代码审查、AI 文档分析、AI SQL 优化器等）。
- 需要前端界面 + 后端 API + 接一个 AI 模型。
- 用户强调"可演示""真实""不要假按钮""3 分钟讲完"。

**不适用**：纯静态页、纯后端 CLI、或要扩展成企业级平台（保持轻量原型级别，别过度设计）。

## 二、标准目录结构

```
<project>/
  frontend/            # Next.js 14 App Router + TS + Tailwind
  backend/             # FastAPI + SQLAlchemy + SQLite
    main.py            # 入口，使用相对导入 from .api import ...
    api/               # 路由：import_routes / model_routes / ai_routes
    analyzer/          # 启发式扫描器（无 AI 也能产出结构）
    ai/                # client(调模型) / audit(审提示词) / chat / preset_data / graph
    models/            # Pydantic schemas
    storage/           # db(SQLAlchemy) + common(取当前模型)
    data/app.db        # SQLite
    requirements.txt
  sample-project/      # 内置可一键导入的样例工程
  README.md
```

## 三、后端（FastAPI + SQLite）

1. **依赖**：`fastapi uvicorn python-multipart sqlalchemy requests`（见 `assets/backend/requirements.txt`）。
2. **隔离 venv（Windows 关键坑）**：用 managed Python 建独立 venv，Windows 下可执行文件在 `<venv>/Scripts/python.exe`（不是 `bin/`）。不要污染 `envs/default`。详细步骤见 `references/windows_pitfalls.md`。
3. **启动方式（关键坑）**：`main.py` 用相对导入（`from .api import ...`），必须从项目根目录以包形式启动：`PYTHONPATH=<root> <venv>/Scripts/python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`。在 `backend/` 内直接 `uvicorn main:app` 会因相对导入崩溃。
4. **双模式（最重要设计）**：详见 `references/dual_mode_design.md`。核心：`storage/common.get_active_model()` 仅在存在 active 且 `api_key` 非空的配置时返回模型 dict，否则返回 `None` → 前端/后端切换 **默认模式**；模式徽标在默认模式下显示 `● 默认`，实时模式下显示用户配置的模型名（如 `● Kimi K3`）。**红线：默认模式结果必须通用合法固定，不得署名任何厂商真实输出；仅当用户填入自己的 Key 才进入实时模式并如实署名该用户模型。**
5. **启发式扫描器**（`analyzer/project_analyzer.py`，无 AI 也能跑）：服务识别（构建文件 / `src/` 目录）、API 识别（`@GetMapping`/`app.get()` 等）、数据库识别（`jdbc:/redis:///postgres://` 等）、**跨服务依赖**（Java 包名 `com.shop.user` 无连字符，不能简单子串匹配，需按 `.` 分片去连字符比对，见 `references/dual_mode_design.md` 的扫描细节）。
6. **AI 调用**（`ai/client.py`）：用 `requests` 直接打 OpenAI 兼容 `/v1/chat/completions`（不引 SDK）。要求模型返回 JSON，解析失败时回退到内置固定结果 + 记 `real_error`。
7. **模型配置安全**：API Key 入库明文（本地应用），返回前端时一律掩码（`sk****ef`），绝不明文回传。

## 四、前端（Next.js 14 App Router）

1. **脚手架**：`npm create next-app` 在沙箱常失败，推荐**手写**配置（`assets/frontend/` 提供 `package.json` / `tsconfig.json` / `next.config.mjs` / `tailwind.config.ts` / `postcss.config.mjs` / `globals.css` 模板）。
2. **依赖**：`next@14 react@18 framer-motion reactflow @monaco-editor/react lucide-react` + radix-ui 系列（slot/tabs/dialog/tooltip/progress）+ tailwindcss@3 typescript@5。
3. **npm 安装（关键坑）**：国内/受限网络常 `ECONNRESET` 回滚，切镜像 `registry.npmmirror.com` + `--prefer-offline` 重试（详见 `references/windows_pitfalls.md`）。
4. **手写 shadcn 风格组件**：`button/card/input/badge/progress/tabs`（用 `cn` = `class-variance-authority` + `clsx` + `tailwind-merge`）。
5. **暗色 Bento 主题**：`darkMode:'class'`，色板深空黑 / 银 / 蓝(primary) / 绿(accent) / 红(danger)，**严禁紫色**。`assets/frontend/globals.css` 已声明对应 CSS 变量。
6. **架构图**：React Flow，节点 `type`(service/database/redis/mq) 决定颜色；**必须**把 `type/label/risk` 存入 `node.data` 并接 `onNodeClick`，否则"点击节点看依赖"失效。
7. **源码查看**：Monaco Editor 展示"AI 正在读的代码"（默认模式用代表片段，真实导入抽最大源码文件前 N 行）。
8. **API 封装**：`src/lib/api.ts` 统一 fetch（`http://localhost:8000`），含 ZIP 上传 `FormData`。

## 五、端到端验证清单（交付前必跑）

跑 `scripts/verify_app.py`（源自真实 36 项断言），覆盖：后端根路径 / `/api/model` 默认 `configured:false` / 样例导入与扫描 / 审计双模式 / chat 关键词 / 测试假 Key 干净 401 / 真实 ZIP 服务·API·DB·跨服务依赖检出 / 资源缺失返回 404 / 前后端字段对齐。也可改 `scripts/scaffold.py` 一键生成标准目录骨架。完整清单见原表（保留在 `references/windows_pitfalls.md` 末尾）。

## 六、参考实现

AI 微服务架构审查员（`F:/lanyun/ai-arch-auditor/`）：含完整后端路由、双模式、启发式扫描、React Flow 架构图、Monaco 源码查看、暗色 Bento 仪表盘，以及 `_test/deep_test.py` 端到端测试（36 项）。复刻同类应用时，改 `ai/preset_data.py` 固定剧本与 `analyzer` 扫描规则即可。

## Resources

### scripts/
- `scaffold.py`：按第二节目录结构在当前目录生成 `frontend/`（含手写配置模板）与 `backend/`（含 `main.py`、`requirements.txt`、相对导入骨架），避免沙箱内 `npm create next-app` 失败。
- `verify_app.py`：端到端校验脚本（36 项断言），覆盖双模式、扫描、AI chat、错误路径、前后端契约。

### references/
- `tech_stack.md`：技术栈选型理由、手写脚手架模板说明、暗色 Bento 主题色板与 CSS 变量、React Flow / Monaco 接入要点。
- `dual_mode_design.md`：默认模式 / 实时模式 判定逻辑、固定数据红线、启发式扫描规则（含跨服务依赖分片匹配算法）、API Key 掩码规范。
- `windows_pitfalls.md`：Windows 高频坑速查表（venv 布局、相对导入启动、端口占用、npm ECONNRESET、安全删除拦截）+ 端到端验证清单原文。

### assets/
- `frontend/`：可直接复制的 Next.js 手写配置模板（`package.json`、`tsconfig.json`、`next.config.mjs`、`tailwind.config.ts`、`postcss.config.mjs`、`globals.css`、`lib/utils.ts`）。
- `backend/`：`requirements.txt` 与 `main.py` 入口模板（相对导入 + CORS + router 注册）。
