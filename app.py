"""
app.py - 楚雄师范学院校园智能助手 Web 界面
现代极简设计，紫金色调，含登录/注册 + 对话历史
"""
import os
import json
import gradio as gr
import markdown
from vector_store import create_vector_store, get_collection_stats
from rag_agent import RAGAgent
import auth

collection = create_vector_store()
stats = get_collection_stats(collection)
agent = RAGAgent(collection)
DOC_COUNT = stats["document_count"]
print(f"[初始化] 向量库已就绪，共 {DOC_COUNT} 条知识片段")

SESSION = {"user_id": None, "username": None, "conv_id": None, "messages": []}

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
    path = os.path.join(DOCS_DIR, filename)
    if not os.path.exists(path):
        return "<p>文档暂未收录</p>"
    with open(path, "r", encoding="utf-8") as f:
        md_text = f.read()
    lines = md_text.split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return markdown.markdown("\n".join(lines).strip(), extensions=["tables", "fenced_code"])

DOC_HTML_CACHE = {}
for label, filename in SIDEBAR_DOC_MAP.items():
    if filename not in DOC_HTML_CACHE:
        DOC_HTML_CACHE[filename] = load_doc_html(filename)

PROMPT_CHIPS = [
    ("📚", "图书馆几点开门？"), ("🏠", "宿舍几点关门？"), ("🍜", "食堂可以现金？"),
    ("🎓", "国家奖学金条件？"), ("🏥", "校医院在哪？"), ("🌐", "校园网怎么连？"),
    ("📖", "怎么选课？"), ("🔥", "火把节放假吗？"), ("📋", "毕业论文答辩？"),
    ("🧠", "心理咨询？"), ("🎒", "新生报到？"), ("📝", "怎么换宿舍？"),
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
    if SESSION["user_id"] and SESSION.get("conv_id"):
        SESSION["messages"].append({"role": "user", "content": message})
        SESSION["messages"].append({"role": "assistant", "content": answer})
        first_msg = next((m["content"] for m in SESSION["messages"] if m["role"] == "user"), "新对话")
        title = first_msg[:30] if SESSION["conv_id"] else "新对话"
        auth.save_conversation(SESSION["conv_id"], SESSION["messages"], title)
    return answer

def handle_login(username, password):
    if not username or not password:
        return "请输入用户名和密码", gr.update(), gr.update()
    ok, msg, uid = auth.login(username, password)
    if ok:
        SESSION["user_id"] = uid
        SESSION["username"] = username
        SESSION["conv_id"] = None
        SESSION["messages"] = []
        cid = auth.create_conversation(uid, "新对话")
        SESSION["conv_id"] = cid
        convs = auth.get_user_conversations(uid)
        return msg, gr.update(selected="tabChat"), convs
    return msg, gr.update(), gr.update()

def handle_register(username, password):
    if not username or not password:
        return "请输入用户名和密码", gr.update(), gr.update()
    ok, msg = auth.register(username, password)
    if ok:
        return "注册成功！请登录", gr.update(visible=True), gr.update(visible=False)
    else:
        return msg, gr.update(), gr.update()

def handle_new_chat():
    if SESSION["user_id"] is None:
        return None
    cid = auth.create_conversation(SESSION["user_id"], title="新对话")
    SESSION["conv_id"] = cid
    SESSION["messages"] = []
    return auth.get_user_conversations(SESSION["user_id"])

def handle_load_chat(conv_id):
    if conv_id is None or conv_id == "" or SESSION["user_id"] is None:
        return [], gr.update()
    try:
        cid = int(conv_id)
    except (ValueError, TypeError):
        return [], gr.update()
    conv = auth.load_conversation(cid)
    if conv is None:
        return [], gr.update()
    SESSION["conv_id"] = cid
    SESSION["messages"] = conv.get("messages", [])
    chat_history = []
    msgs = SESSION["messages"]
    i = 0
    while i + 1 < len(msgs):
        if msgs[i]["role"] == "user" and msgs[i + 1]["role"] == "assistant":
            chat_history.append([msgs[i]["content"], msgs[i + 1]["content"]])
        i += 1
    convs = auth.get_user_conversations(SESSION["user_id"])
    return chat_history, convs

def handle_del_chat(conv_id):
    if conv_id is None or conv_id == "" or SESSION["user_id"] is None:
        return gr.update()
    try:
        cid = int(conv_id)
    except (ValueError, TypeError):
        return gr.update()
    auth.delete_conversation(cid)
    if SESSION["conv_id"] == cid:
        SESSION["conv_id"] = None
        SESSION["messages"] = []
    return auth.get_user_conversations(SESSION["user_id"])

def build_history_html(convs, active_id):
    if convs is None:
        convs = []
    lines = ['<div class="hist-section"><div class="hist-header">对话历史</div>']
    for c in convs[:5]:
        cid = c["id"]
        title = c.get("title", "新对话")
        active_cls = " hist-active" if cid == active_id else ""
        safe_title = title.replace("'", "\\'").replace('"', '&quot;').replace("<", "&lt;").replace(">", "&gt;")
        lines.append(
            f'<div class="hist-item{active_cls}" onclick="loadChat({cid})">'
            f'<span class="hist-title">{safe_title}</span>'
            f'<span class="hist-del" onclick="event.stopPropagation();delChat({cid})">x</span>'
            f'</div>'
        )
    lines.append('<div class="hist-new-btn" onclick="newChat()">+ 新对话</div></div>')
    return "\n".join(lines)

def build_sidebar_html():
    items = ""
    for ico, label in SIDEBAR_ITEMS:
        filename = SIDEBAR_DOC_MAP.get(label, "")
        doc_title = filename.replace(".md", "") if filename else label
        items += f'<div class="sb-item" onclick="openDoc(\'{label}\',\'{doc_title}\')"><span class="sb-icon">{ico}</span>{label}</div>'
    return f"""<div class="sb-header">知识分类</div><div class="sb-grid">{items}</div>
    <div class="sb-footer">DeepSeek + ChromaDB<br>{DOC_COUNT} 条校园知识</div>"""

def build_modal_html():
    doc_divs = ""
    for label, filename in SIDEBAR_DOC_MAP.items():
        html_content = DOC_HTML_CACHE.get(filename, "<p>加载失败</p>")
        doc_divs += f'<div id="doc-{label}" style="display:none">{html_content}</div>\n'
    return f"""
    <div class="doc-overlay" id="docOverlay" onclick="if(event.target===this)closeDoc()">
        <div class="doc-modal">
            <div class="doc-modal-head">
                <span class="doc-modal-title" id="docTitle">文档</span>
                <button class="doc-modal-close" onclick="closeDoc()">X</button>
            </div>
            <div class="doc-modal-body" id="docBody"></div>
        </div>
    </div>"""

def build_welcome_html():
    return """<div class="welcome-card"><div class="welcome-avatar">🤗</div>
    <div class="welcome-text"><div class="welcome-title">同学你好呀！</div>
    <div class="welcome-sub">我是楚雄师范学院的小助手，关于校园生活的问题尽管问我！</div></div></div>"""

def build_chips_html():
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

SIDEBAR_ITEMS = [
    ("🏠", "宿舍"), ("📚", "图书馆"), ("🍜", "食堂"), ("🎓", "奖助"),
    ("📖", "教务"), ("🌐", "网络"), ("🏥", "校医"), ("🔥", "文化"),
    ("🚗", "出行"), ("🧠", "心理"), ("🎒", "新生"), ("📋", "毕业"),
]

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Serif+SC:wght@400;600;700&display=swap');
:root{--brand:#6F4A8E;--brand-light:#A07FC0;--brand-bg:rgba(111,74,142,0.04);--bg:#F7F4F9;--card:#FFFFFF;--text:#1E1F23;--text2:#6A6E78;--text3:#ADB0B8;--border:#E8E3EC;--green:#789978;--green-bg:rgba(120,153,120,0.07);--shadow:0 8px 32px rgba(111,74,142,0.05)}
*{-webkit-font-smoothing:antialiased}
body{background:var(--bg)!important;margin:0;font-family:'Inter','Noto Serif SC',sans-serif}
.gradio-container{background:var(--bg)!important;min-height:100vh!important}
/* 花瓣 */
@keyframes petalFall{0%{transform:translateY(-10vh) rotate(0deg) scale(0.4);opacity:0}8%{opacity:0.12}85%{opacity:0.06}100%{transform:translateY(110vh) rotate(720deg) scale(0.7);opacity:0}}
.bg-petal{position:fixed;top:-10vh;z-index:0;pointer-events:none}
.bg-petal:nth-child(1){left:2%;animation:petalFall 22s linear infinite;font-size:28px}
.bg-petal:nth-child(2){left:12%;animation:petalFall 28s linear infinite 3s;font-size:22px}
.bg-petal:nth-child(3){left:22%;animation:petalFall 24s linear infinite 6s;font-size:32px}
.bg-petal:nth-child(4){left:32%;animation:petalFall 30s linear infinite 1.5s;font-size:26px}
.bg-petal:nth-child(5){left:42%;animation:petalFall 26s linear infinite 5s;font-size:30px}
.bg-petal:nth-child(6){left:52%;animation:petalFall 28s linear infinite 3.5s;font-size:24px}
.bg-petal:nth-child(7){left:62%;animation:petalFall 32s linear infinite 7s;font-size:28px}
.bg-petal:nth-child(8){left:72%;animation:petalFall 22s linear infinite 2s;font-size:26px}
.bg-petal:nth-child(9){left:82%;animation:petalFall 26s linear infinite 4.5s;font-size:32px}
.bg-petal:nth-child(10){left:92%;animation:petalFall 24s linear infinite 6.5s;font-size:24px}
.hang-line{position:fixed;top:20px;z-index:0;pointer-events:none;width:40px;height:1px;background:var(--border);opacity:0.3}
.hang-line:nth-child(11){left:8%}.hang-line:nth-child(12){left:22%}.hang-line:nth-child(13){left:38%}.hang-line:nth-child(14){left:52%}
.hang-line:nth-child(15){left:65%}.hang-line:nth-child(16){left:78%}.hang-line:nth-child(17){left:88%}.hang-line:nth-child(18){left:95%}
.hang-item{position:fixed;top:8px;z-index:0;pointer-events:none;font-size:14px;opacity:0.08}
.hang-item:nth-child(19){left:6%}.hang-item:nth-child(20){left:20%}.hang-item:nth-child(21){left:36%}.hang-item:nth-child(22){left:50%}
.hang-item:nth-child(23){left:63%}.hang-item:nth-child(24){left:76%}.hang-item:nth-child(25){left:86%}.hang-item:nth-child(26){left:93%}
.bottom-deco{position:fixed;z-index:0;pointer-events:none}
@keyframes rockWave{0%,100%{transform:translateY(0) rotate(-3deg);opacity:0.03}50%{transform:translateY(-4px) rotate(3deg);opacity:0.05}}
@keyframes shroomFloat{0%,100%{transform:translateY(0) scale(1);opacity:0.02}50%{transform:translateY(-6px) scale(1.05);opacity:0.04}}
.yuanmou-man{bottom:30px;right:40px;font-size:36px;animation:rockWave 6s ease-in-out infinite}
.shroom{bottom:25px;font-size:22px;animation:shroomFloat 4s ease-in-out infinite}
.shroom1{left:280px}.shroom2{left:340px;animation-delay:.8s}
.shroom3{left:400px;animation-delay:1.6s}.shroom4{left:460px;animation-delay:2.4s}
.shroom5{left:520px;animation-delay:3.2s}
/* 导航 */
.navbar{display:flex;align-items:center;justify-content:space-between;padding:6px 20px;border-bottom:1px solid var(--border);background:rgba(255,255,255,0.6)}
.nav-left{display:flex;align-items:center;gap:10px}
.nav-logo{width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,var(--brand),var(--brand-light));display:flex;align-items:center;justify-content:center;font-size:14px;color:white}
.nav-title{font-size:20px;font-weight:700;color:var(--text);letter-spacing:-.3px}
.nav-title-sub{font-size:12px;color:var(--text2);margin-left:4px}
.nav-right{display:flex;align-items:center;gap:12px}
.nav-stat{font-size:12px;color:var(--text2);display:flex;align-items:center;gap:4px}
.nav-dot{width:5px;height:5px;border-radius:50%;background:var(--green);box-shadow:0 0 0 2px var(--green-bg);animation:pulse 2.5s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.8);opacity:.2}}
/* 布局 */
.app-wrap{display:flex!important;flex:1!important;min-height:0!important;padding:0 4px!important;gap:8px!important}
.sidebar{width:15%!important;min-width:120px!important;max-width:160px!important;flex-shrink:0!important}
.sb-header{font-size:13px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;padding:0 4px}
.sb-grid{display:flex;flex-direction:column;gap:1px;margin-bottom:8px}
.sb-item{display:flex;align-items:center;gap:4px;padding:4px 6px;border-radius:4px;font-size:13px;color:var(--text2);cursor:pointer;transition:all .12s ease}
.sb-item:hover{background:var(--brand-bg);color:var(--brand)}
.sb-icon{font-size:14px;width:16px;text-align:center}
.sb-footer{font-size:10px;color:var(--text3);line-height:1.4;padding:6px 4px;border-top:1px solid var(--border);margin-top:6px}
.chat-area{flex:1!important;min-width:0!important;display:flex!important;flex-direction:column!important}
/* 历史记录 */
.hist-section{margin-top:6px;border-top:1px solid var(--border);padding-top:4px}
.hist-header{font-size:11px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:.5px;margin-bottom:3px}
.hist-item{display:flex;align-items:center;padding:4px 6px;border-radius:4px;font-size:12px;color:var(--text2);cursor:pointer;transition:all .12s ease;margin-bottom:1px}
.hist-item:hover{background:var(--brand-bg);color:var(--brand)}
.hist-item.hist-active{background:var(--brand-bg);color:var(--brand);border-left:2px solid var(--brand)}
.hist-title{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hist-del{margin-left:4px;opacity:0;font-size:11px;color:var(--text3);transition:opacity .12s ease;padding:0 2px;border-radius:2px}
.hist-item:hover .hist-del{opacity:.5}.hist-del:hover{opacity:1!important;color:#c33!important}
.hist-new-btn{font-size:13px;color:var(--brand);padding:4px 6px;border-radius:4px;cursor:pointer;transition:all .12s ease;margin-top:2px}
.hist-new-btn:hover{background:var(--brand-bg)}
/* 登录 */
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:60vh}
.login-card{background:var(--card);border-radius:20px;box-shadow:0 12px 48px rgba(111,74,142,0.06);padding:32px;max-width:380px;width:100%;margin:0 auto}
.login-title-markdown h3{font-size:22px!important;font-weight:600!important;color:var(--text)!important;text-align:center!important;margin:0 0 4px!important}
.login-sub-markdown p{font-size:13px!important;color:var(--text2)!important;text-align:center!important;margin:0 0 20px!important}
.login-field{margin-bottom:10px!important}
.login-field input{background:var(--bg)!important;border:1px solid var(--border)!important;border-radius:10px!important;padding:10px 14px!important;font-size:14px!important}
.login-msg-markdown p{font-size:12px!important;text-align:center!important}
.login-submit-btn{width:100%!important;padding:10px!important;border-radius:10px!important;font-size:15px!important;font-weight:500!important}
.switch-link-row{justify-content:center!important;margin-top:12px!important}
.switch-link-row p{font-size:13px!important;color:var(--text2)!important;margin:0!important}
.switch-link-row button{font-size:13px!important;color:#36c!important;text-decoration:underline!important}
/* 欢迎卡片 */
.welcome-card{display:flex;align-items:center;gap:8px;padding:8px 14px;margin:0}
.welcome-avatar{font-size:28px;flex-shrink:0}
.welcome-title{font-size:16px;font-weight:600;color:var(--text);margin-bottom:1px}
.welcome-sub{font-size:12px;color:var(--text2)}
/* 芯片 */
.chip-bar{display:flex;flex-wrap:wrap;gap:3px;padding:0 12px 4px;justify-content:center}
.chip{display:inline-flex;align-items:center;gap:2px;padding:2px 7px;background:var(--brand-bg);border:1px solid var(--border);border-radius:10px;font-size:9px;font-weight:400;color:var(--text2);cursor:pointer;user-select:none;transition:all .15s ease}
.chip:hover{background:rgba(111,74,142,0.07);border-color:var(--brand-light);color:var(--brand)}
.chip-ico{font-size:10px}
/* 聊天 */
.chat-wrapper{flex:1!important;display:flex!important;flex-direction:column!important;min-height:0!important}
.user-wrap{background:rgba(111,74,142,0.06)!important;border:1px solid rgba(111,74,142,0.08)!important;border-radius:14px 14px 4px 14px!important;margin:6px 0!important;padding:9px 14px!important;color:var(--text)!important;font-weight:400!important;font-size:13px!important;line-height:1.65!important;max-width:85%!important;float:right!important;clear:both!important}
.bot-wrap{background:rgba(247,244,249,0.6)!important;border:1px solid var(--border)!important;border-left:3px solid var(--brand-light)!important;border-radius:14px 14px 14px 4px!important;margin:6px 0!important;padding:9px 14px!important;color:var(--text)!important;font-weight:400!important;font-size:13px!important;line-height:1.65!important;max-width:100%!important;clear:both!important}
.textbox-wrap{background:var(--bg)!important;border:1.5px solid var(--border)!important;border-radius:28px!important;padding:0 4px 0 18px!important;display:flex!important;align-items:center!important;margin:0 16px 10px!important;transition:border-color .25s!important}
.textbox-wrap:focus-within{border-color:var(--brand)!important;box-shadow:0 0 0 4px rgba(111,74,142,0.08)!important}
input,textarea{background:transparent!important;color:var(--text)!important;font-weight:400!important;font-size:14px!important;border:none!important;padding:10px 0!important}
input::placeholder{color:var(--text3)!important}
button:not(.example-btn){background:var(--brand)!important;border:none!important;color:white!important;border-radius:50%!important;width:36px!important;height:36px!important;min-width:36px!important;padding:0!important;display:flex!important;align-items:center!important;justify-content:center!important;font-size:14px!important;box-shadow:0 2px 8px rgba(111,74,142,0.12)!important;transition:all .25s ease!important}
button:hover:not(.example-btn){transform:scale(1.06)!important;box-shadow:0 4px 20px rgba(111,74,142,0.2)!important}
.message-wrap{flex:1!important;overflow-y:auto!important;padding:4px 16px 0!important}
footer{display:none!important}
.scroll-wrap{background:transparent!important}
/* 文档弹窗 */
.doc-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.3);z-index:999;align-items:center;justify-content:center}
.doc-overlay.active{display:flex}
.doc-modal{background:var(--card);border-radius:16px;max-width:700px;width:90%;max-height:80vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,.1)}
.doc-modal-head{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid var(--border)}
.doc-modal-title{font-size:16px;font-weight:600;color:var(--text)}
.doc-modal-close{background:none!important;border:none!important;font-size:18px!important;color:var(--text3)!important;cursor:pointer!important;width:auto!important;height:auto!important;box-shadow:none!important;padding:4px!important}
.doc-modal-close:hover{color:var(--text)!important;transform:none!important;box-shadow:none!important}
.doc-modal-body{padding:20px;overflow-y:auto;font-size:13px;line-height:1.7;color:var(--text)}
.doc-modal-body h1{font-size:18px;margin:0 0 8px}.doc-modal-body h2{font-size:15px;margin:12px 0 6px}.doc-modal-body h3{font-size:13px;margin:10px 0 4px}
.doc-modal-body p{margin:0 0 6px}.doc-modal-body table{border-collapse:collapse;width:100%;margin:8px 0;font-size:12px}
.doc-modal-body th,.doc-modal-body td{border:1px solid var(--border);padding:4px 8px;text-align:left}
.doc-modal-body th{background:var(--brand-bg);color:var(--brand);font-weight:600}
.doc-modal-body code{background:#f5f5f5;padding:1px 4px;border-radius:3px;font-size:12px}
/* 登录Tabs */
.tabs{background:transparent!important}
.tabs button{background:transparent!important;border:none!important;color:var(--text2)!important}
.tabs button.selected{color:var(--brand)!important;border-bottom:2px solid var(--brand)!important}
"""

def build_ui():
    with gr.Blocks(title="楚雄师范学院 · 校园智能助手", css=CUSTOM_CSS, theme=gr.themes.Soft()) as demo:
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
        </div><div style="position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden">
        <span class="bottom-deco yuanmou-man">🗿</span>
        <span class="bottom-deco shroom shroom1">🍄</span><span class="bottom-deco shroom shroom2">🍄</span>
        <span class="bottom-deco shroom shroom3">🍄</span><span class="bottom-deco shroom shroom4">🍄</span><span class="bottom-deco shroom shroom5">🍄</span>
        </div>""")

        gr.HTML(f"""<div class="navbar"><div class="nav-left">
        <div class="nav-logo">🎓</div><div class="nav-title">楚雄师范学院</div><div class="nav-title-sub">校园智能助手</div>
        </div><div class="nav-right">
        <div class="nav-stat">📚 {DOC_COUNT} 条知识</div>
        <div class="nav-stat"><span class="nav-dot"></span> 在线</div>
        </div></div>""")

        with gr.Tabs(elem_id="mainTabs") as tabs:
            with gr.Tab("登录", id="tabLogin"):
                with gr.Column(elem_classes="login-wrap"):
                    with gr.Column(elem_classes="login-card", elem_id="loginForm") as login_col:
                        gr.Markdown("### 登录", elem_classes="login-title-markdown")
                        gr.Markdown("欢迎使用校园智能助手", elem_classes="login-sub-markdown")
                        login_user = gr.Textbox(label="用户名", placeholder="请输入用户名", elem_classes="login-field")
                        login_pass = gr.Textbox(label="密码", placeholder="请输入密码", type="password", elem_classes="login-field")
                        login_msg = gr.Markdown("", elem_classes="login-msg-markdown")
                        login_submit_btn = gr.Button("登 录", variant="primary", elem_classes="login-submit-btn")
                        with gr.Row(elem_classes="switch-link-row"):
                            gr.Markdown("还没有账号？")
                            switch_to_register_btn = gr.Button("点此注册", variant="link", size="sm")

                    with gr.Column(elem_classes="login-card", elem_id="registerForm", visible=False) as reg_col:
                        gr.Markdown("### 注册", elem_classes="login-title-markdown")
                        gr.Markdown("创建你的专属账号", elem_classes="login-sub-markdown")
                        reg_user = gr.Textbox(label="用户名", placeholder="至少2个字符", elem_classes="login-field")
                        reg_pass = gr.Textbox(label="密码", placeholder="至少3个字符", type="password", elem_classes="login-field")
                        reg_msg = gr.Markdown("", elem_classes="login-msg-markdown")
                        reg_submit_btn = gr.Button("注 册", variant="primary", elem_classes="login-submit-btn")
                        with gr.Row(elem_classes="switch-link-row"):
                            switch_to_login_btn = gr.Button("← 返回登录", variant="link", size="sm")

            with gr.Tab("对话", id="tabChat"):
                with gr.Row(elem_classes="app-wrap"):
                    with gr.Column(elem_classes="sidebar", scale=1):
                        gr.HTML(build_sidebar_html())
                        hist_placeholder = gr.HTML("")
                    with gr.Column(elem_classes="chat-area", scale=9):
                        gr.HTML(build_welcome_html())
                        gr.HTML(build_chips_html())
                        with gr.Column(elem_classes="chat-wrapper"):
                            chat = gr.ChatInterface(fn=respond, title="", description="")
                        gr.HTML(build_modal_html())

        conv_state = gr.State([])
        chat_state = gr.State([])

        switch_to_register_btn.click(lambda: (gr.update(visible=False), gr.update(visible=True)), [], [login_col, reg_col])
        switch_to_login_btn.click(lambda: (gr.update(visible=True), gr.update(visible=False)), [], [login_col, reg_col])

        def on_login(user, pwd):
            msg, tab_upd, convs = handle_login(user, pwd)
            if not isinstance(convs, list): convs = []
            return msg, tab_upd, convs

        login_submit_btn.click(on_login, [login_user, login_pass], [login_msg, tabs, conv_state])
        reg_submit_btn.click(handle_register, [reg_user, reg_pass], [reg_msg, login_col, reg_col])

        newchat_btn2 = gr.Button("新对话", visible=False, elem_id="newchatBridge")
        loadchat_btn2 = gr.Button("加载", visible=False, elem_id="loadchatBridge")
        delchat_btn2 = gr.Button("删除", visible=False, elem_id="delchatBridge")
        convid_input = gr.Textbox(visible=False, elem_id="bridgeConvId")

        conv_state.change(lambda convs: build_history_html(convs, SESSION.get("conv_id")), [conv_state], [hist_placeholder])
        newchat_btn2.click(handle_new_chat, [], [conv_state])
        loadchat_btn2.click(handle_load_chat, [convid_input], [chat_state, conv_state])
        delchat_btn2.click(handle_del_chat, [convid_input], [conv_state])

    return demo

if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="127.0.0.1", server_port=7860, share=False, show_error=True,
        css=CUSTOM_CSS, theme=gr.themes.Soft(),
        js="""function openDoc(l,t){var b=document.getElementById('docBody');var s=document.getElementById('doc-'+l);b.innerHTML=s?s.innerHTML:'<p>...</p>';document.getElementById('docTitle').textContent='📄 '+t;document.getElementById('docOverlay').classList.add('active');b.scrollTop=0;}function closeDoc(){document.getElementById('docOverlay').classList.remove('active');}document.addEventListener('keydown',function(e){if(e.key==='Escape')closeDoc();});function fillInput(t){var ta=document.querySelector('#tabChat textarea');if(ta){ta.focus();var ns=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;ns.call(ta,t);ta.dispatchEvent(new Event('input',{bubbles:true}));}}function newChat(){var b=document.getElementById('newchatBridge');if(b)b.click();}function loadChat(id){var i=document.getElementById('bridgeConvId');if(i&&i.tagName==='INPUT'){i.value=String(id);i.dispatchEvent(new Event('input',{bubbles:true}));}else if(i&&i.tagName==='TEXTAREA'){var ns=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;ns.call(i,String(id));i.dispatchEvent(new Event('input',{bubbles:true}));}var b=document.getElementById('loadchatBridge');if(b)b.click();}function delChat(id){if(!confirm('确定删除此对话？'))return;var i=document.getElementById('bridgeConvId');if(i&&i.tagName==='INPUT'){i.value=String(id);i.dispatchEvent(new Event('input',{bubbles:true}));}else if(i&&i.tagName==='TEXTAREA'){var ns=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;ns.call(i,String(id));i.dispatchEvent(new Event('input',{bubbles:true}));}var b=document.getElementById('delchatBridge');if(b)b.click();}""",
    )
