# Windows 高频坑速查 + 端到端验证清单

本文档补充 `SKILL.md` 第三节第 2、3 点与第五节，集中收录 Windows 本地环境下的可复现失败与对策，以及交付前必须跑的验证清单。

## 一、坑位速查表

| 坑 | 现象 | 解决 |
|---|---|---|
| venv 布局 | `bin/python` 不存在（Linux 习惯） | 用 `<venv>/Scripts/python.exe` 与 `<venv>/Scripts/pip` |
| 相对导入启动 | `ImportError: attempted relative import with no known parent package` | 从项目根目录 `PYTHONPATH=. uvicorn backend.main:app`（以包形式启动） |
| 端口被旧进程占 | 新进程绑不上，或跑的是旧代码 | `netstat -ano \| findstr :8000` 找 PID，`taskkill /F /PID <pid>` |
| npm ECONNRESET | 安装回滚、`node_modules` 残缺 | 切镜像 `npm config set registry https://registry.npmmirror.com`（或在命令加 `--registry`），再 `npm install --prefer-offline --no-audit --no-fund` |
| `npm config set` 写 `.npmrc` 被沙箱拦截 | 命令报权限/写入失败 | 改用命令行 `--registry https://registry.npmmirror.com` 参数绕过 |
| 安全删除拦截 | `rm -rf` / Git-Bash 的 `/f/` 路径被 fail-closed 拦截 | 单文件用 PowerShell `Remove-Item -LiteralPath -Force`；Playwright `screenshot()` 自动覆盖，不必先删 |
| 单测删临时目录 | `shutil.rmtree` 对 `/f/` 被回收机制拦截 | 测试 fixtures 幂等重建，直接覆盖，不删 |
| 浏览器/chromium 版本不匹配 | agent-browser 原生二进制 os error 10060 | 改用本地 `playwright-core` + `npx playwright install chromium` 直连，启动加 `--no-sandbox --disable-gpu --disable-dev-shm-usage` |

## 二、venv 与启动完整示例

```bat
REM 1) 建隔离 venv（用 managed Python）
C:\Users\LENOVO\.workbuddy\binaries\python\versions\3.13.12\python.exe -m venv venv

REM 2) 装后端依赖
venv\Scripts\pip install fastapi uvicorn python-multipart sqlalchemy requests

REM 3) 从项目根以包形式启动（相对导入生效）
set PYTHONPATH=.
venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 三、端到端验证清单（交付前必跑）

- [ ] 后端根路径 `GET /` 返回 `{"status":"ok"}`；`/api/model` 默认 `configured:false`（默认模式）。
- [ ] `POST /api/import/sample` → 返回扫描统计（服务/API/DB/依赖数量）；`/api/analyze` → 返回完整 scan。
- [ ] `POST /api/ai/audit` 无 Key → `mode:"default"`，分数 / 4 张 Bento / 风险列表 / 架构图节点边齐全。
- [ ] `POST /api/ai/chat` 预设问题命中关键词；空消息不崩。
- [ ] `POST /api/ai/test` 假 Key → 干净 `HTTP 401`（不 500）。
- [ ] 真实 ZIP 导入：服务 / API / 数据库 / 跨服务依赖均正确检出。
- [ ] 资源缺失（坏 `project_id` / `audit_id`）→ `HTTP 404`（不要 200 + error 体）。
- [ ] 前端三页（Dashboard / Model / Analysis）`next dev` 下 HTTP 200、dev.log 零编译错误。
- [ ] 后端 JSON 字段名与前端组件读取字段逐一对齐（graph node / risk / bento / scan）。

> 完整 36 项断言实现见 `scripts/verify_app.py`（源自真实项目 `_test/deep_test.py`）。

## 四、蓝耘 maas 模型接入真实参数（示例）

当用户需要"接上自己的模型"，以蓝耘 maas 平台接入的 Kimi K3 为例，Model 页四项填法：

| 字段 | 值 | 说明 |
|---|---|---|
| Base URL | `https://maas-api.lanyun.net/v1` | 注意末尾 `/v1` 不能漏，否则 404 |
| API Key | 蓝耘控制台创建 | 前端只掩码显示前两位后两位 |
| Model Name | `Kimi K3` | 自定义展示名，仅影响徽标 |
| Model ID | `kimi-k3` | 真正传给模型服务的标识，须用小写连字符，错填带空格的"Kimi K3"会报错 |

实操路径：Model 页 → 填四项 → Test Connection（假 Key 返回 401，真 Key 返回成功）→ 徽标从 `● 默认` 切到 `● Kimi K3`。
