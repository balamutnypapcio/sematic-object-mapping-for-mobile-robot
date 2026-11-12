#!/usr/bin/env bash
# Builds the image (if needed), starts the container and opens a shell in it.
# For more terminals run ./start.sh again (the running container is reused).
set -e
cd "$(dirname "$0")"

# Write .env so the container user gets the same UID/GID as you
# and can access the GPU render device.
RENDER_GID=$(getent group render | cut -d: -f3)
cat > .env <<EOF
HOST_UID=$(id -u)
HOST_GID=$(id -g)
RENDER_GID=${RENDER_GID:-44}
EOF

# Allow the container to open windows (Gazebo, RViz2)
xhost +local:docker >/dev/null 2>&1 || echo "Warning: xhost failed, GUI apps may not open."

docker compose up -d --build
docker compose exec ros_dev bash