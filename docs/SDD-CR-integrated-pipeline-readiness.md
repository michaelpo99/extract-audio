# SDD/CR：整合流程前置修正規格

狀態：Pending
日期：2026-06-21
適用 repo：extract-audio

## 目前決策

本 CR 先暫停，不進入實作。

原因是目前重新評估後，`extract-audio` 應維持為輕量、獨立的 media utility；它的責任是從影片抽取音軌，不應被 `transcribe-audio`、WhisperX、Torch、CUDA、LLM polishing 或完整 transcript pipeline 綁住。

下一步方向是：

```text
extract-audio
  - 保留為獨立 repo
  - 聚焦影片抽音軌
  - 依賴維持輕量：ffmpeg / ffprobe

transcribe-audio
  - 從本 repo 拆出到新的 transcribe-audio repo
  - 聚焦 media pool -> raw transcript
  - 可保留自己的抽音軌前處理邏輯，不必與 extract-audio 強制共用

transcript-polish
  - 後續再評估是否與 transcribe-audio 合併為 transcript pipeline
```

## Pending 原因

原 CR 假設 `extract-audio`、`transcribe-audio`、`transcript-polish` 未來可能合併成同一工具集，因此設計了統一的 sidecar layout、metadata contract 與 audio-output policy。

目前此假設已改變。新的架構判斷是：

- `extract-audio` 與 `transcribe-audio` 雖然都有抽音軌邏輯，但它們是不同工具，可依各自需求維護不同策略。
- `extract-audio` 不需要知道 transcript、polish、meta pipeline 的完整契約。
- `transcribe-audio` 才是 transcript pipeline 的 producer，應拆出後在新 repo 重新設計自己的 CR。

因此，這份文件只保留為歷史決策紀錄，不代表目前要實作的規格。

## 後續處理

等 `transcribe-audio` 拆出到新 repo 後，再重新評估：

1. `extract-audio` 是否仍需要新增 `--output-dir`、`--output-mode`、manifest 等功能。
2. `transcribe-audio` 是否要採用 sidecar layout，例如 `Meeting.transcript/` 與 `Meeting.meta/`。
3. `transcribe-audio` 是否要和 `transcript-polish` 合併成更完整的 transcript pipeline。
4. 本文件是否應刪除、改寫成 extract-only CR，或移動到 archive。
