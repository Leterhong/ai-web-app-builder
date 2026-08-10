#!/usr/bin/env python3
"""scaffold.py - 按 ai-web-app-builder 标准目录结构生成全栈 AI Web 应用骨架。

用法:
    python scaffold.py [project_name] [--out DIR]

- 在项目根生成 frontend/ (手写 Next.js 14 配置) + backend/ (FastAPI 相对导入骨架)
- 不触发 npm install（沙箱内易失败），仅产出文件；依赖清单见 assets/frontend/package.json
- 幂等：已存在文件不覆盖，避免误删用户改动
"""
import argparse
import os

FRONTEND_FILES = {
    "package.json": """{
  "name": "ai-app-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": { "dev": "next dev", "build": "next build", "start": "next start", "lint": "next lint" },
  "dependencies": {
    "next": "14.2.15", "react": "^18.3.1", "react-dom": "^18.3.1",
    "framer-motion": "^11.11.0", "reactflow": "^11.11.4", "@monaco-editor/react": "^4.6.0",
    "lucide-react": "^0.451.0", "class-variance-authority": "^0.7.0", "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.4", "tailwindcss-animate": "^1.0.7",
    "@radix-ui/react-slot": "^1.1.0", "@radix-ui/react-tabs": "^1.1.0",
    "@radix-ui/react-dialog": "^1.1.1", "@radix-ui/react-tooltip": "^1.1.2", "@radix-ui/react-progress": "^1.1.0"
  },
  "devDependencies": {
    "typescript": "^5.6.2", "@types/node": "^20.16.0", "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0", "tailwindcss": "^3.4.13", "postcss": "^8.4.47", "autoprefixer": "^10.4.20"
  }
}
""",
    "tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2017", "lib": ["dom", "dom.iterable", "esnext"], "allowJs": true,
    "skipLibCheck": true, "strict": true, "noEmit": true, "esModuleInterop": true,
    "module": "esnext", "moduleResolution": "bundler", "resolveJsonModule": true,
    "isolatedModules": true, "jsx": "preserve", "incremental": true,
    "plugins": [{ "name": "next" }], "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
""",
    "next.config.mjs": """/** @type {import('next').NextConfig} */
const nextConfig = { reactStrictMode: true };
export default nextConfig;
""",
    "postcss.config.mjs": """export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
""",
    "tailwind.config.ts": """import type { Config } from "tailwindcss";
const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))", foreground: "hsl(var(--foreground))",
        muted: "hsl(var(--muted))", "muted-foreground": "hsl(var(--muted-foreground))",
        primary: "hsl(var(--primary))", accent: "hsl(var(--accent))", danger: "hsl(var(--danger))",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
""",
    "src/app/globals.css": """:root {
  --background: 222 47% 5%;
  --foreground: 210 40% 96%;
  --muted: 217 33% 17%;
  --muted-foreground: 215 20% 65%;
  --primary: 199 89% 48%;
  --accent: 152 60% 45%;
  --danger: 0 72% 51%;
}
* { box-sizing: border-box; }
html, body { padding: 0; margin: 0; background: hsl(var(--background)); color: hsl(var(--foreground)); }
""",
    "src/app/layout.tsx": """export const metadata = { title: "AI App" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="zh" className="dark"><body>{children}</body></html>);
}
""",
    "src/app/page.tsx": """export default function Home() {
  return (<main className="p-10"><h1 className="text-2xl font-bold">AI App</h1></main>);
}
""",
    "src/lib/utils.ts": """import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }
""",
}

BACKEND_FILES = {
    "requirements.txt": "fastapi\nuvicorn\npython-multipart\nsqlalchemy\nrequests\n",
    "main.py": '''"""AI Web App - FastAPI 入口。

启动：从项目根目录
  PYTHONPATH=. venv/Scripts/python.exe -m uvicorn backend.main:app --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import import_routes, model_routes, ai_routes
from .storage.db import init_db

app = FastAPI(title="AI Web App")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
init_db()
app.include_router(import_routes.router, prefix="/api")
app.include_router(model_routes.router, prefix="/api")
app.include_router(ai_routes.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok", "name": "AI Web App"}
''',
    "api/__init__.py": "",
    "api/import_routes.py": '''from fastapi import APIRouter
router = APIRouter()
''',
    "api/model_routes.py": '''from fastapi import APIRouter
router = APIRouter()
''',
    "api/ai_routes.py": '''from fastapi import APIRouter
router = APIRouter()
''',
    "storage/__init__.py": "",
    "storage/db.py": '''from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
engine = create_engine("sqlite:///data/app.db", connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
def init_db():
    import os; os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(engine)
''',
}


def write_file(path: str, content: str):
    if os.path.exists(path):
        print(f"  skip (exists): {path}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  wrote: {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", default="ai-app")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    root = os.path.join(os.path.abspath(a.out), a.project)
    print(f"Scaffolding into {root}")
    for rel, content in FRONTEND_FILES.items():
        write_file(os.path.join(root, "frontend", rel), content)
    for rel, content in BACKEND_FILES.items():
        write_file(os.path.join(root, "backend", rel), content)
    print("Done. Next: cd into frontend && npm install --registry https://registry.npmmirror.com --prefer-offline")


if __name__ == "__main__":
    main()
