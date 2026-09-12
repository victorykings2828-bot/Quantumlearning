# Start the Quantum Learning Laboratory on this computer.
#
#   .\start.ps1             start it (builds the first time, which is slow)
#   .\start.ps1 -Stop        stop it
#   .\start.ps1 -Logs        watch what it is doing
#   .\start.ps1 -SetKey      turn on live AI answers with your provider key
#   .\start.ps1 -CheckAi     ask the provider whether your key actually works
#
# Everything runs locally in containers. Nothing is deployed and nothing is
# sent anywhere, unless you add an AI key yourself in step 6 of the README.

[CmdletBinding()]
param(
    [switch]$Stop,
    [switch]$Logs,
    [switch]$SetKey,
    [switch]$CheckAi,
    [string]$Key
)

$ErrorActionPreference = 'Stop'

# Work from the folder this script lives in, whatever directory you ran it from.
Set-Location -Path $PSScriptRoot

$port = if ($env:WEB_PORT) { $env:WEB_PORT } else { '8080' }
$url = "http://localhost:$port"

function Write-Bold($text) { Write-Host $text -ForegroundColor White }
function Write-Fail($text) { Write-Host "`n$text" -ForegroundColor Red }

# `docker compose` is current; `docker-compose` is the older standalone binary.
# Rewrite one KEY=value line in backend/.env, adding it if it is not there.
function Set-EnvVar($name, $value) {
    $file = 'backend/.env'
    $lines = Get-Content $file
    $found = $false
    $out = foreach ($line in $lines) {
        if ($line -match "^$name=") { "$name=$value"; $found = $true } else { $line }
    }
    if (-not $found) { $out += "$name=$value" }
    Set-Content -Path $file -Value $out
}

function Test-Compose {
    & docker compose version *> $null
    return ($LASTEXITCODE -eq 0)
}

function Compose {
    if (Test-Compose) { & docker compose @args } else { & docker-compose @args }
}

if ($Stop) {
    Write-Bold 'Stopping...'
    Compose down
    Write-Host 'Stopped. Your saved progress is kept. Run .\start.ps1 to start again.'
    exit 0
}

if ($Logs) {
    Compose logs -f
    exit $LASTEXITCODE
}

if ($SetKey) {
    # The key is written only to backend/.env, which git ignores. It is never
    # printed, never committed, and never reaches the browser.
    if (-not (Test-Path 'backend/.env')) { Copy-Item 'backend/.env.example' 'backend/.env' }
    if (-not $Key) {
        $secure = Read-Host -Prompt 'Paste your NVIDIA API key (it will not be shown)' -AsSecureString
        $Key = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
    }
    if (-not $Key) { Write-Fail 'No key given. Nothing changed.'; exit 1 }

    # Both of these matter. A key alone leaves the tutor in authored mode.
    Set-EnvVar 'NVIDIA_API_KEY' $Key
    Set-EnvVar 'TUTOR_PROVIDER' 'nvidia'
    Write-Bold 'Saved to backend/.env and switched the tutor to the live provider.'

    & docker info *> $null
    if ($LASTEXITCODE -eq 0 -and (Compose ps -q api)) {
        # --force-recreate matters: a container already built from the old
        # backend/.env keeps those values until it is replaced.
        Write-Host 'Restarting so it picks up the key...'
        Compose up -d --force-recreate api | Out-Null
        Write-Host ''
        & $PSCommandPath -CheckAi
        exit $LASTEXITCODE
    }
    Write-Host 'Start it with .\start.ps1, then check the key with .\start.ps1 -CheckAi'
    exit 0
}

if ($CheckAi) {
    if (-not (Compose ps -q api)) {
        Write-Fail 'It is not running. Start it with .\start.ps1 first.'
        exit 1
    }
    Write-Bold 'Asking the provider a real question...'
    Compose exec -T api python -m app.tools.tutor_smoke
    exit $LASTEXITCODE
}

# ---------------------------------------------------------------- prerequisites
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Fail 'Docker is not installed.'
    Write-Host @'
Install Docker Desktop, then run this script again:

    https://www.docker.com/products/docker-desktop/

Accept the installer defaults. Open Docker Desktop once after installing and
leave it running - you are ready when it shows "Engine running".
'@
    exit 1
}

& docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Fail 'Docker is installed but not running.'
    Write-Host @'
Open the Docker Desktop application and wait until it shows "Engine running"
at the bottom left, then run this script again.
'@
    exit 1
}

# ------------------------------------------------------------------ configuration
# The API reads backend/.env. Without it the tutor uses the written course
# material, which is a supported way to run the demo - not a broken state.
if (-not (Test-Path 'backend/.env')) {
    Write-Bold 'First run: creating backend/.env from the example.'
    Copy-Item 'backend/.env.example' 'backend/.env'
    Write-Host 'The tutor will answer from the authored course material.'
    Write-Host 'To use live AI instead, see step 6 of README.md.'
    Write-Host ''
}

# A key with the provider still set to "authored" is the one misconfiguration
# that looks like it worked. Say so rather than starting quietly in the wrong mode.
if (Test-Path 'backend/.env') {
    $envText = Get-Content 'backend/.env'
    $hasKey = $envText | Where-Object { $_ -match '^NVIDIA_API_KEY=.+' }
    $isLive = $envText | Where-Object { $_ -match '^TUTOR_PROVIDER=nvidia' }
    if ($hasKey -and -not $isLive) {
        Write-Fail 'You have an API key set, but the tutor is still in authored mode.'
        Write-Host @'
Your key will be ignored until the provider is switched. Fix it with:

    .\start.ps1 -SetKey

Continuing in authored mode for now.

'@
    }
}

# ------------------------------------------------------------------------ start
Write-Bold 'Starting the Quantum Learning Laboratory...'
Write-Host 'The first run builds everything and takes 5-15 minutes.'
Write-Host 'Later runs take about 20 seconds. Lots of scrolling text is normal.'
Write-Host ''

Compose up --build -d
if ($LASTEXITCODE -ne 0) {
    Write-Fail 'It did not start.'
    Write-Host @'
See what went wrong with:

    .\start.ps1 -Logs

The most common causes are Docker Desktop having stopped, and port 8080 already
being used by something else. To use a different port:

    $env:WEB_PORT=9090; .\start.ps1
'@
    exit 1
}

# The containers are starting, which is not the same as the page answering.
# Ask the page directly, so "Ready" is only ever printed when it is true.
Write-Host ''
Write-Host 'Waiting for it to finish starting' -NoNewline
$ready = $false
foreach ($attempt in 1..90) {
    try {
        Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 | Out-Null
        $ready = $true
        break
    }
    catch {
        Write-Host '.' -NoNewline
        Start-Sleep -Seconds 2
    }
}
Write-Host ''

if (-not $ready) {
    Write-Fail "The containers started but $url is not answering yet."
    Write-Host @'
It may still be starting. Wait a minute and open the address in your browser.
If it is still not there, see what went wrong with:

    .\start.ps1 -Logs
'@
    exit 1
}

Write-Bold "Ready - open $url"
Start-Process $url
Write-Host @"

  Open it in your browser:   $url

  Stop it:                   .\start.ps1 -Stop
  See what it is doing:      .\start.ps1 -Logs

You can close this window. The app keeps running until you stop it.
"@
