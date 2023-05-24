FROM python:3.11.2-bullseye
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH /root/.local/bin:$PATH

RUN mkdir project
COPY pyproject.toml project/
COPY poetry.lock project/
WORKDIR ./project

RUN poetry config virtualenvs.in-project true
RUN poetry install

COPY . .
