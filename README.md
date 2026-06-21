# transcribe-audio

`transcribe-audio` 是一支 Bash CLI，用來掃描指定目錄第一層的音檔與影片檔，必要時先從影片抽出第一條音軌，再用 WhisperX 批次轉成逐字稿。

這個 repo 只負責 transcription 階段，不包含獨立的 `extract-audio` 工具。`transcribe-audio` 內部可以保留自己的影片抽音軌前處理邏輯，因為它的需求是服務轉錄 pipeline；獨立抽音軌工具由 `extract-audio` repo 維護。

正式文件集中放在 `docs/`：

- 安裝說明：[docs/INSTALL.md](docs/INSTALL.md)
- 需求規格：[docs/SDD-whisperx-batch-transcribe.md](docs/SDD-whisperx-batch-transcribe.md)
- 拆分與整合前置 CR：[docs/SDD-CR-integrated-pipeline-readiness.md](docs/SDD-CR-integrated-pipeline-readiness.md)
- 實測筆記：[docs/notes/WhisperX 在 WSL2 的安裝與使用筆記.md](<docs/notes/WhisperX 在 WSL2 的安裝與使用筆記.md>)

## 功能

- 掃描指定目錄第一層的音檔與影片檔。
- 音檔可直接納入轉錄。
- 影片會先抽出第一條音軌到同一目錄，再納入轉錄。
- 若影片已有同 stem 的可用音檔，預設沿用既有音檔，不重新抽取。
- 預設語言為 `zh`。
- 預設只輸出 `txt`。
- 預設輸出到目標目錄下的 `transcript/`。
- 支援 `--diarize` 啟用說話者分離。
- 執行前會檢查 WhisperX、Python、Torch、FFmpeg、CUDA 與 Hugging Face 權限。
- 會依硬體自動推估 `model`、`device`、`compute_type`、`batch_size`。
- 會輸出 `_run-summary.txt` 與 `_environment.txt`。

## 專案結構

```text
transcribe-audio/
├── .gitignore
├── README.md
├── bin/
│   └── transcribe-audio
└── docs/
    ├── INSTALL.md
    ├── SDD-whisperx-batch-transcribe.md
    ├── SDD-CR-integrated-pipeline-readiness.md
    └── notes/
        └── WhisperX 在 WSL2 的安裝與使用筆記.md
```

## 快速開始

先安裝系統依賴：

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv
```

準備 WhisperX 環境：

```bash
python3 -m venv "$HOME/.venvs/whisperx"
source "$HOME/.venvs/whisperx/bin/activate"
python -m pip install --upgrade pip setuptools wheel
pip install whisperx
```

直接執行專案內腳本：

```bash
./bin/transcribe-audio
./bin/transcribe-audio --check
./bin/transcribe-audio "/mnt/d/Videos/Meeting"
./bin/transcribe-audio --diarize "/mnt/d/Videos/Meeting"
```

若想安裝成全域指令，請看 [docs/INSTALL.md](docs/INSTALL.md)。

## 用法

```bash
transcribe-audio [目錄]
transcribe-audio --check [目錄]
transcribe-audio --force [目錄]
transcribe-audio --diarize [目錄]
```

### 常用範例

```bash
./bin/transcribe-audio
./bin/transcribe-audio "/mnt/d/Videos/Meeting"
./bin/transcribe-audio --check "/mnt/d/Videos/Meeting"
./bin/transcribe-audio --force "/mnt/d/Videos/Meeting"
./bin/transcribe-audio --diarize --min-speakers 2 --max-speakers 6 "/mnt/d/Videos/Meeting"
```

## 輸出

預設輸出到來源目錄下的 `transcript/`：

```text
Meeting/
├── meeting.mp4
├── meeting.m4a
└── transcript/
    ├── meeting.txt
    ├── _run-summary.txt
    └── _environment.txt
```

## 注意事項

- 目前只掃描指定目錄第一層，不遞迴子目錄。
- 影片只抽第一條音軌。
- 若同名音檔或逐字稿輸出已存在且未指定 `--force`，會盡量沿用或跳過。
- 預設語言是 `zh`；若音訊不是中文，請明確指定 `--language`。
- 使用 `--diarize` 前，需先確認 Hugging Face token 與 pyannote gated model 權限已可用。
- `transcript/` 與本地測試目錄不應提交到 Git。

## 與 extract-audio 的關係

`extract-audio` 是獨立輕量工具，專注影片抽音軌，只需要 FFmpeg/FFprobe。

`transcribe-audio` 是轉錄 pipeline 工具，抽音軌只是轉錄前處理的一部分，因此兩者允許保留不同實作與不同輸出策略。

## 授權

依你的需求自行補上授權條款。
