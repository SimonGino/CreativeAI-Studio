# CreativeAI-Studio（MVP）

单用户本地创作工作台：后端 FastAPI + 本地 SQLite + 本地资产落盘（`./data`）。

当前进度：后端已实现基础 API（Settings/Assets/Models/Jobs）+ 轻量 Runner（支持 `image.generate` / `video.generate` / `video.extend`）；前端 `web/` 已实现「生成/资产/历史/设置」基础页面并通过 Vite 代理直连后端。

## 目录结构

- `backend/`：FastAPI + SQLite + Runner
- `web/`：React（Vite）前端
- `docs/`：设计与计划

## 后端启动

依赖：Python 3.12+、已安装 `uv`

```bash
cd backend
DATA_DIR=../data uv run uvicorn creativeai_studio.main:app --reload --port 8000
```

打开 API 文档：`http://127.0.0.1:8000/docs`

## 前端启动

依赖：Node.js（建议 18+）+ `pnpm`

```bash
cd web
pnpm install
pnpm dev
```

前端地址：`http://127.0.0.1:5173`（默认）

> 已在 `web/vite.config.ts` 配置 `/api` 代理到 `http://127.0.0.1:8000`，所以本地开发不需要额外配置 CORS。

### 常用环境变量

- `DATA_DIR`：数据目录（默认 `./data`，包含 `app.db`、资产与凭据文件）

### 设置 API Key（本地明文存储，MVP）

```bash
curl -X PUT http://127.0.0.1:8000/api/settings \
  -H 'content-type: application/json' \
  -d '{"google_api_key":"YOUR_KEY","default_auth_mode":"api_key"}'
```

### 创建一个文生图任务（image.generate）

```bash
curl -X POST http://127.0.0.1:8000/api/jobs \
  -H 'content-type: application/json' \
  -d '{
    "job_type":"image.generate",
    "model_id":"nano-banana-pro",
    "params":{"prompt":"a cute cat","aspect_ratio":"1:1","image_size":"1k"},
    "auth":{"mode":"api_key"}
  }'
```

> 任务创建后会自动入队并由 Runner 异步执行；结果可通过 `GET /api/jobs/{id}` 查看 `result.output_asset_id`，再用 `GET /api/assets/{assetId}/content` 获取文件内容。

## 测试

```bash
cd backend
DATA_DIR=../data uv run pytest -q
```
