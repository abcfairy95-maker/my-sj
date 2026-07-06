import gradio as gr
from vector_store import create_vector_store, get_collection_stats
from rag_agent import RAGAgent

collection = create_vector_store()
stats = get_collection_stats(collection)
agent = RAGAgent(collection)

print(f"[初始化] 向量库已就绪，共 {stats['document_count']} 条知识片段")

QUICK_TOPICS = [
    "📚 图书馆周末几点开门？",
    "🏠 宿舍晚上几点关门？",
    "🍜 食堂可以用现金吗？",
    "🚌 校园网怎么连接？",
    "🎓 国家奖学金申请条件？",
    "🏥 校医院在哪里？",
    "🔥 火把节放不放假？",
    "📖 毕业论文什么时候答辩？",
]

def respond(message, history):
    if not message or not message.strip():
        return "请输入你的问题。"
    try:
        answer, docs, sources = agent.ask(message, n_results=3, chat_history=history)
    except TypeError:
        dict_history = []
        for item in history or []:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                dict_history.append({"role": "user", "content": item[0]})
                dict_history.append({"role": "assistant", "content": item[1]})
        answer, docs, sources = agent.ask(message, n_results=3, chat_history=dict_history)
    if sources:
        tags = "  ".join([f"[{s.replace('.md','')}]" for s in sources])
        answer += f"\n\n📎 参考来源：{tags}"
    return answer

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');

:root {
    --brand: #6F4A8E;
    --brand-light: #A07FC0;
    --brand-bg: rgba(111,74,142,0.04);
    --bg: #F7F4F9;
    --card: #FFFFFF;
    --text: #1E1F23;
    --text2: #6A6E78;
    --text3: #ADB0B8;
    --border: #E8E3EC;
    --green: #789978;
    --green-bg: rgba(120,153,120,0.07);
    --shadow: 0 8px 32px rgba(111,74,142,0.05);
}

* { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
html, body { margin: 0; padding: 0; height: 100%; background: var(--bg) !important; overflow: hidden !important; }

.gradio-container {
    background: var(--bg) !important;
    height: 100vh !important;
    overflow: hidden !important;
    padding: 0 !important;
    position: relative !important;
}

/* ─── 背景动态 ─── */
@keyframes petalFall {
    0% { transform: translateY(-5vh) rotate(0deg) scale(0.3); opacity: 0; }
    8% { opacity: 0.12; }
    85% { opacity: 0.06; }
    100% { transform: translateY(105vh) rotate(540deg) scale(0.5); opacity: 0; }
}
.petal { position: fixed; top: -5vh; z-index: 0; pointer-events: none; }
.petal:nth-child(1) { left: 4%; animation: petalFall 18s linear infinite; font-size: 13px; }
.petal:nth-child(2) { left: 12%; animation: petalFall 22s linear infinite 2s; font-size: 11px; }
.petal:nth-child(3) { left: 22%; animation: petalFall 20s linear infinite 5s; font-size: 14px; }
.petal:nth-child(4) { left: 32%; animation: petalFall 26s linear infinite 1s; font-size: 12px; }
.petal:nth-child(5) { left: 42%; animation: petalFall 24s linear infinite 4s; font-size: 13px; }
.petal:nth-child(6) { left: 52%; animation: petalFall 19s linear infinite 3s; font-size: 10px; }
.petal:nth-child(7) { left: 62%; animation: petalFall 28s linear infinite 6s; font-size: 12px; }
.petal:nth-child(8) { left: 72%; animation: petalFall 17s linear infinite 7s; font-size: 11px; }
.petal:nth-child(9) { left: 82%; animation: petalFall 23s linear infinite 2.5s; font-size: 14px; }
.petal:nth-child(10) { left: 92%; animation: petalFall 21s linear infinite 5.5s; font-size: 12px; }

@keyframes floatMushroom {
    0%, 100% { transform: translate(0, 0); opacity: 0.025; }
    50% { transform: translate(8px, -10px); opacity: 0.045; }
}
.mushroom { position: fixed; bottom: 35px; z-index: 0; pointer-events: none; animation: floatMushroom 22s ease-in-out infinite; }
.mushroom:nth-child(11) { left: 230px; font-size: 26px; }
.mushroom:nth-child(12) { left: 280px; animation-delay: 3s; font-size: 20px; }
.mushroom:nth-child(13) { left: 340px; animation-delay: 6s; font-size: 24px; }
.mushroom:nth-child(14) { left: 400px; animation-delay: 9s; font-size: 22px; }
.mushroom:nth-child(15) { left: 460px; animation-delay: 12s; font-size: 28px; }
.mushroom:nth-child(16) { left: 520px; animation-delay: 15s; font-size: 18px; }

@keyframes spinSlow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.sun-deco { position: fixed; top: 45px; right: 35px; z-index: 0; pointer-events: none; font-size: 32px; opacity: 0.02; animation: spinSlow 50s linear infinite; }

@keyframes rockWave { 0%, 100% { transform: translateY(0) rotate(-3deg); opacity: 0.02; } 50% { transform: translateY(-4px) rotate(3deg); opacity: 0.035; } }
.rock-deco { position: fixed; bottom: 45px; right: 45px; z-index: 0; pointer-events: none; font-size: 36px; animation: rockWave 7s ease-in-out infinite; }

/* ─── 布局 ─── */
.app-root { display: flex !important; height: 100vh !important; overflow: hidden !important; position: relative !important; z-index: 1 !important; }

/* 侧边栏 20% */
.app-sidebar { width: 20% !important; min-width: 160px !important; max-width: 220px !important; flex-shrink: 0 !important; height: 100vh !important; display: flex !important; flex-direction: column !important; padding: 18px 10px 12px 14px !important; border-right: 1px solid var(--border) !important; overflow-y: auto !important; }
.sb-brand { font-family: 'Noto Sans SC', sans-serif; font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 1px; }
.sb-brand em { font-style: normal; color: var(--brand); }
.sb-desc { font-family: 'Noto Sans SC', sans-serif; font-size: 10px; font-weight: 400; color: var(--text2); margin-bottom: 14px; }
.sb-sec { font-family: 'Noto Sans SC', sans-serif; font-size: 8px; font-weight: 500; color: var(--text3); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; padding: 0 6px; }
.sb-item { display: flex; align-items: center; gap: 5px; padding: 4px 6px; margin-bottom: 1px; border-radius: 4px; font-family: 'Noto Sans SC', sans-serif; font-size: 10px; font-weight: 400; color: var(--text2); cursor: pointer; user-select: none; transition: all 0.1s ease; }
.sb-item:hover { background: var(--brand-bg); color: var(--brand); }
.sb-item .ico { font-size: 11px; width: 16px; text-align: center; }
.sb-foot { margin-top: auto; padding-top: 8px; border-top: 1px solid var(--border); font-family: 'Noto Sans SC', sans-serif; font-size: 8px; color: var(--text3); line-height: 1.5; }

/* ─── 主区 80% ─── */
.app-main { flex: 1 !important; min-width: 0 !important; height: 100vh !important; display: flex !important; flex-direction: column !important; padding: 12px 20px 12px 20px !important; }

.chat-card { flex: 1 !important; display: flex !important; flex-direction: column !important; background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 16px !important; box-shadow: var(--shadow) !important; overflow: hidden !important; min-height: 0 !important; }

/* 头部 */
.chat-head { display: flex; align-items: center; justify-content: space-between; padding: 8px 16px 6px 16px; border-bottom: 1px solid var(--border); flex-shrink: 0; }
.ch-head-l { display: flex; align-items: center; gap: 6px; }
.ch-avatar { width: 24px; height: 24px; border-radius: 5px; background: linear-gradient(135deg, var(--brand) 0%, var(--brand-light) 100%); display: flex; align-items: center; justify-content: center; font-size: 11px; color: white; flex-shrink: 0; }
.ch-name { font-family: 'Noto Sans SC', sans-serif; font-size: 11px; font-weight: 600; color: var(--text); }
.ch-st { display: flex; align-items: center; gap: 3px; font-family: 'Noto Sans SC', sans-serif; font-size: 8px; color: var(--green); }
.ch-dot { width: 4px; height: 4px; border-radius: 50%; background: var(--green); box-shadow: 0 0 0 2px var(--green-bg); animation: pulse 2.5s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.8); opacity: 0.2; } }
.ch-head-r { display: flex; align-items: center; gap: 4px; font-family: 'Noto Sans SC', sans-serif; font-size: 8px; color: var(--text2); }
.kb-badge { background: var(--brand-bg); color: var(--brand); padding: 1px 5px; border-radius: 3px; font-size: 8px; font-weight: 500; }

/* 推荐问题 */
.topic-bar { display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; padding: 8px 16px 4px 16px; flex-shrink: 0; }
.topic-chip { padding: 3px 9px; background: var(--brand-bg); border: 1px solid var(--border); border-radius: 11px; font-family: 'Noto Sans SC', sans-serif; font-size: 10px; font-weight: 400; color: var(--text2); cursor: pointer; user-select: none; transition: all 0.15s ease; }
.topic-chip:hover { background: rgba(111,74,142,0.07); border-color: var(--brand-light); color: var(--brand); }

/* 气泡 */
.user-wrap { background: rgba(111,74,142,0.06) !important; border: 1px solid rgba(111,74,142,0.08) !important; border-radius: 14px 14px 4px 14px !important; margin: 6px 0 !important; padding: 9px 14px !important; color: var(--text) !important; font-family: 'Noto Sans SC', sans-serif !important; font-weight: 450 !important; font-size: 13px !important; line-height: 1.65 !important; max-width: 85% !important; float: right !important; clear: both !important; }
.bot-wrap { background: rgba(247,244,249,0.6) !important; border: 1px solid var(--border) !important; border-left: 3px solid var(--brand-light) !important; border-radius: 14px 14px 14px 4px !important; margin: 6px 0 !important; padding: 9px 14px !important; color: var(--text) !important; font-family: 'Noto Sans SC', sans-serif !important; font-weight: 400 !important; font-size: 13px !important; line-height: 1.65 !important; max-width: 100% !important; clear: both !important; }

/* 输入框 */
.textbox-wrap { background: var(--bg) !important; border: 1.5px solid var(--border) !important; border-radius: 28px !important; padding: 0 4px 0 18px !important; transition: all 0.3s ease !important; display: flex !important; align-items: center !important; margin: 0 16px 10px 16px !important; }
.textbox-wrap:focus-within { border-color: var(--brand) !important; box-shadow: 0 0 0 4px rgba(111,74,142,0.08) !important; }
input, textarea { background: transparent !important; color: var(--text) !important; font-family: 'Noto Sans SC', sans-serif !important; font-weight: 400 !important; font-size: 14px !important; border: none !important; padding: 10px 0 !important; }
input::placeholder { color: var(--text3) !important; }

button:not(.example-btn) { background: var(--brand) !important; border: none !important; color: white !important; border-radius: 50% !important; width: 36px !important; height: 36px !important; min-width: 36px !important; padding: 0 !important; display: flex !important; align-items: center !important; justify-content: center !important; font-size: 14px !important; box-shadow: 0 2px 8px rgba(111,74,142,0.12) !important; transition: all 0.25s ease !important; }
button:hover:not(.example-btn) { transform: scale(1.06) !important; box-shadow: 0 4px 20px rgba(111,74,142,0.2) !important; }

footer, .example-wrap { display: none !important; }
.gr-box, .gr-form { background: transparent !important; border: none !important; box-shadow: none !important; }
label, .label-text { display: none !important; }
.scroll-wrap { background: transparent !important; }
.message-wrap { flex: 1 !important; overflow-y: auto !important; padding: 4px 16px 0 16px !important; }
"""

SIDEBAR_ITEMS = [
    ("🏠", "宿舍"), ("📚", "图书馆"), ("🍜", "食堂"),
    ("🎓", "奖助"), ("📖", "教务"), ("🚌", "网络"),
    ("🏥", "校医"), ("🔥", "文化"), ("🚗", "出行"),
    ("🧠", "心理"), ("🎒", "新生"), ("📋", "毕业"),
]

def build_ui():
    with gr.Blocks(
        title="楚雄师范学院 · 校园智能助手",
    ) as demo:
        gr.HTML("""
        <div class="petal">🌸</div><div class="petal">🌺</div><div class="petal">🌸</div>
        <div class="petal">🌺</div><div class="petal">🌸</div><div class="petal">🌺</div>
        <div class="petal">🌸</div><div class="petal">🌺</div><div class="petal">🌸</div>
        <div class="petal">🌺</div>
        <div class="mushroom">🍄</div><div class="mushroom">🍄</div><div class="mushroom">🍄</div>
        <div class="mushroom">🍄</div><div class="mushroom">🍄</div><div class="mushroom">🍄</div>
        <div class="sun-deco">☀️</div>
        <div class="rock-deco">🗿</div>
        """)

        with gr.Row(elem_classes="app-root"):
            with gr.Column(elem_classes="app-sidebar"):
                gr.HTML("""
                <div class="sb-brand"><em>楚雄</em>师范学院</div>
                <div class="sb-desc">校园智能问答助手</div>
                <div class="sb-sec">知识分类</div>
                """)
                for ico, label in SIDEBAR_ITEMS:
                    gr.HTML(f'<div class="sb-item"><span class="ico">{ico}</span>{label}</div>')
                gr.HTML("""
                <div class="sb-foot">DeepSeek + ChromaDB<br>181 条校园知识</div>
                """)

            with gr.Column(elem_classes="app-main"):
                with gr.Column(elem_classes="chat-card"):
                    gr.HTML("""
                    <div class="chat-head">
                        <div class="ch-head-l">
                            <div class="ch-avatar">🎓</div>
                            <div>
                                <div class="ch-name">校园智能助手</div>
                                <div class="ch-st"><span class="ch-dot"></span> 在线</div>
                            </div>
                        </div>
                        <div class="ch-head-r">
                            <span class="kb-badge">📚 181 条</span>
                            <span style="opacity:0.25;">·</span>
                            <span>v2.0</span>
                        </div>
                    </div>
                    """)

                    topics_html = '<div class="topic-bar">'
                    for t in QUICK_TOPICS:
                        topics_html += f'<span class="topic-chip">{t}</span>'
                    topics_html += '</div>'
                    gr.HTML(topics_html)

                    chat = gr.ChatInterface(
                        fn=respond,
                        title="",
                        description="",
                    )

    return demo

if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=False,
        show_error=True,
        css=CUSTOM_CSS,
    )
