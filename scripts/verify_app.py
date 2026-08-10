#!/usr/bin/env python3
"""verify_app.py - 全栈 AI Web 应用端到端验证（源自真实 36 项断言，精简为通用版）。

用法:
    python verify_app.py [--base http://localhost:8000] [--frontend http://localhost:3000]

覆盖:
    1. 后端根路径 / 与 /api/model 默认模式
    2. 样例导入 + 分析 返回完整结构
    3. 审计双模式（无 Key → mode:"default"）
    4. chat 关键词命中 + 空消息不崩
    5. test 假 Key → 干净 401
    6. 真实 ZIP 服务/API/DB/跨服务依赖检出
    7. 资源缺失 → 404
    8. 前端三页 HTTP 200

不依赖外部 fixture 文件：内置内存 ZIP 构造微服务样例。
"""
import argparse
import io
import json
import zipfile

try:
    import requests
except ImportError:
    print("requests not installed: pip install requests")
    raise SystemExit(1)

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, "PASS" if cond else "FAIL", detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))


def build_fixture_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("order-service/pom.xml", "<project><artifactId>order-service</artifactId></project>")
        z.writestr("order-service/src/main/java/com/shop/order/OrderController.java",
                   "package com.shop.order;\nimport com.shop.user.UserClient;\n"
                   "import org.springframework.web.bind.annotation.*;\n"
                   "@RestController\n@RequestMapping(\"/api/orders\")\npublic class OrderController {\n"
                   "  @Autowired private UserClient userClient;\n"
                   "  @GetMapping(\"/{id}\")\n  public String getOrder(@PathVariable Long id){userClient.validate(id);return \"o\"+id;}\n"
                   "  @PostMapping\n  public String createOrder(){userClient.notify(1L);return \"created\";}\n}\n")
        z.writestr("order-service/src/main/resources/application.yml",
                   "spring:\n  datasource:\n    url: jdbc:mysql://db-order:3306/order\n  redis:\n    url: redis://redis-order:6379\n")
        z.writestr("user-service/build.gradle", "plugins { id 'org.springframework.boot' }")
        z.writestr("user-service/src/main/java/com/shop/user/UserController.java",
                   "package com.shop.user;\nimport org.springframework.web.bind.annotation.*;\n"
                   "@RestController\n@RequestMapping(\"/api/users\")\npublic class UserController {\n"
                   "  @GetMapping(\"/{id}\")\n  public String getUser(@PathVariable Long id){return \"u\"+id;}\n}\n")
        z.writestr("payment-service/package.json", '{"name":"payment-service","dependencies":{"express":"^4"}}')
        z.writestr("payment-service/src/index.js",
                   "const express=require('express');const app=express();\n"
                   "app.post('/api/pay',(req,res)=>res.json({ok:1}));\n"
                   "const redis=require('redis');\napp.listen(3000);\n")
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--frontend", default="http://localhost:3000")
    a = ap.parse_args()
    B = a.base.rstrip("/")

    # 1. root
    r = requests.get(f"{B}/", timeout=10)
    check("GET / returns ok", r.status_code == 200 and r.json().get("status") == "ok")

    # 2. model default mode
    r = requests.get(f"{B}/api/model", timeout=10)
    mj = r.json()
    check("/api/model default configured:false", r.status_code == 200 and mj.get("configured") is False)

    # 3. sample import + analyze
    r = requests.post(f"{B}/api/import/sample", timeout=15)
    check("POST /api/import/sample", r.status_code == 200 and "project_id" in r.json())
    pid = r.json().get("project_id")
    r = requests.post(f"{B}/api/analyze", json={"project_id": pid}, timeout=20)
    scan = r.json()
    check("POST /api/analyze structure", r.status_code == 200 and scan.get("mode") == "default" and "services" in scan)
    svc_n = len(scan.get("services", []))
    api_n = len(scan.get("apis", []))
    db_n = len(scan.get("databases", []))
    dep_n = len(scan.get("dependencies", []))
    print(f"    fixture scan: services={svc_n} apis={api_n} dbs={db_n} deps={dep_n}")

    # 4. audit default mode
    r = requests.post(f"{B}/api/ai/audit", json={"project_id": pid}, timeout=30)
    aj = r.json()
    check("POST /api/ai/audit default mode", r.status_code == 200 and aj.get("mode") == "default" and "score" in aj)

    # 5. chat keyword + empty
    r = requests.post(f"{B}/api/ai/chat", json={"project_id": pid, "message": "最紧急的风险是什么"}, timeout=20)
    check("POST /api/ai/chat keyword", r.status_code == 200 and r.json().get("reply"))
    r = requests.post(f"{B}/api/ai/chat", json={"project_id": pid, "message": ""}, timeout=20)
    check("POST /api/ai/chat empty msg no crash", r.status_code in (200, 400))

    # 6. test fake key → 401
    r = requests.post(f"{B}/api/ai/test", json={"api_key": "sk-fake-0000"}, timeout=20)
    check("POST /api/ai/test fake key → 401", r.status_code == 401)

    # 7. real ZIP scan
    zbytes = build_fixture_zip()
    files = {"file": ("proj.zip", zbytes, "application/zip")}
    r = requests.post(f"{B}/api/import/zip", files=files, timeout=30)
    if r.status_code == 200:
        zpid = r.json().get("project_id")
        r2 = requests.post(f"{B}/api/analyze", json={"project_id": zpid}, timeout=20)
        zs = r2.json()
        check("real ZIP: services>=3", len(zs.get("services", [])) >= 3, str(len(zs.get("services", []))))
        check("real ZIP: apis>=3", len(zs.get("apis", [])) >= 3)
        check("real ZIP: databases>=2", len(zs.get("databases", [])) >= 2)
        check("real ZIP: cross-service deps>=1", len(zs.get("dependencies", [])) >= 1, str(len(zs.get("dependencies", []))))
    else:
        check("real ZIP import endpoint", False, f"status {r.status_code}")

    # 8. 404 on missing resource
    r = requests.post(f"{B}/api/ai/audit", json={"project_id": "nonexistent-id"}, timeout=20)
    check("audit missing project → 404", r.status_code == 404)

    # 9. frontend pages 200
    for path in ["/", "/model", "/analysis/" + (pid or "x")]:
        r = requests.get(f"{a.frontend}{path}", timeout=15)
        check(f"frontend GET {path} → 200", r.status_code == 200, f"status {r.status_code}")

    total = len(RESULTS)
    passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
    print(f"\nTOTAL {total} | PASS {passed} | FAIL {total - passed}")
    raise SystemExit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
