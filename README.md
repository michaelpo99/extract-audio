# extract-audio

`extract-audio` 是一支輕量 Bash CLI，用來掃描指定目錄第一層的常見影片檔，抽取第一條音軌，並輸出到目標目錄下的 `audio/` 子目錄。

這個 repo 只負責影片抽音軌，不包含 WhisperX 轉錄流程。批次轉錄工具已拆到獨立 repo：`transcribe-audio`。

正式文件集中放在 `docs/`：

- 安裝說明：[docs/INSTALL.md](docs/INSTALL.md)
- 整合流程舊 CR / pending 紀錄：[docs/SDD-CR-integrated-pipeline-readiness.md](docs/SDD-CR-integrated-pipeline-readiness.md)

## 功能

- 掃描指定目錄中的常見影片格式，未指定時預設目前目錄。
- 每個影片只處理第一條音軌。
- 常見音訊格式直接抽出，不重新編碼。
- 不常見格式先嘗試放入 `.mka` 容器。
- 直接抽取失敗時，才轉成無損 `flac`。
- 輸出到目標目錄下的 `audio/`。
- 已存在的輸出檔預設跳過，可用 `--force` 覆蓋。
- 支援中文、空白與特殊字元檔名。

## 專案結構

```text
extract-audio/
├── .gitignore
├── README.md
├── bin/
│   └── extract-audio
└── docs/
    ├── INSTALL.md
    └── SDD-CR-integrated-pipeline-readiness.md
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
./bin/extract-audio --force "/mnt/d/Videos/Meeting"
```

若想安裝成全域指令，請看 [docs/INSTALL.md](docs/INSTALL.md)。

## 用法

```bash
extract-audio [目錄]
extract-audio --force [目錄]
```

### 範例

```bash
./bin/extract-audio
./bin/extract-audio "/mnt/d/Videos/Meeting"
./bin/extract-audio --force "/mnt/d/Videos/Meeting"
```

## 輸出

假設來源目錄為：

```text
Meeting/
  a.mp4
  b.mkv
```

執行：

```bash
extract-audio ./Meeting
```

輸出：

```text
Meeting/
  a.mp4
  b.mkv
  audio/
    a.m4a
    b.flac
```

實際副檔名會依來源音訊 codec 決定。若無法直接抽取，會 fallback 成 FLAC。

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

- 目前只抽第一條音軌。
- 只掃描指定目錄第一層，不遞迴子目錄。
- 若輸出已存在且未指定 `--force`，會直接跳過。
- 本工具不需要 WhisperX、Torch、CUDA 或 Hugging Face 權限。
- 若要把音檔或影片轉成逐字稿，請使用獨立 repo `transcribe-audio`。

## 授權

依你的需求自行補上授權條款。
