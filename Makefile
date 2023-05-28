SHELL = /bin/bash

uvicorn:
	source ./.venv/bin/activate && uvicorn main:app --host 0.0.0.0 --workers 5
