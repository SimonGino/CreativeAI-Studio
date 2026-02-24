## CreativeAI-Studio Backend

启动（开发）：

```bash
DATA_DIR=../data uv run uvicorn creativeai_studio.main:app --reload --port 8000
```

运行测试：

```bash
DATA_DIR=../data uv run pytest -q
```
