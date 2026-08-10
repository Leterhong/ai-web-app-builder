# 技术栈选型与脚手架说明

本文档补充 `SKILL.md` 第四节，给出选型理由、手写脚手架模板要点、暗色 Bento 主题与关键组件接入细节。

## 一、为什么手写而非 `npm create next-app`

在受限沙箱 / 国内网络下，`npm create next-app` 常有三类失败：

1. 交互式 prompt 在无人值守环境直接卡死。
2. 模板拉取阶段 `ECONNRESET` / 超时。
3. 自动安装依赖阶段回滚，留下残缺目录。

**结论**：直接手写 `package.json` + `tsconfig.json` + `next.config.mjs` + `tailwind.config.ts` + `postcss.config.mjs` + `globals.css`，再 `npm install` 一次成型。模板见 `assets/frontend/`。

## 二、前端依赖（完整清单）

```jsonc
"dependencies": {
  "next": "14.2.15",
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "framer-motion": "^11.11.0",     // 卡片/列表入场动画
  "reactflow": "^11.11.4",         // 架构图
  "@monaco-editor/react": "^4.6.0",// 源码查看器
  "lucide-react": "^0.451.0",      // 图标
  "class-variance-authority": "^0.7.0",
  "clsx": "^2.1.1",
  "tailwind-merge": "^2.5.4",
  "tailwindcss-animate": "^1.0.7",
  "@radix-ui/react-slot": "^1.1.0",
  "@radix-ui/react-tabs": "^1.1.0",
  "@radix-ui/react-dialog": "^1.1.1",
  "@radix-ui/react-tooltip": "^1.1.2",
  "@radix-ui/react-progress": "^1.1.0"
},
"devDependencies": {
  "typescript": "^5.6.2",
  "@types/node": "^20.16.0",
  "@types/react": "^18.3.0",
  "@types/react-dom": "^18.3.0",
  "tailwindcss": "^3.4.13",
  "postcss": "^8.4.47",
  "autoprefixer": "^10.4.20"
}
```

> 版本钉死 Next 14.2.x 与 reactflow 11.x，避免 Next 15 / reactflow 12 的 breaking change 在沙箱内反复调试。

## 三、暗色 Bento 主题

`tailwind.config.ts` 设 `darkMode: 'class'`，并在 `<html>` 上加 `class="dark"`。`globals.css` 声明以下 HSL 变量（节选）：

```css
:root {
  --background: 222 47% 5%;      /* 深空黑 */
  --foreground: 210 40% 96%;
  --muted: 217 33% 17%;
  --muted-foreground: 215 20% 65%;
  --primary: 199 89% 48%;        /* 蓝 */
  --accent: 152 60% 45%;         /* 绿 */
  --danger: 0 72% 51%;           /* 红 */
}
```

**红线：严禁紫色（violet/purple）**。Bento 卡片用深色玻璃拟态 + 细边框，评分环、风险条形、状态点用 primary/accent/danger 区分。

## 四、React Flow 接入要点

- 节点数据**必须**把 `type/label/risk` 存入 `node.data`：
  ```ts
  const nodes = services.map(s => ({
    id: s.id,
    type: 'service',            // service | database | redis | mq
    data: { label: s.name, risk: s.risk, type: 'service' },
    position: { x: ..., y: ... },
  }));
  ```
- **必须**接 `onNodeClick`，否则"点击节点看依赖"失效：
  ```ts
  <ReactFlow nodes={nodes} edges={edges} onNodeClick={(_, n) => setSelected(n.data)} fitView />
  ```
- 边 `edges` 用 `source`/`target` 引用节点 id，颜色随依赖风险等级。

## 五、Monaco 接入要点

- 用 `@monaco-editor/react` 的 `<Editor>` 组件，只读模式 `options={{ readOnly: true }}`。
- 默认模式展示 `ai/preset_data.py` 中的代表代码片段；真实导入时抽"项目内最大源码文件的前 120 行"。
- 语言按文件后缀推断（`.java`→java，`.py`→python，`.ts`→typescript）。

## 六、手写 shadcn 风格组件

`lib/utils.ts` 提供 `cn`：

```ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }
```

`button/card/input/badge/progress/tabs` 组件用 `cn` + `class-variance-authority` 组合变体，避免引整个 shadcn CLI（同样在沙箱不稳）。
