#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."
: "${PZ_TUNNEL:=nodejs-typescript-docker.portzero.local:80}"
export PZ_TUNNEL

project="portzero-example-nodejs-typescript-docker-$$"

docker compose -p "$project" up --build -d

cleanup() {
    docker compose -p "$project" down --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup INT TERM EXIT

container_id="$(docker compose -p "$project" ps -q app)"

attempts=0
until docker exec "$container_id" node -e "fetch('http://127.0.0.1:8080/').then(r => r.arrayBuffer())" >/dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 100 ]; then
        docker logs "$container_id"
        exit 1
    fi
    sleep 0.1
done

host_port="$(docker compose -p "$project" port app 8080 | sed 's/.*://')"
tunnel_host="${PZ_TUNNEL%%:*}"

printf 'PORTZERO_EXAMPLE_LISTENING language=nodejs-typescript variant=docker host=127.0.0.1 port=%s url=http://127.0.0.1:%s/ tunnel=%s tunnel_url=http://%s/\n' "$host_port" "$host_port" "$PZ_TUNNEL" "$tunnel_host"
printf "This Node.js TypeScript container was launched with PZ_TUNNEL=%s. Docker assigned localhost port %s for the container's HTTP endpoint. Next, portzero-local's local daemon will detect PZ_TUNNEL and the listening port, then make it available at http://%s/.\n" "$PZ_TUNNEL" "$host_port" "$tunnel_host"

docker compose -p "$project" logs -f app &
logs_pid="$!"
docker wait "$container_id" >/dev/null
wait "$logs_pid"
