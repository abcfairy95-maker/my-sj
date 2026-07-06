"""
文档加载与切片模块
从 docs/ 目录加载 Markdown 文档，按固定长度切片。
"""

import os
import re


def load_documents(docs_dir: str = "docs") -> list[tuple[str, str]]:
    """
    加载指定目录下所有 .md 文件。
    
    参数:
        docs_dir: 文档目录路径
    
    返回:
        (文件名, 文件内容) 元组列表
    """
    docs = []
    if not os.path.isdir(docs_dir):
        raise FileNotFoundError(f"文档目录不存在: {docs_dir}")

    for filename in sorted(os.listdir(docs_dir)):
        if filename.endswith(".md"):
            filepath = os.path.join(docs_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                docs.append((filename, content))
    if not docs:
        raise ValueError(f"{docs_dir} 目录下没有找到 .md 文件")
    return docs


def split_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """
    将单篇长文本按字符数切分为多个重叠片段。
    优先在段落边界切分，避免在句子中间断开。
    
    参数:
        text: 输入文本
        chunk_size: 每个片段的目标字符数
        overlap: 相邻片段的重叠字符数
    
    返回:
        文本片段列表
    """
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]

        if end < text_len:
            last_newline = chunk.rfind("\n")
            if last_newline > chunk_size // 2:
                end = start + last_newline + 1
                chunk = text[start:end]

        cleaned = chunk.strip()
        if cleaned:
            chunks.append(cleaned)

        if end == text_len:
            break

        start = end - overlap
        if start >= text_len:
            break

    return chunks


def split_texts(documents: list[str], chunk_size: int = 300, overlap: int = 50) -> list[str]:
    all_chunks = []
    for doc in documents:
        all_chunks.extend(split_text(doc, chunk_size, overlap))
    return all_chunks


def load_and_split(docs_dir: str = "docs", chunk_size: int = 300, overlap: int = 50) -> tuple[list[str], list[str]]:
    """加载文档并切片，一步完成。返回 (chunks, sources)。"""
    doc_pairs = load_documents(docs_dir)
    all_chunks = []
    all_sources = []
    for filename, content in doc_pairs:
        chunks = split_text(content, chunk_size, overlap)
        all_chunks.extend(chunks)
        all_sources.extend([filename] * len(chunks))
    return all_chunks, all_sources


# ============================================================
# 快速自检
# ============================================================
if __name__ == "__main__":
    chunks, sources = load_and_split("docs")
    print(f"共加载 {len(chunks)} 个文本片段")
    if chunks:
        print(f"\n第一个片段前 120 字:\n{chunks[0][:120]}")
        print(f"来源: {sources[0]}")
        avg_len = sum(len(c) for c in chunks) // len(chunks)
        print(f"\n片段平均长度: {avg_len} 字")
        print(f"最短片段: {min(len(c) for c in chunks)} 字")
        print(f"最长片段: {max(len(c) for c in chunks)} 字")
