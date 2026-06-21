# SDD/CR：整合流程前置修正規格

狀態：Proposed
日期：2026-06-21
適用 repo：extract-audio

## 1. 背景與目的

本 repo 目前提供 `extract-audio` 與 `transcribe-audio`。其中 `transcribe-audio` 已經是前段 pipeline 工具：它會掃描來源目錄第一層的音檔與影片檔，遇到影片時可先抽出第一條音軌，再呼叫 WhisperX 產生逐字稿。

未來若要把 `extract-audio`、`transcribe-audio`、`transcript-polish` 合併成同一工具集，合併前應先讓本 repo 成為穩定的 media/transcript producer。此 CR 不要求立即合併 repo，也不要求立即改寫成 Python monorepo；目標是先建立一致的目錄契約、輸出契約與 metadata 邊界。

核心原則：

- 來源目錄視為 media pool，可同時放影片與音檔。
- 不預設建立 `Meeting.audio/`，避免原本就是音檔的案例發生不必要複製。
- 若影片已有同 stem 可用音檔，`transcribe-audio` 應沿用該音檔，不重新抽取。
- 逐字稿與 metadata 應可輸出到來源目錄旁的 sibling sidecar 目錄。
- metadata 不應混入後續 `transcript-polish` 會掃描的逐字稿目錄。

## 2. 現況問題

### 2.1 audio 輸出策略不一致

`extract-audio` 目前固定輸出到來源目錄下的 `audio/` 子目錄；`transcribe-audio` 遇到影片時，抽出的音檔則放回來源目錄同一層。兩者各自合理，但若要做整合 pipeline，必須把 `transcribe-audio` 的 audio policy 明文化並提供參數控制。

本 CR 不要求移除 `extract-audio` 的既有 `audio/` 行為，但建議新增可明確指定輸出策略的參數，降低兩支工具長期歧異。

### 2.2 逐字稿輸出固定在來源目錄下的 `transcript/`

現況：

```text
Meeting/
  transcript/
    xxx.txt
    _run-summary.txt
    _environment.txt
    _failed-files.txt
```

若再接 `transcript-polish --dir Meeting/transcript`，容易形成：

```text
Meeting/
  transcript/
    formatted/
      xxx.md
```

這會造成階層過深，也讓正文與控制檔混在一起。

### 2.3 metadata 與正文混雜

`_run-summary.txt`、`_environment.txt`、`_failed-files.txt` 屬於執行紀錄，不是逐字稿正文。producer 應避免把這些檔案放入 consumer 的輸入集合，不能只依賴下游工具排除。

## 3. 目標目錄結構

假設來源目錄為：

```text
Meeting/
  a.mp4
  a.m4a
  b.mp4
```

目標預設輸出為：

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

說明：

- `Meeting/` 是 media pool，保留原始影片與音檔；必要時才新增抽出的音檔。
- `Meeting.transcript/` 只放可供下游整理的逐字稿正文。
- `Meeting.meta/` 放 summary、environment、failed list、抽音軌 manifest。
- 不預設建立 `Meeting.audio/`。

## 4. `transcribe-audio` CLI 變更

### 4.1 `--layout legacy|sidecar`

目標預設：`sidecar`。

`sidecar` 模式下：

```bash
transcribe-audio ./Meeting
```

等價於：

```bash
transcribe-audio ./Meeting \
  --layout sidecar \
  --audio-output same-dir \
  --transcript-output ../Meeting.transcript \
  --meta-output ../Meeting.meta
```

注意：`../Meeting.transcript` 與 `../Meeting.meta` 是根據來源目錄的 parent directory 推導，不是根據 shell current working directory 推導。

為相容舊行為，必須保留：

```bash
transcribe-audio ./Meeting --layout legacy
```

legacy 模式可維持：

```text
Meeting/transcript/
```

若擔心直接改預設造成破壞，可分階段：第一階段新增 `--layout sidecar` 並維持 legacy 預設；第二階段再把 sidecar 改成預設。本 CR 的目標狀態是 sidecar 成為預設。

### 4.2 `--audio-output same-dir|sidecar|cache|none`

建議語意：

- `same-dir`：預設。抽出的音檔放回來源目錄，並可被後續執行重用。
- `sidecar`：抽出的音檔放到 `SOURCE.audio/`。這是選配，不作為預設。
- `cache`：抽出的音檔放到 cache/meta 目錄，例如 `SOURCE.meta/audio/`。
- `none`：不從影片抽音軌，只處理既有音檔；沒有同名音檔的影片應記錄 skipped/failed reason。

### 4.3 `--transcript-output PATH`

明確指定逐字稿輸出目錄。若未指定且 layout 為 sidecar，預設為：

```text
SOURCE_PARENT/SOURCE_BASENAME.transcript
```

### 4.4 `--meta-output PATH`

明確指定 metadata 輸出目錄。若未指定且 layout 為 sidecar，預設為：

```text
SOURCE_PARENT/SOURCE_BASENAME.meta
```

### 4.5 `--no-meta`

選擇性參數。停用 metadata 檔案輸出。整合流程不建議使用。

## 5. `extract-audio` CLI 補強

`extract-audio` 可保留目前 `SOURCE/audio/` 預設，但建議新增：

```text
--output-dir PATH
--output-mode child|same-dir|sidecar
```

建議語意：

- `child`：現行行為，輸出到 `SOURCE/audio/`。
- `same-dir`：輸出到來源目錄同一層。
- `sidecar`：輸出到 `SOURCE_PARENT/SOURCE_BASENAME.audio/`。
- `--output-dir` 明確指定時，優先於 `--output-mode`。

這不是整合流程的硬性必要條件，但可讓兩支工具長期維持一致的路徑語意。

## 6. 同名音檔重用規則

`transcribe-audio` 應先掃描來源目錄第一層音檔，建立 stem 對應。遇到影片時：

1. 取影片 stem。
2. 若已有同 stem 可用音檔，且未指定 `--force`，沿用既有音檔。
3. 若沒有同 stem 音檔，依 `--audio-output` 決定是否抽音軌。
4. 若直接抽取失敗，可 fallback 成 FLAC。
5. 所有 reuse/extract/failed/skipped 狀態都應寫入 `extracted-audio.tsv`。

此規則的目的，是支援使用者把 video 與 audio 都放在 `Meeting/`，而不是強迫先搬移或複製音檔。

## 7. Metadata 規格

sidecar layout 下 metadata 檔名應使用工具前綴：

```text
transcribe-run-summary.txt
transcribe-environment.txt
transcribe-failed-files.txt
extracted-audio.tsv
```

`extracted-audio.tsv` 格式：

```text
video_file	audio_file	codec	status	reason
a.mp4	a.m4a	aac	reused_existing_audio	
b.mp4	b.flac	flac	extracted	
c.mp4			no_audio_stream	no audio stream found
```

建議狀態值：

```text
reused_existing_audio
extracted
converted_to_flac
no_audio_stream
extract_failed
skipped_by_audio_output_none
```

## 8. 與 transcript-polish 的整合契約

`transcribe-audio` 在 sidecar layout 下必須保證：

- `TRANSCRIPT_DIR` 只放正文逐字稿，預設為 `.txt`。
- metadata 不放入 `TRANSCRIPT_DIR`。
- 完成時 stdout 末尾輸出可解析的結果資訊。

建議 stdout 末尾：

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

## 9. 路徑防呆規則

必須報錯的情況：

- 來源目錄不存在。
- sidecar 推導結果等於來源目錄。
- `--transcript-output` 等於來源目錄。
- `--meta-output` 等於來源目錄。
- `--transcript-output` 等於 `--meta-output`。
- 來源目錄是 filesystem root，無法安全推導 sidecar，除非使用者明確指定輸出目錄。

## 10. 測試案例

### 10.1 同名音檔已存在

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

- 不重新抽音軌。
- 使用 `a.m4a` 轉錄。
- 產生 `Meeting.transcript/a.txt`。
- `Meeting.meta/extracted-audio.tsv` 記錄 `reused_existing_audio`。

### 10.2 影片無同名音檔

輸入：

```text
Meeting/
  b.mp4
```

預期：

- 抽出 `Meeting/b.<ext>`。
- 產生 `Meeting.transcript/b.txt`。
- metadata 放在 `Meeting.meta/`。
- `Meeting.transcript/` 不得有 `_run-summary.txt`、`_environment.txt`、`_failed-files.txt`。

### 10.3 legacy layout

執行：

```bash
transcribe-audio ./Meeting --layout legacy
```

預期：

- 保留舊輸出 `Meeting/transcript/`。
- 舊 metadata 命名可暫時保留。
- 下游工具仍應有自己的 `_*.txt` 排除保護。

### 10.4 明確指定輸出目錄

執行：

```bash
transcribe-audio ./Meeting \
  --transcript-output /tmp/out/transcript \
  --meta-output /tmp/out/meta
```

預期：

- 使用指定目錄。
- 指定目錄不存在時自動建立。
- 指定目錄與來源目錄相同時報錯。

## 11. 實作順序建議

1. 抽出 path resolution 函式，集中處理 source parent、basename、sidecar 推導。
2. 新增 `--layout`、`--transcript-output`、`--meta-output`。
3. 將 sidecar layout 下的 summary/environment/failed files 移到 meta dir。
4. 新增 `extracted-audio.tsv`。
5. 新增 `--audio-output`。
6. 補 README、INSTALL、既有 SDD 中的目錄範例。
7. 視相容性策略決定何時把 sidecar 設為預設。

## 12. 驗收標準

完成後，以下指令應可作為合併前的穩定 producer contract：

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
