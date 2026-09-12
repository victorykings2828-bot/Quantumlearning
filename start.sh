#!/usr/bin/env bash
#
# Start the Quantum Learning Laboratory on this computer.
#
#   ./start.sh          start it (builds the first time, which is slow)
#   ./start.sh --stop   stop it
#   ./start.sh --logs   watch what it is doing
#
# Everything runs locally in containers. Nothing is deployed and nothing is
# sent anywhere, unless you add an AI key yourself in step 6 of the README.

set -euo pipefail

# Work from the folder this script lives in, whatever directory you ran it from.
# Done with parameter expansion rather than `dirname` so it needs nothing extra.
script_dir="${BASH_SOURCE[0]%/*}"
[ "$script_dir" = "${BASH_SOURCE[0]}" ] && script_dir="."
cd "$script_dir"

readonly URL="http://localhost:${WEB_PORT:-8080}"

bold() { printf '\033[1m%s\033[0m\n' "$1"; }
fail() { printf '\n\033[1;31m%s\033[0m\n' "$1" >&2; }

open_browser() {
  if command -v open >/dev/null 2>&1; then open "$URL" >/dev/null 2>&1 || true
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true
  fi
}

# `docker compose` is current; `docker-compose` is the older standalone binary.
compose() {
  if docker compose version >/dev/null 2>&1; then docker compose "$@"
  else docker-compose "$@"
  fi
}

case "${1:-start}" in
  --stop|stop)
    bold "Stopping…"
    compose down
    echo "Stopped. Your saved progress is kept. Run ./start.sh to start again."
    exit 0
    ;;
  --logs|logs)
    exec compose logs -f
    ;;
  --help|-h)
    sed -n '2,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
    ;;
esac

# ---------------------------------------------------------------- prerequisites
if ! command -v docker >/dev/null 2>&1; then
  fail "Docker is not installed."
  cat <<'MSG'
Install Docker Desktop, then run this script again:

    https://www.docker.com/products/docker-desktop/

Accept the installer defaults. Open Docker Desktop once after installing and
leave it running — you are ready when it shows "Engine running".
MSG
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  fail "Docker is installed but not running."
  cat <<'MSG'
Open the Docker Desktop application and wait until it shows "Engine running"
at the bottom left, then run this script again.
MSG
  exit 1
fi

# ------------------------------------------------------------------ configuration
# The API reads backend/.env. Without it the tutor uses the written course
# material, which is a supported way to run the demo — not a broken state.
if [ ! -f backend/.env ]; then
  bold "First run: creating backend/.env from the example."
  cp backend/.env.example backend/.env
  echo "The tutor will answer from the authored course material."
  echo "To use live AI instead, see step 6 of README.md."
  echo
fi

# ------------------------------------------------------------------------ start
bold "Starting the Quantum Learning Laboratory…"
echo "The first run builds everything and takes 5–15 minutes."
echo "Later runs take about 20 seconds. Lots of scrolling text is normal."
echo

if ! compose up --build -d; then
  fail "It did not start."
  cat <<'MSG'
See what went wrong with:

    ./start.sh --logs

The most common causes are Docker Desktop having stopped, and port 8080 already
being used by something else. To use a different port:

    WEB_PORT=9090 ./start.sh
MSG
  exit 1
fi

# The containers are starting, which is not the same as the page answering.
# Ask the page directly, so "Ready" is only ever printed when it is true.
printf '\nWaiting for it to finish starting'
ready=""
for _ in $(seq 1 90); do
  if curl -fsS -o /dev/null "$URL" 2>/dev/null; then ready="yes"; break; fi
  printf '.'
  sleep 2
done
echo

if [ -z "$ready" ]; then
  fail "The containers started but $URL is not answering yet."
  cat <<'MSG'
It may still be starting. Wait a minute and open the address in your browser.
If it is still not there, see what went wrong with:

    ./start.sh --logs
MSG
  exit 1
fi

bold "Ready — open $URL"
open_browser
cat <<MSG

  Open it in your browser:   $URL

  Stop it:                   ./start.sh --stop
  See what it is doing:      ./start.sh --logs

You can close this terminal window. The app keeps running until you stop it.
MSG
