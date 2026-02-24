# 参考图资产选择器（Modal）设计

## 目标

在「生成」页的 `image.generate` 模式下，将“参考图（可选）”输入升级为与全站一致的交互：

- 用按钮触发本地上传（隐藏原生 `input[type=file]`）。
- 支持从资产库选择已有图片（默认展示“生成”，可切换“上传/全部”），选择后回填 `reference_image_asset_id`。
- 选中后在生成页展示缩略图 + 资产 ID，并支持一键清除。

## 用户流程

### 上传参考图
1. 点击「上传参考图」
2. 选择本地图片文件
3. 前端调用 `/api/assets/upload` 上传成功后，设置 `reference_image_asset_id = <uploaded_asset_id>`

### 从资产选择
1. 点击「从资产选择」
2. 打开 Modal
3. 默认筛选：`media_type=image` + `origin=generated`
4. 用户可切换来源：生成 / 上传 / 全部，并可分页浏览
5. 点击某张缩略图 → 立即选中并关闭 Modal → 回填 `reference_image_asset_id`

### 清除
点击「清除」将 `reference_image_asset_id` 置空。

## 组件与模块

- `Modal`：基础遮罩层 + 面板 + Esc/点击遮罩关闭（轻量、可复用）。
- `ImageAssetPickerModal`：
  - 仅面向图片资产（`media_type=image`）。
  - 来源筛选（生成/上传/全部）、分页、缩略图网格、选中态高亮。
  - 通过 `api.listAssets` 拉取列表，通过点击条目回传 `Asset`。

> 该能力先只用于“参考图”，后续如需可复用到视频首帧/尾帧输入。

## 数据流与接口

- 列表：`GET /api/assets?media_type=image&origin=<generated|upload|空>&limit=24&offset=<n>`
- 预览缩略图：`GET /api/assets/<id>/content`
- 写入作业参数：`params.reference_image_asset_id`

## 错误与边界

- 资产列表加载失败：Modal 内展示错误提示（并保留“关闭/重试”）。
- 列表为空：显示“暂无资产”空态。
- 分页：当返回数量 `< limit` 时禁用“下一页”。

## 非目标（本次不做）

- 按关键词搜索
- 多选
- 无限滚动/虚拟列表

