"""文案智能解析 — 将用户输入拆分为场景列表"""
import re


def parse_to_slides(content: str, title: str = "") -> list[dict]:
    """
    将文案按段落拆分为场景

    规则:
    1. `# 标题` → title 场景
    2. `## 小标题` → 带标题的 bullets 场景
    3. `![keyword]` → image 场景
    4. 普通段落 → bullets 场景
    5. 空行 → 场景分隔
    """
    slides = []
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    for para in paragraphs:
        lines = para.split("\n")
        first_line = lines[0]
        body = " ".join(lines[1:]).strip() if len(lines) > 1 else ""

        if first_line.startswith("# "):
            # 一级标题 → title 场景
            t = first_line[2:].strip()
            slides.append({
                "type": "title",
                "title": t,
                "text": body or t,
                "keywords": _extract_keywords(t + " " + body),
                "config": {},
            })

        elif first_line.startswith("## "):
            # 二级标题 → 带标题的 bullets
            subt = first_line[3:].strip()
            slides.append({
                "type": "bullets",
                "title": subt,
                "text": body or subt,
                "keywords": _extract_keywords(subt + " " + body),
                "config": {},
            })

        elif first_line.startswith("!["):
            # 图片场景: ![搜索关键词]
            m = re.match(r"!\[(.+)\]", first_line)
            if m:
                kw = m.group(1)
                slides.append({
                    "type": "image",
                    "title": "",
                    "text": body,
                    "keywords": [kw],
                    "config": {"imageQuery": kw},
                })
            else:
                # Malformed ![ — treat as plain paragraph
                t = para[:50].replace("\n", " ")
                slides.append({
                    "type": "bullets",
                    "title": t,
                    "text": para,
                    "keywords": _extract_keywords(para),
                    "config": {},
                })

        else:
            # 普通段落 → bullets
            t = para[:50].replace("\n", " ")
            slides.append({
                "type": "bullets",
                "title": t,
                "text": para,
                "keywords": _extract_keywords(para),
                "config": {},
            })

    # 如果没有 title 场景，自动添加一个
    has_title = any(s["type"] == "title" for s in slides)
    if not has_title:
        slides.insert(0, {
            "type": "title",
            "title": title or "未命名视频",
            "text": "",
            "keywords": _extract_keywords(title) if title else ["未命名"],
            "config": {},
        })

    # 最后添加片尾
    slides.append({
        "type": "outro",
        "title": "感谢观看",
        "text": "",
        "keywords": [],
        "config": {},
    })

    return slides


def _extract_keywords(text: str, max_kw: int = 5) -> list[str]:
    """提取关键词 (中文2-4字 / 英文3+字母)"""
    words = re.findall(r"[一-鿿]{2,4}|[a-zA-Z]{3,}", text)
    seen = set()
    keywords = []
    for w in sorted(words, key=len, reverse=True):
        if w.lower() not in seen:
            keywords.append(w)
            seen.add(w.lower())
        if len(keywords) >= max_kw:
            break
    return keywords if keywords else ["科技"]
