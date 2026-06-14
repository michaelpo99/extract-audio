#!/usr/bin/env python3
import argparse
import importlib.metadata
import importlib.util
import os
import platform
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

DEFAULT_MODEL = "Qwen/Qwen2.5-3B-Instruct"
DEFAULT_OUTPUT_DIR = "formatted"
SUPPORTED_EXTENSIONS = {".txt", ".md"}
EXCLUDED_INPUT_NAMES = {"_run-summary.txt", "_environment.txt"}

SYSTEM_PROMPT = """你是一個專業的繁體中文文章編輯與排版助理。你的任務是將逐字稿整理為台灣習慣的繁體中文 Markdown。

必須嚴格遵守以下規則：
1. 【忠於原文】絕對不要重寫、增加或重新闡釋原文內容，不要添加講者沒有說的話。
2. 【標點與分段】為原始文字加上適當標點，並根據語意自然停頓切分段落。
3. 【標題】只有在主題自然切換時，才加上簡潔的 Markdown 標題；標題不得發明原文沒有的結論。
4. 【台灣繁體化】將簡體字與大陸用語轉為台灣常見的繁體中文與慣用語。
5. 【禁止雜訊】不要輸出英文說明、分隔線、程式碼區塊標記或任何與正文無關的字樣。
6. 【僅輸出結果】直接輸出整理後的 Markdown 內容。"""

REPAIR_PROMPT = """你是一個嚴格的繁體中文逐字稿修稿助理。請根據「原始逐字稿」檢查並修正「整理草稿」。

必須嚴格遵守以下規則：
1. 不得新增原始逐字稿沒有的資訊。
2. 必須改為台灣常用繁體中文，避免簡繁混雜。
3. 不得混入英文單字、英文句子、分隔線或程式碼區塊標記。
4. 修正明顯的語音辨識錯字與不自然斷句。
5. 只在主題非常明確時才加標題；若全文主題單一，可以不加標題。
6. 最終只輸出可直接存檔的 Markdown 正文。"""

BUILTIN_REPLACEMENTS = {
    "POA": "PUA",
    "poa": "PUA",
    "AIP": "IP",
    "aip": "IP",
    "物理资料": "物料資料",
    "物理資料": "物料資料",
    "攻深入局": "躬身入局",
    "孤身入局": "躬身入局",
    "权权庶民": "權、術、名、地、閒、錢",
    "權權庶民": "權、術、名、地、閒、錢",
    "五大能開店": "武大郎開店",
    "五大能开店": "武大郎開店",
    "預支差": "預製菜",
    "预支差": "預製菜",
    "偏西西": "拼夕夕",
}


class UserFacingError(Exception):
    pass


@dataclass
class RuntimeInfo:
    python_version: str
    torch_version: str
    transformers_version: str
    cuda_available: bool
    cuda_runtime: str
    gpu_name: str
    gpu_vram_mb: str
    import_error: str


@dataclass
class LoadedModel:
    tokenizer: object
    model: object
    device: str
    dtype_name: str


def load_opencc_converter():
    if importlib.util.find_spec("opencc") is not None:
        from opencc import OpenCC  # type: ignore

        return OpenCC("s2twp")
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="使用本地 LLM 整理逐字稿為台灣繁體 Markdown。"
    )
    parser.add_argument("--file", help="處理單一檔案，僅接受 .txt 或 .md")
    parser.add_argument("--dir", help="處理指定目錄第一層的 .txt 與 .md")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="指定 Hugging Face 模型名稱")
    parser.add_argument("--replace-dict", help="載入外部強制替換詞彙表")
    parser.add_argument("--style-guide", help="載入額外 AI 參考指引檔")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="指定輸出子目錄名稱或路徑，預設為 formatted",
    )
    parser.add_argument("-f", "--force", action="store_true", help="覆蓋已存在的輸出檔")
    return parser


def detect_runtime_info() -> RuntimeInfo:
    python_version = platform.python_version()
    torch_version = ""
    transformers_version = ""
    cuda_available = False
    cuda_runtime = ""
    gpu_name = ""
    gpu_vram_mb = ""
    errors: List[str] = []

    try:
        torch_version = importlib.metadata.version("torch")
    except importlib.metadata.PackageNotFoundError:
        pass
    except Exception as exc:
        errors.append(f"讀取 torch 版本失敗：{exc}")

    try:
        transformers_version = importlib.metadata.version("transformers")
    except importlib.metadata.PackageNotFoundError:
        pass
    except Exception as exc:
        errors.append(f"讀取 transformers 版本失敗：{exc}")

    if importlib.util.find_spec("torch") is not None:
        try:
            import torch  # type: ignore

            cuda_available = bool(torch.cuda.is_available())
            cuda_runtime = str(getattr(torch.version, "cuda", "") or "")
            if cuda_available:
                gpu_name = str(torch.cuda.get_device_name(0))
                props = torch.cuda.get_device_properties(0)
                gpu_vram_mb = str(int(props.total_memory // (1024 * 1024)))
        except Exception as exc:
            errors.append(f"檢查 torch/CUDA 失敗：{exc}")

    return RuntimeInfo(
        python_version=python_version,
        torch_version=torch_version,
        transformers_version=transformers_version,
        cuda_available=cuda_available,
        cuda_runtime=cuda_runtime,
        gpu_name=gpu_name,
        gpu_vram_mb=gpu_vram_mb,
        import_error="; ".join(errors),
    )


def resolve_input_files(args: argparse.Namespace) -> Tuple[List[Path], Path, str]:
    if args.file and args.dir:
        raise UserFacingError("錯誤：--file 與 --dir 不可同時指定。")

    if args.file:
        file_path = Path(args.file).expanduser().resolve()
        validate_input_file(file_path)
        return [file_path], file_path.parent, str(file_path)

    scan_dir = Path(args.dir or ".").expanduser().resolve()
    if not scan_dir.is_dir():
        raise UserFacingError(f"錯誤：目錄不存在：{scan_dir}")

    files = []
    for path in sorted(scan_dir.iterdir()):
        if not path.is_file():
            continue
        if should_skip_input(path, scan_dir / DEFAULT_OUTPUT_DIR):
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)

    return files, scan_dir, str(scan_dir)


def validate_input_file(path: Path) -> None:
    if not path.exists():
        raise UserFacingError(f"錯誤：檔案不存在：{path}")
    if not path.is_file():
        raise UserFacingError(f"錯誤：不是檔案：{path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise UserFacingError(f"錯誤：不支援的副檔名：{path.suffix or '<none>'}")


def should_skip_input(path: Path, default_output_dir: Path) -> bool:
    if path.name in EXCLUDED_INPUT_NAMES:
        return True
    if path.name.startswith("."):
        return True
    try:
        path.relative_to(default_output_dir)
        return True
    except ValueError:
        return False


def resolve_output_dir(args: argparse.Namespace, base_dir: Path) -> Path:
    output_value = args.output_dir
    candidate = Path(output_value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    if candidate.parts and len(candidate.parts) > 1:
        return (Path.cwd() / candidate).resolve()
    return (base_dir / output_value).resolve()


def load_replace_dict(path_str: Optional[str]) -> Dict[str, str]:
    if not path_str:
        return {}

    path = Path(path_str).expanduser().resolve()
    if not path.is_file():
        raise UserFacingError(f"錯誤：替換詞彙表不存在：{path}")

    replacements: Dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=>" not in line:
                raise UserFacingError(
                    f"錯誤：替換詞彙表格式錯誤：{path}:{line_no}: {raw_line.rstrip()}"
                )
            source, target = [part.strip() for part in line.split("=>", 1)]
            if not source or not target:
                raise UserFacingError(
                    f"錯誤：替換詞彙表格式錯誤：{path}:{line_no}: {raw_line.rstrip()}"
                )
            replacements[source] = target
    return replacements


def load_style_guide(path_str: Optional[str]) -> str:
    if not path_str:
        return ""

    path = Path(path_str).expanduser().resolve()
    if not path.is_file():
        raise UserFacingError(f"錯誤：style guide 不存在：{path}")
    return path.read_text(encoding="utf-8").strip()


def apply_replacements(content: str, replacements: Dict[str, str]) -> str:
    for source, target in replacements.items():
        content = content.replace(source, target)
    return content


def normalize_transcript_text(content: str, converter) -> str:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if converter is not None:
        normalized = converter.convert(normalized)
    return normalized


def derive_title_hint(input_path: Path) -> str:
    stem = input_path.stem.strip()
    if not stem:
        return ""
    if "#" in stem:
        return ""
    if re.search(r"[A-Za-z]{3,}", stem):
        return ""
    if not re.search(r"[\u4e00-\u9fff]", stem):
        return ""
    return stem[:30]


def build_messages(content: str, style_guide: str, title_hint: str) -> List[Dict[str, str]]:
    user_parts = [
        "以下是原始逐字稿：",
        "---",
        content,
        "---",
    ]
    if title_hint:
        user_parts.extend(["", f"檔名主題提示：{title_hint}"])
    if style_guide:
        user_parts.extend(
            [
                "",
                "以下是額外參考規則，僅在不違反原文的前提下使用：",
                style_guide,
            ]
        )
    user_parts.append("")
    user_parts.append("請直接輸出校正與排版後的台灣繁體中文 Markdown 內容。")
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(user_parts)},
    ]


def build_repair_messages(
    original_content: str, draft: str, style_guide: str, title_hint: str
) -> List[Dict[str, str]]:
    user_parts = [
        "以下是原始逐字稿：",
        "---",
        original_content,
        "---",
        "",
        "以下是整理草稿：",
        "---",
        draft,
        "---",
    ]
    if title_hint:
        user_parts.extend(["", f"檔名主題提示：{title_hint}"])
    if style_guide:
        user_parts.extend(
            [
                "",
                "以下是額外參考規則，僅在不違反原文的前提下使用：",
                style_guide,
            ]
        )
    user_parts.extend(
        [
            "",
            "請修正草稿中的簡繁混用、英文混入、分隔線、錯字與段落問題，直接輸出最終 Markdown。",
        ]
    )
    return [
        {"role": "system", "content": REPAIR_PROMPT},
        {"role": "user", "content": "\n".join(user_parts)},
    ]


def clean_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    lines = [line for line in text.splitlines() if line.strip() not in {"---", "***"}]
    while lines and is_trailing_note(lines[-1]):
        lines.pop()
    return "\n".join(lines).strip()


def is_trailing_note(line: str) -> bool:
    normalized = line.strip()
    if not normalized:
        return False
    keywords = ("完成", "校正", "排版", "繁體", "修正")
    return len(normalized) < 50 and any(keyword in normalized for keyword in keywords)


def load_model(model_name: str) -> LoadedModel:
    try:
        import torch  # type: ignore
    except ModuleNotFoundError as exc:
        raise UserFacingError(
            "錯誤：缺少 torch。請先在目標 Python 環境安裝 torch。"
        ) from exc

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    except ModuleNotFoundError as exc:
        raise UserFacingError(
            "錯誤：缺少 transformers。請先在目標 Python 環境安裝 transformers。"
        ) from exc

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if not hasattr(tokenizer, "apply_chat_template"):
            raise UserFacingError(
                f"錯誤：模型 tokenizer 不支援 chat template：{model_name}"
            )
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        model = AutoModelForCausalLM.from_pretrained(model_name, dtype=dtype)
        for attr in ("temperature", "top_p", "top_k"):
            if hasattr(model.generation_config, attr):
                setattr(model.generation_config, attr, None)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda":
            model = model.to(device)
        return LoadedModel(
            tokenizer=tokenizer,
            model=model,
            device=device,
            dtype_name="float16" if device == "cuda" else "float32",
        )
    except UserFacingError:
        raise
    except Exception as exc:
        hint = ""
        lower = str(exc).lower()
        if "401" in lower or "403" in lower or "gated" in lower or "token" in lower:
            hint = "；若此模型需要授權，請確認 HF_TOKEN 或 Hugging Face CLI 登入狀態"
        raise UserFacingError(f"錯誤：模型載入失敗：{model_name}: {exc}{hint}") from exc


def generate_response(loaded_model: LoadedModel, messages: List[Dict[str, str]]) -> str:
    model = loaded_model.model
    tokenizer = loaded_model.tokenizer

    try:
        prompt_text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    except Exception as exc:
        raise UserFacingError(f"錯誤：無法建立模型對話模板：{exc}") from exc

    try:
        import torch  # type: ignore
    except ModuleNotFoundError as exc:
        raise UserFacingError("錯誤：執行時找不到 torch。") from exc

    model_inputs = tokenizer([prompt_text], return_tensors="pt").to(model.device)
    with torch.no_grad():
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=4096,
            do_sample=False,
        )

    generated_ids = [
        output_ids[len(input_ids) :]
        for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return clean_response(response)


def should_repair_output(draft: str, converter) -> bool:
    if not draft:
        return True
    if re.search(r"[A-Za-z]{4,}", draft):
        return True
    if "\n---\n" in draft or draft.startswith("---") or draft.endswith("---"):
        return True
    paragraphs = [part.strip() for part in draft.split("\n\n") if part.strip()]
    if len(paragraphs) < 2 and len(draft) > 500:
        return True
    if converter is not None and converter.convert(draft) != draft:
        return True
    return False


def process_text(
    content: str,
    loaded_model: LoadedModel,
    style_guide: str,
    title_hint: str,
    converter,
) -> str:
    draft = generate_response(loaded_model, build_messages(content, style_guide, title_hint))
    if converter is not None:
        draft = converter.convert(draft)
    draft = clean_response(draft)

    if should_repair_output(draft, converter):
        repaired = generate_response(
            loaded_model,
            build_repair_messages(content, draft, style_guide, title_hint),
        )
        if converter is not None:
            repaired = converter.convert(repaired)
        repaired = clean_response(repaired)
        if repaired:
            draft = repaired

    if title_hint and not re.search(r"^\s{0,3}#{1,6}\s", draft, flags=re.MULTILINE):
        draft = f"# {title_hint}\n\n{draft}".strip()

    return draft


def format_bool(value: bool) -> str:
    return "true" if value else "false"


def print_run_config(
    source_label: str,
    file_count: int,
    output_dir: Path,
    model_name: str,
    runtime_info: RuntimeInfo,
    replace_dict_path: Optional[str],
    style_guide_path: Optional[str],
    force: bool,
    device: str,
    dtype_name: str,
) -> None:
    print(f"[config] input={source_label}")
    print("[config] scan_depth=1")
    print("[config] file_types=.txt,.md")
    print(f"[config] files_found={file_count}")
    print(f"[config] output_dir={output_dir}")
    print(f"[config] model={model_name}")
    print(f"[config] device={device}")
    print(f"[config] dtype={dtype_name}")
    print(f"[config] cuda_available={format_bool(runtime_info.cuda_available)}")
    if runtime_info.gpu_name:
        print(f"[config] gpu={runtime_info.gpu_name}")
    print(f"[config] replace_dict={replace_dict_path or 'none'}")
    print(f"[config] style_guide={style_guide_path or 'none'}")
    print(f"[config] force={format_bool(force)}")


def write_summary_files(
    output_dir: Path,
    source_label: str,
    files: Sequence[Path],
    args: argparse.Namespace,
    runtime_info: RuntimeInfo,
    device: str,
    dtype_name: str,
    counts: Dict[str, int],
) -> None:
    now = datetime.now().astimezone()
    summary_lines = [
        f"timestamp={now.isoformat()}",
        f"cwd={Path.cwd()}",
        f"input={source_label}",
        "scan_depth=1",
        "file_types=.txt,.md",
        f"files_found={len(files)}",
        f"output_dir={output_dir}",
        f"model={args.model}",
        f"device={device}",
        f"dtype={dtype_name}",
        f"replace_dict={args.replace_dict or 'none'}",
        f"style_guide={args.style_guide or 'none'}",
        f"force={format_bool(args.force)}",
        f"success={counts['success']}",
        f"skipped={counts['skipped']}",
        f"failed={counts['failed']}",
    ]
    environment_lines = [
        f"timestamp={now.isoformat()}",
        f"cwd={Path.cwd()}",
        f"python_version={runtime_info.python_version}",
        f"torch_version={runtime_info.torch_version or 'missing'}",
        f"transformers_version={runtime_info.transformers_version or 'missing'}",
        f"cuda_available={format_bool(runtime_info.cuda_available)}",
        f"cuda_runtime={runtime_info.cuda_runtime or 'n/a'}",
        f"gpu_name={runtime_info.gpu_name or 'n/a'}",
        f"gpu_vram_mb={runtime_info.gpu_vram_mb or 'n/a'}",
        f"model={args.model}",
        f"device={device}",
        f"dtype={dtype_name}",
    ]
    if runtime_info.import_error:
        environment_lines.append(f"import_error={runtime_info.import_error}")

    (output_dir / "_run-summary.txt").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )
    (output_dir / "_environment.txt").write_text(
        "\n".join(environment_lines) + "\n", encoding="utf-8"
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        files, base_dir, source_label = resolve_input_files(args)
        if not files:
            raise UserFacingError(
                f"錯誤：找不到可處理檔案：{base_dir}（僅掃描第一層 .txt/.md）"
            )

        output_dir = resolve_output_dir(args, base_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        external_replacements = load_replace_dict(args.replace_dict)
        style_guide = load_style_guide(args.style_guide)
        runtime_info = detect_runtime_info()
        converter = load_opencc_converter()

        print(f"正在載入模型 {args.model}...", flush=True)
        loaded_model = load_model(args.model)
        print("模型載入完成。", flush=True)

        print_run_config(
            source_label=source_label,
            file_count=len(files),
            output_dir=output_dir,
            model_name=args.model,
            runtime_info=runtime_info,
            replace_dict_path=args.replace_dict,
            style_guide_path=args.style_guide,
            force=args.force,
            device=loaded_model.device,
            dtype_name=loaded_model.dtype_name,
        )
        print(f"[run] queued={len(files)}")

        counts = {"success": 0, "skipped": 0, "failed": 0}
        all_replacements = dict(BUILTIN_REPLACEMENTS)
        all_replacements.update(external_replacements)

        for index, input_path in enumerate(files, 1):
            output_path = output_dir / f"{input_path.stem}.md"
            if output_path.exists() and not args.force:
                print(f"[{index}/{len(files)}] skipped -> {output_path}")
                counts["skipped"] += 1
                continue

            print(f"[{index}/{len(files)}] processing {input_path.name}")
            try:
                raw_content = input_path.read_text(encoding="utf-8")
                processed_input = apply_replacements(raw_content, all_replacements)
                processed_input = normalize_transcript_text(processed_input, converter)
                title_hint = derive_title_hint(input_path)
                result = process_text(
                    processed_input,
                    loaded_model,
                    style_guide,
                    title_hint,
                    converter,
                )
                output_path.write_text(result + ("\n" if result and not result.endswith("\n") else ""), encoding="utf-8")
                print(f"[{index}/{len(files)}] done -> {output_path}")
                counts["success"] += 1
            except Exception as exc:
                print(f"[{index}/{len(files)}] failed -> {input_path.name}: {exc}")
                counts["failed"] += 1

        write_summary_files(
            output_dir=output_dir,
            source_label=source_label,
            files=files,
            args=args,
            runtime_info=runtime_info,
            device=loaded_model.device,
            dtype_name=loaded_model.dtype_name,
            counts=counts,
        )

        print(
            f"[summary] total={len(files)} success={counts['success']} "
            f"skipped={counts['skipped']} failed={counts['failed']}"
        )
        print(f"[summary] output_dir={output_dir}")
        return 0 if counts["failed"] == 0 else 1
    except UserFacingError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
