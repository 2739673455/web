.PHONY: help init_db app test fd

help:
	@echo "make init_db   		- 初始化数据库"
	@echo "make app       		- 启动后端应用"
	@echo "make test      		- 运行测试"
	@echo "make fd        		- 启动前端开发服务器"
	@echo "make clean        	- 清理临时文件"

init_db:
	cd backend && uv run -m app.init_db
app:
	cd backend && uv run -m app.main
test:
	cd backend && uv run -m pytest tests/
fd:
	cd frontend && pnpm dev

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "logs" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
