# 安裝程序

這個專案提供一支 Bash 指令：

```text
extract-audio
```

用途是掃描指定目錄中的影片檔，抽取第一條音軌，並輸出到目標目錄下的 `audio/` 子目錄。

## 1. 安裝系統依賴

在 Ubuntu / WSL：

```bash
sudo apt update
sudo apt install -y ffmpeg
```

確認 FFmpeg 與 FFprobe 可用：

```bash
ffmpeg -version
ffprobe -version
```

本工具不需要 Python、WhisperX、Torch、CUDA 或 Hugging Face 權限。

## 2. 取得專案

```bash
git clone https://github.com/michaelpo99/extract-audio.git
cd extract-audio
```

若你是本機手動建立或測試，也可以直接進入專案目錄：

```bash
cd ~/extract-audio
```

## 3. 使用 install.sh 安裝 CLI

預設安裝到：

```text
~/bin/extract-audio
```

執行：

```bash
bash install.sh
```

檢查安裝與依賴：

```bash
bash install.sh --check
```

指定安裝目錄：

```bash
bash install.sh --bin-dir "$HOME/.local/bin"
```

指定 prefix，會安裝到 `PREFIX/bin`：

```bash
sudo bash install.sh --prefix /usr/local
```

移除全域指令：

```bash
bash install.sh --uninstall
```

`install.sh` 不會自動修改 shell 設定檔。若安裝目錄不在 PATH，腳本會提示應加入的 `export PATH=...`。

## 4. 直接執行

不安裝也可以直接執行 repo 內腳本：

```bash
./bin/extract-audio
./bin/extract-audio "/mnt/d/Videos/Meeting"
./bin/extract-audio --force "/mnt/d/Videos/Meeting"
```

## 5. 手動安裝成全域指令

若不使用 `install.sh`，也可以手動複製：

```bash
mkdir -p ~/bin
cp ./bin/extract-audio ~/bin/extract-audio
chmod +x ~/bin/extract-audio
```

把 `~/bin` 加入 PATH：

```bash
grep -qxF 'export PATH="$HOME/bin:$PATH"' ~/.bashrc || \
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
```

重新載入 shell：

```bash
source ~/.bashrc
```

確認安裝：

```bash
which extract-audio
extract-audio --help
```

## 6. 更新安裝

若腳本有新版本：

```bash
git pull
bash install.sh
```

## 7. 驗證

最小驗證：

```bash
extract-audio --help
```

實際驗證可準備一個包含影片檔的目錄：

```bash
extract-audio "/mnt/d/Videos/Meeting"
```

預期會在目標目錄下產生：

```text
Meeting/audio/
```

## 8. 移除

只移除全域指令：

```bash
bash install.sh --uninstall
```

移除專案目錄：

```bash
cd ~
rm -rf ~/extract-audio
```
