#!/bin/bash
# ============================================================
# MOC Instruction Viewer — ECS 一键部署脚本
# 在阿里云 ECS (Ubuntu 22.04) 上首次部署时执行
# ============================================================
set -e

APP_DIR="/opt/moc-viewer"
DATA_DIR="/data/moc-viewer"
WWW_DIR="/var/www/moc-viewer"
GIT_REPO="https://github.com/codeqian/moc-instruction-viewer.git"

echo "=== 1/8 安装系统依赖 ==="
apt-get update -y
apt-get install -y nginx python3 python3-pip python3-venv git curl

echo "=== 2/8 创建目录结构 ==="
mkdir -p "$APP_DIR"
mkdir -p "$DATA_DIR"/{source,ldraw-lib,cache/packed,cache/steps,logs}
mkdir -p "$WWW_DIR"

echo "=== 3/8 克隆项目 ==="
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR" && git pull
else
    git clone "$GIT_REPO" "$APP_DIR"
fi

echo "=== 4/8 安装后端依赖 ==="
cd "$APP_DIR/backend"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 安装 Node.js (使用 nodesource)
echo "=== 5/8 安装 Node.js ==="
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

echo "=== 6/8 构建前端 ==="
cd "$APP_DIR/frontend"
npm install
npm run build
cp -r dist/* "$WWW_DIR/"

echo "=== 7/8 配置 Nginx ==="
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/moc-viewer
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/moc-viewer /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "=== 8/8 配置后端服务 ==="
cp "$APP_DIR/deploy/moc-viewer.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable moc-viewer
systemctl restart moc-viewer

echo ""
echo "============================================"
echo " 部署完成！"
echo ""
echo " 还需手动操作："
echo " 1. 上传 LDraw 零件库到 $DATA_DIR/ldraw-lib/"
echo " 2. 上传模型 .ldr 文件到 $DATA_DIR/source/"
echo " 3. 将域名 DNS 解析到本 ECS 公网 IP"
echo " 4. 如用域名，修改 /etc/nginx/sites-available/moc-viewer"
echo "    将 server_name _; 改为你的域名"
echo "    nginx -t && systemctl reload nginx"
echo "============================================"
