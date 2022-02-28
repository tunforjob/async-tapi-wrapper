FROM python:3.10 as base

FROM base as builder

RUN pip install pipenv

WORKDIR /app/

COPY Pipfile* ./
RUN pipenv install --system --deploy --dev
COPY . .

FROM base
WORKDIR /app/
COPY --from=builder /app/ .
COPY --from=builder /usr/local /usr/local
