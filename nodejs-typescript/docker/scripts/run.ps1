$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")
if (-not $env:PZ_TUNNEL) {
    $env:PZ_TUNNEL = "nodejs-typescript-docker.portzero.local:80"
}

$project = "portzero-example-nodejs-typescript-docker-$PID"

docker compose -p $project up --build -d

try {
    $containerId = docker compose -p $project ps -q app
    $ready = $false
    for ($attempt = 0; $attempt -lt 100; $attempt++) {
        docker exec $containerId node -e "fetch('http://127.0.0.1:8080/').then(r => r.arrayBuffer())" *> $null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Milliseconds 100
    }
    if (-not $ready) {
        docker logs $containerId
        throw "Timed out waiting for the Node.js TypeScript container HTTP endpoint."
    }

    $hostPort = (docker compose -p $project port app 8080).Split(":")[-1]
    $tunnelHost = $env:PZ_TUNNEL.Split(":")[0]

    Write-Output "PORTZERO_EXAMPLE_LISTENING language=nodejs-typescript variant=docker host=127.0.0.1 port=$hostPort url=http://127.0.0.1:$hostPort/ tunnel=$env:PZ_TUNNEL tunnel_url=http://$tunnelHost/"
    Write-Output "This Node.js TypeScript container was launched with PZ_TUNNEL=$env:PZ_TUNNEL. Docker assigned localhost port $hostPort for the container's HTTP endpoint. Next, portzero-local's local daemon will detect PZ_TUNNEL and the listening port, then make it available at http://$tunnelHost/."

    docker compose -p $project logs -f app
}
finally {
    docker compose -p $project down --remove-orphans | Out-Null
}
