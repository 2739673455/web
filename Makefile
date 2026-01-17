.PHONY: app

init_db:
	uv run app/utils/_init_db.py
app:
	uv run -m app.main