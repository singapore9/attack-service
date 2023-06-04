SHELL = /bin/bash

load_cloud_environment:
	source ./.venv/bin/activate && python -m internal.on_startup

uvicorn:
	source ./.venv/bin/activate && \
	python -m internal.on_startup & \
	mkdir logs && touch logs/attack-service.log && \
	source ./.venv/bin/activate && \
	uvicorn main:app --host 0.0.0.0 --workers 5 --log-config attack_service_log_config.ini
