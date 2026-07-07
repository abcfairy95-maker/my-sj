"""
app.py — 楚雄师范学院校园智能助手 Web 界面
现代极简设计，紫金色调
"""
import os
import gradio as gr
import markdown
from vector_store import create_vector_store, get_collection_stats
from rag_agent import RAGAgent

collection = create_vector_store()
stats = get_collection_stats(collection)
agent = RAGAgent(collection)

DOC_COUNT = stats["document_count"]
print(f"[初始化] 向量库已就绪，共 {DOC_COUNT} 条知识片段")

# 加载所有文档并转为HTML，用于侧边栏点击查看
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
SIDEBAR_DOC_MAP = {
    "宿舍": "校园生活指南.md", "图书馆": "图书馆使用指南.md",
    "食堂": "校园生活指南.md", "奖助": "学生奖助政策.md",
    "教务": "教务学籍管理.md", "网络": "信息技术与网络服务指南.md",
    "校医": "校园安全与应急.md", "文化": "学生社团与组织指南.md",
    "出行": "校园交通与出行指南.md", "心理": "校园安全与应急.md",
    "新生": "新生入学指南.md", "毕业": "毕业与就业指南.md",
}

def load_doc_html(filename):
    """读取md文件并转为HTML"""
    path = os.path.join(DOCS_DIR, filename)
    if not os.path.exists(path):
        return "<p>文档暂未收录</p>"
    with open(path, "r", encoding="utf-8") as f:
        md_text = f.read()
    # 移除一级标题（避免重复显示）
    lines = md_text.split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    md_text = "\n".join(lines).strip()
    return markdown.markdown(md_text, extensions=["tables", "fenced_code"])

# 预加载所有文档HTML
DOC_HTML_CACHE = {}
for label, filename in SIDEBAR_DOC_MAP.items():
    if filename not in DOC_HTML_CACHE:
        DOC_HTML_CACHE[filename] = load_doc_html(filename)

PROMPT_CHIPS = [
    ("📚", "图书馆几点开门？"),
    ("🏠", "宿舍几点关门？"),
    ("🍜", "食堂可以现金？"),
    ("🎓", "国家奖学金条件？"),
    ("🏥", "校医院在哪？"),
    ("🌐", "校园网怎么连？"),
    ("📖", "怎么选课？"),
    ("🔥", "火把节放假吗？"),
    ("📋", "毕业论文答辩？"),
    ("💳", "校园卡丢了？"),
    ("🧠", "心理咨询预约？"),
    ("🚗", "学校地址在哪？"),
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
        tags = " · ".join([s.replace(".md", "") for s in sources])
        answer += f"\n\n<div class='source-tag'>📎 {tags}</div>"
    return answer

CUSTOM_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=ZCOOL+XiaoWei&family=Noto+Serif+SC:wght@700;900&family=Noto+Sans+SC:wght@400;500;600;700&display=swap');

:root {
    --brand:        #6C47A1;
    --brand-dark:   #4A3070;
    --brand-light:  #9B7EC4;
    --brand-soft:   #EDE4F7;
    --brand-wash:   #F8F5FB;
    --bg:           #FAFAFC;
    --surface:      #FFFFFF;
    --text:         #1C1C28;
    --text2:        #5E5E72;
    --text3:        #A0A0B4;
    --border:       #E8E8F0;
    --border-light: #F0F0F6;
    --green:        #52B788;
    --green-bg:     rgba(82,183,136,0.08);
    --radius-sm:    8px;
    --radius-md:    14px;
    --radius-lg:    20px;
}

* {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
}
html, body {
    margin:0; padding:0; background: var(--bg) !important;
    font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', 'Hiragino Sans GB', sans-serif !important;
    font-kerning: normal; font-feature-settings: 'kern';
    font-size: 15px; line-height: 1.6;
    -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;
}

/* ══════════════════════════════════════
   背景装饰 — 飘落花瓣 + 顶部线绳悬挂
   ══════════════════════════════════════ */

/* 飘落花瓣 */
@keyframes petalDrift {
    0%   { transform: translateY(-6vh) rotate(0deg) scale(0.5); opacity: 0; }
    8%   { opacity: 0.08; }
    85%  { opacity: 0.04; }
    100% { transform: translateY(106vh) rotate(600deg) scale(0.8); opacity: 0; }
}
.bg-petal {
    position: fixed; top: -6vh; z-index: 0; pointer-events: none;
    animation: petalDrift linear infinite;
    filter: blur(0.5px); opacity: 0.06;
}
.bg-petal:nth-child(1)  { left: 2%;  animation-duration: 28s; font-size: 44px; animation-delay: 0s; }
.bg-petal:nth-child(2)  { left: 9%;  animation-duration: 32s; font-size: 38px; animation-delay: 3s; }
.bg-petal:nth-child(3)  { left: 16%; animation-duration: 26s; font-size: 48px; animation-delay: 6s; }
.bg-petal:nth-child(4)  { left: 23%; animation-duration: 36s; font-size: 40px; animation-delay: 1.5s; }
.bg-petal:nth-child(5)  { left: 30%; animation-duration: 30s; font-size: 45px; animation-delay: 5s; }
.bg-petal:nth-child(6)  { left: 37%; animation-duration: 24s; font-size: 36px; animation-delay: 3.5s; }
.bg-petal:nth-child(7)  { left: 44%; animation-duration: 34s; font-size: 42px; animation-delay: 7s; }
.bg-petal:nth-child(8)  { left: 51%; animation-duration: 29s; font-size: 39px; animation-delay: 2s; }
.bg-petal:nth-child(9)  { left: 58%; animation-duration: 38s; font-size: 46px; animation-delay: 4.5s; }
.bg-petal:nth-child(10) { left: 65%; animation-duration: 27s; font-size: 34px; animation-delay: 6.5s; }
.bg-petal:nth-child(11) { left: 72%; animation-duration: 31s; font-size: 41px; animation-delay: 8s; }
.bg-petal:nth-child(12) { left: 79%; animation-duration: 35s; font-size: 37px; animation-delay: 1s; }
.bg-petal:nth-child(13) { left: 86%; animation-duration: 25s; font-size: 43px; animation-delay: 9s; }
.bg-petal:nth-child(14) { left: 93%; animation-duration: 33s; font-size: 35px; animation-delay: 4s; }

/* 顶部悬挂线绳 — 极淡 */
@keyframes lineSwing {
    0%,100% { transform: rotate(-1.5deg); }
    50%     { transform: rotate(1.5deg); }
}
.hang-line {
    position: fixed; top: 0; z-index: 0; pointer-events: none;
    width: 1px; opacity: 0.1;
    background: linear-gradient(to bottom, rgba(108,71,161,0.3), transparent);
}
.hang-line:nth-child(15) { left: 5%;  height: 70px; animation: lineSwing 5s ease-in-out infinite; }
.hang-line:nth-child(16) { left: 14%; height: 85px; animation: lineSwing 6s ease-in-out infinite 1s; }
.hang-line:nth-child(17) { left: 25%; height: 60px; animation: lineSwing 4.5s ease-in-out infinite 2s; }
.hang-line:nth-child(18) { left: 36%; height: 75px; animation: lineSwing 5.5s ease-in-out infinite 0.5s; }
.hang-line:nth-child(19) { left: 48%; height: 80px; animation: lineSwing 4s ease-in-out infinite 1.5s; }
.hang-line:nth-child(20) { left: 60%; height: 65px; animation: lineSwing 5s ease-in-out infinite 2.5s; }
.hang-line:nth-child(21) { left: 72%; height: 72px; animation: lineSwing 4.8s ease-in-out infinite 0.8s; }
.hang-line:nth-child(22) { left: 83%; height: 68px; animation: lineSwing 5.2s ease-in-out infinite 1.8s; }

/* 悬挂物 — 极淡 */
@keyframes hangBounce {
    0%,100% { transform: translateY(0) rotate(0deg); }
    40%     { transform: translateY(-6px) rotate(-3deg); }
    70%     { transform: translateY(1px) rotate(2deg); }
}
.hang-item {
    position: fixed; z-index: 0; pointer-events: none; opacity: 0.05;
    animation: hangBounce 6s ease-in-out infinite;
}
.hang-item:nth-child(23) { left: 4.5%; top: 66px; font-size: 24px; animation-delay: 0s; }
.hang-item:nth-child(24) { left: 13.5%;top: 80px; font-size: 22px; animation-delay: 1s; }
.hang-item:nth-child(25) { left: 24.5%;top: 56px; font-size: 28px; animation-delay: 2s; }
.hang-item:nth-child(26) { left: 35.5%;top: 70px; font-size: 24px; animation-delay: 0.5s; }
.hang-item:nth-child(27) { left: 47.5%;top: 75px; font-size: 22px; animation-delay: 1.5s; }
.hang-item:nth-child(28) { left: 59.5%;top: 60px; font-size: 26px; animation-delay: 2.5s; }
.hang-item:nth-child(29) { left: 71.5%;top: 67px; font-size: 23px; animation-delay: 0.8s; }
.hang-item:nth-child(30) { left: 82.5%;top: 63px; font-size: 25px; animation-delay: 1.8s; }

/* ── 根容器 ── */
.gradio-container {
    max-width: 100vw !important;
    width: 100vw !important;
    background: var(--bg) !important;
    min-height: 100vh !important;
    padding: 0 !important;
    margin: 0 !important;
}
/* 干掉 Gradio 默认的内容区域约束 */
.contain, .gradio-container .contain,
.main, .gradio-container .main,
.app, .gradio-container .app,
[class*="gradio"] .prose {
    max-width: 100% !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}
/* Row/Column 全宽 */
.gradio-row, .gradio-column,
.gr-row, .gr-column,
[class*="row"][class*="gap"],
[class*="col"][class*="gap"] {
    max-width: 100% !important;
}
/* ChatInterface 全宽 */
.chatbot, .chatbot > div,
.chat-interface, .chat-interface > div {
    max-width: 100% !important;
    width: 100% !important;
}

/* ══════════════════════════════════════
   底部装饰 — 元谋人 + 蘑菇动画
   ══════════════════════════════════════ */
@keyframes rockRock {
    0%,100% { transform: translateY(0) rotate(-2deg); opacity: 0.06; }
    50%     { transform: translateY(-6px) rotate(3deg); opacity: 0.10; }
}
@keyframes shroomFloat {
    0%,100% { transform: translate(0, 0) scale(1); opacity: 0.06; }
    33%     { transform: translate(6px, -8px) scale(1.1); opacity: 0.09; }
    66%     { transform: translate(-4px, -3px) scale(0.95); opacity: 0.07; }
}
.bottom-deco {
    position: fixed; bottom: 0; z-index: 0; pointer-events: none;
}
.yuanmou-man {
    left: 20px; bottom: 10px; font-size: 48px;
    animation: rockRock 6s ease-in-out infinite;
}
.shroom {
    animation: shroomFloat 8s ease-in-out infinite;
}
.shroom:nth-child(2)  { left: 90px;  bottom: 25px; font-size: 24px; animation-delay: 1.5s; }
.shroom:nth-child(3)  { left: 140px; bottom: 15px; font-size: 20px; animation-delay: 3s; }
.shroom:nth-child(4)  { left: 190px; bottom: 30px; font-size: 26px; animation-delay: 4.5s; }
.shroom:nth-child(5)  { left: 240px; bottom: 18px; font-size: 18px; animation-delay: 6s; }
.shroom:nth-child(6)  { left: 290px; bottom: 28px; font-size: 22px; animation-delay: 2s; }

/* ══════════════════════════════════════
   顶部导航栏 — 楚雄师范学院加大+艺术字
   ══════════════════════════════════════ */
.navbar {
    position: sticky; top: 0; z-index: 50;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 42px; height: 46px;
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border);
}
.nav-left { display: flex; align-items: center; gap: 14px; }
.nav-logo {
    width: 36px; height: 36px; border-radius: 10px;
    background: linear-gradient(135deg, #6C47A1 0%, #A07FC0 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; color: white;
    box-shadow: 0 2px 8px rgba(108,71,161,0.25);
}
/* 艺术字标题 — 站酷小薇书法体 + 渐变 + 发光 */
.nav-title {
    font-family: 'ZCOOL XiaoWei', 'STKaiti', 'KaiTi', 'Noto Serif SC', serif;
    font-size: 26px; font-weight: 700;
    background: linear-gradient(135deg, #3D2258 0%, #6C47A1 40%, #A07FC0 70%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 3px;
    text-shadow: none;
    filter: drop-shadow(0 2px 4px rgba(108,71,161,0.12));
}
.nav-title-sub {
    font-family: 'Noto Sans SC', sans-serif;
    font-size: 12px; font-weight: 400; color: var(--text3);
    margin-left: 4px;
    -webkit-text-fill-color: #A0A0B4;
}
.nav-right { display: flex; align-items: center; gap: 14px; }
.nav-stat {
    display: flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 500; color: var(--text2);
    padding: 3px 10px; border-radius: 14px;
    background: var(--brand-wash); border: 1px solid var(--brand-soft);
}
.nav-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green);
    box-shadow: 0 0 0 3px var(--green-bg); animation: dotPulse 2s ease-in-out infinite; }
@keyframes dotPulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

/* ══════════════════════════════════════
   主布局 — 侧边栏1:聊天区9
   ══════════════════════════════════════ */
.app-wrap {
    min-height: calc(100vh - 46px) !important;
    width: 100% !important;
    padding: 0 42px !important; margin: 0 !important;
    gap: 8px !important;
}

/* ── 左侧知识分类 ── */
.sidebar {
    min-width: 90px !important; max-width: 120px !important;
    padding-top: 8px; display: flex; flex-direction: column;
}
.sb-header {
    font-size: 11px; font-weight: 700; color: var(--text3);
    text-transform: uppercase; letter-spacing: 1.2px;
    margin-bottom: 8px; padding-left: 2px;
}
.sb-grid {
    display: flex; flex-direction: column; gap: 4px;
}
.sb-item {
    display: flex; align-items: center; gap: 6px;
    padding: 7px 8px; border-radius: 6px;
    font-size: 13px; font-weight: 500; color: var(--text2);
    cursor: pointer; transition: all 0.15s;
    background: transparent; border: 1px solid transparent;
    user-select: none;
}
.sb-item:hover { background: var(--brand-wash); color: var(--brand); border-color: var(--brand-soft); }
.sb-icon { font-size: 14px; width: 18px; text-align: center; flex-shrink: 0; }
.sb-footer { margin-top: auto; padding-top: 10px; border-top: 1px solid var(--border-light);
    font-size: 10px; color: var(--text3); line-height: 1.6; }

/* ── 主聊天区 — 紧贴侧边栏，零间隙 ── */
.chat-area {
    flex: 1; min-width: 0; padding: 6px 0 6px 0 !important;
    display: flex; flex-direction: column;
}

/* ══════════════════════════════════════
   紧凑欢迎卡片
   ══════════════════════════════════════ */
.welcome-card {
    background: linear-gradient(135deg, var(--brand-wash) 0%, rgba(237,228,247,0.2) 100%);
    border: 1px solid var(--brand-soft); border-radius: var(--radius-md);
    padding: 10px 16px; margin-bottom: 4px;
    display: flex; align-items: center; gap: 12px;
    flex-shrink: 0;
}
.welcome-emoji { font-size: 32px; flex-shrink: 0; animation: wave 2s ease-in-out infinite; }
@keyframes wave { 0%,100%{transform:rotate(0)} 25%{transform:rotate(-8deg)} 75%{transform:rotate(8deg)} }
.welcome-text { flex: 1; }
.welcome-title { font-size: 15px; font-weight: 700; color: var(--brand-dark); margin-bottom: 2px; }
.welcome-desc { font-size: 12px; color: var(--text2); line-height: 1.4; }

/* ══════════════════════════════════════
   提示问题芯片 — 3行小字体
   ══════════════════════════════════════ */
.chip-bar {
    display: flex; flex-wrap: wrap; gap: 4px;
    margin-bottom: 4px; flex-shrink: 0;
}
.chip {
    padding: 3px 10px; border-radius: 12px;
    background: var(--surface); border: 1px solid var(--border);
    font-size: 11px; font-weight: 400; color: var(--text2);
    cursor: pointer; transition: all 0.15s; user-select: none;
    white-space: nowrap;
}
.chip:hover { background: var(--brand-wash); color: var(--brand); border-color: var(--brand-soft); }
.chip:active { transform: scale(0.96); }
.chip-ico { margin-right: 2px; }

/* ══════════════════════════════════════
   聊天卡片 — 强制白色底色，覆盖Gradio主题
   ══════════════════════════════════════ */
.chat-wrapper {
    flex: 1; display: flex; flex-direction: column;
    background: #FFFFFF !important;
    border: 1px solid var(--border);
    border-radius: var(--radius-lg); box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    overflow: hidden; min-height: 0;
    max-width: 100% !important; width: 100% !important;
}
/* 强制覆盖Gradio Soft主题可能注入的暗色 */
.chat-wrapper > div,
.chat-wrapper .chatbot,
.chat-wrapper .message-wrap,
.chat-wrapper .message-row,
.chat-wrapper [class*="chat"] {
    background: #FFFFFF !important;
}
.chatbot {
    background: #FFFFFF !important;
    border: none !important; box-shadow: none !important;
}

/* 用户气泡 — 浅薰衣草渐变 */
.user-wrap, .user {
    background: linear-gradient(135deg, #B8A4D0 0%, #C9B8DD 100%) !important;
    border: none !important;
    border-radius: 16px 16px 4px 16px !important;
    margin: 6px 0 !important; padding: 10px 15px !important;
    color: #3D2D55 !important;
    font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif !important;
    font-size: 14.5px !important; font-weight: 500 !important;
    line-height: 1.6 !important;
    max-width: 55% !important; min-width: 185px !important;
    margin-left: auto !important;
    box-shadow: 0 2px 8px rgba(150,120,200,0.12) !important;
    word-break: break-word !important; overflow-wrap: break-word !important;
}

/* 助手气泡 — 浅灰紫，约15字/行 */
.bot-wrap, .bot {
    background: #F5F2F9 !important;
    border: 1px solid #E8E3F0 !important;
    border-radius: 16px 16px 16px 4px !important;
    margin: 6px 0 !important; padding: 12px 16px !important;
    color: #1C1C28 !important;
    font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif !important;
    font-size: 14.5px !important; font-weight: 400 !important;
    line-height: 1.7 !important;
    max-width: 75% !important; min-width: 200px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
    word-break: break-word !important; overflow-wrap: break-word !important;
}

/* 来源标签 */
.source-tag {
    display: inline-block; margin-top: 4px; padding: 2px 8px;
    background: rgba(108,71,161,0.07); border-radius: 10px;
    font-size: 10.5px; color: var(--brand); font-weight: 500;
}

/* ══════════════════════════════════════
   消息区域 + 滚动条 — 强制白色背景
   ══════════════════════════════════════ */
.message-wrap {
    flex: 1 !important; overflow-y: auto !important;
    padding: 12px 10px !important;
    background: #FFFFFF !important;
}
.message-wrap::-webkit-scrollbar { width: 4px; }
.message-wrap::-webkit-scrollbar-track { background: transparent; }
.message-wrap::-webkit-scrollbar-thumb { background: #E0DCE6; border-radius: 8px; }

/* ══════════════════════════════════════
   输入区域
   ══════════════════════════════════════ */
.textbox-wrap {
    flex: 1; display: flex; align-items: center;
    background: #FAFAFC !important;
    border: 1.5px solid rgba(180,160,210,0.25) !important;
    border-radius: 24px !important;
    padding: 0 4px 0 16px !important;
    transition: all 0.3s ease !important;
    box-shadow:
        0 4px 16px rgba(150,120,200,0.1),
        0 2px 4px rgba(150,120,200,0.06),
        inset 0 2px 0 rgba(255,255,255,0.95),
        inset 0 -1px 0 rgba(150,120,200,0.04) !important;
    transform: translateY(0);
}
.textbox-wrap:focus-within {
    border-color: rgba(150,120,200,0.45) !important;
    box-shadow:
        0 8px 28px rgba(150,120,200,0.16),
        0 3px 8px rgba(150,120,200,0.1),
        inset 0 2px 0 rgba(255,255,255,1),
        0 0 0 6px rgba(150,120,200,0.06) !important;
    transform: translateY(-3px);
}
input, textarea {
    background: transparent !important;
    color: var(--text) !important;
    font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif !important;
    font-size: 14px !important; font-weight: 400 !important;
    letter-spacing: 0.2px !important;
    border: none !important; padding: 9px 0 !important; outline: none !important;
}
input::placeholder, textarea::placeholder { color: var(--text3) !important; }

/* 发送按钮 */
button:not(.example-btn) {
    background: var(--brand) !important; border: none !important;
    color: white !important; border-radius: 50% !important;
    width: 36px !important; height: 36px !important; min-width: 36px !important;
    padding: 0 !important; display: flex !important;
    align-items: center !important; justify-content: center !important;
    font-size: 15px !important; cursor: pointer !important;
    box-shadow: 0 2px 6px rgba(108,71,161,0.18) !important;
    transition: all 0.2s ease !important;
}
button:hover:not(.example-btn) {
    transform: scale(1.06); background: var(--brand-dark) !important;
    box-shadow: 0 4px 12px rgba(108,71,161,0.25) !important;
}
button:active:not(.example-btn) { transform: scale(0.94) !important; }

/* 隐藏默认元素 */
footer, .footer { display: none !important; }
.scroll-wrap { background: transparent !important; }

/* 响应式 */
@media (max-width: 768px) {
    .app-wrap { flex-direction: column; padding: 0 12px !important; gap: 4px !important; }
    .sidebar { max-width: none !important; min-width: auto !important; padding-top: 4px; }
    .sb-grid { flex-direction: row; flex-wrap: wrap; gap: 4px; }
    .sb-item { padding: 4px 8px; font-size: 11px; }
    .sb-header { margin-bottom: 4px; }
    .sb-footer { display: none; }
    .welcome-card { flex-direction: column; text-align: center; gap: 4px; padding: 10px 14px; }
    .nav-title { font-size: 20px; }
}

/* ══════════════════════════════════════
   文档弹窗 Modal
   ══════════════════════════════════════ */
.doc-overlay {
    display: none; position: fixed; inset: 0; z-index: 999;
    background: rgba(0,0,0,0.45); backdrop-filter: blur(4px);
    align-items: center; justify-content: center;
}
.doc-overlay.active { display: flex; }
.doc-modal {
    background: #FFFFFF; border-radius: 18px;
    width: min(900px, 92vw); max-height: 85vh;
    display: flex; flex-direction: column;
    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
    animation: modalIn 0.25s ease-out;
}
@keyframes modalIn {
    from { transform: translateY(24px) scale(0.96); opacity: 0; }
    to   { transform: translateY(0) scale(1); opacity: 1; }
}
.doc-modal-head {
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 24px; border-bottom: 1px solid #EDE8F2;
    flex-shrink: 0;
}
.doc-modal-title {
    font-family: 'ZCOOL XiaoWei', 'Noto Serif SC', serif;
    font-size: 20px; font-weight: 700; color: #4A3070;
}
.doc-modal-close {
    width: 32px; height: 32px; border-radius: 50%;
    border: none; background: #F5F2F9; color: #6C47A1;
    font-size: 18px; cursor: pointer; display: flex;
    align-items: center; justify-content: center;
    transition: all 0.15s;
}
.doc-modal-close:hover { background: #EDE4F7; }
.doc-modal-body {
    flex: 1; overflow-y: auto; padding: 20px 28px;
    font-size: 14px; line-height: 1.8; color: #1C1C28;
    font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
}
.doc-modal-body h2 { font-size: 18px; color: #4A3070; margin: 20px 0 10px; border-left: 3px solid #A07FC0; padding-left: 10px; }
.doc-modal-body h3 { font-size: 15px; color: #5E5E72; margin: 14px 0 6px; }
.doc-modal-body table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 13px; }
.doc-modal-body th { background: #F5F2F9; padding: 8px 12px; text-align: left; font-weight: 600; color: #4A3070; border: 1px solid #E8E3F0; }
.doc-modal-body td { padding: 6px 12px; border: 1px solid #E8E3F0; }
.doc-modal-body strong { color: #6C47A1; }
.doc-modal-body ul, .doc-modal-body ol { padding-left: 20px; }
.doc-modal-body li { margin: 4px 0; }
.doc-modal-body::-webkit-scrollbar { width: 5px; }
.doc-modal-body::-webkit-scrollbar-track { background: transparent; }
.doc-modal-body::-webkit-scrollbar-thumb { background: #E0DCE6; border-radius: 8px; }
"""

SIDEBAR_ITEMS = [
    ("🏠", "宿舍"), ("📚", "图书馆"), ("🍜", "食堂"),
    ("🎓", "奖助"), ("📖", "教务"), ("🌐", "网络"),
    ("🏥", "校医"), ("🔥", "文化"), ("🚗", "出行"),
    ("🧠", "心理"), ("🎒", "新生"), ("📋", "毕业"),
]

def build_sidebar_html():
    items = ""
    for ico, label in SIDEBAR_ITEMS:
        filename = SIDEBAR_DOC_MAP.get(label, "")
        # 获取该文档的标题（文件名去掉.md）
        doc_title = filename.replace(".md", "") if filename else label
        items += f'<div class="sb-item" onclick="openDoc(\'{label}\',\'{doc_title}\')"><span class="sb-icon">{ico}</span>{label}</div>'
    return f"""
    <div class="sb-header">知识分类</div>
    <div class="sb-grid">{items}</div>
    <div class="sb-footer">DeepSeek + ChromaDB<br>{DOC_COUNT} 条校园知识</div>
    """

def build_modal_html():
    """生成包含所有文档内容的隐藏弹窗 + JS函数"""
    # 将每个文档HTML注入到页面
    doc_divs = ""
    for label, filename in SIDEBAR_DOC_MAP.items():
        html_content = DOC_HTML_CACHE.get(filename, "<p>加载失败</p>")
        # 用data属性存HTML，避免XSS
        safe_html = html_content.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        doc_divs += f'<div id="doc-{label}" style="display:none">{safe_html}</div>\n'
    
    return f"""
    <div class="doc-overlay" id="docOverlay" onclick="if(event.target===this)closeDoc()">
        <div class="doc-modal">
            <div class="doc-modal-head">
                <span class="doc-modal-title" id="docTitle">文档</span>
                <button class="doc-modal-close" onclick="closeDoc()">✕</button>
            </div>
            <div class="doc-modal-body" id="docBody"></div>
        </div>
    </div>
    {doc_divs}
    """

def build_welcome_html():
    return """
    <div class="welcome-card">
        <div class="welcome-emoji">👋</div>
        <div class="welcome-text">
            <div class="welcome-title">同学你好，有什么可以帮你？</div>
            <div class="welcome-desc">我是校园智能助手，关于宿舍、食堂、图书馆、教务、奖助等问题都可以问我</div>
        </div>
    </div>
    """

def build_chips_html():
    """生成可点击的提示问题芯片 — 点击后填充到输入框"""
    chips = ""
    for ico, text in PROMPT_CHIPS:
        safe = text.replace("'", "\\'").replace('"', '&quot;')
        chips += (
            f'<span class="chip" onclick="'
            f'(function(){{'
            f'var ta=document.querySelector(\'textarea\');'
            f'if(ta){{'
            f'var ns=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,\'value\').set;'
            f'ns.call(ta,\'{ico} {safe}\');'
            f'ta.dispatchEvent(new Event(\'input\',{{bubbles:true}}));'
            f'ta.focus();'
            f'}}'
            f'}})()'
            f'"><span class="chip-ico">{ico}</span>{text}</span>'
        )
    return f'<div class="chip-bar">{chips}</div>'


def build_ui():
    with gr.Blocks(title="楚雄师范学院 · 校园智能助手") as demo:
        # 背景装饰 — 飘落花瓣 + 线绳悬挂
        gr.HTML("""<div style="position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden">
        <span class="bg-petal">🌸</span><span class="bg-petal">🌺</span>
        <span class="bg-petal">🌸</span><span class="bg-petal">🌺</span>
        <span class="bg-petal">🌸</span><span class="bg-petal">🌺</span>
        <span class="bg-petal">🌸</span><span class="bg-petal">🌺</span>
        <span class="bg-petal">🌸</span><span class="bg-petal">🌺</span>
        <span class="bg-petal">🌸</span><span class="bg-petal">🌺</span>
        <span class="bg-petal">🌸</span><span class="bg-petal">🌺</span>
        <span class="hang-line"></span><span class="hang-line"></span>
        <span class="hang-line"></span><span class="hang-line"></span>
        <span class="hang-line"></span><span class="hang-line"></span>
        <span class="hang-line"></span><span class="hang-line"></span>
        <span class="hang-item">🗿</span><span class="hang-item">☀️</span>
        <span class="hang-item">🌸</span><span class="hang-item">🗿</span>
        <span class="hang-item">🌺</span><span class="hang-item">☀️</span>
        <span class="hang-item">🌸</span><span class="hang-item">🌺</span>
        </div>""")

        # 底部元谋人 + 小蘑菇
        gr.HTML("""<div style="position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden">
        <span class="bottom-deco yuanmou-man">🗿</span>
        <span class="bottom-deco shroom">🍄</span>
        <span class="bottom-deco shroom">🍄</span>
        <span class="bottom-deco shroom">🍄</span>
        <span class="bottom-deco shroom">🍄</span>
        <span class="bottom-deco shroom">🍄</span>
        </div>""")

        # 顶部导航 — 楚雄师范学院大号艺术字
        gr.HTML(f"""
        <div class="navbar">
            <div class="nav-left">
                <div class="nav-logo">🎓</div>
                <div class="nav-title">楚雄师范学院</div>
                <div class="nav-title-sub">校园智能助手</div>
            </div>
            <div class="nav-right">
                <div class="nav-stat">📚 {DOC_COUNT} 条知识</div>
                <div class="nav-stat"><span class="nav-dot"></span> 在线</div>
            </div>
        </div>
        """)

        with gr.Row(elem_classes="app-wrap"):
            # 左侧知识分类
            with gr.Column(elem_classes="sidebar", scale=1):
                gr.HTML(build_sidebar_html())

            # 右侧主区域
            with gr.Column(elem_classes="chat-area", scale=9):
                # 紧凑欢迎卡片
                gr.HTML(build_welcome_html())

                # 提示问题芯片 — 3行小字体
                gr.HTML(build_chips_html())

                # 聊天框
                with gr.Column(elem_classes="chat-wrapper"):
                    chat = gr.ChatInterface(
                        fn=respond,
                        title="",
                        description="",
                    )

        # 文档弹窗
        gr.HTML(build_modal_html())

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(),
        js="""
        function openDoc(label, title) {
            var body = document.getElementById('docBody');
            var src = document.getElementById('doc-' + label);
            body.innerHTML = src ? src.innerHTML : '<p>文档加载中...</p>';
            document.getElementById('docTitle').textContent = '📄 ' + title;
            document.getElementById('docOverlay').classList.add('active');
            body.scrollTop = 0;
        }
        function closeDoc() {
            document.getElementById('docOverlay').classList.remove('active');
        }
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeDoc();
        });
        """,
    )
