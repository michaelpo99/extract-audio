#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'EOF'
用法：
  bash install.sh
  bash install.sh --bin-dir DIR
  bash install.sh --prefix DIR
  bash install.sh --check
  bash install.sh --uninstall

說明：
  安裝 extract-audio 到使用者可執行目錄。
  預設安裝位置：$HOME/bin/extract-audio

選項：
      --bin-dir DIR    指定安裝目錄，例如：$HOME/.local/bin
      --prefix DIR     安裝到 DIR/bin，例如：--prefix /usr/local
      --check          只檢查目前安裝與依賴狀態
      --uninstall      從安裝目錄移除 extract-audio
  -h, --help           顯示說明
EOF
}

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_file="$script_dir/bin/extract-audio"
bin_dir="${HOME}/bin"
mode="install"

while (($# > 0)); do
    case "$1" in
        --bin-dir)
            if [[ $# -lt 2 ]]; then
                echo "錯誤：--bin-dir 需要目錄參數" >&2
                exit 2
            fi
            bin_dir="$2"
            shift 2
            ;;
        --prefix)
            if [[ $# -lt 2 ]]; then
                echo "錯誤：--prefix 需要目錄參數" >&2
                exit 2
            fi
            bin_dir="$2/bin"
            shift 2
            ;;
        --check)
            mode="check"
            shift
            ;;
        --uninstall)
            mode="uninstall"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "錯誤：未知參數：$1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

target_file="$bin_dir/extract-audio"

check_status() {
    echo "專案目錄：$script_dir"
    echo "來源檔案：$source_file"
    echo "安裝目錄：$bin_dir"
    echo "目標檔案：$target_file"
    echo

    if [[ -x "$target_file" ]]; then
        echo "[OK] 已安裝：$target_file"
    elif [[ -e "$target_file" ]]; then
        echo "[WARN] 已存在但不可執行：$target_file"
    else
        echo "[INFO] 尚未安裝 extract-audio"
    fi

    for command_name in ffmpeg ffprobe; do
        if command -v "$command_name" >/dev/null 2>&1; then
            echo "[OK] 找到 $command_name"
        else
            echo "[WARN] 找不到 $command_name"
        fi
    done

    if [[ ":$PATH:" == *":$bin_dir:"* ]]; then
        echo "[OK] PATH 已包含：$bin_dir"
    else
        echo "[WARN] PATH 尚未包含：$bin_dir"
        echo "      可加入：export PATH=\"$bin_dir:\$PATH\""
    fi
}

if [[ "$mode" == "check" ]]; then
    check_status
    exit 0
fi

if [[ "$mode" == "uninstall" ]]; then
    rm -f -- "$target_file"
    echo "已移除：$target_file"
    exit 0
fi

if [[ ! -f "$source_file" ]]; then
    echo "錯誤：找不到來源檔案：$source_file" >&2
    echo "請在 extract-audio repo 根目錄執行：bash install.sh" >&2
    exit 1
fi

mkdir -p -- "$bin_dir"
cp -- "$source_file" "$target_file"
chmod 755 "$target_file"

echo "已安裝：$target_file"

if [[ ":$PATH:" != *":$bin_dir:"* ]]; then
    echo
    echo "提醒：目前 PATH 尚未包含 $bin_dir"
    echo "可加入 shell 設定檔："
    echo "  export PATH=\"$bin_dir:\$PATH\""
fi

echo
"$target_file" --help >/dev/null 2>&1 || true
echo "完成。可執行：extract-audio --help"
