.PHONY: help init_db app test fd

help:
	@echo "make init_db   - 初始化数据库"
	@echo "make app       - 启动后端应用"
	@echo "make test      - 运行测试"
	@echo "make fd        - 启动前端开发服务器"

init_db:
	uv run app/utils/_init_db.py
app:
	uv run -m app.main
test:
	uv run pytest tests/
fd:
	cd fd && pnpm dev