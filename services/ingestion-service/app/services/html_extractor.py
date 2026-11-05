from __future__ import annotations

from bs4 import BeautifulSoup, Tag
from app.domain.models import ContentBlock


REMOVE_TAGS = [
    "script", "style", "noscript", "nav", "footer", "header",
    "aside", "form", "button", "svg", "iframe"
]


def extract_html(html: str) -> tuple[str, list[ContentBlock]]:
    soup = BeautifulSoup(html, "html.parser")

    for selector in [
        "nav", "footer", "header", "aside", "script", "style",
        "noscript", "form", "button", "svg", "iframe",
        "[role=navigation]", "[role=banner]", "[role=contentinfo]"
    ]:
        for node in soup.select(selector):
            node.decompose()

    title = ""
    if soup.title and soup.title.get_text(strip=True):
        title = soup.title.get_text(" ", strip=True)

    root = soup.find("main") or soup.find("article") or soup.body or soup
    blocks: list[ContentBlock] = []
    heading_path: list[str] = []

    for node in root.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "li", "blockquote", "td", "th"],
        recursive=True,
    ):
        if not isinstance(node, Tag):
            continue
        text = node.get_text(" ", strip=True)
        if not text:
            continue

        if node.name and node.name.startswith("h") and len(node.name) == 2:
            level = int(node.name[1])
            heading_path = heading_path[: level - 1]
            heading_path.append(text)
            if not title and level == 1:
                title = text
            continue

        block_type = "code" if node.name == "pre" else (
            "list_item" if node.name == "li" else (
                "table_cell" if node.name in {"td", "th"} else "text"
            )
        )
        blocks.append(
            ContentBlock(
                heading_path=heading_path.copy(),
                block_type=block_type,
                text=text,
            )
        )

    if not title:
        h1 = root.find("h1")
        title = h1.get_text(" ", strip=True) if h1 else "Untitled document"

    return title, blocks
