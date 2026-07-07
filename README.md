# MOC Instruction Viewer

在线 LDR/MPD 拼搭图纸浏览服务 —— 将 Studio 导出的 LDraw 文件打包为 packed MPD，通过 Three.js 在浏览器中渲染 3D 模型并支持分步浏览。

## 项目结构

```
backend/          FastAPI 后端服务
frontend/         Vite + Three.js 前端
data/             本地开发数据目录
  source/         模型源文件 (.ldr/.mpd)
  ldraw-lib/      LDraw 零件库
  cache/          打包缓存
  logs/           运行日志
```

## 快速开始

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 访问

打开浏览器访问 `http://localhost:5173/viewer/10001`

## 许可证

本项目采用 [PolyForm Noncommercial License 1.0.0](LICENSE) —— 允许非商业用途下的使用、修改和分发，商业使用需另行授权。
