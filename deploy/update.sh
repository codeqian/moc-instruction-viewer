#!/bin/bash
# ============================================================
# MOC Instruction Viewer — 更新部署脚本
# 代码有修改后执行此脚本更新线上
# ============================================================
set -e

APP_DIR="/opt/moc-viewer"
WWW_DIR="/var/www/moc-viewer"

echo "=== 拉取最新代码 ==="
cd "$APP_DIR"
git pull

echo "=== 更新后端依赖 ==="
cd "$APP_DIR/backend"
source venv/bin/activate
pip install -r requirements.txt -q

echo "=== 重建前端 ==="
cd "$APP_DIR/frontend"
npm install --silent
npm run build
rm -rf "$WWW_DIR"/*
cp -r dist/* "$WWW_DIR/"

echo "=== 重启后端 ==="
systemctl restart moc-viewer

echo "=== 重载 Nginx ==="
nginx -t && systemctl reload nginx

echo "更新完成！"
