#!/usr/bin/env bash
# 把可视化页面打包成单个二进制文件
#
#   ./build.sh          本机打包（macOS 打出来的只能在 macOS 跑，Linux 同理）
#   ./build.sh docker   用 Docker 打出 Linux x86_64 产物（推荐：部署到云服务器时用它）
#
# 产物：dist/mimotion-web
set -euo pipefail
cd "$(dirname "$0")"

NAME="mimotion-web"
ENTRY="web_app.py"

# Windows 的 --add-data 分隔符是 ; 其它平台是 :
SEP=":"
case "$(uname -s)" in
MINGW* | MSYS* | CYGWIN*) SEP=";" ;;
esac

build() {
    pyinstaller --noconfirm --clean --onefile --name "$NAME" \
        --add-data "templates${SEP}templates" \
        --collect-all flask \
        --collect-all waitress \
        --collect-all Crypto \
        --collect-all requests \
        --collect-all pytz \
        --collect-all dotenv \
        --hidden-import util.aes_help \
        --hidden-import util.zepp_helper \
        --hidden-import util.push_util \
        --hidden-import main \
        --exclude-module tkinter \
        "$ENTRY"
}

if [[ "${1:-local}" == "docker" ]]; then
    echo "==> 使用 Docker 构建 Linux 二进制"
    docker build -f Dockerfile.build -t mimotion-build .
    docker run --rm -v "$PWD/dist:/src/dist" mimotion-build
else
    if python3 -c "import PyInstaller" >/dev/null 2>&1; then
        echo "==> 使用当前环境的 PyInstaller"
    else
        echo "==> 创建打包虚拟环境 .build-venv"
        [[ -d .build-venv ]] || python3 -m venv .build-venv
        # shellcheck disable=SC1091
        source .build-venv/bin/activate
        pip install -q -U pip
        pip install -q -r requirements.txt -r requirements-build.txt
    fi
    build
fi

echo "==> 完成，产物：$(pwd)/dist/${NAME}"
