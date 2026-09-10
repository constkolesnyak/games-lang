#!/bin/zsh
# Keep the local site running: installs a per-user launchd agent for scripts/serve.py (port 8777, restarts on login/crash).
# Remove with: launchctl bootout gui/$UID/dev.konst.games; rm ~/Library/LaunchAgents/dev.konst.games.plist
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PLIST=~/Library/LaunchAgents/dev.konst.games.plist
mkdir -p ~/Library/LaunchAgents "$ROOT/.logs"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>dev.konst.games</string>
  <key>ProgramArguments</key><array><string>$(command -v python3)</string><string>$ROOT/scripts/serve.py</string></array>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>EnvironmentVariables</key><dict><key>PORT</key><string>8777</string><key>AUTO_PUSH</key><string>1</string><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$ROOT/.logs/serve.log</string>
  <key>StandardErrorPath</key><string>$ROOT/.logs/serve.log</string>
</dict></plist>
PL
launchctl bootout gui/$UID/dev.konst.games 2>/dev/null || true
launchctl bootstrap gui/$UID "$PLIST"
sleep 1; launchctl print gui/$UID/dev.konst.games | grep -E "state|pid" | head -2
echo "→ http://localhost:8777/"
