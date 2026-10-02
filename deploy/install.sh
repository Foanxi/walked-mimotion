#!/usr/bin/env bash
# 在 Linux 服务器上以源码方式部署 mimotion 可视化页面（venv + systemd 常驻）
#
# 用法（在本仓库根目录执行）：
#   sudo ./deploy/install.sh                     # 安装到 /opt/mimotion，端口 8888
#   sudo ./deploy/install.sh /opt/mimotion 9000  # 自定义目录与端口
#
# 支持 Ubuntu / Debian / CentOS / RHEL（x86_64、aarch64 均可）
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"
DIR="${1:-/opt/mimotion}"
PORT="${2:-8888}"
SVC="mimotion-web"

if [[ ${EUID} -ne 0 ]]; then
    echo "请使用 root 或 sudo 运行：sudo $0"
    exit 1
fi

echo "==> 源码：$SRC"
echo "==> 安装目录：$DIR  端口：$PORT"

# 1. 系统依赖
if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq python3 python3-venv python3-pip rsync
elif command -v dnf >/dev/null 2>&1; then
    dnf install -y -q python3 python3-pip rsync
elif command -v yum >/dev/null 2>&1; then
    yum install -y -q python3 python3-pip rsync
else
    echo "未识别的包管理器，请手动安装：python3 / python3-venv / pip / rsync"
    exit 1
fi

# 2. 同步代码（排除无关文件，保留已存在的 .env）
mkdir -p "$DIR"
if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
        --exclude '.git' --exclude '.build-venv' --exclude 'venv' \
        --exclude 'dist' --exclude 'build' --exclude '__pycache__' --exclude '.env' \
        "$SRC/" "$DIR/"
else
    cp -r "$SRC"/. "$DIR/"
fi

# 3. 虚拟环境与依赖
python3 -m venv "$DIR/venv"
"$DIR/venv/bin/pip" install -q -U pip
"$DIR/venv/bin/pip" install -q -r "$DIR/requirements.txt"

# 4. 配置文件
if [[ ! -f "$DIR/.env" ]]; then
    if [[ -f "$DIR/.env.example" ]]; then
        cp "$DIR/.env.example" "$DIR/.env"
        echo "==> 已生成 $DIR/.env，请填入账号密码后执行：sudo systemctl restart $SVC"
    else
        echo "==> 未找到 .env.example，请自行创建 $DIR/.env"
    fi
fi

# 5. systemd 常驻（账号密码等敏感配置由程序自己从 .env 读取，避免被 systemd 错误解析）
cat >"/etc/systemd/system/${SVC}.service" <<EOF
[Unit]
Description=mimotion web ui
After=network.target

[Service]
Type=simple
WorkingDirectory=${DIR}
Environment=PORT=${PORT}
Environment=DATA_DIR=${DIR}
ExecStart=${DIR}/venv/bin/python ${DIR}/web_app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "$SVC"

echo
echo "==> 部署完成"
echo "    配置文件：$DIR/.env"
echo "    访问地址：http://服务器公网IP:${PORT}"
echo "    查看日志：journalctl -u ${SVC} -f"
echo "    重启服务：systemctl restart ${SVC}"
echo "    停止服务：systemctl stop ${SVC}"
echo
echo "提示：如有防火墙/安全组，需放行 ${PORT} 端口"
echo "      ufw allow ${PORT}/tcp   或   firewall-cmd --add-port=${PORT}/tcp --permanent && firewall-cmd --reload"
