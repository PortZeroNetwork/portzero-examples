#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."
: "${PZ_TUNNEL:=python-docker.portzero.local:80}"
export PZ_TUNNEL

image="portzero-example-python-docker"
container="portzero-example-python-docker-$$"

docker build -t "$image" .
container_id="$(docker run --rm -d --name "$container" -e "PZ_TUNNEL=$PZ_TUNNEL" -p 127.0.0.1::8080 "$image")"

cleanup() {
    docker stop "$container_id" >/dev/null 2>&1 || true
}
trap cleanup INT TERM EXIT

attempts=0
until docker exec "$container_id" python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/', timeout=1).read()" >/dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 100 ]; then
        docker logs "$container_id"
        exit 1
    fi
    sleep 0.1
done

host_port="$(docker port "$container_id" 8080/tcp | sed 's/.*://')"
tunnel_host="${PZ_TUNNEL%%:*}"

printf 'PORTZERO_EXAMPLE_LISTENING language=python variant=docker host=127.0.0.1 port=%s url=http://127.0.0.1:%s/ tunnel=%s tunnel_url=http://%s/\n' "$host_port" "$host_port" "$PZ_TUNNEL" "$tunnel_host"
printf "This Python container was launched with PZ_TUNNEL=%s. Docker assigned localhost port %s for the container's HTTP endpoint. Next, portzero-local's local daemon will detect PZ_TUNNEL and the listening port, then make it available at http://%s/.\n" "$PZ_TUNNEL" "$host_port" "$tunnel_host"

docker logs -f "$container_id" &
logs_pid="$!"
docker wait "$container_id" >/dev/null
wait "$logs_pid"
