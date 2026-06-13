# 安裝程序

這個專案目前提供兩支 Bash 指令：

1. `extract-audio`：從影片抽取第一條音軌。
2. `transcribe-audio`：掃描目錄中的音檔與影片檔，必要時先抽音軌，再用 WhisperX 批次轉文字。

你可以直接在專案目錄內執行，也可以安裝成全域指令。

## 1. 安裝系統依賴

在 Ubuntu / WSL：

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv
```

確認：

```bash
ffmpeg -version
ffprobe -version
```

`extract-audio` 只需要 FFmpeg。

`transcribe-audio` 除了 FFmpeg 之外，還需要可用的 WhisperX Python 環境。

## 2. 取得專案

如果你是本機建立：

```bash
cd ~/extract-audio
```

如果之後放到 Git 遠端，可用：

```bash
git clone <your-repo-url>
cd extract-audio
```

## 3. 準備 WhisperX 環境

如果你只要用 `extract-audio`，這一節可以跳過。

若要使用 `transcribe-audio`，請先準備 WhisperX：

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

1. Hugging Face 帳號
2. 可讀取 `pyannote/speaker-diarization-community-1` 的權限
3. 可用的 `HF_TOKEN`

## 4. 直接執行

先給執行權限：

```bash
chmod +x ./bin/extract-audio
chmod +x ./bin/transcribe-audio
```

直接使用：

```bash
./bin/extract-audio
./bin/extract-audio "/mnt/d/Videos/Meeting"
./bin/extract-audio --force
./bin/transcribe-audio
./bin/transcribe-audio --check
./bin/transcribe-audio "/mnt/d/Videos/Meeting"
./bin/transcribe-audio --diarize "/mnt/d/Videos/Meeting"
```

## 5. 安裝成全域指令

建立個人 `bin` 目錄並複製腳本：

```bash
mkdir -p ~/bin
cp ./bin/extract-audio ~/bin/extract-audio
cp ./bin/transcribe-audio ~/bin/transcribe-audio
chmod +x ~/bin/extract-audio
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
which extract-audio
which transcribe-audio
extract-audio --help
transcribe-audio --help
```

## 6. 更新安裝

若腳本有新版本：

```bash
cd ~/extract-audio
cp ./bin/extract-audio ~/bin/extract-audio
cp ./bin/transcribe-audio ~/bin/transcribe-audio
chmod +x ~/bin/extract-audio
chmod +x ~/bin/transcribe-audio
```

若 WhisperX 環境也有更新需求，可另外更新：

```bash
source "$HOME/.venvs/whisperx/bin/activate"
pip install --upgrade whisperx
```

## 7. 驗證

最小驗證：

```bash
extract-audio --help
transcribe-audio --help
transcribe-audio --check
```

若要驗證 diarization：

```bash
export HF_TOKEN="你的 token"
transcribe-audio --check --diarize
```

## 8. 移除

如果只移除全域指令：

```bash
rm -f ~/bin/extract-audio
rm -f ~/bin/transcribe-audio
```

如果也要移除 WhisperX 虛擬環境：

```bash
rm -rf "$HOME/.venvs/whisperx"
```

如果也要刪掉專案目錄：

```bash
cd ~
rm -rf ~/extract-audio
```
