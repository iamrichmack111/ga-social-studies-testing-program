#!/usr/bin/env bash
set -euo pipefail
D="$(cd "$(dirname "${BASH_SOURCE[0]}")"&&pwd)";ID="ga-social-studies-testing-program";cd "$D"
python3 -m venv .venv;.venv/bin/python -m pip install --upgrade pip;.venv/bin/python -m pip install -r requirements.txt
mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/scalable/apps"
cp assets/logo.svg "$HOME/.local/share/icons/hicolor/scalable/apps/$ID.svg"
cat >"$HOME/.local/share/applications/$ID.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Georgia Social Studies Testing Program
Comment=Adaptive Georgia social studies testing for Grades 3-8
Exec=$D/start-desktop.sh
Path=$D
Icon=$HOME/.local/share/icons/hicolor/scalable/apps/$ID.svg
Terminal=false
Categories=Education;
EOF
chmod +x start-desktop.sh "$HOME/.local/share/applications/$ID.desktop"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null||true
echo "Installed. Run ./start-desktop.sh"
