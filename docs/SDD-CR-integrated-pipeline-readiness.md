# SDD/CR：transcribe-audio 拆分與整合前置規格

狀態：Proposed
日期：2026-06-21
適用 repo：transcribe-audio

## 1. 背景

`transcribe-audio` 已從原本的 `extract-audio` repo 拆出，成為獨立 repo。

拆分後的責任邊界如下：

```text
extract-audio
  - 輕量 media utility
  - 專注影片抽音軌
  - 只需要 FFmpeg / FFprobe

transcribe-audio
  - transcription pipeline producer
  - 掃描音檔與影片檔
  - 必要時自行抽音軌
  - 使用 WhisperX 產生 raw transcript

transcript-polish
  - transcript consumer / polished markdown producer
  - 後續再評估是否與 transcribe-audio 合併
```

## 2. 決策

### 2.1 不強制共用抽音軌邏輯

`extract-audio` 與 `transcribe-audio` 都可能需要抽音軌，但用途不同：

- `extract-audio` 的抽音軌結果是最終輸出。
- `transcribe-audio` 的抽音軌結果是轉錄前處理。

因此兩者可以保留各自實作，不需要為了消除重複而強制抽 shared core。若未來發現維護成本過高，再評估共用 library 或讓 `transcribe-audio` 呼叫 `extract-audio`。

### 2.2 transcribe-audio 仍應維持 media pool 模型

來源目錄可同時放音檔與影片檔：

```text
Meeting/
  a.mp4
  a.m4a
  b.mp4
```

預期：

- `a.mp4` 若已有 `a.m4a`，預設沿用既有音檔。
- `b.mp4` 若沒有同 stem 音檔，才抽音軌。
- 逐字稿輸出到 `Meeting/transcript/`。

### 2.3 sidecar layout 暫不在本次拆分實作

先維持現行輸出：

```text
Meeting/transcript/
```

未來再評估是否改為：

```text
Meeting.transcript/
Meeting.meta/
```

這件事應在 `transcribe-audio` 新 repo 內另開 CR，不再放在 `extract-audio` repo 內處理。

## 3. 本次拆分範圍

### 3.1 transcribe-audio repo 應保留

```text
bin/transcribe-audio
README.md
docs/INSTALL.md
docs/SDD-whisperx-batch-transcribe.md
docs/SDD-CR-integrated-pipeline-readiness.md
docs/notes/WhisperX 在 WSL2 的安裝與使用筆記.md
```

### 3.2 transcribe-audio repo 應移除

```text
bin/extract-audio
```

README 與 INSTALL 不應再宣稱本 repo 提供 `extract-audio`。

## 4. 後續可評估 CR

拆分完成後，可另外評估：

1. 是否新增 `Meeting.transcript/` 與 `Meeting.meta/` sidecar layout。
2. 是否新增 `--transcript-output`、`--meta-output`。
3. 是否將 `transcript-polish` 合併到同一 pipeline repo。
4. 是否新增 `transcribe-and-polish` wrapper。
5. 是否保留或調整內部抽音軌策略。

## 5. 驗收標準

拆分完成後：

- `transcribe-audio` repo 的 README 只描述 `transcribe-audio`。
- `transcribe-audio` repo 的 INSTALL 只安裝 `transcribe-audio`。
- `bin/extract-audio` 不存在於 `transcribe-audio` repo。
- `extract-audio` repo 不再包含 `bin/transcribe-audio`。
- `extract-audio` repo 的 README 與 INSTALL 不再描述 WhisperX 轉錄流程。
