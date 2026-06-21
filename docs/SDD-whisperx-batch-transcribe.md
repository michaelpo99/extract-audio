# SDD: transcribe-audio 批次轉錄工具

最後更新：2026-06-21
適用 repo：transcribe-audio

## 1. 目標

設計一支 Shell 工具，掃描指定目錄第一層的音檔與影片檔，若遇到影片檔則可先抽出第一條音軌到同一目錄，再使用 WhisperX 批次轉成逐字稿，並將輸出統一放到目標目錄下的 `transcript/` 目錄。

這支工具的定位是 media pool 到 raw transcript 的 producer：

1. 盡量零設定即可使用。
2. 執行前先做環境檢查，避免跑到一半才失敗。
3. 可用參數決定是否開啟講者分離。
4. 根據硬體條件自動選擇合理的模型與效能參數。
5. 可直接處理音檔；遇到影片時可自行完成轉錄前所需的抽音軌前處理。

指令名稱：

```text
transcribe-audio
```

## 2. 使用情境

### 2.1 主要情境

使用者在某個資料夾中已有音檔或影片檔，例如：

```text
Meeting/
  meeting-01.m4a
  meeting-02.mp4
  meeting-03.wav
```

執行：

```bash
transcribe-audio ./Meeting
```

工具自動：

1. 掃描 `Meeting/` 第一層音檔與影片檔。
2. 檢查 WhisperX / Python / FFmpeg / GPU / Hugging Face 權限是否可用。
3. 若遇到影片檔，先尋找同 stem 的既有音檔；若沒有可用音檔，才抽出第一條音軌。
4. 根據硬體自動決定 `model`、`device`、`compute_type`、`batch_size`。
5. 逐一轉錄音檔。
6. 輸出到 `Meeting/transcript/`。

### 2.2 講者分離情境

```bash
transcribe-audio ./Meeting --diarize
```

工具需額外：

1. 檢查 `HF_TOKEN` 是否存在，或 Hugging Face CLI 是否已登入。
2. 檢查 pyannote gated model 是否可存取。
3. 若授權未完成，應在正式轉錄前中止並顯示清楚原因。

### 2.3 覆蓋重跑情境

```bash
transcribe-audio ./Meeting --force
```

若已有同名抽出音檔或逐字稿輸出，允許覆蓋。

## 3. 輸入範圍

### 3.1 支援音檔

```text
.m4a
.mp3
.wav
.flac
.aac
.ogg
.opus
.wma
.mka
.ac3
.eac3
```

### 3.2 支援影片檔

```text
.mp4
.m4v
.mkv
.mov
.avi
.webm
.wmv
.flv
.ts
.mts
.m2ts
.mpg
.mpeg
.3gp
.ogv
.vob
.mxf
```

### 3.3 掃描規則

- 只掃描目標目錄第一層。
- 不遞迴子目錄。
- 音檔與影片檔可放在同一個來源目錄。
- 同 stem 音檔已存在時，影片預設沿用該音檔，不重新抽取。

## 4. 輸出

預設輸出：

```text
Meeting/
  meeting-01.m4a
  meeting-02.mp4
  meeting-02.m4a
  transcript/
    meeting-01.txt
    meeting-02.txt
    _run-summary.txt
    _environment.txt
```

說明：

- 抽出的音檔目前放回來源目錄同一層。
- 逐字稿輸出到 `transcript/`。
- `_run-summary.txt` 記錄本次處理摘要。
- `_environment.txt` 記錄環境資訊。

## 5. CLI

```text
transcribe-audio [目錄]
transcribe-audio --check [目錄]
transcribe-audio --force [目錄]
transcribe-audio --diarize [目錄]
```

主要選項：

```text
-d, --diarize                 啟用說話者分離
-f, --force                   覆蓋既有音檔與逐字稿輸出
    --check                   只檢查環境與推估參數，不執行轉錄
    --model NAME              指定模型，例如 small、medium、large-v3
    --device auto|cuda|cpu    指定裝置，預設 auto
    --batch-size N            指定 batch size
    --compute-type TYPE       指定 compute type：default|float16|float32|int8
    --language CODE           指定語言，預設 zh
    --output-format FORMAT    指定輸出格式，預設 txt
    --min-speakers N          diarize 時設定最小講者數
    --max-speakers N          diarize 時設定最大講者數
    --verbose                 顯示詳細資訊
-h, --help                    顯示說明
```

## 6. 與 extract-audio 的邊界

`extract-audio` 是獨立輕量工具，專注影片抽音軌，不需要 WhisperX、Torch、CUDA 或其他轉錄環境。

`transcribe-audio` 是轉錄工具。它內部可以保留抽音軌邏輯，因為這是轉錄前處理的一部分；該邏輯不必與 `extract-audio` 強制共用，也允許因不同需求產生不同策略。

## 7. 非目標

本工具不負責：

- 產生潤稿後 Markdown。
- 摘要、會議紀錄、待辦事項整理。
- 取代獨立的 `extract-audio` 工具。
- 深層遞迴掃描整個目錄樹。

潤稿或格式整理應由 `transcript-polish` 或未來 pipeline 工具負責。

## 8. 驗收標準

1. `transcribe-audio --check` 可只檢查環境，不產生輸出。
2. `transcribe-audio ./Meeting` 可處理第一層音檔。
3. 遇到影片檔時，若同 stem 音檔已存在，預設沿用既有音檔。
4. 遇到影片檔且無同 stem 音檔時，可抽出第一條音軌後轉錄。
5. 成功轉錄後，逐字稿出現在 `Meeting/transcript/`。
6. 執行結束後產生 `_run-summary.txt` 與 `_environment.txt`。
7. 指定 `--diarize` 時，會先檢查 Hugging Face / pyannote 權限。
