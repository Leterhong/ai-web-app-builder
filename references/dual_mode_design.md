# 默认模式 / 实时模式 双模式设计

本文档补充 `SKILL.md` 第三节第 4、5 点，给出双模式判定逻辑、固定数据红线、启发式扫描规则与 API Key 掩码规范。

## 一、模式判定逻辑

后端 `storage/common.py`：

```python
def get_active_model():
    cfg = ModelConfig.query.filter_by(active=True).first()
    if cfg and cfg.api_key:        # 必须 active 且 api_key 非空
        return {"base_url": cfg.base_url, "api_key": cfg.api_key,
                "model_name": cfg.model_name, "model_id": cfg.model_id}
    return None                    # 返回 None → 默认模式
```

所有走 AI 的接口（`audit`/`chat`/`test`）统一前置判断：

```python
model = get_active_model()
if not model:
    return build_preset_audit(...)   # 固定剧本
try:
    return call_real_model(model, ...)
except Exception as e:
    # 优雅降级：记录 real_error 并回退到固定结果，不 500
    return {**build_preset_audit(...), "real_error": str(e)}
```

前端 `api.ts` 读 `/api/model` 的 `configured` 字段，决定徽标：

- `configured: false` → 显示 `● 默认`
- `configured: true`  → 显示 `● {model_name}`（如 `● Kimi K3`）

## 二、固定数据红线（重要）

- 默认模式结果**必须**是通用、合法、与任何真实厂商输出无关的"剧本数据"（如评分 78、4 张 Bento、3 个 Critical 风险、架构图节点/边）。
- **不得**在默认模式结果里署名具体厂商模型（如不得写"由 GPT-4 生成"）。
- 仅当用户填入自己的 Key 并进入实时模式，才如实署名**该用户配置**的模型名。
- 红线目的：避免无 Key 演示被误读为某厂商背书，也避免幻觉署名。

## 三、启发式扫描规则（`analyzer/project_analyzer.py`）

无 AI 也能跑，输入是解压后的项目目录或 ZIP：

| 维度 | 识别方式 |
|---|---|
| 服务 | 构建文件 `pom.xml` / `build.gradle` / `package.json` / `go.mod`，或含 `src/` 的顶层目录 |
| API | `@GetMapping/@PostMapping/@PutMapping/@DeleteMapping`、`@app.route`、`app.get()`、`router.get()`、`@RequestMapping` |
| 数据库 | 连接串 `jdbc:mysql://` / `jdbc:postgresql://` / `redis://` / `postgres://` / `mysql://` |
| 缓存/消息 | `redis://`、`kafka`、`rabbitmq`、`amqp://` |

### 跨服务依赖（关键坑）

Java 包名是 `com.shop.user`（**无连字符**），不能简单用 `.{服务名}.` 子串匹配——`user-service` 永远匹配不到 `com.shop.user`。

正确算法（`_import_hits_service`）：

```python
def _import_hits_service(import_path: str, service_set: set[str]) -> bool:
    parts = [p for p in import_path.replace("-", "").split(".") if p]
    for svc in service_set:
        svc_norm = svc.replace("-", "")
        # 首段匹配（user-service → "user" 命中 com.shop.user）
        if svc_norm == parts[0] or svc_norm in parts:
            return True
    return False
```

这样 `import com.shop.user.UserClient` 才能被归入对 `user-service` 的依赖。

### 跳过的目录

`.git node_modules target build dist __pycache__ .idea .vscode`

## 四、AI 调用（`ai/client.py`）

用 `requests` 直接打 OpenAI 兼容接口，不引 SDK：

```python
resp = requests.post(
    f"{model['base_url'].rstrip('/')}/chat/completions",
    headers={"Authorization": f"Bearer {model['api_key']}"},
    json={"model": model["model_id"], "messages": [...],
          "response_format": {"type": "json_object"}, "temperature": 0.2},
    timeout=60,
)
data = resp.json()["choices"][0]["message"]["content"]
return json.loads(data)   # 解析失败 → 抛异常 → 上层回退到固定结果
```

> `base_url` 必须含 `/v1` 后缀（如 `https://maas-api.lanyun.net/v1`），否则 404。

## 五、API Key 掩码规范

入库可明文（本地应用），但 `/api/model` 返回前端时一律掩码：

```python
def mask_key(k: str) -> str:
    if not k or len(k) < 8:
        return "****"
    return k[:2] + "****" + k[-2:]
```

绝不把明文 Key 放进任何 `200` 响应体。
