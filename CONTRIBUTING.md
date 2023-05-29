# Contributing & Development

For development it's nice to have installed pre-commit (https://pre-commit.com/)

pre-commit 3.3.1

## Project Structure

Path | Description | Hint
--- | --- | ---
/internal | **models, work with DB, calculations** |
/internal/extractor.py | "cloud environment config" parsing |
/internal/on_startup.py | saving the result of extractor.py to DB in more optimal datastructures |
/main.py | **FastAPI server** |
/routers | FastAPI endpoints (with versions, but now latest version is equal to v1) |
/middlewares | **FastAPI request/response wrappers** |
/middlewares/check_service_status_middleware.py | Starts attacks only when "cloud environment config" was successfully parsed | Can be disabled by putting CHECK_SERVICE_STATUS=1 in .env
/middlewares/save_service_statistic_middleware.py | Saves statistic info about requests | Can be disabled by putting SAVE_SERVICE_STATISTIC=1 in .env


## TODO
Realtime dashboards:
- Add integration with Prometheus + Graphana

Realtime troubleshooting:
- Add integration with NewRelic / Sentry

Remote logs access:
- Change print (which is works fine with `docker compose logs`) to logging module. Add integration with Elasticsearch

Optimization:
- Use kind of cache for duplicated /attack endpoint (for example, from already saved requests)
