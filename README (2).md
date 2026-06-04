#!/usr/bin/env bash
# AgriMarket Recommendation Feature
# Phase 5: One-command deployment script
# Author: AJEICHEK ABEL NISSI (CT23A010)
#
# Usage:
#   ./scripts/deploy.sh              # deploy with 'latest' images
#   ./scripts/deploy.sh abc1234      # deploy specific git SHA tag
#
# Requires: docker, docker-compose, .env file in this directory

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/phase5_cicd/docker-compose.yml"
ENV_FILE="$PROJECT_DIR/phase5_cicd/.env"

TAG="${1:-latest}"

echo "============================================"
echo "  AgriMarket deployment — tag: $TAG"
echo "============================================"

# Check prerequisites
if ! command -v docker &>/dev/null; then
    echo "ERROR: docker is not installed or not in PATH"
    exit 1
fi
if ! command -v docker-compose &>/dev/null; then
    echo "ERROR: docker-compose is not installed or not in PATH"
    exit 1
fi
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env file not found at $ENV_FILE"
    echo "Copy .env.example to .env and fill in your values."
    exit 1
fi

export TRACKER_TAG="$TAG"
export API_TAG="$TAG"

# Pull latest images
echo ""
echo "Pulling images..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull tracker api

# Rolling restart
echo ""
echo "Starting containers..."
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# Wait for services
echo ""
echo "Waiting for health checks..."
sleep 8

# Smoke test
TRACKER_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/health)
API_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5002/health)

echo ""
echo "Tracker health: HTTP $TRACKER_OK"
echo "API health:     HTTP $API_OK"

if [ "$TRACKER_OK" = "200" ] && [ "$API_OK" = "200" ]; then
    echo ""
    echo "Deploy complete. Both services are healthy."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
else
    echo ""
    echo "ERROR: Health check failed. Rolling back to 'stable' tag."
    TRACKER_TAG=stable API_TAG=stable \
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d || true
    echo "Rollback attempted. Check logs with: docker-compose logs"
    exit 1
fi
