SHELL = /bin/bash

load_cloud_environment:
	source ./.venv/bin/activate && python -m internal.on_startup

uvicorn:
	source ./.venv/bin/activate && python -m internal.on_startup & source ./.venv/bin/activate && uvicorn main:app --host 0.0.0.0 --workers 5
