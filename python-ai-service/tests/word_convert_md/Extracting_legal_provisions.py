import re
import json
from markitdown import MarkItDown


def parse_law_text(text):
    lines = text.splitlines()

    result = {
        "title": "",
        "revision": "",
        "chapters": [],
        "all_articles": []
    }

    current_chapter = None
    current_article = None
    article_content_lines = []

    in_toc = False  # 是否在目录区域
    passed_toc = False  # 是否已经越过目录进入正文

    def flush_article():
        if current_article and article_content_lines:
            full_content = "\n".join(article_content_lines).strip()
            current_article["content"] = full_content
            sub_items = re.findall(r'（[一二三四五六七八九十]+）[^（]*', full_content)
            current_article["sub_items"] = [item.strip() for item in sub_items] if sub_items else []
            if current_chapter:
                current_chapter["articles"].append(current_article)
            result["all_articles"].append(current_article)

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 标题（第一条非空行）
        if not result["title"]:
            result["title"] = line
            continue

        # 修订信息
        if line.startswith('（') and ('修正' in line or '修订' in line):
            result["revision"] = line
            continue

        # 检测目录开始
        if "目　　录" in line or "目录" in line:
            in_toc = True
            continue

        # 检测章节（但跳过目录部分）
        chapter_match = re.match(r'^第[一二三四五六七八九十百]+章\s+', line)
        if chapter_match:
            # 如果当前在目录中，且该行以 > 开头（Markdown引用），则忽略
            if in_toc and line.startswith('>'):
                continue
            # 如果还没越过目录，但此行不以 > 开头，说明已进入正文，取消目录标记
            if in_toc:
                in_toc = False
                passed_toc = True
            # 闭合之前的条款
            if current_article:
                flush_article()
                current_article = None
                article_content_lines = []
            # 创建新章节
            current_chapter = {
                "title": line,
                "articles": []
            }
            result["chapters"].append(current_chapter)
            continue

        # 条款匹配
        article_match = re.match(r'^第[一二三四五六七八九十百]+条\s+', line)
        if article_match:
            if current_article:
                flush_article()
            current_article = {
                "number": article_match.group().strip(),
                "content": "",
                "sub_items": []
            }
            remaining = line[len(article_match.group()):].strip()
            article_content_lines = [remaining] if remaining else []
            continue

        # 普通行：如果当前在目录中但又不是章节标题，继续跳过（如空行、项目符号等）
        if in_toc:
            continue

        # 正文中的续行
        if current_article:
            article_content_lines.append(line)

    # 收尾
    if current_article:
        flush_article()

    return result

# ===== 使用示例 =====
if __name__ == "__main__":
    md = MarkItDown()
    # 替换为你的文件路径
    doc_path = r"C:\Users\hao.jingyu\Desktop\中华人民共和国商标法_20260626.docx"
    converted = md.convert(doc_path)
    # 注意：如果 converted.markdown 不是真正的 Markdown，就用 converted.text_content
    # 这里使用 text_content（纯文本）
    md_text = converted.text_content

    parsed = parse_law_text(md_text)
    print(json.dumps(parsed, ensure_ascii=False, indent=2))