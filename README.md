# extract-audio

這個 repo 目前提供兩支 Bash 指令：

1. `extract-audio`：從影片檔抽取第一條音軌。
2. `transcribe-audio`：掃描目錄中的音檔與影片檔，必要時先抽音軌，再用 WhisperX 批次轉成文字。

正式文件集中放在 `docs/`：

- 安裝說明：[docs/INSTALL.md](docs/INSTALL.md)
- 需求規格：[docs/SDD-whisperx-batch-transcribe.md](docs/SDD-whisperx-batch-transcribe.md)
- 實測筆記：[docs/notes/WhisperX 在 WSL2 的安裝與使用筆記.md](<docs/notes/WhisperX 在 WSL2 的安裝與使用筆記.md>)

## 功能

### `extract-audio`

- 掃描指定目錄中的常見影片格式，未指定時預設目前目錄
- 每個影片只處理第一條音軌
- 常見音訊格式直接抽出，不重新編碼
- 不常見格式先嘗試放入 `.mka` 容器
- 直接抽取失敗時，才轉成無損 `flac`
- 輸出到目標目錄下的 `audio/`
- 已存在的輸出檔預設跳過，可用 `--force` 覆蓋
- 支援中文、空白與特殊字元檔名

### `transcribe-audio`

- 掃描指定目錄第一層的音檔與影片檔
- 影片會先抽出第一條音軌到同一目錄，再納入轉錄
- 預設語言為 `zh`
- 預設只輸出 `txt`
- 預設輸出到目標目錄下的 `transcript/`
- 支援 `--diarize` 啟用說話者分離
- 執行前會檢查 WhisperX、Python、Torch、FFmpeg、CUDA 與 Hugging Face 權限
- 會依硬體自動推估 `model`、`device`、`compute_type`、`batch_size`
- 會輸出 `_run-summary.txt` 與 `_environment.txt`

## 專案結構

```text
extract-audio/
├── .gitignore
├── README.md
├── bin/
│   ├── extract-audio
│   └── transcribe-audio
└── docs/
    ├── INSTALL.md
    ├── SDD-whisperx-batch-transcribe.md
    └── notes/
        └── WhisperX 在 WSL2 的安裝與使用筆記.md
```

## 快速開始

先安裝 FFmpeg：

```bash
sudo apt update
sudo apt install -y ffmpeg
```

直接執行專案內腳本：

```bash
./bin/extract-audio
./bin/extract-audio "/mnt/d/Videos/Meeting"
./bin/extract-audio --force
./bin/transcribe-audio
./bin/transcribe-audio --check
./bin/transcribe-audio --diarize
```

若想安裝成全域指令，請看 [docs/INSTALL.md](docs/INSTALL.md)。

## 用法

```bash
extract-audio [目錄]
extract-audio --force [目錄]
transcribe-audio [目錄]
transcribe-audio --check [目錄]
transcribe-audio --diarize [目錄]
```

### 範例

```bash
./bin/extract-audio
./bin/extract-audio "/mnt/d/Videos/Meeting"
./bin/extract-audio --force "/mnt/d/Videos/Meeting"
./bin/transcribe-audio
./bin/transcribe-audio "/mnt/d/Videos/Meeting"
./bin/transcribe-audio --check "/mnt/d/Videos/Meeting"
./bin/transcribe-audio --diarize "/mnt/d/Videos/Meeting"
```

## 輸出格式邏輯

| 原音訊 codec | 直接輸出 |
| --- | --- |
| AAC | M4A |
| ALAC | M4A |
| MP3 | MP3 |
| FLAC | FLAC |
| Opus | OPUS |
| Vorbis | OGG |
| AC-3 | AC3 |
| E-AC-3 | EAC3 |
| PCM | WAV |
| 其他格式 | MKA |
| 無法直接抽取 | FLAC |

## 注意事項

- 目前只抽第一條音軌
- 只掃描指定目錄第一層，不遞迴子目錄
- 若輸出已存在且未指定 `--force`，會直接跳過
- `transcribe-audio` 的預設語言是 `zh`，若音訊不是中文，請明確指定 `--language`
- 使用 `--diarize` 前，需先確認 Hugging Face token 與 pyannote gated model 權限已可用
- `transcript/` 與本地測試目錄不應提交到 Git

## 授權

依你的需求自行補上授權條款。
