# attack-service
Service for scanning linked VMs for weak items

## How it works?
This service contains from:
- Back-end FastAPI server
- MongoDB database
- .env file
- JSON file with "cloud environment config"
- Python3 script for pre-processing JSON file


Service behaviour:

1. Python3 script does JSON-file parsing, saves it's info into DB for faster responses.

1. FastAPI server handles requests

    - all the endpoints you can see when start running this service on http://localhost/docs

    x.1. Has endpoint /status - it shows can server do attack or not (when #1 finished with fail, for example)

    x.2. Requests related to attacks return info about attack only if /status is OK. Otherwise, they return info from /status endpoint.

    x.3. Info about requests duration is saved during request time.


## Running
For local start you should have:

- Docker 20.10.23
- Docker Compose version v2.15.1
- .env file in this directory (check .env.sample as example with more info)
- JSON file with "cloud environment config" in this directory

#### Hint: you can just copy .env.sample file and rename the copy to ".env"
#### Hint 2: CLOUD_ENV_PATH in .env file - relative path to "cloud environment config"

```bash
docker compose up --build
```

You can see all the endpoints on http://localhost/docs after successful start.

Check http://localhost/docs#/default/get_status_status_get (or http://localhost/status), after successful starting docker containers.

If it has ```"ok": true```,  then "cloud environment config" was successfully parsed.

#### Hint 3: if you want to see logs, then use docker: ``docker compose logs --no-color > ~/prefered/location/for/logs.txt``

## Contributing
See CONTRIBUTING.md
