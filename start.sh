#!/usr/bin/env bash
# Buduje (jeśli trzeba) i uruchamia kontener, potem otwiera w nim terminal.
# Kolejne terminale: ./start.sh jeszcze raz (kontener już działa, tylko się podłącza).
set -e
cd "$(dirname "$0")"

export HOST_UID=$(id -u)
export HOST_GID=$(id -g)
RENDER_GID=$(getent group render | cut -d: -f3 || true)
export RENDER_GID=${RENDER_GID:-44}

xhost +local:docker >/dev/null
docker compose up -d --build
docker compose exec ros_dev bash
