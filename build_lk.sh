#!/usr/bin/env bash
# ============================================================
# build_lk.sh — сборка кабинета: JSX → чистый JS (без Babel в браузере)
# Запускать на сервере один раз (и после любого изменения .jsx).
# Требует node + npm.
# ============================================================
set -e

cd "$(dirname "$0")"
LK_DIR="static/lk"

echo "[build] Проверка node..."
node --version || { echo "node не установлен. Установите: curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs"; exit 1; }

echo "[build] Установка Babel (локально, разово)..."
mkdir -p .build
cd .build
if [ ! -d node_modules/@babel/core ]; then
  npm init -y >/dev/null 2>&1
  npm install --no-save @babel/core @babel/cli @babel/preset-react
fi
cd ..

echo "[build] Компиляция app.bundle.jsx → app.bundle.js ..."
./.build/node_modules/.bin/babel "$LK_DIR/app.bundle.jsx" \
  --presets @babel/preset-react \
  --out-file "$LK_DIR/app.bundle.js"

echo "[build] Готово: $LK_DIR/app.bundle.js"
echo "[build] Теперь в templates/lk.html подключите app.bundle.js (см. lk.prod.html)"
