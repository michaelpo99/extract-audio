# SDD: 逐字稿整理 CLI 工具

最後更新：2026-06-14

## 1. 目標

設計一支 CLI 工具，掃描「當前目錄」或指定目錄中的逐字稿檔案，使用本地端 LLM 進行校正、繁體化、標點補全、分段與 Markdown 排版，並將輸出統一放到來源目錄下的 `formatted/` 子目錄。

這支工具的定位是：

1. 盡量零設定即可使用。
2. 預設行為以「掃描目前目錄第一層」為主，符合日常批次處理習慣。
3. 工具本身不執行 WhisperX，只處理 WhisperX 或其他來源已產生的文字稿。
4. 支援內建規則、外部替換詞彙表與額外 AI 指引三層整理策略。
5. 可用參數切換模型，但預設值應適合 `RTX 3080 10GB` 的本地使用情境。

建議指令名稱：

```text
bin/transcript-polish
```

若之後安裝成全域指令，建議名稱：

```text
transcript-polish
```

---

## 2. 使用情境

### 2.1 主要情境

使用者在某個資料夾中已有逐字稿，例如：

```text
episode-01.txt
episode-02.txt
episode-03.md
```

執行：

```bash
./bin/transcript-polish
```

工具自動：

1. 掃描目前目錄第一層的 `.txt` 與 `.md` 檔案。
2. 排除 `formatted/` 內既有成品與明顯非輸入用途檔案。
3. 載入內建替換規則。
4. 使用預設模型整理逐字稿。
5. 將輸出寫入 `./formatted/`。

### 2.2 指定單一檔案情境

執行：

```bash
./bin/transcript-polish --file ./episode-01.txt
```

工具只處理指定檔案，並將輸出寫入：

```text
./formatted/episode-01.md
```

### 2.3 指定目錄情境

執行：

```bash
./bin/transcript-polish --dir ./transcript
```

工具需：

1. 只掃描 `./transcript` 第一層。
2. 不遞迴子目錄。
3. 將輸出寫入：

```text
./transcript/formatted/
```

### 2.4 使用外部替換詞彙表情境

執行：

```bash
./bin/transcript-polish --replace-dict ./replacements.txt
```

工具需先載入外部替換表，再與內建規則一併套用到每份輸入文字後，才送入模型。

### 2.5 使用額外 AI 指引情境

執行：

```bash
./bin/transcript-polish --style-guide ./style-guide.txt
```

工具需將該檔案內容附加到 prompt，作為額外參考規則，但不得宣稱其效果等同強制替換。

### 2.6 覆蓋重跑情境

執行：

```bash
./bin/transcript-polish --force
```

若 `formatted/` 內已有同名輸出，允許覆蓋。

---

## 3. 非目標

第一版不處理以下需求：

1. 不做子目錄遞迴掃描。
2. 不保留輸入 `.md` 的原始 Markdown 結構。
3. 不讓 AI 自由解析任意格式的替換詞彙表並保證正確套用。
4. 不直接執行 WhisperX、Whisper 或其他語音辨識流程。
5. 不先實作量化模型載入流程，但文件可保留後續擴充方向。

---

## 4. CLI 規格

### 4.1 基本用法

```bash
transcript-polish
transcript-polish --file <path>
transcript-polish --dir <path>
transcript-polish --model <name>
transcript-polish --replace-dict <path>
transcript-polish --style-guide <path>
transcript-polish --force
```

### 4.2 參數

```text
--file <path>
    處理單一檔案，僅接受 .txt 或 .md。

--dir <path>
    處理指定目錄第一層的 .txt 與 .md。

--model <name>
    指定 Hugging Face 模型名稱。
    預設為 Qwen/Qwen2.5-3B-Instruct。

--replace-dict <path>
    載入外部強制替換詞彙表。

--style-guide <path>
    載入額外 AI 參考指引檔。

--output-dir <name-or-path>
    指定輸出子目錄名稱或路徑。
    若未指定，預設為 formatted。

-f, --force
    覆蓋已存在的輸出檔。

-h, --help
    顯示說明。
```

### 4.3 參數衝突與優先順序

```text
使用者明確指定 > 自動推定 > 內建預設值
```

規則如下：

1. `--file` 與 `--dir` 不可同時指定。
2. 若未指定 `--file` 與 `--dir`，預設掃描目前工作目錄。
3. 若指定 `--output-dir`，優先使用使用者指定值。
4. 若指定 `--model`，不得自動改用其他模型。

---

## 5. 輸入與輸出規格

### 5.1 輸入檔案

預設支援以下副檔名：

```text
*.txt
*.md
```

語意如下：

1. `.txt` 視為原始逐字稿。
2. `.md` 視為可讀文字來源。
3. `.md` 輸入不保留其原本 Markdown 結構，輸出時一律重新生成標準化 Markdown。

### 5.2 預設掃描規則

若未指定 `--file` 或 `--dir`，固定掃描：

```text
目前工作目錄第一層
```

第一版需排除：

1. 輸出子目錄 `formatted/`。
2. `_run-summary.txt`
3. `_environment.txt`
4. 明顯非輸入用途的隱藏暫存檔。

### 5.3 輸出目錄

預設輸出到：

```text
formatted/
```

具體規則：

1. 預設掃描目前目錄時，輸出到 `./formatted/`。
2. 使用 `--dir ./transcript` 時，輸出到 `./transcript/formatted/`。
3. 使用 `--file ./a/b/c.txt` 時，輸出到 `./a/b/formatted/`。
4. 若使用者明確指定 `--output-dir`，則依指定值輸出。

### 5.4 輸出檔名

若輸入：

```text
./episode-01.txt
```

輸出：

```text
./formatted/episode-01.md
```

若輸入：

```text
./episode-02.md
```

輸出：

```text
./formatted/episode-02.md
```

### 5.5 覆蓋策略

1. 若目標輸出檔已存在且未指定 `--force`，則跳過。
2. 若指定 `--force`，則允許覆蓋。
3. 批次模式下單檔失敗不得中止全部流程，應繼續處理其他檔案。

---

## 6. 文字整理規則

### 6.1 三層規則模型

工具需明確區分以下三層規則：

1. 內建強制替換規則。
2. 外部強制替換詞彙表。
3. 外部 AI 參考指引。

這三層的語意不得混淆。

### 6.2 內建強制替換規則

內建規則用於修正常見且高確定性的音辨錯字，例如：

```text
POA => PUA
AIP => IP
物理資料 => 物料資料
攻深入局 => 躬身入局
```

此類規則在送入模型前以程式邏輯直接套用，屬於強制生效。

### 6.3 外部強制替換詞彙表

第一版格式固定為：

```text
來源 => 目標
```

例如：

```text
POA => PUA
偏西西 => 拼夕夕
預支差 => 預製菜
```

解析規則：

1. 忽略空白行。
2. 忽略以 `#` 開頭的註解行。
3. 每行必須可拆成 `來源 => 目標`。
4. 無法解析時，需回報行號與原始內容。

### 6.4 外部 AI 參考指引

`--style-guide` 檔案內容不做結構解析，整份文字直接附加到 prompt。

其用途是提供：

1. 用語偏好。
2. 禁則。
3. 台灣慣用語替換方向。
4. 段落或標題風格偏好。

但其效果屬於模型參考，不得等同於強制替換規則。

---

## 7. Prompt 與模型規格

### 7.1 Prompt 結構

Prompt 至少應包含三部分：

1. 固定 system instruction。
2. 使用者輸入的逐字稿原文。
3. 額外 style guide 內容（若有）。

固定 system instruction 應要求模型：

1. 忠於原文，不新增原文沒有的內容。
2. 補上適當標點。
3. 根據語意分段。
4. 在主題自然切換時，適度加上簡潔的 Markdown 標題。
5. 標題需依據原文已存在的主題，不得憑空發明結論。
6. 轉為台灣繁體中文。
7. 只輸出整理後的 Markdown 成品。

### 7.2 預設模型

第一版預設模型：

```text
Qwen/Qwen2.5-3B-Instruct
```

選用理由：

1. 中文能力與指令遵循能力在本任務上屬於合理基準。
2. 對 `RTX 3080 10GB` 較容易以 `float16` 本地運行。
3. 作為第一版預設值，部署阻力較低。

### 7.3 RTX 3080 10GB 建議

在 `RTX 3080 10GB` 上的建議策略：

1. 預設使用 `Qwen2.5-3B-Instruct`。
2. 若後續追求更高品質，可評估 `Qwen2.5-7B-Instruct` 的量化版本。
3. 第一版不強制實作量化模型支援，但文件可保留此升級方向。

### 7.4 其他模型相容性

若使用者指定其他模型，工具需：

1. 嘗試載入指定 tokenizer 與 model。
2. 若缺少 chat template 或對話格式不相容，需回報清楚錯誤。
3. 不應只丟出難以理解的原始 traceback 作為唯一訊息。

---

## 8. 執行流程

### 8.1 標準流程

工具應依序執行：

1. 解析 CLI 參數。
2. 驗證 `--file` / `--dir` 是否衝突。
3. 確定輸入來源與輸出目錄。
4. 掃描待處理檔案。
5. 載入外部替換詞彙表與 style guide。
6. 載入 tokenizer 與模型。
7. 逐檔讀取文字內容。
8. 套用內建強制替換。
9. 套用外部強制替換。
10. 組合 prompt。
11. 呼叫模型生成整理後內容。
12. 清理模型輸出。
13. 寫入輸出檔案。
14. 輸出執行摘要。

### 8.2 輸出清理

模型輸出清理需處理：

1. Markdown code fence。
2. 明顯的多餘前言或後記。
3. 顯然不是成品內容的客套說明。

但清理規則不得過度寬鬆到誤刪合法 Markdown 內容。

---

## 9. 依賴與執行環境

### 9.1 核心依賴

第一版核心依賴：

```text
Python 3.10+
torch
transformers
```

### 9.2 建議環境

建議執行環境：

1. WSL2 或 Linux。
2. 支援 CUDA 的 NVIDIA GPU。
3. 至少可容納預設模型的本地磁碟空間與顯示記憶體。

### 9.3 首次執行行為

首次執行時，模型可能需從 Hugging Face 下載並快取到本機。

因此文件需明確說明：

1. 第一次執行可能需要網路。
2. 之後若模型已快取，可離線重複使用。
3. 預設公開模型情境下，不強制要求 `HF_TOKEN`。
4. 若指定 gated、private 或需授權的模型，需先滿足 Hugging Face 存取條件，例如 `HF_TOKEN` 或 CLI 登入。

### 9.4 後續擴充依賴

若未來支援量化模型，可再納入：

```text
accelerate
bitsandbytes
```

---

## 10. 執行摘要、進度與輸出檔

### 10.1 執行前摘要

正式處理前，工具應先輸出一段簡潔的執行摘要，至少包含：

1. 輸入來源。
2. 掃描深度。
3. 支援副檔名。
4. 待處理檔案數。
5. 輸出目錄。
6. 使用模型。
7. 執行裝置與 dtype。
8. 是否載入外部替換表。
9. 是否載入 style guide。
10. 是否啟用 `--force`。

### 10.2 多檔進度輸出

多檔處理時，標準輸出應顯示簡化進度格式，讓使用者能快速掌握：

1. 總共有幾個作業。
2. 目前正在處理第幾個。
3. 每個檔案的結果是成功、跳過或失敗。

建議格式：

```text
[run] queued=12
[1/12] processing episode-01.txt
[1/12] done -> formatted/episode-01.md
[2/12] processing episode-02.txt
[2/12] skipped -> formatted/episode-02.md
[3/12] processing episode-03.md
[3/12] failed -> <reason>
```

第一版不要求：

1. 百分比進度條。
2. 預估剩餘時間。
3. Token 級別生成進度。

### 10.3 輸出摘要檔

工具在輸出目錄下應產生：

```text
_run-summary.txt
_environment.txt
```

用途如下：

1. `_run-summary.txt`：記錄本次執行設定、檔案總數、成功數、跳過數、失敗數。
2. `_environment.txt`：記錄 Python、`torch`、`transformers`、CUDA、GPU、模型名稱、工作目錄與執行時間。

---

## 11. 錯誤處理與摘要

### 11.1 錯誤處理原則

工具需盡量回報可操作的錯誤訊息，而不是只有原始 traceback。

至少需涵蓋：

1. 缺少 `torch` 或 `transformers`。
2. 模型載入失敗。
3. 指定輸入檔不存在。
4. 指定副檔名不支援。
5. 替換詞彙表格式錯誤。
6. 指定目錄找不到可處理檔案。

### 11.2 批次模式容錯

批次模式下：

1. 單一檔案失敗應記錄並繼續處理其他檔案。
2. 全部處理完後再輸出摘要。

### 11.3 結束摘要

結束時至少輸出：

1. 成功數。
2. 跳過數。
3. 失敗數。
4. 輸出目錄位置。

---

## 12. 檔案結構建議

若後續不受現有檔名限制，建議方向如下：

```text
bin/transcript-polish
docs/SDD-transcript-polish.md
```

若後續擴充為模組化 Python 專案，可再演進為：

```text
src/transcript_polish/
```

第一版仍可接受單一主程式，但不建議長期維持兩份完整相同的腳本副本。
