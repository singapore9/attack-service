SHELL = /bin/bash

image_name = attack-service

build:
	docker build -t $(image_name) .

run: build
	docker run -it $(image_name) /bin/bash

uvicorn:
	source ./.venv/bin/activate && uvicorn main:app --host 0.0.0.0 --workers 5
