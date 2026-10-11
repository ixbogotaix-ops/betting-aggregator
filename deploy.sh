#!/bin/bash
set -e

echo "=========================================="
echo "  AI Sports Aggregator - Deploy Script"
echo "=========================================="

echo "1. Pulling latest code from GitHub..."
git pull origin main || git pull origin master

echo "2. Rebuilding and restarting containers..."
docker compose down || true
docker compose up -d --build

echo "3. Cleaning up old Docker images..."
docker image prune -f

echo "=========================================="
echo "  Deploy completed! App is running on port 80"
echo "=========================================="
