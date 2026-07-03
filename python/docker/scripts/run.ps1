$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")
if (-not $env:PZ_TUNNEL) {
    $env:PZ_TUNNEL = "python-docker.portzero.local:80"
}

$image = "portzero-example-python-docker"
$container = "portzero-example-python-docker-$PID"

docker build -t $image .
$containerId = docker run --rm -d --name $container -e "PZ_TUNNEL=$env:PZ_TUNNEL" -p "127.0.0.1::8080" $image

try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 100; $attempt++) {
        docker exec $containerId python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/', timeout=1).read()" *> $null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Milliseconds 100
    }
    if (-not $ready) {
        docker logs $containerId
        throw "Timed out waiting for the Python container HTTP endpoint."
    }

    $hostPort = (docker port $containerId "8080/tcp").Split(":")[-1]
    $tunnelHost = $env:PZ_TUNNEL.Split(":")[0]

    Write-Output "PORTZERO_EXAMPLE_LISTENING language=python variant=docker host=127.0.0.1 port=$hostPort url=http://127.0.0.1:$hostPort/ tunnel=$env:PZ_TUNNEL tunnel_url=http://$tunnelHost/"
    Write-Output "This Python container was launched with PZ_TUNNEL=$env:PZ_TUNNEL. Docker assigned localhost port $hostPort for the container's HTTP endpoint. Next, portzero-local's local daemon will detect PZ_TUNNEL and the listening port, then make it available at http://$tunnelHost/."

    docker logs -f $containerId
}
finally {
    docker stop $containerId | Out-Null
}
