# SDD: 批次音檔轉文字 Shell 工具

最後更新：2026-06-13

## 1. 目標

設計一支 Shell 工具，掃描「當前目錄」中的音檔與影片檔，若遇到影片檔則先抽出音軌到同一目錄，再使用 WhisperX 批次轉成逐字稿，並將輸出統一放到當前目錄下的 `transcript/` 目錄。

這支工具的定位是：

1. 盡量零設定即可使用。
2. 執行前先做環境檢查，避免跑到一半才失敗。
3. 可用參數決定是否開啟講者分離。
4. 根據硬體條件自動選擇合理的模型與效能參數。
5. 對目前這個 repo 的使用習慣友善，風格延續 `bin/extract-audio`。

建議指令名稱：

```text
bin/transcribe-audio
```

若之後安裝成全域指令，建議名稱：

```text
transcribe-audio
```

---

## 2. 使用情境

### 2.1 主要情境

使用者在某個資料夾中已有音檔，例如：

```text
meeting-01.m4a
meeting-02.mp3
meeting-03.wav
```

執行：

```bash
./bin/transcribe-audio
```

工具自動：

1. 掃描目前目錄第一層音檔與影片檔。
2. 檢查 WhisperX / Python / FFmpeg / GPU / Hugging Face 權限是否可用。
3. 若遇到影片檔，先抽出音軌到同一目錄。
4. 根據硬體自動決定 `model`、`device`、`compute_type`、`batch_size`。
5. 逐一轉錄音檔。
6. 輸出到 `./transcript/`。

### 2.2 講者分離情境

執行：

```bash
./bin/transcribe-audio --diarize
```

工具需額外：

1. 檢查 `HF_TOKEN` 是否存在，或 Hugging Face CLI 是否已登入。
2. 檢查 pyannote gated model 是否可存取。
3. 若授權未完成，應在正式轉錄前中止並顯示清楚原因。

### 2.3 覆蓋重跑情境

執行：

```bash
./bin/transcribe-audio --force
```

若已有同名輸出，允許覆蓋。

### 2.4 先檢查不執行情境

執行：

```bash
./bin/transcribe-audio --check
```

只做環境檢查與硬體評估，不實際轉錄。

---

## 3. 非目標

第一版不處理以下需求：

1. 不做子目錄遞迴掃描。
2. 不做 GUI。
3. 不直接把 `SPEAKER_00` 自動替換成人名。
4. 不直接產生最終會議紀錄摘要。
5. 不管理 Hugging Face token 建立流程，只做檢查與提示。

---

## 4. CLI 規格

### 4.1 基本用法

```bash
transcribe-audio [目錄]
transcribe-audio --diarize [目錄]
transcribe-audio --force [目錄]
transcribe-audio --check [目錄]
```

### 4.2 參數

```text
-d, --diarize
    啟用說話者分離。

-f, --force
    覆蓋已存在的輸出檔。

--check
    只檢查環境與推估參數，不執行轉錄。

--model <name>
    手動指定 Whisper 模型，例如：small、medium、large-v3。

--device <auto|cuda|cpu>
    指定裝置，預設 auto。

--batch-size <n>
    手動指定 batch size；若未指定則自動推估。

--compute-type <default|float16|float32|int8>
    手動指定 compute type；若未指定則自動推估。

--language <code>
    指定語言，預設 zh。
    WhisperX CLI 沒有繁中/簡中代碼區分，工具層以 zh 代表中文。

--output-format <all|txt|json|srt|vtt|tsv>
    指定輸出格式，預設 txt。

--min-speakers <n>
    diarization 時設定最小講者數。

--max-speakers <n>
    diarization 時設定最大講者數。

--name-by-stem
    輸出目錄下直接使用原檔名 stem 作為輸出前綴。

--skip-existing
    若偵測主要輸出已存在則跳過；預設開啟。

--verbose
    顯示詳細執行資訊。

-h, --help
    顯示說明。
```

### 4.3 參數優先順序

```text
使用者明確指定 > 自動偵測推估 > 內建預設值
```

例如：

1. 若使用者指定 `--model medium`，即使 GPU 很強也不得改成 `large-v3`。
2. 若使用者指定 `--device cpu`，即使 CUDA 可用也必須用 CPU。

---

## 5. 輸入與輸出規格

### 5.1 輸入檔案

預設掃描指定目錄第一層的常見音檔：

```text
*.m4a
*.mp3
*.wav
*.flac
*.aac
*.ogg
*.opus
*.wma
*.mka
```

同時掃描常見影片檔：

```text
*.mp4
*.mov
*.mkv
```

若偵測到影片檔，工具需先抽音軌，再將抽出的音檔納入同一次批次轉錄。

抽音軌策略：

1. 抽出的音檔放在與來源影片相同的目錄。
2. 優先直接複製音訊串流，不重新編碼。
3. 若直接抽取失敗，退回轉成 FLAC。
4. 抽音軌命名策略應與既有 `extract-audio` 盡量一致。

例如：

```text
meeting-01.mp4
→ meeting-01.m4a
```

或在無法直接封裝時：

```text
meeting-01.mp4
→ meeting-01.flac
```

### 5.2 輸出目錄

固定輸出到：

```text
./transcript/
```

### 5.3 每個音檔的輸出

若輸入：

```text
./meeting-01.m4a
```

輸出：

```text
./transcript/meeting-01.json
./transcript/meeting-01.txt
./transcript/meeting-01.srt
./transcript/meeting-01.vtt
./transcript/meeting-01.tsv
```

第一版預設 `output_format=txt` 時，至少要保證：

```text
./transcript/meeting-01.txt
```

其餘格式只在使用者指定時輸出。

### 5.4 額外輸出

建議每次執行再額外寫出：

```text
./transcript/_run-summary.txt
./transcript/_environment.txt
./transcript/_failed-files.txt
```

用途：

1. `_run-summary.txt`：記錄本次處理數量、成功失敗、參數。
2. `_environment.txt`：記錄 Python、WhisperX、Torch、GPU、CUDA runtime。
3. `_failed-files.txt`：列出失敗檔名與原因。

---

## 6. 系統流程

### 6.1 執行流程

```text
啟動
  ↓
解析 CLI 參數
  ↓
檢查系統依賴
  ↓
檢查 WhisperX 執行環境
  ↓
掃描音檔與影片檔
  ↓
若有影片檔，先抽音軌到同目錄
  ↓
偵測硬體與推估參數
  ↓
若有 --diarize，檢查 HF 權限
  ↓
逐檔執行 WhisperX
  ↓
彙整結果與摘要
  ↓
結束
```

### 6.2 單檔處理流程

```text
確認輸入檔存在
  ↓
若為影片檔，先抽出音軌並取得實際待轉錄音檔
  ↓
確認輸出是否已存在
  ↓
建立暫存輸出目錄或暫存檔
  ↓
執行 whisperx
  ↓
檢查主要輸出是否成功產生
  ↓
成功則寫入 summary
失敗則記錄錯誤並繼續下一檔
```

---

## 7. 環境檢查規格

### 7.1 必要依賴

執行前必須檢查：

1. `bash`
2. `ffmpeg`
3. `ffprobe`
4. `python`
5. `whisperx`
6. `find`

### 7.2 WhisperX 執行檢查

至少驗證以下事項：

1. `whisperx --help` 可成功執行。
2. `python -c "import torch"` 成功。
3. `python -c "import whisperx"` 成功。

### 7.3 GPU 檢查

若 `--device auto` 或 `--device cuda`：

1. 檢查 `nvidia-smi` 是否存在。
2. 檢查 `torch.cuda.is_available()` 是否為 `True`。
3. 取得 GPU 名稱。
4. 盡可能取得顯存資訊。

### 7.4 diarization 額外檢查

若指定 `--diarize`，必須檢查：

1. `HF_TOKEN` 是否存在，或 `hf auth whoami` 成功。
2. 是否能存取 `pyannote/speaker-diarization-community-1`。
3. 權限不足時直接失敗，不進入批次轉錄。

### 7.5 檢查失敗策略

```text
必要條件不成立 → 直接中止
單一音檔格式不支援 → 跳過並記錄
單一音檔轉錄失敗 → 記錄後繼續處理下一檔
```

---

## 8. 硬體自動調參規格

### 8.1 偵測來源

優先從以下來源取得資訊：

1. `torch.cuda.is_available()`
2. `torch.cuda.get_device_name(0)`
3. `torch.cuda.get_device_properties(0).total_memory`
4. `nvidia-smi --query-gpu=name,memory.total --format=csv,noheader`

### 8.2 自動推估策略

#### A. NVIDIA GPU 10GB 以上

```text
device=cuda
model=large-v3
compute_type=float16
batch_size=8
```

#### B. NVIDIA GPU 6GB 到 9GB

```text
device=cuda
model=medium
compute_type=float16
batch_size=4
```

若使用者明確要求品質優先，可放寬為：

```text
model=large-v3
compute_type=int8 或 float16
batch_size=2
```

#### C. NVIDIA GPU 4GB 到 5GB

```text
device=cuda
model=medium
compute_type=float16
batch_size=2
```

若 diarization 開啟且 OOM 風險高，可降為：

```text
model=small
compute_type=int8
batch_size=1
```

#### D. 無可用 NVIDIA CUDA

```text
device=cpu
model=small
compute_type=int8
batch_size=2
```

### 8.3 安全降級策略

若執行中遇到 OOM，可考慮第二版加入自動重試：

```text
batch_size 8 → 4 → 2 → 1
float16 → int8
large-v3 → medium → small
```

第一版可先不做自動重試，只需在前置檢查與 summary 中提示推估參數。

### 8.4 顯示策略

正式執行前必須列出最終使用參數，例如：

```text
裝置：cuda
GPU：NVIDIA GeForce RTX 3080
模型：large-v3
compute_type：float16
batch_size：8
語言：zh
diarize：yes
```

---

## 9. WhisperX 執行規格

### 9.1 基本命令模板

```bash
whisperx "$input_file" \
  --model "$model" \
  --language "$language" \
  --device "$device" \
  --compute_type "$compute_type" \
  --batch_size "$batch_size" \
  --output_dir "$output_dir"
```

預設若未指定 `--output-format`，實際命令應附加：

```bash
--output_format txt
```

### 9.2 啟用講者分離

```bash
whisperx "$input_file" \
  --model "$model" \
  --language "$language" \
  --device "$device" \
  --compute_type "$compute_type" \
  --batch_size "$batch_size" \
  --diarize \
  --hf_token "$HF_TOKEN" \
  --output_dir "$output_dir"
```

### 9.3 講者數指定

若使用者帶入：

```text
--min-speakers
--max-speakers
```

只在 `--diarize` 模式下附加到 WhisperX 命令。

若未開 `--diarize` 卻傳入講者數參數，應直接報錯。

---

## 10. 日誌與輸出訊息規格

### 10.1 主控台輸出

需維持與 `extract-audio` 相近的可讀風格，例如：

```text
來源目錄：.
輸出目錄：./transcript
模式：批次轉錄
講者分離：開啟

[檢查] ffmpeg：OK
[檢查] whisperx：OK
[檢查] CUDA：OK
[檢查] pyannote token：OK
[抽取] meeting-00.mp4 → meeting-00.m4a

[轉錄] meeting-01.m4a
[完成] meeting-01.txt
[轉錄] meeting-02.mp3
[失敗] meeting-02.mp3
```

### 10.2 執行摘要

結束時至少顯示：

```text
總檔案數：5
成功：4
失敗：1
跳過：0
輸出目錄：./transcript
```

### 10.3 Exit Code

```text
0  全部成功，或僅有合理跳過
1  環境檢查失敗
2  CLI 參數錯誤
3  有檔案執行失敗
```

---

## 11. 推薦附加功能

這些不是最小可行版本必做，但很值得一起規劃。

### 11.1 `--dry-run`

顯示會處理哪些檔案、會用什麼參數，但不實際執行。

### 11.2 `--formats`

允許自訂輸出格式，例如只輸出：

```bash
--formats txt,json
```

### 11.3 `--workers`

限制同時處理數量。第一版建議固定單工，第二版才考慮平行化。

原因：

1. GPU 記憶體競爭複雜。
2. 多工 diarization 更容易爆顯存。
3. Shell 版先求穩定。

### 11.4 `--archive-source`

處理成功後可選擇將原始音檔移到：

```text
./processed-audio/
```

第一版可不做，但未來做批次作業時很實用。

### 11.5 `--keep-video-audio`

若影片已先抽成音檔，是否保留抽出的音檔。由於你目前需求是「音檔放同一個目錄」，第一版建議預設保留，不做自動刪除。

### 11.6 `--append-date-dir`

自動輸出到：

```text
./transcript/20260613-153000/
```

可避免多次執行互相覆蓋。

### 11.7 `--emit-env-file`

額外輸出可重現環境資訊，便於之後比對：

```text
Python version
whisperx version
torch version
pyannote version
transformers version
GPU / CUDA
```

### 11.8 `--hotwords-file`

指定一份技術詞彙或人名表，傳給 WhisperX 的 `--hotwords`，提升專有名詞命中率。

### 11.9 `--continue-on-error`

雖然預設就應該對單檔失敗繼續，但仍可明確提供這個選項，讓策略更清楚。

---

## 12. 實作建議

### 12.1 腳本結構

建議延續 `bin/extract-audio` 的 Bash 風格，拆成幾個函式：

1. `usage`
2. `parse_args`
3. `check_dependencies`
4. `check_whisperx_env`
5. `detect_hardware`
6. `choose_profile`
7. `check_diarization_access`
8. `scan_input_files`
9. `build_whisperx_args`
10. `transcribe_one`
11. `write_summary`

### 12.2 Python 輔助邏輯

因為 GPU / Torch / 記憶體偵測用 Bash 很醜，建議在腳本內嵌一小段 Python 取得：

1. `torch.cuda.is_available()`
2. GPU 名稱
3. VRAM
4. Torch / WhisperX 版本

Shell 只負責：

1. CLI
2. 目錄掃描
3. 呼叫 WhisperX
4. 錯誤控制

### 12.3 第一版推薦範圍

第一版先做到：

1. 掃描目前目錄音檔與影片檔
2. 影片先抽音軌到同目錄
3. 輸出到 `transcript/`
4. 預設 `language=zh`
5. 預設 `output_format=txt`
6. `--diarize`
7. `--force`
8. `--check`
9. 環境檢查
10. 基本硬體自動調參
11. run summary

不要第一版就做：

1. 自動 OOM 重試
2. 多工平行轉錄
3. 熱詞檔案解析
4. 會議摘要後處理

---

## 13. 驗收標準

### 13.1 功能驗收

1. 在含有 3 個音檔的目錄執行，能正確掃描並建立 `transcript/`。
2. 在含有影片檔的目錄執行，能先抽音軌到同目錄，再進入轉錄流程。
3. 不帶 `--diarize` 時，能成功輸出逐字稿。
4. 預設輸出格式為 `txt`。
5. 帶 `--diarize` 且有正確 token 時，能成功輸出含 speaker 的結果。
6. 帶 `--diarize` 但沒有 token 或未接受條款時，能在執行前清楚失敗。
7. 已存在輸出時，預設跳過；帶 `--force` 時覆蓋。

### 13.2 錯誤驗收

1. 缺 `ffmpeg` 時能明確提示。
2. 缺 `whisperx` 時能明確提示。
3. `torch.cuda.is_available()` 為 `False` 時能安全降到 CPU。
4. 單一音檔失敗時，其他檔案仍會繼續執行。

### 13.3 可維護性驗收

1. 腳本不把 WhisperX 命令散落在多處。
2. 所有自動推估參數都有單一決策點。
3. 日誌與 summary 可以讓使用者回頭查到當時使用的參數。

---

## 14. 建議的下一步

建議按以下順序實作：

1. 先做 `--check` 與硬體偵測。
2. 再做單檔轉錄。
3. 再做批次掃描與 summary。
4. 最後接上 `--diarize` 與 Hugging Face 權限檢查。

如果你要我直接接著做，我建議下一步不是先寫完整腳本，而是先把這份 SDD 收斂成第一版的最小功能集合，然後我就能直接開始實作 `bin/transcribe-audio`。
