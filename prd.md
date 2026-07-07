# MOC Instruction Viewer — 实现文档

## 1. 方案定位

在线 LDR / MPD 拼搭图纸浏览服务。

用户通过模型 `id` 打开网页，系统从服务器本地磁盘读取 Studio 导出的 `.ldr` 或 `.mpd` 文件，后端生成 MPD 缓存文件（含颜色配置），前端通过 Three.js LDrawLoader 加载并渲染模型。零件依赖由 LDrawLoader 通过 API 按需加载。

---

## 2. 核心目标

### 2.1 第一阶段（已实现）

- 支持按模型 `id` 在线查看 LDR / MPD 模型。
- 模型源文件存储在服务器本地磁盘。
- 后端根据 `id` 查找源文件，不暴露真实文件路径。
- 后端生成包含颜色配置的 MPD 缓存文件。
- 前端加载 MPD + 按需拉取零件依赖。
- 支持模型旋转、缩放、平移、重置视角。初始正面视角。
- 支持缓存，避免每次访问重新处理。

### 2.2 第二阶段（已实现）

- 解析源文件中的 `0 STEP` 步骤信息。
- 上一页 / 下一页分步浏览。
- 每一步累计模型显示。
- 本步新增零件统计。
- 键盘快捷键支持（← → 切换步骤，R 重置视角）。

### 2.3 暂不实现

- 不复刻 Studio 的 PDF 页面排版和每页镜头视角。
- 不实现 callout 局部放大框、箭头安装提示。
- 不实现防截图、防录屏。
- 不做复杂订单系统，只预留 token 鉴权接口。

---

## 3. 实际数据流

```
浏览器                          后端                           磁盘
──────                         ────                           ────

① GET /viewer/:id              Vite 返回 HTML + JS

② GET /api/models/:id/meta     model_service 查找源文件
                                step_service 检测 0 STEP
                                返回 meta JSON
                                (自动触发步骤缓存生成)

③ GET /api/models/:id/packed   pack_service 读取源文件
   或 /api/models/:id/steps/:n  嵌入 LDConfig.ldr
                                返回 MPD 文本 (约 135KB)

④ LDrawLoader 解析 MPD
   遇到 "1 16 ... 3001.dat"
   → ensureDataLoaded 无缓存命中
   → fetchData("3001.dat")
   → 尝试 /api/ldraw/3001.dat (404)
   → 尝试 /api/ldraw/parts/3001.dat (200)
   → 递归加载图元依赖
   → Promise.all 完成 → 渲染
```

### 关键设计决策：为什么不嵌入零件到 MPD

原始设计是将所有依赖零件递归打包进 MPD（`0 FILE` 块），但 Three.js LDrawLoader 存在一个解析 bug：

- `0 FILE 3001.dat` 解析时文件名取到的是 `" 3001.dat"`（带前导空格）
- 零件引用查找时文件名是 `"3001.dat"`（trim 过的）
- 两者不匹配，缓存命中率 = 0，235 个嵌入文件全部走了网络加载

因此改为：MPD 仅包含模型内容 + 颜色配置（共约 135KB），零件由 LDrawLoader 通过 `/api/ldraw/` 按需加载。

---

## 4. Three.js r170 兼容要点

Three.js r170 的 LDrawLoader **必须**显式设置条件线材质，否则静默报错：

```js
import { LineMaterial } from "three/examples/jsm/lines/LineMaterial.js";

const loader = new LDrawLoader();
loader.setConditionalLineMaterial(LineMaterial); // 必须！
loader.partsLibraryPath = "/api/ldraw/";
```

`partsLibraryPath` 指向零件库 API。LDrawLoader 的 `fetchData()` 会按优先级试探路径：
`/<file>` → `/parts/<file>` → `/p/<file>` → `/models/<file>` → lowercase retry

---

## 5. 项目目录结构

```
moc-instruction-viewer/
├── prd.md
├── LICENSE                     # PolyForm Noncommercial 1.0.0
├── .gitignore
│
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 应用入口，挂载 /api/ldraw 静态文件
│   ├── config.py               # 目录路径、缓存策略
│   ├── requirements.txt        # fastapi, uvicorn, pydantic
│   ├── api/
│   │   └── model_api.py        # API 路由 (meta/packed/steps)
│   ├── services/
│   │   ├── model_service.py    # 模型查找与元信息
│   │   ├── pack_service.py     # MPD 生成（模型 + 颜色配置）
│   │   ├── step_service.py     # 分步解析、manifest 生成、累计 MPD
│   │   └── cache_service.py    # 缓存文件读写管��
│   └── ldraw/
│       ├── parser.py           # LDraw 行解析、0 STEP 切分、引用收集
│       ├── dependency_resolver.py  # 零件库查找（递归解析）
│       └── mpd_writer.py       # MPD 合并写入
│
├── frontend/                   # Vite + Three.js 前端
│   ├── index.html              # Viewer 页面
│   ├── package.json            # three, vite
│   ├── vite.config.js          # API 代理到 :8000
│   └── src/
│       ├── main.js             # 入口：URL 解析、UI 控制、步骤切换
│       ├── viewer.js           # 3D 渲染：场景/相机/灯光/OrbitControls/LDrawLoader
│       └── style.css           # 深色主题样式
│
└── data/                       # 数据目录（不提交）
    ├── source/                 # 模型源文件 (<id>.ldr / <id>.mpd)
    ├── ldraw-lib/              # LDraw 官方零件库
    │   ├── LDConfig.ldr
    │   ├── parts/
    │   ├── p/
    │   └── models/
    ├── cache/
    │   ├── packed/             # 完整 MPD 缓存
    │   └── steps/              # 分步 MPD 缓存 + manifest.json
    └── logs/
```

---

## 6. API 设计

### 6.1 前端页面

```http
GET /viewer/:id
```

Vite 返回 SPA 页面，前端从 URL 解析模型 ID 后请求数据接口。

### 6.2 获取模型元信息

```http
GET /api/models/:id/meta
```

**响应：**
```json
{
  "id": "10001",
  "name": "高达头像",
  "format": "ldr",
  "version": 1,
  "hasPackedCache": true,
  "hasSteps": true,
  "totalSteps": 37
}
```

首次请求时自动触发步骤缓存生成（`ensure_steps`）。

### 6.3 获取完整 MPD

```http
GET /api/models/:id/packed
```

返回 MPD 文本（模型内容 + LDConfig + LDCfgalt）。懒生成缓存。

### 6.4 获取步骤清单

```http
GET /api/models/:id/steps
```

**响应：**
```json
{
  "id": "10001",
  "name": "高达头像",
  "totalSteps": 37,
  "steps": [
    {
      "step": 1,
      "partCount": 4,
      "newParts": [
        { "partId": "3001.dat", "color": "16", "count": 2 }
      ]
    }
  ]
}
```

### 6.5 获取某一步累计 MPD

```http
GET /api/models/:id/steps/:stepNo
```

返回该步的累计模型 MPD（第 1 步到第 N 步的所有零件）。

### 6.6 零件库静态服务

```http
GET /api/ldraw/parts/3001.dat
GET /api/ldraw/p/4-4cyli.dat
```

FastAPI `StaticFiles` 挂载 `data/ldraw-lib/` 到 `/api/ldraw`。供前端 LDrawLoader 按需拉取。

---

## 7. 分步浏览策略

### 累计步骤

```
step_001 = 第 1 步内所有零件
step_002 = 第 1 步 + 第 2 步
step_003 = 第 1 步 + 第 2 步 + 第 3 步
```

每一步都是累计结果，保证用户看到已拼好的完整模型。

### 新增零件统计

同一步中相同 `partId + color` 合并计数。前端展示 `第 n / total 步` 和本步新增零件列表。

### 子模型策略

第一版：主模型步骤按 `0 STEP` 切分，子模型作为整体引用。

---

## 8. 前端渲染细节

### 初始相机

正面略微俯视（Z 轴正前方 + Y 轴略高），`fitCameraToObject` 自动适配模型包围盒。

### 交互

| 操作 | 方式 |
|------|------|
| 旋转 | 鼠标左键拖拽 |
| 缩放 | 滚轮（1 ~ 2000 范围） |
| 平移 | 鼠标右键拖拽 |
| 重置视角 | 点击按钮 / 按 R |
| 上/下一步 | 按钮 / ← → 键盘 |

### 无步骤时的 UI

当模型没有 `0 STEP` 时，隐藏步骤控制栏，只显示模型名称和重置按钮。

---

## 9. 缓存策略

### 缓存结构

```
data/cache/packed/10001.v1.packed.mpd     # 完整 MPD
data/cache/steps/10001/
  manifest.json                            # 步骤元数据
  step_001.packed.mpd
  step_002.packed.mpd
  ...
```

### 缓存失效

- 源文件被替换（检测 mtime）
- TTL 超时（默认 24h，可配置）
- 手动 `POST /api/admin/models/:id/rebuild`

### 推荐策略

上传后预生成 + 首次访问懒生成兜底。

---

## 10. 安全设计

- **ID 校验**：`^[a-zA-Z0-9_]+$`，拒绝 `../` 等路径遍历
- **不暴露真实路径**：只返回 API 地址，不返回磁盘路径
- **源文件不直接公开**：用户只能通过 `/api/models/:id/packed` 访问
- **Token 鉴权预留**：接口支持 `?token=xxxx` 参数

---

## 11. 错误处理

| 场景 | 后端 | 前端 |
|------|------|------|
| 模型不存在 | 404 | "图纸不存在，请确认链接是否正确" |
| 步骤不存在 | 404 | "当前步骤不存在" |
| 文件解析失败 | 500 + 日志 | "图纸文件不完整，请联系客服" |
| ID 格式非法 | 400 | "无效的模型 ID" |

---

## 12. 部署

### 推荐技术栈

```
前端：Vite + Three.js r170
后端：FastAPI + uvicorn
反向代理：Nginx
进程管理：systemd / pm2
```

### Nginx 配置要点

```nginx
# 前端 SPA
location / {
    try_files $uri /index.html;
}

# API 代理到后端
location /api/ {
    proxy_pass http://127.0.0.1:8000/;
}
```

零件库通过 `/api/ldraw/` 走后端代理，不需要 Nginx 单独暴露。

### 服务器目录

```
/data/ldr-viewer/
  source/        # 模型源文件（必须）
  ldraw-lib/     # LDraw 零件库（必须）
  cache/         # 自动生成
  logs/          # 自动生成
```

---

## 13. 开发环境

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173/viewer/10001`
