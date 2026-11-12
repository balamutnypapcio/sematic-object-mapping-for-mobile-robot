#!/usr/bin/env bash
# Builds the image (if needed), starts the container and opens a shell in it.
# For more terminals run ./start.sh again (the running container is reused).
set -e
cd "$(dirname "$0")"

bash .devcontainer/init.sh
docker compose up -d --build
docker compose exec ros_dev bash
