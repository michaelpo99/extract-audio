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

## 3. 直接執行

先給執行權限：

```bash
chmod +x ./bin/extract-audio
```

直接使用：

```bash
./bin/extract-audio
./bin/extract-audio "/mnt/d/Videos/Meeting"
./bin/extract-audio --force "/mnt/d/Videos/Meeting"
```

## 4. 安裝成全域指令

建立個人 `bin` 目錄並複製腳本：

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

## 5. 更新安裝

若腳本有新版本：

```bash
cd ~/extract-audio
cp ./bin/extract-audio ~/bin/extract-audio
chmod +x ~/bin/extract-audio
```

## 6. 驗證

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

## 7. 移除

只移除全域指令：

```bash
rm -f ~/bin/extract-audio
```

移除專案目錄：

```bash
cd ~
rm -rf ~/extract-audio
```
