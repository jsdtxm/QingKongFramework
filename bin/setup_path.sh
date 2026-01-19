#!/bin/sh
# QingKongFramework Environment Setup Script

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$SCRIPT_DIR:$PATH"

HOME_DIR="${HOME:-$(eval echo ~$(whoami))}"

add_to_rc() {
    RC_FILE="$1"
    EXPORT_LINE="export PATH=\"$SCRIPT_DIR:\$PATH\""
    if [ -f "$RC_FILE" ]; then
        if ! grep -qF "$SCRIPT_DIR" "$RC_FILE" 2>/dev/null; then
            echo "" >> "$RC_FILE"
            echo "# QingKongFramework" >> "$RC_FILE"
            echo "$EXPORT_LINE" >> "$RC_FILE"
            echo "[QingKongFramework] Added to $RC_FILE"
        else
            echo "[QingKongFramework] Already configured in $RC_FILE"
        fi
    fi
}

add_to_rc "$HOME_DIR/.bashrc"
add_to_rc "$HOME_DIR/.zshrc"

echo "[QingKongFramework] Setup complete. Please restart your terminal or run: source $HOME_DIR/.bashrc"
