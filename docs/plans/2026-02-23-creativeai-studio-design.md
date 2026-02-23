# CreativeAI-Studio（MVP）设计文档

日期：2026-02-23  
状态：已确认（用户 OK）  
定位：单用户本地工具（后续可演进为 SaaS）  

## 1. 背景与目标

希望在本仓库实现一个本地可运行的创作工作台，支持：

- AI 文生图（当前仅支持 `nano banana pro`）
- AI 图/文生视频（当前仅支持 `veo3.1`、`veo3.1 fast`）
- 资产管理（上传/生成产物统一入库）与历史任务可追溯
- 视频延长（Extend）：Vertex AI 路径下依赖 GCS Bucket 输出

同时，架构需满足：

- MVP 不过度设计、易部署、稳定可用
- 模型/供应商可扩展（后续添加更多模型/供应商，尽量不重写 UI/业务）
- 为未来 SaaS 化保留边界（存储/队列/鉴权可替换）

## 2. 非目标（MVP 不做）

- 登录、多租户、计费、配额
- 复杂编辑能力（时间线、剪辑、特效、批量工作流等）
- 分布式队列/多 worker（先单机跑通）

## 3. 需求范围（MVP）

### 3.1 文生图（含可选参考图）

- 输入：`prompt`、可选上传图片（reference）、`resolution`（随模型约束）、`aspect_ratio`（含 `auto`）
- 输出：图片文件落盘 + 资产入库 + 任务历史可复现

### 3.2 图/文生视频（可选首尾帧）

- 输入：`prompt`、`duration`（随模型约束）、`aspect_ratio`、可选 `start_image`、可选 `end_image`
- 允许不上传图片（纯文生视频）
- 输出：视频文件落盘 + 资产入库 + 任务历史可复现

### 3.3 延长视频（Extend）

- 输入：选择一条已存在的视频资产 + `extend_seconds` + 可选 `prompt`
- 仅 Vertex 方式支持（MVP）
- 需要配置 `VERTEX_GCS_BUCKET`（bucket-name，不含 `gs://`）
- 输出：延长后的视频作为新资产入库，并关联原视频（parent 关系）

### 3.4 资产管理与历史

- 资产库：按类型（图/视频）、来源（upload/generated）、模型、时间筛选
- 历史任务：状态（queued/running/succeeded/failed/canceled）、错误可复制、产物可追溯
- 一键复用：从任意历史任务“克隆参数再生成/再延长”

### 3.5 设置（本地保存）

- 默认鉴权模式：API Key 或 Vertex JSON（二选一作为默认）
- 任务级覆盖：每次创建任务可临时覆盖鉴权模式（默认=全局设置）
- UI 支持保存：
  - API Key：粘贴保存（本机明文存储，后续 SaaS 再升级）
  - Vertex JSON：上传保存到本地 `./data/credentials/vertex-sa.json`
- `VERTEX_GCS_BUCKET` 在设置页配置，并提供“测试”能力

## 4. 技术栈与仓库形态

- 后端：Python + `uv` + FastAPI
- 前端：React + pnpm（Vite）
- 数据：SQLite（本地）+ 本地文件夹（资产落盘）

推荐 Monorepo：

- `backend/`：FastAPI API、任务 Runner、Provider、资产存储
- `web/`：React UI
- `docs/`：设计与计划文档

## 5. 架构概览（可扩展但保持简单）

### 5.1 核心模块（后端）

- `ModelCatalog`：模型能力定义（分辨率、比例、时长、是否支持首尾帧、是否支持 extend 等）
- `Provider`（策略模式）：
  - `GoogleAIStudioProvider`：API Key 路径
  - `GoogleVertexProvider`：service-account JSON + project/location + GCS（用于 extend/或后续更多能力）
- `JobRunner`：内置轻量队列（单机并发控制、状态更新、重启恢复）
- `AssetStore`：本地落盘 + 资产 URL 输出（后续可替换对象存储）

### 5.2 数据流（概览）

1) 前端创建任务（/jobs）  
2) 后端写入 `jobs`（queued）并入队  
3) Runner 执行 → 调用 Provider → 下载/落盘产物  
4) 写入 `assets` + 关联表 → 更新 `jobs`（succeeded/failed）  
5) 前端轮询或 SSE 订阅获取状态与结果  

## 6. 存储设计

### 6.1 目录布局（默认 `DATA_DIR=./data`）

- `./data/app.db`：SQLite
- `./data/assets/`
  - `uploads/`：用户上传
  - `generated/`：模型生成（含延长产物）
- `./data/credentials/vertex-sa.json`：Vertex service account JSON
- `./data/tmp/`：下载/转存中转（任务结束清理）

### 6.2 SQLite 表（概览）

`settings`
- 单用户 key/value（value 为 JSON 字符串，便于扩展）

`assets`
- 统一记录上传/生成产物（路径、尺寸、时长、来源、关联 job）

`jobs`
- 记录任务类型、模型、鉴权模式、状态、参数快照、结果摘要、错误信息

`job_assets`
- 任务与资产的多对多关系（role：input/start/end/output 等），便于历史复现与 UI 展示

## 7. 模型能力与参数校验

### 7.1 统一 Catalog（后端单一事实来源）

`GET /api/models` 返回：

- `model_id`、`media_type`（image/video）
- `auth_support`（api_key/vertex）与 `auth_required`（如 extend 强制 vertex）
- `prompt_max_chars`
- image：`resolution_presets`、`aspect_ratios`、`reference_image_supported`
- video：`duration_range/enum`、`aspect_ratios`、`start_end_image_supported`、`extend_supported`

### 7.2 Auto 长宽比规则（MVP）

- 若有输入图且选择 `auto`：取输入图宽高比，映射到模型支持的最接近比例
- 若无输入图且 `auto`：
  - 图片默认 `1:1`
  - 视频默认 `16:9`

后端在创建/执行任务时计算最终 `width/height` 并写入 `jobs.params_json`，确保历史可复现。

## 8. 任务系统（Runner）与可靠性

### 8.1 状态机

- `queued` → `running` → `succeeded|failed`
- 可取消：`queued` 可立即取消；`running` 为 best-effort（记录取消请求并尽量终止）

### 8.2 重启恢复

服务启动时扫描：

- `running` 且超时/无心跳 → 标记 `failed`（或按策略重试，MVP 先 fail-fast）
- `queued` → 重新入队

### 8.3 前端更新策略

MVP 使用轮询（1~2s）拉取 job 状态；后续可加 SSE（不破坏现有 API）。

## 9. Vertex Extend 与 `VERTEX_GCS_BUCKET`

### 9.1 配置约束

- `VERTEX_GCS_BUCKET` 必填（bucket 名称，不含 `gs://`）
- 在创建 `video.extend` job 时强校验：未配置直接返回 400（可读错误）

### 9.2 Extend 数据流

1) 本地输入视频上传到 `gs://<bucket>/creativeai-studio/<jobId>/input.mp4`  
2) 调 Vertex extend 任务，输出到同 bucket 的 job 前缀  
3) 完成后下载输出到本地 `./data/assets/generated/videos/<jobId>/out.mp4`  
4) 产物入库为新资产，并记录 `parent_asset_id` 指向原视频  
5) （可选）清理 GCS 中转文件（MVP 可先保留便于排错）

## 10. API 列表（摘要）

前缀统一 `/api`（为未来 SaaS 网关/鉴权做准备）。

Models
- `GET /api/models`

Assets
- `POST /api/assets/upload`
- `GET /api/assets`
- `GET /api/assets/{id}`
- `GET /api/assets/{id}/content`

Jobs
- `POST /api/jobs`
- `GET /api/jobs`
- `GET /api/jobs/{id}`
- `POST /api/jobs/{id}/cancel`
- `POST /api/jobs/{id}/clone`

Settings
- `GET /api/settings`
- `PUT /api/settings`
- `POST /api/settings/vertex-sa`
- `POST /api/settings/test`

## 11. 前端信息架构（暗色现代风，避免蓝紫渐变）

导航：`生成` / `资产` / `历史` / `设置`

生成页（参考 Seedance 的“左参右预览”布局）
- 左侧：模型选择、提示词、分辨率/时长、长宽比（含 auto）、上传（reference/start/end）
- 右侧：运行状态、结果预览（图 viewer / 视频 player）、下载/复制、复用参数

资产页
- Grid + 筛选；点击卡片 Drawer 展示详情；可“作为输入用于生成/延长”

历史页
- 列表/表格展示任务状态；支持查看详情、取消、克隆复用

设置页
- 默认鉴权模式（API Key / Vertex）
- API Key 保存（mask 展示）
- Vertex JSON 上传保存 + project/location
- `VERTEX_GCS_BUCKET` 配置与测试

## 12. 安全与隐私（MVP）

- 单机单用户：凭据与资产均保存在本地 `./data`
- API Key 明文存储（MVP），后续 SaaS 需迁移到加密存储（KMS/Vault）并做访问控制

## 13. 演进路线（向 SaaS 迁移）

保持 API 与模块边界不变，逐步替换基础设施：

- SQLite → Postgres（带用户/租户字段）
- 本地 `AssetStore` → 对象存储（GCS/S3）
- 内置 Runner → 分布式队列（Celery/RQ/Cloud Tasks）
- Settings → per-user/per-tenant secrets 管理
- 增加 Auth、RBAC、配额与计费

