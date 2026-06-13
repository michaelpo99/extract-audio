# WhisperX 在 WSL2 的安裝與使用筆記

最後更新：2026-06-13

這份文件是基於我在 WSL2 的實測紀錄整理而成，目標不是完整翻譯官方文件，而是保留一套「目前這台機器已驗證可用」的安裝與操作流程。

如果只是要在這個 repo 的工作流中使用 WhisperX，建議流程如下：

```text
影片
  ↓
./bin/extract-audio 先抽出音軌
  ↓
WhisperX 轉錄 / 對齊 / 說話者分離
  ↓
JSON / TXT / SRT / VTT / TSV
```

## 快速結論

1. 在這台 WSL2 + RTX 3080 的環境中，`whisperx` 已可正常使用 CUDA。
2. 目前實測可用組合為 `whisperx 3.8.6`、`torch 2.8.0`、`pyannote-audio 4.0.4`。
3. 不做講者分離時，`large-v3 + cuda + float16 + batch_size 8` 可正常執行。
4. 要做 diarization，除了 `--diarize` 之外，還需要 Hugging Face token 與 pyannote gated model 權限。
5. 這份筆記中的 batch size、模型大小與硬體建議，屬於實務起始值，不是 WhisperX 官方保證值。

## 一、WhisperX 是什麼

WhisperX 是建立在 Whisper／faster-whisper 之上的長音訊語音辨識工具，主要能力包括：

1. 將影片或音訊轉成文字。
2. 使用 GPU 批次處理，提高長音訊轉錄速度。
3. 使用 VAD 偵測有人說話的區段，減少靜音與部分幻覺。
4. 透過 alignment 模型改善時間軸，產生較精準的字詞時間。
5. 結合 pyannote，將不同講者標成 `SPEAKER_00`、`SPEAKER_01`。
6. 輸出 TXT、JSON、SRT、VTT、TSV 等格式。

WhisperX 的基本處理流程是：

```text
影片或音訊
   ↓
Whisper 語音辨識
   ↓
Alignment 時間校準
   ↓
pyannote 說話者分離（選用）
   ↓
TXT／JSON／SRT／VTT／TSV
```

WhisperX 的「說話者分離」只會判斷不同聲音，不會直接知道姓名：

```text
SPEAKER_00
SPEAKER_01
SPEAKER_02
```

要得到 Michael、Lily、Alexis 等姓名，需再由人工、聲紋比對，或依逐字稿內容、與會者名單和詞彙表推測。

---

## 二、這次實際使用環境

本次已成功執行的環境：

```text
作業系統：Windows 11
Linux 環境：WSL2 Ubuntu
Python：3.12
虛擬環境：~/.venvs/whisperx
GPU：NVIDIA RTX 3080
模型：large-v3
裝置：CUDA
CUDA runtime：12.8
計算精度：float16
Batch size：8
語言：中文 zh
```

本機目前已確認的相關套件版本：

```text
whisperx        3.8.6
torch           2.8.0
pyannote-audio  4.0.4
transformers    4.57.6
faster-whisper  1.2.1
```

成功執行後產生：

```text
20260609_151512.json
20260609_151512.srt
20260609_151512.tsv
20260609_151512.txt
20260609_151512.vtt
```

其中最值得保留的是：

* `JSON`：包含分段、時間與 Speaker 等結構化資訊。
* `TXT`：方便閱讀及交給 ChatGPT。
* `SRT／VTT`：影片字幕。
* `TSV`：方便後續用程式或試算表分析。

---

## 三、WSL2 與 GPU 前置檢查

### 1. 確認 WSL 可以看到 NVIDIA GPU

```bash
nvidia-smi
```

若能看到 RTX 3080／3050、顯示記憶體與驅動版本，表示 WSL 已能使用 GPU。

WSL2 使用的是 Windows 主機安裝的 NVIDIA 驅動程式。不要在 WSL 內另外安裝一般 Linux NVIDIA 顯示驅動，以免破壞 WSL 的 GPU 對接。

### 2. 安裝基本套件

```bash
sudo apt update
sudo apt install -y ffmpeg python3-venv
```

確認 FFmpeg：

```bash
ffmpeg -version
ffprobe -version
```

WhisperX 可以直接處理 MP4、M4A、MP3、WAV 等檔案。影片不一定要預先抽音軌；但若要保存、重複測試或批次處理，先抽成 M4A 會比較方便。

這個 repo 已有抽音軌腳本，可直接先跑：

```bash
./bin/extract-audio "/mnt/d/Videos/Meeting"
```

預設輸出會放在目標目錄下的 `audio/`。

---

## 四、建立獨立 Python 虛擬環境

```bash
python3 -m venv "$HOME/.venvs/whisperx"
source "$HOME/.venvs/whisperx/bin/activate"

python -m pip install --upgrade pip setuptools wheel
pip install whisperx
```

第一次安裝會連帶下載與解析較多相依套件，耗時比一般 Python CLI 工具長是正常現象。

啟用後，命令提示字元通常會變成：

```text
(whisperx) michaelpo@DESKTOP-Main:~$
```

檢查：

```bash
which python
which pip
which whisperx
```

正常應指向：

```text
/home/michaelpo/.venvs/whisperx/bin/python
/home/michaelpo/.venvs/whisperx/bin/pip
/home/michaelpo/.venvs/whisperx/bin/whisperx
```

### `source .../activate` 的作用

```bash
source "$HOME/.venvs/whisperx/bin/activate"
```

作用是將 WhisperX 虛擬環境的 `bin` 放到目前 shell 的 `PATH` 前面，讓：

```bash
python
pip
whisperx
```

都使用這個獨立環境內的版本。

關閉 terminal 後，啟用狀態就會消失。重新開啟 WSL 時，需要再次執行 `source`。

離開虛擬環境：

```bash
deactivate
```

也可以不啟用，直接執行完整路徑：

```bash
"$HOME/.venvs/whisperx/bin/whisperx" --help
```

---

## 五、確認 PyTorch 能使用 GPU

```bash
python - <<'PY'
import torch

print("PyTorch version :", torch.__version__)
print("CUDA available  :", torch.cuda.is_available())
print("CUDA runtime    :", torch.version.cuda)

if torch.cuda.is_available():
    print("GPU             :", torch.cuda.get_device_name(0))
PY
```

RTX 3080 正常時應類似：

```text
CUDA available  : True
GPU             : NVIDIA GeForce RTX 3080
```

我這台機器目前實際輸出為：

```text
CUDA available  : True
CUDA runtime    : 12.8
GPU             : NVIDIA GeForce RTX 3080
```

如果是 `False`，表示目前安裝的 PyTorch 沒有 CUDA 支援，或 Windows／WSL 的 NVIDIA 驅動有問題。

這時應到 PyTorch 官方安裝頁，依當時版本選擇：

```text
OS：Linux
Package：Pip
Language：Python
Compute Platform：CUDA
```

不要盲目套用舊版 PyTorch 安裝命令，因為 CUDA wheel 與 PyTorch 版本會更新。

---

## 六、不區分講者的使用方式

RTX 3080 的實測指令：

```bash
whisperx "$HOME/audio/20260609_151512.m4a" \
  --model large-v3 \
  --language zh \
  --device cuda \
  --compute_type float16 \
  --batch_size 8 \
  --output_dir "$HOME/transcript/"
```

參數說明：

```text
--model large-v3
    使用高品質多語言 Whisper 模型。

--language zh
    直接指定中文，省去語言偵測並降低誤判。

--device cuda
    使用 NVIDIA GPU。

--compute_type float16
    使用半精度 GPU 運算，RTX 顯示卡的主要選擇。
    目前 CLI 的 `default` 在 GPU 上也會偏向 float16，但實測筆記中仍明寫較不易混淆。

--batch_size 8
    一次批次處理的數量。越大通常越快，但佔用更多 VRAM。

--output_dir
    指定輸出目錄。
```

若發生 CUDA out of memory：

```bash
--batch_size 4
```

再不足則：

```bash
--batch_size 2
```

降低 batch size 通常只影響速度，不直接降低辨識品質。

---

## 七、使用 Hugging Face 與 pyannote 區分講者

### 1. Hugging Face 的用途

Hugging Face 類似 AI 模型的 GitHub。

WhisperX 的說話者分離會使用：

```text
pyannote/speaker-diarization-community-1
```

模型放在 Hugging Face，因此第一次下載需要：

1. 免費 Hugging Face 帳號。
2. 接受該模型的使用條件。
3. 建立 Access Token。
4. 將 Token 提供給 WhisperX。

本機運算不使用 Hugging Face 雲端 GPU，因此不按音訊時間收費。主要成本是自己的 GPU、電力與儲存空間。

### 2. 接受 pyannote 模型條款

登入 Hugging Face，進入：

```text
pyannote/speaker-diarization-community-1
```

按下類似：

```text
Agree and access repository
Accept conditions
```

這一步非常重要。

只有建立 Token，但沒有在模型頁接受條款，會出現：

```text
403 Forbidden
GatedRepoError
Access to model is restricted
```

### 3. 建立 Token

進入：

```text
Settings
→ Access Tokens
→ Create new token
```

建議：

```text
名稱：whisperx-wsl
類型：Read
```

個人測試環境使用普通 `Read` Token 即可。

正式部署可考慮 Fine-grained Token，只開放：

```text
Read access to contents of public gated repositories
```

不需要：

* Write
* Repository 管理
* Billing
* Inference Endpoint
* Organization 管理

若只需要下載 gated public model，權限原則上維持最小即可；沒有必要給寫入或帳號管理權限。

### 4. 在 WSL 設定 Token

為避免 Token 出現在 shell history：

```bash
read -rsp "Hugging Face token: " HF_TOKEN
echo
export HF_TOKEN
```

確認有設定，但不要印出完整 Token：

```bash
if [[ -n "${HF_TOKEN:-}" ]]; then
    echo "HF_TOKEN 已設定：${HF_TOKEN:0:6}..."
else
    echo "HF_TOKEN 未設定"
fi
```

環境變數只存在目前 shell。關掉 terminal 後，需重新設定。

也可以登入 Hugging Face CLI：

```bash
hf auth login
hf auth whoami
```

必須確認：

* 瀏覽器接受模型條款的帳號
* Token 所屬帳號
* `hf auth whoami` 顯示的帳號

三者相同。

### 5. 單獨測試模型存取權

不要每次都重跑整份會議，可以先測試：

```bash
python - <<'PY'
import os
from huggingface_hub import hf_hub_download

token = os.environ.get("HF_TOKEN")
if not token:
    raise SystemExit("HF_TOKEN 尚未設定")

path = hf_hub_download(
    repo_id="pyannote/speaker-diarization-community-1",
    filename="config.yaml",
    token=token,
)

print("存取成功：", path)
PY
```

若成功，就表示：

* Token 正確
* 帳號已接受條款
* 模型可下載

若這一步失敗，先不要直接重跑整個 `whisperx --diarize`，否則只會浪費下載與轉錄時間。

---

## 八、區分講者的執行方式

```bash
whisperx "$HOME/audio/20260609_151512.m4a" \
  --model large-v3 \
  --language zh \
  --device cuda \
  --compute_type float16 \
  --batch_size 8 \
  --diarize \
  --hf_token "$HF_TOKEN" \
  --output_dir "$HOME/transcript-diarized/"
```

新增參數：

```text
--diarize
    啟用 pyannote 說話者分離。

--hf_token "$HF_TOKEN"
    使用 Hugging Face Token 下載或載入 pyannote 模型。
```

結果會出現：

```text
SPEAKER_00
SPEAKER_01
SPEAKER_02
SPEAKER_03
```

### 已知實際發言人數

如果確定只有四個人發言：

```bash
--min_speakers 4 \
--max_speakers 4
```

完整範例：

```bash
whisperx "$HOME/audio/20260609_151512.m4a" \
  --model large-v3 \
  --language zh \
  --device cuda \
  --compute_type float16 \
  --batch_size 8 \
  --diarize \
  --min_speakers 4 \
  --max_speakers 4 \
  --hf_token "$HF_TOKEN" \
  --output_dir "$HOME/transcript-diarized/"
```

若名單有六人，但不確定每個人是否有發言，應給範圍：

```bash
--min_speakers 2 \
--max_speakers 6
```

不要因為會議名單有六人就強制六位 Speaker。沒有發言的人不應算入。

---

## 九、不同硬體的參數建議

以下是實務起始值，不是硬性規定。實際仍取決於 VRAM、音訊長度、模型版本和其他正在使用 GPU 的程式。

### RTX 3080，10GB／12GB

品質優先：

```bash
--model large-v3
--device cuda
--compute_type float16
--batch_size 8
```

若 VRAM 不足：

```bash
--batch_size 4
```

再不足：

```bash
--batch_size 2
```

這是目前實測成功的主要設定。

### RTX 3050，4GB

穩定優先：

```bash
--model medium
--device cuda
--compute_type float16
--batch_size 2
```

若仍不足：

```bash
--model small
--batch_size 2
```

想測試 large-v3：

```bash
--model large-v3
--device cuda
--compute_type int8
--batch_size 1
```

但 4GB VRAM 跑 large-v3、alignment 和 diarization 比較容易遇到記憶體問題，不建議作為固定預設。

### RTX 3050，6GB／8GB

這台機器目前已驗證可用，而且可作為日常預設：

```bash
--model large-v3
--device cuda
--compute_type float16
--batch_size 2
```

若想保守一些、減少顯示記憶體使用：

```bash
--model medium
--device cuda
--compute_type float16
--batch_size 2
```

如果 8GB 且記憶體足夠，可嘗試：

```bash
--model large-v3
--compute_type float16
--batch_size 4
```

### 2026-06-13：RTX 3050 6GB 實測 benchmark

測試目錄：

```text
$HOME/test/multimedia
```

測試方式：

1. 使用 `transcribe-audio --force` 強制覆蓋既有逐字稿。
2. 同一批 4 個 `.m4a` 音檔，分別比較 `medium` 與 `large-v3`。
3. 額外比較 `large-v3` 在 `batch_size 2` 與 `batch_size 1` 的差異。
4. 轉錄期間每秒記錄一次 `nvidia-smi`。

實測結果：

| 組合                  | 總耗時 | 峰值 GPU 使用率 | 峰值顯存 | 備註 |
| ------------------- | ----: | -------------: | -------: | --- |
| `medium + batch 2`  | 175 秒 |          100% |  3037 MB | 品質較穩、顯存壓力小 |
| `large-v3 + batch 2` | 176 秒 |          100% |  5009 MB | 這台機器可穩定完成 |
| `large-v3 + batch 1` | 179 秒 |          100% |  4497 MB | 顯存略降，但速度沒有更快 |

這批資料的結論：

1. `large-v3 + float16 + batch_size 2` 在這台 `RTX 3050 6GB` 上可穩定完成，且速度與 `medium + batch_size 2` 幾乎相同。
2. `large-v3` 比 `medium` 多吃大約 `2GB` 顯存，但在這台機器上仍落在可接受範圍內。
3. 把 `batch_size` 從 `2` 降到 `1`，只省下約 `500MB` 顯存，卻沒有帶來速度優勢，因此不適合作為日常預設。
4. 因為流程中還包含 VAD、alignment、I/O 與模型切換，所以 `nvidia-smi` 的平均 GPU 使用率不會全程維持高檔；但在 transcription 核心階段，GPU 會頻繁衝到 `95%~100%`。

因此目前這台 `RTX 3050 6GB` 的建議日常配置改為：

```bash
--model large-v3
--device cuda
--compute_type float16
--batch_size 2
```

### Intel／AMD 核顯

標準 WhisperX CUDA 安裝不會直接使用 Intel 或 AMD 核顯，因此在這套操作中應視為 CPU 模式。

建議：

```bash
whisperx "audio.m4a" \
  --model small \
  --language zh \
  --device cpu \
  --compute_type int8 \
  --batch_size 2 \
  --output_dir transcript/
```

若 CPU 與記憶體較好，可以嘗試：

```bash
--model medium
--device cpu
--compute_type int8
--batch_size 2
```

但速度會明顯比 NVIDIA GPU 慢。

CPU／核顯環境不建議用 large-v3 作為日常設定，除非可以接受很長的等待時間。

### 硬體建議摘要

| 硬體           | 模型                | compute type | batch size |
| ------------ | ----------------- | ------------ | ---------: |
| RTX 3080     | large-v3          | float16      |  8，OOM 改 4 |
| RTX 3050 8GB | large-v3          | float16／int8 |        2～4 |
| RTX 3050 6GB | large-v3          | float16      |          2 |
| RTX 3050 4GB | medium            | float16      |          2 |
| CPU／核顯       | small             | int8         |          2 |
| 高階 CPU、品質優先  | medium            | int8         |        1～2 |

降低記憶體需求的優先順序：

```text
先降低 batch size
→ 再改 compute_type int8
→ 最後才改用較小模型
```

其中降低 batch size 主要影響一次送進 GPU 的音訊片段數量。它不是同時並行處理多個檔案，而是讓單次推論打包更多或更少片段：

1. `batch size` 較大：通常較快，但更吃顯存。
2. `batch size` 較小：通常較省顯存，但不一定更快。

在這次 `RTX 3050 6GB` 的實測中，`large-v3` 將 `batch_size` 從 `2` 降為 `1`，顯存只下降約 `500MB`，總時間卻從 `176 秒` 增加到 `179 秒`，因此 `2` 仍是較好的日常值。

---

## 十、說話者編號與姓名判斷

pyannote 只做 diarization：

```text
誰在什麼時候講話
```

它不會理解逐字稿內容，也不知道姓名。

例如：

```text
SPEAKER_00：Arthur 沒有明確要求十五號完成。
SPEAKER_01：Michael，你那邊的測試進度如何？
```

可以再交給 ChatGPT，並同時提供：

1. 與會者名單。
2. 公司與職稱。
3. 誰主持會議。
4. 每人的主要工作領域。
5. 人名、公司名與技術詞彙表。
6. 會議議程。
7. 已知某幾段的實際講者。

先要求 ChatGPT 只產生對照表：

```text
SPEAKER_00 → Michael，信心高
SPEAKER_01 → Alexis，信心中
SPEAKER_02 → 賴文海，信心高
SPEAKER_03 → Lily，信心中
```

人工確認後，才把 Speaker 標籤套用到全文。

本次錄音人工確認的結果為：

```text
SPEAKER_00 = Michael
SPEAKER_01 = Alexis
SPEAKER_02 = 賴文海／海哥
SPEAKER_03 = Lily
```

這份對照只適用於這支錄音。

下一支錄音的 `SPEAKER_00` 可能變成其他人，Speaker 編號不能跨檔案固定沿用。

---

## 十一、詞彙表的用途

詞彙表適合修正：

* 人名
* 公司名
* 客戶名
* 專案名
* Azure 服務
* 技術縮寫
* 中英混講造成的同音錯誤

例如：

```yaml
terms:
  - canonical: Azure
    variants:
      - A9
      - Agil

  - canonical: VNet
    variants:
      - LAN
      - V NET

  - canonical: 圓興
    variants:
      - 原心
      - 原新

  - canonical: Wayne
    variants:
      - 問
```

詞彙表可用於：

1. WhisperX 轉錄後的文字校正。
2. ChatGPT 推測 Speaker 姓名。
3. 產生會議記錄。
4. 後續建立知識庫。

詞彙表不應直接無條件取代所有相似文字。要結合上下文，避免把普通詞錯改成專有名詞。

---

## 十二、從 WhisperX 到會議記錄的建議流程

```text
MP4／M4A
   ↓
WhisperX large-v3 原始辨識
   ↓
pyannote 分離 Speaker
   ↓
保存原始 JSON／TXT
   ↓
提供與會者名單與詞彙表
   ↓
ChatGPT 推測 Speaker 姓名
   ↓
人工確認 Speaker 對照
   ↓
ChatGPT 校正錯字、專有名詞與段落
   ↓
產生正式會議記錄
```

建議至少保留三份資料：

```text
meeting.raw.json
meeting.raw.txt
meeting.corrected.md
```

不要讓 LLM 校正版直接覆蓋 WhisperX 原始輸出。

若後續要交給 ChatGPT 或其他 LLM 整理內容，建議一律保留：

```text
原始 JSON
原始 TXT
人工確認過的 Speaker 對照表
```

正式會議記錄中的下列內容應回查原始稿或音訊：

* 決策
* 負責人
* 金額
* 日期
* 期限
* 合約
* 股權
* 支付與請款
* 對外承諾

---

## 十三、這次實測得到的重要結論

### 1. WhisperX 的中文技術會議辨識品質不錯

本次 `large-v3` 在中文技術會議中，對下列內容的辨識整體優於 NotebookLM 的原始逐字稿：

* 英文技術名詞
* Azure
* VM
* VPN
* Docker
* Kubernetes
* Oracle
* PostgreSQL
* MySQL
* 人名與產品名

但仍會出現：

```text
Azure → A9
駐點 → 注點
兼著做 → 堅持做
向心力 → 相心力
正式 email → 政治 email
```

因此仍需要詞彙表與上下文校正。

### 2. WhisperX 可能漏掉部分句子

本次 WhisperX 在愛買議題開頭漏掉一段背景說明。

因此即使整體辨識品質好，也不能假設逐字稿百分之百完整。

重要會議可考慮：

* 使用另一個 ASR 產生第二份逐字稿交叉比對。
* 或抽查關鍵段落音訊。
* 對決議、金額、時程做人工查核。

### 3. 說話者分離並不完美

常見問題：

* 短句被併入前一位講者。
* 同一個人被拆成兩個 Speaker。
* 兩人同時說話時容易錯。
* 「嗯」「對」「好」等短回應容易歸錯人。
* 混合麥克風、遠端壓縮和回音會降低準確度。

所以 Speaker 姓名推測必須人工確認。

### 4. 有名字不代表逐字稿比較準

另一套工具若已套用名單與詞彙表，看起來會比 WhisperX 流暢，但這可能是後處理優勢，不一定代表原始 ASR 聽得更準。

應分開評估：

```text
原始語音辨識品質
說話者切分品質
詞彙校正品質
語意修復品質
```

### 5. 會議記錄不應只依賴單一稿件

最佳做法：

```text
完整度較高的逐字稿作為主稿
WhisperX 原始稿作為查核
關鍵爭議處回聽音訊
```

如果有正式會議記錄需求，應把 WhisperX 視為高品質初稿與查核素材，而不是最終法律或商務文本。

---

## 十四、常見錯誤處理

### `whisperx: command not found`

原因：虛擬環境沒有啟用。

```bash
source "$HOME/.venvs/whisperx/bin/activate"
```

或：

```bash
"$HOME/.venvs/whisperx/bin/whisperx" --help
```

### `CUDA available: False`

可能原因：

* Windows NVIDIA 驅動未正確安裝。
* WSL 無法看到 GPU。
* 安裝到 CPU 版 PyTorch。
* 虛擬環境不是原本安裝 WhisperX 的環境。

依序檢查：

```bash
nvidia-smi
which python
which whisperx
python -c "import torch; print(torch.cuda.is_available())"
```

### `403 Forbidden`／`GatedRepoError`

這不是 CUDA 錯誤，而是 Hugging Face 授權問題。

檢查：

1. 是否在模型頁接受條款。
2. Token 是否為 Read。
3. Token 和瀏覽器是否為同一帳號。
4. `HF_TOKEN` 是否正確。
5. `hf auth whoami` 是否顯示正確帳號。

### `403 Forbidden` 但明明已經有 token

最常見不是 token 格式錯，而是：

1. Hugging Face 網站上的模型條款尚未按下接受。
2. 瀏覽器登入帳號與 token 所屬帳號不是同一個。
3. shell 裡的 `HF_TOKEN` 與你以為設定的值不是同一個。

### `gradient_checkpointing ... deprecated`

這是 Transformers 套件的棄用警告。

若後續仍正常顯示：

```text
Performing alignment
Performing diarization
```

通常可以先忽略，不是本次執行失敗的原因。

### CUDA out of memory

依序調整：

```text
batch 8 → batch 4 → batch 2 → batch 1
```

再不行：

```text
float16 → int8
```

再不行：

```text
large-v3 → medium → small
```

---

## 十五、建立隨時可用的命令

建立包裝程式：

```bash
mkdir -p "$HOME/bin"

cat > "$HOME/bin/whisperx-local" <<'EOF'
#!/usr/bin/env bash
exec "$HOME/.venvs/whisperx/bin/whisperx" "$@"
EOF

chmod +x "$HOME/bin/whisperx-local"
```

確保 `~/bin` 在 PATH：

```bash
grep -qxF 'export PATH="$HOME/bin:$PATH"' "$HOME/.bashrc" ||
    echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"

source "$HOME/.bashrc"
```

之後不用啟用 virtual environment：

```bash
whisperx-local "$HOME/audio/meeting.m4a" \
  --model large-v3 \
  --language zh \
  --device cuda \
  --compute_type float16 \
  --batch_size 8 \
  --output_dir "$HOME/transcript/"
```

如果你只偶爾使用 WhisperX，直接保留完整路徑也可以；建立 `whisperx-local` 只是為了減少重複輸入。

---

## 十六、保存目前可用環境

WhisperX、PyTorch、pyannote、Transformers 等套件更新後，可能發生相容性變化。

目前環境已經成功，建議立刻保存版本：

```bash
source "$HOME/.venvs/whisperx/bin/activate"

python --version
pip show whisperx torch pyannote.audio transformers
pip freeze > "$HOME/whisperx-requirements-20260613.txt"
```

也可保存完整診斷：

```bash
{
    date
    uname -a
    python --version
    nvidia-smi
    ffmpeg -version | head -n 1
    pip show whisperx torch pyannote.audio transformers
} > "$HOME/whisperx-environment-20260613.txt"
```

若未來更新後失敗，可以根據這份記錄還原或比較套件版本。

在目前環境能正常工作的情況下，不應為了追求最新版而隨意升級所有套件。

若未來要重新整理這份筆記，建議優先更新：

1. `pip show whisperx torch pyannote.audio transformers`
2. `whisperx --help`
3. 一次不帶 diarization 的實測結果
4. 一次帶 diarization 的實測結果
