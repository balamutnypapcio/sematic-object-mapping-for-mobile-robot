#!/usr/bin/env bash
# Runs on the host before the container starts (used by start.sh and VS Code).
# Writes .env next to docker-compose.yml, so the container user gets the same
# UID/GID as you, and allows the container to open windows (Gazebo, RViz2).
set -e
cd "$(dirname "$0")/.."

RENDER_GID=$(getent group render | cut -d: -f3)
cat > .env <<EOF
HOST_UID=$(id -u)
HOST_GID=$(id -g)
RENDER_GID=${RENDER_GID:-44}
EOF

xhost +local:docker >/dev/null 2>&1 || echo "Warning: xhost failed, GUI apps may not open."
