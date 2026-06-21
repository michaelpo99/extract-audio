# SDD/CR：整合流程前置修正規格

狀態：Proposed
日期：2026-06-21
適用 repo：extract-audio

## 1. 背景與目的

本專案目前提供 `extract-audio` 與 `transcribe-audio` 兩個工具。`transcribe-audio` 已經不只是單純轉錄工具，它會掃描媒體目錄中的音檔與影片檔，必要時先從影片抽出第一條音軌，再呼叫 WhisperX 產生逐字稿。

未來若要把 `extract-audio`、`transcribe-audio`、`transcript-polish` 合併成同一工具集，合併前必須先讓目前兩個 repo 具備一致的目錄契約、輸出契約與 metadata 邊界。此 CR 的目標不是立即合併 repo，也不是立即改寫成 Python monorepo，而是先把 `extract-audio` repo 修正成可被後續整合流程穩定呼叫的 producer。

核心方向：

- 來源目錄視為 media pool，可同時放影片與音檔。
- 不預設建立 `Meeting.audio/`，避免原本就是音檔的情境發生不必要複製。
- 同名音檔已存在時，影片轉錄應沿用既有音檔，不重新抽音軌。
- 逐字稿與 metadata 應能輸出到來源目錄外側的 sibling sidecar 目錄。
- metadata 不應混入後續 `transcript-polish` 會掃描的逐字稿目錄。

## 2. 現況問題

### 2.1 `extract-audio` 與 `transcribe-audio` 的 audio 輸出策略不一致

`extract-audio` 目前固定輸出到來源目錄下的 `audio/` 子目錄；`transcribe-audio` 遇到影片時，則把抽出的音檔放回來源目錄同一層。這兩種策略各有合理性，但在同一 repo 裡同時存在，會讓未來 pipeline 很難形成一致契約。

本 CR 不要求移除 `extract-audio` 的 `audio/` 行為，但要求 `transcribe-audio` 明確定義自己的 audio policy，並提供參數控制。

### 2.2 逐字稿輸出固定在來源目錄下的 `transcript/`

目前 `transcribe-audio ./Meeting` 會產生：

```text
Meeting/
  transcript/
    xxx.txt
    _run-summary.txt
    _environment.txt
```

如果後續再執行 `transcript-polish --dir ./Meeting/transcript`，預設又會產生：

```text
Meeting/
  transcript/
    formatted/
      xxx.md
```

這造成目錄階層過深，且 metadata 與正文輸出混在同一層。

### 2.3 統計與環境資訊會進入後續文字處理目錄

`transcribe-audio` 目前把 `_run-summary.txt`、`_environment.txt`、`_failed-files.txt` 放在逐字稿輸出目錄。即使下游工具排除了部分檔案，這仍然是脆弱契約；producer 應盡量不要把非正文檔案放入 consumer 的輸入集合。

## 3. 目標行為

### 3.1 預設 media pool 模型

來源目錄維持作為 media pool：

```text
Meeting/
  a.mp4
  a.m4a
  b.mp4
```

處理規則：

- `a.mp4` 若已有同 stem 的 `a.m4a`、`a.mp3`、`a.wav`、`a.flac` 等可用音檔，預設沿用該音檔，不重新抽取。
- `b.mp4` 若沒有同 stem 可用音檔，才從影片抽出第一條音軌。
- 預設抽出的音檔放回來源目錄同一層，例如 `Meeting/b.flac`。
- 不預設產生 `Meeting.audio/`。

目標輸出：

```text
Meeting/
  a.mp4
  a.m4a
  b.mp4
  b.flac

Meeting.transcript/
  a.txt
  b.txt

Meeting.meta/
  transcribe-run-summary.txt
  transcribe-environment.txt
  transcribe-failed-files.txt
  extracted-audio.tsv
```

### 3.2 sidecar layout 預設

`transcribe-audio ./Meeting` 在新規格下預設應等價於：

```bash
transcribe-audio ./Meeting \
  --layout sidecar \
  --audio-output same-dir \
  --transcript-output ../Meeting.transcript \
  --meta-output ../Meeting.meta
```

其中 `../Meeting.transcript` 與 `../Meeting.meta` 是相對於來源目錄 `Meeting/` 的 parent directory 推導出的 sibling 目錄，不是相對於 shell current working directory。

若來源目錄為絕對路徑 `/mnt/d/Videos/Meeting`，則預設輸出為：

```text
/mnt/d/Videos/Meeting.transcript/
/mnt/d/Videos/Meeting.meta/
```

### 3.3 legacy layout 保留

為降低破壞性，必須保留舊行為：

```bash
transcribe-audio ./Meeting --layout legacy
```

legacy layout：

```text
Meeting/
  transcript/
    xxx.txt
    _run-summary.txt
    _environment.txt
    _failed-files.txt
```

若實作時擔心直接改預設造成使用者不適，可分兩階段：

1. 第一階段新增 `--layout sidecar`，但仍維持 `legacy` 預設，執行時提示未來預設將改為 sidecar。
2. 第二階段將預設改為 `sidecar`，保留 `--layout legacy`。

本 CR 的目標狀態是 `sidecar` 成為預設。

## 4. CLI 變更規格

### 4.1 `transcribe-audio` 新增參數

```text
--layout legacy|sidecar
```

控制預設輸出位置組合。目標預設值為 `sidecar`。

```text
--audio-output same-dir|sidecar|cache|none
```

控制影片抽音軌的輸出策略。

- `same-dir`：預設。抽出的音檔放回來源目錄，並可被後續執行重用。
- `sidecar`：抽出的音檔放到 sibling `SOURCE.audio/`。此模式僅供需要隔離衍生音檔時使用，不應作為預設。
- `cache`：抽出的音檔放到 metadata 或 cache 目錄下，例如 `SOURCE.meta/audio/`。此模式適合臨時處理，不保證使用者直接管理。
- `none`：不從影片抽音軌，只處理來源目錄中既有音檔。若遇到沒有同名音檔的影片，應記錄 skipped 或 failed reason。

```text
--transcript-output PATH
```

明確指定逐字稿輸出目錄。若未指定且 layout 為 sidecar，預設為 `SOURCE_PARENT/SOURCE_BASENAME.transcript`。

```text
--meta-output PATH
```

明確指定 metadata 輸出目錄。若未指定且 layout 為 sidecar，預設為 `SOURCE_PARENT/SOURCE_BASENAME.meta`。

```text
--no-meta
```

選擇性參數。停用 metadata 檔案輸出；不建議在整合流程使用。

### 4.2 `extract-audio` 新增參數，作為一致性補強

`extract-audio` 可保留原本 `audio/` 預設，但應新增明確輸出參數，避免它與 `transcribe-audio` 的策略永久分歧：

```text
--output-dir PATH
--output-mode child|same-dir|sidecar
```

建議語意：

- `child`：現行行為，輸出到 `SOURCE/audio/`。
- `same-dir`：輸出到來源目錄同一層。
- `sidecar`：輸出到 `SOURCE_PARENT/SOURCE_BASENAME.audio/`。
- `--output-dir` 指定時，優先於 `--output-mode`。

此變更不是整合流程的必要條件，但可降低兩支工具的長期歧異。

## 5. 路徑推導規則

### 5.1 source basename

來源目錄必須先 resolve 為絕對路徑，再取 basename：

```text
source_dir=/mnt/d/Videos/Meeting
source_parent=/mnt/d/Videos
source_basename=Meeting
```

sidecar 預設：

```text
transcript_dir=/mnt/d/Videos/Meeting.transcript
meta_dir=/mnt/d/Videos/Meeting.meta
```

### 5.2 特殊路徑處理

- 若來源目錄為 filesystem root，不得自動推導 sidecar；必須要求使用者明確指定 `--transcript-output` 與 `--meta-output`。
- 若 sidecar 目錄與來源目錄相同，應報錯。
- 若 `--transcript-output` 與 `--meta-output` 相同，應報錯，避免正文與 metadata 混雜。
- 若 `--audio-output sidecar` 推導出的 `SOURCE.audio/` 與來源目錄相同，應報錯。

## 6. Metadata 規格

### 6.1 sidecar layout 下的 metadata 檔名

sidecar layout 不應使用 `_run-summary.txt` 這類適合混在輸出目錄內的命名。建議改為有工具前綴的檔名：

```text
transcribe-run-summary.txt
transcribe-environment.txt
transcribe-failed-files.txt
extracted-audio.tsv
```

### 6.2 extracted-audio.tsv

當 `transcribe-audio` 從影片抽出音檔時，必須記錄 manifest：

```text
video_file	audio_file	codec	status	reason
b.mp4	b.flac	flac	extracted	
c.mp4	c.m4a	aac	reused_existing_audio	
```

欄位說明：

- `video_file`：來源影片檔，相對於 source dir。
- `audio_file`：使用的音檔，相對於 source dir 或明確標示外部路徑。
- `codec`：偵測到的音訊 codec。
- `status`：`extracted`、`reused_existing_audio`、`no_audio_stream`、`extract_failed`、`skipped_by_audio_output_none`。
- `reason`：失敗或跳過原因，成功時可空白。

此 manifest 的目的不是讓下游工具處理，而是讓使用者清楚知道哪些音檔是工具產生的，日後可安全清理。

## 7. 與 transcript-polish 的整合契約

`transcribe-audio` 在 sidecar layout 下必須保證：

- `TRANSCRIPT_DIR` 只放可被下游文字工具處理的逐字稿正文檔，預設為 `.txt`。
- metadata 檔案不得放入 `TRANSCRIPT_DIR`。
- 若必須因相容性保留 `_*.txt`，只能在 legacy layout 使用。
- 完成時應在 stdout 輸出 machine-readable 或易解析的目錄資訊。

建議 stdout 末尾加入：

```text
[result] transcript_dir=/mnt/d/Videos/Meeting.transcript
[result] meta_dir=/mnt/d/Videos/Meeting.meta
[result] audio_policy=same-dir
```

未來整合 wrapper 可讀取這些資訊，再呼叫：

```bash
transcript-polish --dir /mnt/d/Videos/Meeting.transcript \
  --output-dir /mnt/d/Videos/Meeting.polished \
  --meta-output /mnt/d/Videos/Meeting.meta
```

## 8. 錯誤處理與 exit code

現有 exit code 可保留，但 sidecar layout 應明確區分：

- 0：全部成功，或全部已存在而跳過。
- 1：環境、參數、目錄或 dependency 錯誤。
- 2：CLI 用法錯誤。
- 3：部分媒體轉錄失敗。

若 `--audio-output none` 導致影片無法處理，應視為 skipped 或 failed 取決於是否有可轉錄音檔：

- 若來源目錄有其他音檔成功轉錄，可回傳 3 並記錄 failed/skipped reason。
- 若完全沒有可處理檔案，可回傳 0 或 1 需由實作決定，但必須在文件中固定。

建議：完全沒有可處理檔案回傳 0，因為它不是執行錯誤；但若指定的來源明顯有影片卻因 `--audio-output none` 全部跳過，應在 summary 中明確顯示。

## 9. 測試案例

### 9.1 同名音檔已存在

輸入：

```text
Meeting/
  a.mp4
  a.m4a
```

執行：

```bash
transcribe-audio ./Meeting --layout sidecar
```

預期：

- 不重新抽出 `a.*`。
- 使用 `a.m4a` 轉錄。
- 產生 `Meeting.transcript/a.txt`。
- `Meeting.meta/extracted-audio.tsv` 記錄 `reused_existing_audio`。

### 9.2 影片無同名音檔

輸入：

```text
Meeting/
  b.mp4
```

預期：

- 抽出 `Meeting/b.<ext>`。
- 產生 `Meeting.transcript/b.txt`。
- metadata 放在 `Meeting.meta/`。
- `Meeting.transcript/` 內不得有 `_run-summary.txt`、`_environment.txt`、`_failed-files.txt`。

### 9.3 legacy layout

執行：

```bash
transcribe-audio ./Meeting --layout legacy
```

預期：

- 保留舊輸出 `Meeting/transcript/`。
- 舊 metadata 命名可暫時保留。
- 下游工具仍應有自己的 `_*.txt` 排除保護。

### 9.4 明確指定輸出目錄

執行：

```bash
transcribe-audio ./Meeting \
  --transcript-output /tmp/out/transcript \
  --meta-output /tmp/out/meta
```

預期：

- 不受 `--layout` 預設推導影響。
- 指定目錄不存在時自動建立。
- 指定目錄等於來源目錄時報錯。

## 10. 實作順序建議

1. 抽出 path resolution 函式，集中處理 `source_parent`、`source_basename`、sidecar 目錄推導。
2. 新增 `--layout`、`--transcript-output`、`--meta-output`，先不改 audio 行為。
3. 將 sidecar layout 下的 summary/environment/failed files 移到 meta dir。
4. 新增 `extracted-audio.tsv`。
5. 新增 `--audio-output`。
6. 補 README 與 INSTALL 文件範例。
7. 視相容性策略決定是否立即把 sidecar 設為預設。

## 11. 驗收標準

本 CR 完成後，以下指令應可作為合併前的穩定 producer contract：

```bash
transcribe-audio ./Meeting
```

目標預設輸出：

```text
Meeting/
Meeting.transcript/
Meeting.meta/
```

並且：

- `Meeting.transcript/` 僅包含可供文字整理的逐字稿正文。
- `Meeting.meta/` 包含轉錄摘要、環境資訊、失敗清單與抽音軌 manifest。
- 來源目錄中的同名音檔會被重用，不會無條件複製到 `Meeting.audio/`。
- 使用者仍可透過 `--layout legacy` 回到舊版輸出結構。
