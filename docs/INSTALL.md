# 安裝程序

這個專案提供一支 Bash 指令：

```text
transcribe-audio
```

用途是掃描目錄中的音檔與影片檔，必要時先抽音軌，再用 WhisperX 批次轉文字。

## 1. 安裝系統依賴

在 Ubuntu / WSL：

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv
```

確認 FFmpeg 與 FFprobe 可用：

```bash
ffmpeg -version
ffprobe -version
```

## 2. 取得專案

```bash
git clone https://github.com/michaelpo99/transcribe-audio.git
cd transcribe-audio
```

若你是本機手動建立或測試，也可以直接進入專案目錄：

```bash
cd ~/transcribe-audio
```

## 3. 準備 WhisperX 環境

```bash
python3 -m venv "$HOME/.venvs/whisperx"
source "$HOME/.venvs/whisperx/bin/activate"
python -m pip install --upgrade pip setuptools wheel
pip install whisperx
```

確認：

```bash
"$HOME/.venvs/whisperx/bin/whisperx" --help
"$HOME/.venvs/whisperx/bin/python" -c "import torch; print(torch.cuda.is_available())"
```

若要使用 `--diarize`，還需要：

1. Hugging Face 帳號。
2. 可讀取 `pyannote/speaker-diarization-community-1` 的權限。
3. 可用的 `HF_TOKEN`，或已登入 Hugging Face CLI。

## 4. 直接執行

先給執行權限：

```bash
chmod +x ./bin/transcribe-audio
```

直接使用：

```bash
./bin/transcribe-audio
./bin/transcribe-audio --check
./bin/transcribe-audio "/mnt/d/Videos/Meeting"
./bin/transcribe-audio --diarize "/mnt/d/Videos/Meeting"
```

## 5. 安裝成全域指令

建立個人 `bin` 目錄並複製腳本：

```bash
mkdir -p ~/bin
cp ./bin/transcribe-audio ~/bin/transcribe-audio
chmod +x ~/bin/transcribe-audio
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
which transcribe-audio
transcribe-audio --help
transcribe-audio --check
```

## 6. 更新安裝

若腳本有新版本：

```bash
cd ~/transcribe-audio
cp ./bin/transcribe-audio ~/bin/transcribe-audio
chmod +x ~/bin/transcribe-audio
```

若 WhisperX 環境也有更新需求：

```bash
source "$HOME/.venvs/whisperx/bin/activate"
pip install --upgrade whisperx
```

## 7. 驗證

最小驗證：

```bash
transcribe-audio --help
transcribe-audio --check
```

若要驗證 diarization：

```bash
export HF_TOKEN="你的 token"
transcribe-audio --check --diarize
```

## 8. 移除

只移除全域指令：

```bash
rm -f ~/bin/transcribe-audio
```

移除 WhisperX 虛擬環境：

```bash
rm -rf "$HOME/.venvs/whisperx"
```

移除專案目錄：

```bash
cd ~
rm -rf ~/transcribe-audio
```
