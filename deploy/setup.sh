#!/bin/bash
# =============================================================
# hxz-fortune 初次上线初始化脚本（示例，Ubuntu）
# 使用前：将项目上传到 /opt/hxz-fortune
# 执行：sudo bash /opt/hxz-fortune/deploy/setup.sh
# =============================================================
set -e

DOMAIN="fortune.kiosk.pub"            # 默认域名；如需替换，请编辑此行或在运行前修改
PROJECT_DIR="/opt/hxz-fortune"
SERVICE_NAME="hxz-fortune"
LOG_DIR="/var/log/hxz-fortune"
APP_USER="$(stat -c '%U' "$PROJECT_DIR" 2>/dev/null || true)"

if [ -z "$APP_USER" ] || [ "$APP_USER" = "root" ]; then
    APP_USER="${SUDO_USER:-root}"
fi

if ! id -u "$APP_USER" >/dev/null 2>&1; then
    APP_USER="root"
fi

APP_GROUP="$(id -gn "$APP_USER" 2>/dev/null || echo "$APP_USER")"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: project directory $PROJECT_DIR not found. Place the project at $PROJECT_DIR or adjust PROJECT_DIR in this script."
    exit 1
fi

echo ">>> [1/7] 安装系统依赖（nginx, python3-venv, certbot）"
apt update -qq
apt install -y nginx python3-venv python3-certbot-nginx

echo ">>> [2/7] 创建 Python 虚拟环境并安装依赖（包含 gunicorn）"
cd "$PROJECT_DIR/backend"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install --quiet -r requirements.txt || true
pip install --quiet gunicorn
deactivate

echo ">>> [3/7] 创建日志目录"
mkdir -p "$LOG_DIR"
chown "$APP_USER:$APP_GROUP" "$LOG_DIR"

echo ">>> [4/7] 拷贝并启用 Nginx 站点配置"
cp "$PROJECT_DIR/deploy/nginx-hxz-fortune.conf" /etc/nginx/sites-available/$DOMAIN
# 将文件内的占位符替换为真实域名
sed -i "s|__DOMAIN__|$DOMAIN|g" /etc/nginx/sites-available/$DOMAIN
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/$DOMAIN
# 移除默认站点以防冲突
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ">>> [5/7] 申请 HTTPS 证书（Let's Encrypt）"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos \
    --email admin@$DOMAIN --redirect || true
systemctl reload nginx || true

echo ">>> [6/7] 安装并启动 systemd 服务"
cp "$PROJECT_DIR/deploy/hxz-fortune.service" /etc/systemd/system/$SERVICE_NAME.service
sed -i "s|__APP_USER__|$APP_USER|g; s|__APP_GROUP__|$APP_GROUP|g" /etc/systemd/system/$SERVICE_NAME.service
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME

echo ">>> [7/7] 验收检查"
sleep 2
systemctl status $SERVICE_NAME --no-pager || true
nginx -t || true

echo "=== 初始化完成 ==="
echo "访问地址：https://$DOMAIN"
echo "日志路径：$LOG_DIR"
echo "服务管理：systemctl status|restart|stop $SERVICE_NAME"
