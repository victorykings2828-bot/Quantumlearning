# Start the Quantum Learning Laboratory on this computer.
#
#   .\start.ps1          start it (builds the first time, which is slow)
#   .\start.ps1 -Stop    stop it
#   .\start.ps1 -Logs    watch what it is doing
#
# Everything runs locally in containers. Nothing is deployed and nothing is
# sent anywhere, unless you add an AI key yourself in step 6 of the README.

[CmdletBinding()]
param(
    [switch]$Stop,
    [switch]$Logs
)

$ErrorActionPreference = 'Stop'

# Work from the folder this script lives in, whatever directory you ran it from.
Set-Location -Path $PSScriptRoot

$port = if ($env:WEB_PORT) { $env:WEB_PORT } else { '8080' }
$url = "http://localhost:$port"

function Write-Bold($text) { Write-Host $text -ForegroundColor White }
function Write-Fail($text) { Write-Host "`n$text" -ForegroundColor Red }

# `docker compose` is current; `docker-compose` is the older standalone binary.
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
