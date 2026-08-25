# apps/api needs Node AND Python: src/routes/evaluate.ts spawns
# `python -m engine.cli evaluate` against the engine/ package that lives at
# the repo root, not inside apps/api — so the whole monorepo (not just
# apps/api) must be present in the image, and the build context for this
# Dockerfile MUST be the repo root, e.g.:
#   docker build -f docker/api.Dockerfile -t agentlab-api .
FROM node:20-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY engine/requirements.txt ./engine/requirements.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r engine/requirements.txt
ENV PATH="/opt/venv/bin:${PATH}"

COPY engine/ ./engine/

COPY apps/api/package*.json ./apps/api/
RUN npm ci --prefix apps/api

COPY apps/api/ ./apps/api/
RUN npm run build --prefix apps/api

ENV NODE_ENV=production
EXPOSE 3001
CMD ["node", "apps/api/dist/index.js"]
