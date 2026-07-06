import gradio as gr
from vector_store import create_vector_store, get_collection_stats
from rag_agent import RAGAgent

collection = create_vector_store()
stats = get_collection_stats(collection)
agent = RAGAgent(collection)

print(f"[初始化] 向量库已就绪，共 {stats['document_count']} 条知识片段")

EXAMPLES = [
    "宿舍晚上几点关门？",
    "图书馆周末几点开门？",
    "国家奖学金多少钱？",
    "怎么申请换宿舍？",
    "校园网怎么连接？",
    "新生报到要带什么？",
]

def respond(message: str, history: list) -> str:
    if not message or not message.strip():
        return "请输入你的问题。"
    try:
        answer, docs, sources = agent.ask(message, n_results=3, chat_history=history)
    except TypeError:
        dict_history = []
        for item in history:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                dict_history.append({"role": "user", "content": item[0]})
                dict_history.append({"role": "assistant", "content": item[1]})
        answer, docs, sources = agent.ask(message, n_results=3, chat_history=dict_history)
    if sources:
        answer += f"\n\n---\n📚 **参考来源**: {', '.join(sources)}"
    return answer

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@200;300;400;600;700;900&family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=Ma+Shan+Zheng&display=swap');

:root {
    --bg: #F7F2F5;
    --bg2: #FAF5F8;
    --bg3: #FFF8FA;
    --plum: #6B4E6D;
    --plum-light: #9B7D9D;
    --plum-pale: #D4C3D6;
    --plum-ghost: #EDE4EE;
    --taupe: #8A7E84;
    --charcoal: #2C2A2C;
    --gold: #C9B99A;
}

.gradio-container {
    background: linear-gradient(160deg,
        var(--bg) 0%, var(--bg2) 30%, var(--bg3) 50%, var(--bg2) 70%, var(--bg) 100%) !important;
    min-height: 100vh !important;
    position: relative !important;
    overflow: hidden !important;
}

.gradio-container::before {
    content: '';
    position: fixed;
    top: -25%; left: -10%;
    width: 60%; height: 60%;
    background: radial-gradient(ellipse, rgba(107,78,109,0.035) 0%, transparent 70%);
    pointer-events: none; z-index: 0;
    animation: drift1 30s ease-in-out infinite;
}

.gradio-container::after {
    content: '';
    position: fixed;
    bottom: -20%; right: -10%;
    width: 50%; height: 50%;
    background: radial-gradient(ellipse, rgba(201,185,154,0.035) 0%, transparent 70%);
    pointer-events: none; z-index: 0;
    animation: drift2 35s ease-in-out infinite;
}

@keyframes drift1 {
    0%, 100% { transform: translate(0,0) scale(1); }
    50% { transform: translate(40px,-30px) scale(1.06); }
}
@keyframes drift2 {
    0%, 100% { transform: translate(0,0) scale(1); }
    50% { transform: translate(-30px,40px) scale(1.04); }
}

@keyframes petalFall {
    0% { transform: translateY(-5vh) rotate(0deg) scale(0.4); opacity: 0; }
    5% { opacity: 0.2; }
    90% { opacity: 0.1; }
    100% { transform: translateY(105vh) rotate(480deg) scale(0.7); opacity: 0; }
}
.petal {
    position: fixed; z-index: 2; pointer-events: none; font-size: 11px; opacity: 0;
}
.petal:nth-child(1) { left: 4%; animation: petalFall 30s linear infinite; }
.petal:nth-child(2) { left: 12%; animation: petalFall 26s linear infinite 3s; font-size: 13px; }
.petal:nth-child(3) { left: 20%; animation: petalFall 34s linear infinite 6s; font-size: 10px; }
.petal:nth-child(4) { left: 28%; animation: petalFall 28s linear infinite 2s; }
.petal:nth-child(5) { left: 36%; animation: petalFall 32s linear infinite 7.5s; font-size: 10px; }
.petal:nth-child(6) { left: 44%; animation: petalFall 24s linear infinite 4.5s; }
.petal:nth-child(7) { left: 52%; animation: petalFall 36s linear infinite 8s; font-size: 9px; }
.petal:nth-child(8) { left: 60%; animation: petalFall 27s linear infinite 5s; font-size: 11px; }
.petal:nth-child(9) { left: 68%; animation: petalFall 31s linear infinite 2.5s; font-size: 12px; }
.petal:nth-child(10) { left: 76%; animation: petalFall 29s linear infinite 9s; font-size: 9px; }
.petal:nth-child(11) { left: 84%; animation: petalFall 33s linear infinite 6.5s; }
.petal:nth-child(12) { left: 92%; animation: petalFall 25s linear infinite 3.5s; font-size: 10px; }

@keyframes mushroomWalk {
    0% { transform: translateX(-120px); }
    100% { transform: translateX(calc(100vw + 120px)); }
}

.mushroom-row {
    position: fixed;
    bottom: 10px;
    left: 0;
    width: 100%;
    height: 50px;
    z-index: 3;
    pointer-events: none;
}
.mushroom {
    position: absolute;
    font-size: 26px;
    animation: mushroomWalk 28s linear infinite;
}
.mushroom:nth-child(1) { bottom: 0; animation-duration: 30s; }
.mushroom:nth-child(2) { bottom: 5px; animation-duration: 24s; animation-delay: 4s; font-size: 22px; }
.mushroom:nth-child(3) { bottom: 8px; animation-duration: 28s; animation-delay: 8s; font-size: 30px; }
.mushroom:nth-child(4) { bottom: 2px; animation-duration: 34s; animation-delay: 12s; font-size: 20px; }
.mushroom:nth-child(5) { bottom: 6px; animation-duration: 26s; animation-delay: 16s; font-size: 24px; }
.mushroom:nth-child(6) { bottom: 3px; animation-duration: 32s; animation-delay: 20s; font-size: 28px; }
.mushroom:nth-child(7) { bottom: 7px; animation-duration: 28s; animation-delay: 10s; font-size: 18px; }
.mushroom:nth-child(8) { bottom: 4px; animation-duration: 36s; animation-delay: 14s; font-size: 25px; }
.mushroom:nth-child(9) { bottom: 9px; animation-duration: 22s; animation-delay: 18s; font-size: 22px; }
.mushroom { left: -60px; }

.deco-flower {
    position: fixed; z-index: 1; pointer-events: none; opacity: 0.06;
}
.deco-flower-tl { top: 12px; left: 15px; font-size: 32px; animation: sway 8s ease-in-out infinite; }
.deco-flower-tr { top: 10px; right: 18px; font-size: 26px; animation: sway 9s ease-in-out infinite 2s; }

@keyframes sway {
    0%, 100% { transform: rotate(-3deg) translateY(0); }
    50% { transform: rotate(3deg) translateY(-5px); }
}

.main-card {
    background: rgba(255, 255, 255, 0.55) !important;
    backdrop-filter: blur(40px) saturate(1.1) !important;
    -webkit-backdrop-filter: blur(40px) saturate(1.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    border-radius: 32px !important;
    box-shadow:
        0 12px 60px rgba(201, 185, 154, 0.05),
        0 4px 20px rgba(107, 78, 109, 0.02),
        inset 0 1px 0 rgba(255,255,255,0.7) !important;
    padding: 24px 28px 20px 28px !important;
    max-width: 780px !important;
    margin: 20px auto !important;
    position: relative !important;
    z-index: 10 !important;
}

.hero-section { text-align: center; padding: 4px 10px 0 10px; }
.hero-title {
    font-family: 'Playfair Display', serif !important;
    font-weight: 400 !important;
    font-style: italic !important;
    font-size: 2.1em !important;
    color: var(--plum) !important;
    letter-spacing: 1.5px !important;
    line-height: 1.2 !important;
    margin-bottom: 0 !important;
}
.hero-title-cn {
    font-family: 'Ma Shan Zheng', cursive !important;
    font-size: 1.5em !important;
    color: var(--charcoal) !important;
    letter-spacing: 4px !important;
    opacity: 0.5;
    margin-top: 0;
    line-height: 1.2;
}
.hero-subtitle {
    font-family: 'Noto Serif SC', serif !important;
    font-weight: 200 !important;
    font-size: 0.72em !important;
    color: var(--taupe) !important;
    letter-spacing: 5px !important;
    margin: 6px 0 0 0;
    display: inline-block;
}
.divider-line {
    height: 1px;
    margin: 4px auto 10px auto;
    width: 28%;
    background: linear-gradient(90deg, transparent 0%, var(--plum-pale) 50%, transparent 100%);
}

.culture-strip {
    display: flex; justify-content: center;
    gap: 2px; flex-wrap: wrap;
    margin: 0 0 12px 0;
}
.culture-tag {
    padding: 3px 9px;
    font-size: 0.65em; color: var(--taupe);
    font-family: 'Noto Serif SC', serif; font-weight: 300;
    background: rgba(255,255,255,0.2);
    border: 1px solid var(--plum-ghost);
    border-radius: 12px;
    letter-spacing: 0.5px;
    transition: all 0.3s ease; cursor: default;
}
.culture-tag:hover {
    background: rgba(107,78,109,0.03);
    border-color: var(--plum-pale);
    color: var(--plum);
}

.user-wrap {
    background: rgba(107, 78, 109, 0.03) !important;
    border: 1px solid rgba(107, 78, 109, 0.08) !important;
    border-radius: 20px 20px 6px 20px !important;
    margin: 12px 0 !important;
    padding: 20px 24px !important;
    color: var(--charcoal) !important;
    font-family: 'Noto Serif SC', serif !important;
    font-weight: 350 !important;
    font-size: 0.92em !important;
    line-height: 1.85 !important;
    letter-spacing: 0.4px !important;
    box-shadow:
        0 1px 3px rgba(0,0,0,0.02),
        0 4px 14px rgba(107,78,109,0.04),
        0 12px 32px rgba(107,78,109,0.02),
        inset 0 1px 0 rgba(255,255,255,0.5),
        inset 0 -1px 0 rgba(107,78,109,0.03) !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease !important;
}
.user-wrap:hover {
    transform: translateX(4px) !important;
    box-shadow:
        0 2px 6px rgba(0,0,0,0.02),
        0 8px 24px rgba(107,78,109,0.06),
        0 20px 48px rgba(107,78,109,0.03),
        inset 0 1px 0 rgba(255,255,255,0.5) !important;
}

.bot-wrap {
    background: rgba(255, 255, 255, 0.6) !important;
    border: 1px solid rgba(212, 195, 214, 0.12) !important;
    border-radius: 20px 20px 20px 6px !important;
    margin: 12px 0 !important;
    padding: 20px 24px !important;
    color: var(--charcoal) !important;
    font-family: 'Noto Serif SC', serif !important;
    font-weight: 350 !important;
    font-size: 0.92em !important;
    line-height: 1.85 !important;
    letter-spacing: 0.4px !important;
    box-shadow:
        0 1px 3px rgba(0,0,0,0.01),
        0 6px 20px rgba(201, 185, 154, 0.04),
        0 16px 40px rgba(0, 0, 0, 0.01),
        inset 0 1px 0 rgba(255,255,255,0.6),
        inset 0 -1px 0 rgba(107,78,109,0.02) !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease !important;
}
.bot-wrap:hover {
    transform: translateX(-4px) !important;
    box-shadow:
        0 2px 6px rgba(0,0,0,0.01),
        0 10px 30px rgba(201, 185, 154, 0.06),
        0 24px 56px rgba(0, 0, 0, 0.02),
        inset 0 1px 0 rgba(255,255,255,0.6) !important;
}

.message-wrap {
    display: flex !important;
    flex-direction: column !important;
    gap: 4px !important;
    padding: 2px !important;
}

.textbox-wrap {
    background: rgba(255, 255, 255, 0.7) !important;
    border: 1px solid var(--plum-pale) !important;
    border-radius: 28px !important;
    padding: 2px 2px 2px 22px !important;
    transition: all 0.4s ease !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.01) !important;
}
.textbox-wrap:focus-within {
    border-color: var(--plum-light) !important;
    box-shadow: 0 0 0 4px rgba(107,78,109,0.03), 0 4px 20px rgba(107,78,109,0.02) !important;
}

input, textarea {
    background: transparent !important;
    color: var(--charcoal) !important;
    font-family: 'Noto Serif SC', serif !important;
    font-weight: 300 !important;
    font-size: 0.9em !important;
    border: none !important;
    padding: 10px 0 !important;
}
input::placeholder, textarea::placeholder {
    color: var(--taupe) !important; font-weight: 200 !important; font-size: 0.9em !important;
}

button {
    background: linear-gradient(145deg, var(--plum) 0%, #543B56 100%) !important;
    border: none !important;
    color: white !important;
    border-radius: 24px !important;
    font-family: 'Noto Serif SC', serif !important;
    font-weight: 350 !important;
    font-size: 0.82em !important;
    padding: 6px 22px !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 4px 16px rgba(107,78,109,0.12), inset 0 1px 0 rgba(255,255,255,0.08) !important;
    transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
}
button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(107,78,109,0.2), inset 0 1px 0 rgba(255,255,255,0.08) !important;
}
button:active {
    transform: translateY(0) !important;
    box-shadow: 0 2px 8px rgba(107,78,109,0.12) !important;
}

.example-wrap {
    background: rgba(255,255,255,0.3) !important;
    border: 1px solid var(--plum-ghost) !important;
    border-radius: 12px !important;
    padding: 6px !important;
}
.example-btn {
    background: transparent !important;
    border: 1px solid rgba(201,185,154,0.12) !important;
    color: var(--taupe) !important;
    border-radius: 16px !important;
    padding: 2px 10px !important;
    font-size: 0.72em !important;
    font-family: 'Noto Serif SC', serif !important;
    font-weight: 300 !important;
    transition: all 0.3s ease !important;
}
.example-btn:hover {
    background: rgba(107,78,109,0.03) !important;
    border-color: var(--plum-pale) !important;
    color: var(--plum) !important;
}

.footer-area {
    text-align: center;
    padding: 8px;
    margin-top: 10px;
    font-size: 0.64em;
    color: var(--taupe);
    font-family: 'Noto Serif SC', serif;
    font-weight: 200;
    letter-spacing: 1.5px;
    line-height: 1.8;
    opacity: 0.5;
    border-top: 1px solid var(--plum-ghost);
}

footer { display: none !important; }
.gr-box, .gr-form { background: transparent !important; border: none !important; box-shadow: none !important; }
label, .label-text { color: var(--taupe) !important; font-family: 'Noto Serif SC', serif !important; font-weight: 200 !important; font-size: 0.8em !important; }
.scroll-wrap { background: transparent !important; }
"""

def build_ui():
    with gr.Blocks(
        title="楚雄师范学院校园智能助手",
    ) as demo:
        gr.HTML("""
        <div class="deco-flower deco-flower-tl">🌸</div>
        <div class="deco-flower deco-flower-tr">🌺</div>
        <div class="mushroom-row">
            <div class="mushroom">🍄</div><div class="mushroom">🍄</div><div class="mushroom">🍄</div>
            <div class="mushroom">🍄</div><div class="mushroom">🍄</div><div class="mushroom">🍄</div>
            <div class="mushroom">🍄</div><div class="mushroom">🍄</div><div class="mushroom">🍄</div>
        </div>
        <div class="petal">🌸</div><div class="petal">🌸</div><div class="petal">🌸</div>
        <div class="petal">🌸</div><div class="petal">🌸</div><div class="petal">🌸</div>
        <div class="petal">🌸</div><div class="petal">🌸</div><div class="petal">🌸</div>
        <div class="petal">🌸</div><div class="petal">🌸</div><div class="petal">🌸</div>
        """)

        with gr.Column(elem_classes="main-card"):
            gr.HTML("""
            <div class="hero-section">
                <div class="hero-title">Chuxiong Normal University</div>
                <div class="hero-title-cn">楚雄师范学院</div>
                <div style="margin-top: 8px;">
                    <span class="hero-subtitle">✦ 校园智能问答助手 ✦</span>
                </div>
                <div class="divider-line"></div>
            </div>
            <div class="culture-strip">
                <span class="culture-tag">威楚雄彝</span>
                <span class="culture-tag">学府问道</span>
                <span class="culture-tag">火把传情</span>
                <span class="culture-tag">菌香满园</span>
                <span class="culture-tag">太阳历法</span>
                <span class="culture-tag">梅韵流芳</span>
            </div>
            """)

            chat = gr.ChatInterface(
                fn=respond,
                examples=EXAMPLES,
                title="",
                description="",
            )

            gr.HTML("""
            <div class="footer-area">
                RAG · DeepSeek + ChromaDB + Gradio<br>
                Knowledge Base · 10 Domains · 181 Entries
            </div>
            """)

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
