# 部署到 Cloudflare Pages

主站可完全静态化（localStorage 存进度，没有运行时后端），最适合 CF Pages。

## 构建模式

| 命令 | 场景 | 包含 `/editor`？ |
|---|---|---|
| `npm run dev` | 本地开发 | ✅ |
| `npm run build` | 本地测试完整构建（含动态路由） | ✅ |
| `npm run build:static` | 生产（CF Pages 用这个） | ❌ |

`build:static` 设 `STATIC_EXPORT=1`，`next.config.ts` 里切换：
- `output: 'export'` → 生成 `out/` 静态站点
- `pageExtensions` 排除 `dev.tsx` / `dev.ts` → 跳过 `/editor` 和 `/api/editor`

编辑器和 API 路由文件命名为 `*.dev.tsx` / `*.dev.ts`，只在非静态构建中被识别为页面。

## Cloudflare Pages 设置

1. Cloudflare Dashboard → **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**
2. 选 GitHub 仓库 `hoopyAI/french-flashcard`
3. 构建配置：
   - **Framework preset**: `Next.js (Static HTML Export)`（或留 `None`）
   - **Build command**: `npm run build:static`
   - **Build output directory**: `out`
   - **Root directory**: `/`（保留默认）
   - **Node version**: `20` 或 `22`（在环境变量里加 `NODE_VERSION=22`）
4. 保存后自动触发首次构建，完成后访问 `<project>.pages.dev`

后续每次 push 到 `main` 分支都会自动重建。

## 自定义域名

Pages 项目 → Custom domains → Add domain
- DNS 在 CF：一键绑定，证书自动签发
- DNS 在外部：按提示加 CNAME 记录

## 中国大陆访问

- `*.pages.dev`：GFW 经常阻断，不稳
- 自定义域（CF 代理）：时好时坏，取决于路由的出口节点
- 稳定方案：ICP 备案 + CF China Network（Enterprise）或 DNS-only + 中国 CDN

个人用免费方案 + 偶尔上墙也没啥大问题。
