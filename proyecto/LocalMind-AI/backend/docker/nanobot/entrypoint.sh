#!/bin/sh
dir="$HOME/.nanobot"

# Create config directory if needed
mkdir -p "$dir"

# If a config.json is mounted at /app/config/config.json, symlink it
if [ -f /app/config/config.json ]; then
    cp /app/config/config.json "$dir/config.json"
    echo "Config loaded from /app/config/config.json"
fi

# If skills directory is mounted, symlink workspace skills
if [ -d /app/config/skills ]; then
    mkdir -p "$dir/skills"
    cp -r /app/config/skills/* "$dir/skills/" 2>/dev/null || true
    echo "Skills loaded from /app/config/skills/"
fi

# Check directory is writable
if [ -d "$dir" ] && [ ! -w "$dir" ]; then
    owner_uid=$(stat -c %u "$dir" 2>/dev/null || stat -f %u "$dir" 2>/dev/null)
    cat >&2 <<EOF
Error: $dir is not writable (owned by UID $owner_uid, running as UID $(id -u)).

Fix (pick one):
  Host:   sudo chown -R 1000:1000 ~/.nanobot
  Docker: docker run --user \$(id -u):\$(id -g) ...
EOF
    exit 1
fi

# Default command: start both the gateway (WebSocket) and the REST API server concurrently
if [ "$1" = "gateway" ]; then
    echo "Starting Nanobot gateway in background..."
    nanobot gateway &
    GATEWAY_PID=$!
    
    echo "Starting Nanobot serve..."
    nanobot serve &
    SERVE_PID=$!
    
    # Wait for either process to exit using a standard shell-compatible loop
    while kill -0 $GATEWAY_PID 2>/dev/null && kill -0 $SERVE_PID 2>/dev/null; do
        sleep 1
    done
    
    echo "One of the services exited. Exiting container."
    kill $GATEWAY_PID $SERVE_PID 2>/dev/null
    exit 0
else
    exec nanobot "$@"
fi
