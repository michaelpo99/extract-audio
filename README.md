# extract-audio

從影片檔抽取第一條音軌的 Bash 指令。預設直接複製音訊串流，不重新編碼；只有在直接抽取失敗時，才退回轉成無損 FLAC。

## 功能

- 掃描指定目錄中的常見影片格式，未指定時預設目前目錄
- 每個影片只處理第一條音軌
- 常見音訊格式直接抽出，不重新編碼
- 不常見格式先嘗試放入 `.mka` 容器
- 直接抽取失敗時，才轉成無損 `flac`
- 輸出到目標目錄下的 `audio/`
- 已存在的輸出檔預設跳過，可用 `--force` 覆蓋
- 支援中文、空白與特殊字元檔名

## 專案結構

```text
extract-audio/
├── bin/
│   └── extract-audio
├── INSTALL.md
└── README.md
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
```

若想安裝成全域指令，請看 [INSTALL.md](INSTALL.md)。

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

## 授權

依你的需求自行補上授權條款。
