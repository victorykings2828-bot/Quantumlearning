param([switch]$Stop)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host 'Docker Desktop is needed for this reusable launcher.'
    Write-Host 'The current native review preview is http://127.0.0.1:5189 while its servers are running.'
    exit 1
}
$env:WEB_PORT = '127.0.0.1:8089'
$env:PUBLIC_ORIGIN = 'http://127.0.0.1:8089'
$env:COOKIE_SECURE = 'false'
$composeArgs = @('compose', '--project-name', 'quantumlearning-reviewer-test', '-f', 'compose.yml', '-f', 'compose.review.yml')
if ($Stop) {
    & docker @composeArgs stop
    exit $LASTEXITCODE
}
& docker @composeArgs up -d --build
if ($LASTEXITCODE -ne 0) { throw 'The isolated review stack did not start.' }
$ready = $false
for ($attempt = 0; $attempt -lt 45; $attempt++) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8089/api/v1/health/ready' -TimeoutSec 3
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}
if (-not $ready) { throw 'Review stack started but is not ready. Check docker compose logs for the quantumlearning-reviewer-test project.' }
Write-Host 'Test version ready: http://127.0.0.1:8089'
Write-Host 'Separate database volume and cookie names. Your main instance is unchanged.'
