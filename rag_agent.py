"""
RAG Agent 模块
串联 检索 → 增强 → 生成 全链路，支持命令行交互。
"""

from api_client import call_deepseek
from vector_store import create_vector_store, search, get_collection_stats

# ============================================================
# Prompt 模板
# ============================================================
SYSTEM_PROMPT = """你是楚雄师范学院校园智能助手，专门为在校学生提供准确的校园信息服务。

你的回答必须严格遵守以下规则：
1. 只能基于下方【参考文档】中的内容回答问题
2. 如果【参考文档】中没有相关信息，请明确说"抱歉，我目前的知识库还没有收录这个问题的相关信息。你可以咨询辅导员或相关部门的老师，我后续会补充更多知识内容。"
3. 禁止编造、推测或引用文档中没有的数据和事实——如果你引用了文档中没有的数字或事实，这属于严重错误
4. 回答要简洁清晰、对同学友好，用口语化但专业的语气
5. 如果多条文档信息冲突，优先采用第一条"""

PROMPT_TEMPLATE = """【参考文档】
{context}

【用户问题】
{question}

请基于以上参考文档回答用户的问题。"""


def _format_sources(results: list[dict]) -> list[str]:
    """从检索结果的 metadata 中提取文件名，去重。"""
    sources = []
    seen = set()
    for r in results:
        meta = r.get("metadata") or {}
        source = meta.get("source", "")
        if source and source not in seen:
            sources.append(source)
            seen.add(source)
    return sources


def _format_chat_history(history_messages: list) -> str:
    """将多轮对话历史格式化为文本。只保留最近 3 轮（6 条消息）。"""
    if not history_messages:
        return ""
    recent = history_messages[-6:]  # 最近 3 轮 = 最多 6 条
    lines = []
    for msg in recent:
        role = "用户" if msg.get("role") == "user" else "助手"
        content = msg.get("content", "")
        lines.append(f"{role}：{content}")
    return "\n".join(lines)


class RAGAgent:
    """RAG 问答 Agent：检索 → 增强 → 生成。"""

    def __init__(self, collection):
        self.collection = collection
        self.system_prompt = SYSTEM_PROMPT

    def _build_prompt(self, question: str, docs: list[dict], chat_history: str = "") -> str:
        """将检索到的文档拼接为上下文，组装最终 Prompt。"""
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = (doc.get("metadata") or {}).get("source", "未知来源")
            context_parts.append(
                f"[文档{i}]（来源：{source}）\n{doc['content']}"
            )
        context = "\n\n".join(context_parts) if context_parts else "（未找到相关文档）"

        # 如果有对话历史，加在最前面
        final_prompt = PROMPT_TEMPLATE.format(context=context, question=question)
        if chat_history:
            final_prompt = (
                f"【对话历史】\n{chat_history}\n\n{final_prompt}"
            )
        return final_prompt

    def ask(self, question: str, n_results: int = 3, chat_history: list = None) -> tuple[str, list[dict], list[str]]:
        """
        执行一次 RAG 问答。

        参数:
            question: 用户问题
            n_results: 检索结果数量
            chat_history: Gradio 风格的历史消息列表 [{"role":"user","content":...}, ...]

        返回:
            (answer, retrieved_docs, sources): 回答文本, 检索到的文档列表, 文档来源列表
        """
        # 1. 检索相关文档
        retrieved_docs = search(self.collection, question, n_results=n_results)

        # 2. 提取对话历史
        history_text = _format_chat_history(chat_history) if chat_history else ""

        # 3. 构建带上下文的 Prompt
        prompt = self._build_prompt(question, retrieved_docs, history_text)

        # 4. 调用大模型生成回答
        try:
            answer = call_deepseek(prompt, system_prompt=self.system_prompt)
        except Exception as e:
            answer = f"抱歉，调用 AI 服务时出现错误：{e}\n请稍后重试。"

        # 5. 提取来源
        sources = _format_sources(retrieved_docs)

        return answer, retrieved_docs, sources


# ============================================================
# 命令行交互
# ============================================================
def run_cli():
    """命令行交互式 RAG 对话。"""
    print("=" * 56)
    print("  🏫 楚雄师范学院校园智能助手（RAG CLI）")
    print("  输入问题即可对话，输入 quit / exit / q 退出")
    print("=" * 56)

    # 初始化向量库和 Agent
    collection = create_vector_store()
    stats = get_collection_stats(collection)
    if stats["document_count"] == 0:
        print("\n⚠️  向量库为空，请先运行 build_index.py 构建索引！")
        return

    print(f"\n已加载 {stats['document_count']} 条知识片段")
    agent = RAGAgent(collection)

    chat_history = []  # 多轮对话历史

    while True:
        try:
            question = input("\n🧑 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("再见！")
            break

        answer, docs, sources = agent.ask(question, n_results=3, chat_history=chat_history)

        print(f"\n🤖 助手: {answer}")

        if sources:
            print(f"\n📚 参考来源: {', '.join(sources)}")

        # 记录对话历史（用于多轮对话）
        chat_history.append({"role": "user", "content": question})
        chat_history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    run_cli()
