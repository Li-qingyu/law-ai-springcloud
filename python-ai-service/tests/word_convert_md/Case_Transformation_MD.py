#!/usr/bin/env python3
"""
使用 Marker Python API 将 PDF 转换为 Markdown，
并从裁判文书中提取结构化字段，输出 JSON。
"""

import os
import re
import json
from pathlib import Path
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# ============================================================
# 1. 从 Markdown 文本中提取结构化字段（复用之前的函数）
# ============================================================
def extract_fields(md_text: str) -> dict:
    """
    从裁判文书 Markdown 中提取字段。
    返回字典包含：title, keywords, basic_facts, court_reason, holding,
    related_laws, first_instance, second_instance
    """
    lines = md_text.splitlines()
    # 去除空行
    lines = [ln.strip() for ln in lines if ln.strip()]
    if not lines:
        return {}

    # 提取标题：第一个 # 标题或第一行
    title = lines[0]
    title = re.sub(r'^#+\s*', '', title).strip()
    if not title:
        title = lines[0]

    # 章节标记（支持 '关键词' 或 '## 关键词' 等）
    section_patterns = {
        "keywords": r"(?:##\s*)?关键词",
        "basic_facts": r"(?:##\s*)?基本案情",
        "court_reason": r"(?:##\s*)?裁判理由",
        "holding": r"(?:##\s*)?裁判要旨",
        "related_laws": r"(?:##\s*)?关联索引"
    }

    data = {
        "title": title,
        "keywords": "",
        "basic_facts": "",
        "court_reason": "",
        "holding": "",
        "related_laws": "",
        "first_instance": "",
        "second_instance": ""
    }

    current_field = None
    content_lines = []

    # 遍历行（从第二行开始，因为第一行作为标题）
    for line in lines[1:]:
        matched = False
        for field, pattern in section_patterns.items():
            if re.match(pattern, line, re.IGNORECASE):
                # 保存上一字段内容
                if current_field and content_lines:
                    data[current_field] = "\n".join(content_lines).strip()
                # 切换到新字段
                current_field = field
                content_lines = []
                # 行中剩余内容作为该字段的第一行内容
                remaining = re.sub(pattern, '', line, flags=re.IGNORECASE).strip()
                if remaining:
                    content_lines.append(remaining)
                matched = True
                break

        if not matched:
            if current_field:
                content_lines.append(line)
            # 否则忽略（例如页眉、页码等）

    # 保存最后一个字段
    if current_field and content_lines:
        data[current_field] = "\n".join(content_lines).strip()

    # 提取案号（从全文末尾查找）
    full_text = md_text
    first_match = re.search(r'一审[：:]\s*([^\n]+)', full_text)
    second_match = re.search(r'二审[：:]\s*([^\n]+)', full_text)
    if first_match:
        data["first_instance"] = first_match.group(1).strip()
    if second_match:
        data["second_instance"] = second_match.group(1).strip()

    # 如果没找到，尝试从最后几行找
    if not data["first_instance"]:
        last_lines = full_text.splitlines()[-5:]
        for ln in last_lines:
            if "一审" in ln:
                data["first_instance"] = ln.strip()
                break
    if not data["second_instance"]:
        last_lines = full_text.splitlines()[-5:]
        for ln in last_lines:
            if "二审" in ln:
                data["second_instance"] = ln.strip()
                break

    return data


# ============================================================
# 2. 使用 Marker API 转换 PDF
# ============================================================
def convert_pdf_to_markdown(pdf_path: str) -> str:
    """
    使用 Marker 的 Python API 将 PDF 转换为 Markdown 文本。
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    print("正在初始化 Marker 转换器（首次运行将下载模型）...")
    # 创建模型字典（包含必要的模型）
    model_dict = create_model_dict()
    converter = PdfConverter(
        artifact_dict=model_dict,
        # 可在此传入自定义配置，例如：
        # config=config_dict,
    )

    print(f"正在转换 PDF: {pdf_path} ...")
    rendered = converter(pdf_path)
    # 提取文本（Markdown）和元数据
    text, metadata, images = text_from_rendered(rendered)

    print("转换完成。")
    return text


# ============================================================
# 3. 主流程
# ============================================================
def main(pdf_path: str, output_json_path: str = None):
    try:
        # 1. 转换 PDF -> Markdown
        md_text = convert_pdf_to_markdown(pdf_path)

        # 2. 提取结构化字段
        data = extract_fields(md_text)

        # 3. 输出 JSON（终端）
        print("\n========== 提取结果 ==========")
        print(json.dumps(data, ensure_ascii=False, indent=2))

        # 4. 保存 JSON 文件
        if output_json_path is None:
            # 默认保存到 PDF 同目录，文件名相同，扩展名 .json
            pdf_name = Path(pdf_path).stem
            output_json_path = Path(pdf_path).parent / f"{pdf_name}.json"
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nJSON 已保存至: {output_json_path}")

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        raise


# ============================================================
# 4. 命令行入口
# ============================================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python extract_with_marker_api.py <pdf_file_path> [output_json_path]")
        sys.exit(1)

    pdf_file = sys.argv[1]
    json_file = sys.argv[2] if len(sys.argv) > 2 else None
    main(pdf_file, json_file)