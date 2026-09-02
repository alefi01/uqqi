#!/usr/bin/env bash
# Подготовка дизайн-гейтов (ux-ui-agent-skills) к запуску.
#
# Гейты рендера (taste_audit, slop_tells, verify_states, axe_audit…) поднимают
# Chromium через node-playwright. В контейнерах Claude Code браузеры лежат в
# /opt/pw-browsers, но версия сборки может не совпадать с той, которую ждёт
# npm-пакет playwright, — тогда launch() падает «Executable doesn't exist».
# Скрипт ставит зависимости и подкладывает симлинки на реально доступную сборку.
#
# Запуск:  bash scripts/design_gate_setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

npm install --no-audit --no-fund

PW_DIR="${PLAYWRIGHT_BROWSERS_PATH:-/opt/pw-browsers}"
[ -d "$PW_DIR" ] || { echo "Нет $PW_DIR — гейты рендера недоступны"; exit 0; }

# Какую сборку ждёт установленный playwright
want=$(node -e "
const {chromium}=require('playwright');
chromium.launch().then(b=>b.close()).then(()=>console.log('')).catch(e=>{
  const m=/chromium_headless_shell-(\d+)/.exec(e.message); console.log(m?m[1]:'');
})" || true)
[ -n "$want" ] || { echo "Chromium уже запускается, симлинки не нужны"; exit 0; }

have=$(ls -d "$PW_DIR"/chromium_headless_shell-* 2>/dev/null | head -1 | sed 's/.*-//')
[ -n "$have" ] || { echo "В $PW_DIR нет chromium_headless_shell-*"; exit 1; }

mkdir -p "$PW_DIR/chromium_headless_shell-$want/chrome-headless-shell-linux64"
ln -sf "$PW_DIR/chromium_headless_shell-$have/chrome-linux/headless_shell" \
       "$PW_DIR/chromium_headless_shell-$want/chrome-headless-shell-linux64/chrome-headless-shell"
touch "$PW_DIR/chromium_headless_shell-$want/INSTALLATION_COMPLETE" \
      "$PW_DIR/chromium_headless_shell-$want/DEPENDENCIES_VALIDATED"

mkdir -p "$PW_DIR/chromium-$want/chrome-linux"
ln -sfn "$PW_DIR"/chromium-"$have"/chrome-linux/* "$PW_DIR/chromium-$want/chrome-linux/" 2>/dev/null || true
touch "$PW_DIR/chromium-$want/INSTALLATION_COMPLETE" "$PW_DIR/chromium-$want/DEPENDENCIES_VALIDATED"

echo "Готово: сборка $have подложена как $want"
