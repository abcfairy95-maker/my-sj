"""
app.py - 楚雄师范学院校园智能助手 Web 界面
登录/注册 + 对话历史 + 动态装饰
"""
import os, json, markdown, re
import gradio as gr
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
    "宿舍": "校园生活指南.md", "图书馆": "图书馆使用指南.md", "食堂": "校园生活指南.md",
    "奖助": "学生奖助政策.md", "教务": "教务学籍管理.md", "网络": "信息技术与网络服务指南.md",
    "校医": "校园安全与应急.md", "文化": "学生社团与组织指南.md", "出行": "校园交通与出行指南.md",
    "心理": "校园安全与应急.md", "新生": "新生入学指南.md", "毕业": "毕业与就业指南.md",
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
        title = first_msg[:30]
        auth.save_conversation(SESSION["conv_id"], SESSION["messages"], title)
    return answer

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
    return f"""{doc_divs}
    <div class="doc-overlay" id="docOverlay" onclick="if(event.target===this)closeDoc()">
        <div class="doc-modal"><div class="doc-modal-head">
            <span class="doc-modal-title" id="docTitle">文档</span>
            <button class="doc-modal-close" onclick="closeDoc()">X</button>
        </div><div class="doc-modal-body" id="docBody"></div></div>
    </div>"""

def build_welcome_html():
    return """<div class="welcome-card"><div class="welcome-avatar">🎓</div>
    <div class="welcome-text"><div class="welcome-title">🎉 欢迎来到楚雄师范学院校园智能助手！</div>
    <div class="welcome-sub">我是你的校园AI小助手，背后有200条校园知识库。无论是宿舍几点关门、图书馆几点开门、奖学金怎么申请，还是教务选课、食堂用餐、校园网络、心理咨询……关于校园生活的任何问题，随时问我！</div>
    <div class="welcome-tip">💡 试试点击下方的推荐问题，或者直接输入你的问题～</div></div></div>"""

def build_chips_html():
    chips = ""
    for ico, text in PROMPT_CHIPS:
        safe = text.replace("'", "\\'").replace('"', '&quot;')
        chips += f'<span class="chip" onclick="(function(){{var ta=document.querySelector(\'textarea\');if(ta){{var ns=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,\'value\').set;ns.call(ta,\'{ico} {safe}\');ta.dispatchEvent(new Event(\'input\',{{bubbles:true}}));ta.focus();}}}})()"><span class="chip-ico">{ico}</span>{text}</span>'
    return f'<div class="chip-bar">{chips}</div>'

SIDEBAR_ITEMS = [
    ("🏠", "宿舍"), ("📚", "图书馆"), ("🍜", "食堂"), ("🎓", "奖助"),
    ("📖", "教务"), ("🌐", "网络"), ("🏥", "校医"), ("🔥", "文化"),
    ("🚗", "出行"), ("🧠", "心理"), ("🎒", "新生"), ("📋", "毕业"),
]

CUSTOM_CSS = """@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Serif+SC:wght@400;600;700&family=ZCOOL+KuaiLe&display=swap');
:root{--brand:#6F4A8E;--brand-light:#A07FC0;--brand-bg:rgba(111,74,142,0.04);--bg:#F7F4F9;--card:#FFF;--text:#1E1F23;--text2:#6A6E78;--text3:#ADB0B8;--border:#E8E3EC;--green:#789978;--green-bg:rgba(120,153,120,0.07);--shadow:0 8px 32px rgba(111,74,142,0.05)}
*{-webkit-font-smoothing:antialiased}
body{background:var(--bg)!important;margin:0}
.gradio-container{background:var(--bg)!important;min-height:100vh!important;display:flex!important;flex-direction:column!important}
/* 花瓣 - 随机飘落 */
@keyframes petalFall{0%{transform:translateY(-8vh) rotate(0deg) scale(0.4);opacity:0}8%{opacity:0.2}92%{opacity:0.1}100%{transform:translateY(108vh) rotate(720deg) scale(1.1);opacity:0}}
@keyframes petalFall2{0%{transform:translateY(-8vh) rotate(0deg) scale(0.5);opacity:0}10%{opacity:0.18}90%{opacity:0.08}100%{transform:translateY(108vh) rotate(-540deg) scale(0.9);opacity:0}}
@keyframes petalFall3{0%{transform:translateY(-8vh) rotate(0deg) scale(0.6);opacity:0}6%{opacity:0.15}94%{opacity:0.1}100%{transform:translateY(108vh) rotate(360deg) scale(1);opacity:0}}
.deco-bg .bg-petal{position:fixed;top:-8vh;z-index:0;pointer-events:none}
.deco-bg .bg-petal:nth-child(1){left:4%;font-size:36px;animation:petalFall 38s linear infinite 0s}
.deco-bg .bg-petal:nth-child(2){left:14%;font-size:26px;animation:petalFall2 42s linear infinite 6s}
.deco-bg .bg-petal:nth-child(3){left:22%;font-size:44px;animation:petalFall3 35s linear infinite 12s}
.deco-bg .bg-petal:nth-child(4){left:30%;font-size:30px;animation:petalFall 45s linear infinite 3s}
.deco-bg .bg-petal:nth-child(5){left:38%;font-size:40px;animation:petalFall2 39s linear infinite 18s}
.deco-bg .bg-petal:nth-child(6){left:46%;font-size:28px;animation:petalFall3 48s linear infinite 9s}
.deco-bg .bg-petal:nth-child(7){left:54%;font-size:42px;animation:petalFall 36s linear infinite 21s}
.deco-bg .bg-petal:nth-child(8){left:62%;font-size:32px;animation:petalFall2 44s linear infinite 15s}
.deco-bg .bg-petal:nth-child(9){left:70%;font-size:46px;animation:petalFall3 40s linear infinite 24s}
.deco-bg .bg-petal:nth-child(10){left:78%;font-size:34px;animation:petalFall 43s linear infinite 7s}
.deco-bg .bg-petal:nth-child(11){left:86%;font-size:28px;animation:petalFall2 37s linear infinite 27s}
.deco-bg .bg-petal:nth-child(12){left:94%;font-size:38px;animation:petalFall3 46s linear infinite 2s}
/* 底部装饰 */
@keyframes rockWave{0%,100%{transform:translateY(0) rotate(-3deg);opacity:0.07}50%{transform:translateY(-7px) rotate(3deg);opacity:0.12}}
@keyframes shroomFloat{0%,100%{transform:translateY(0);opacity:0.05}50%{transform:translateY(-12px);opacity:0.09}}
@keyframes fireGlow{0%,100%{opacity:0.05;transform:scale(1)}50%{opacity:0.1;transform:scale(1.2)}}
@keyframes sundialRotate{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
.deco-bottom{position:fixed;bottom:0;left:0;right:0;z-index:9999;pointer-events:none;height:140px}
/* 元谋人 - 错开不重叠 */
.yuanmou-man{position:fixed;font-size:36px;animation:rockWave 5s ease-in-out infinite;z-index:9999}
.yuanmou1{bottom:20px;right:25px;font-size:44px}
.yuanmou2{bottom:35px;left:6%;font-size:28px;animation-delay:1.8s;animation-duration:6s;opacity:0.5}
.yuanmou3{bottom:25px;left:28%;font-size:22px;animation-delay:3.2s;animation-duration:4.5s;opacity:0.35}
/* 蘑菇 - 野生菌不同样子不同大小错开放置 */
.shroom{position:fixed;bottom:12px;z-index:9999;animation:shroomFloat 4.5s ease-in-out infinite}
.shroom1{left:15%;font-size:26px;animation-duration:4.8s}
.shroom2{left:24%;font-size:18px;animation-delay:.8s;animation-duration:5.2s}
.shroom3{left:33%;font-size:30px;animation-delay:1.6s;animation-duration:4s}
.shroom4{left:42%;font-size:20px;animation-delay:2.4s;animation-duration:5.5s}
.shroom5{left:51%;font-size:28px;animation-delay:3s;animation-duration:4.2s}
.shroom6{left:60%;font-size:16px;animation-delay:3.8s;animation-duration:5.8s}
.shroom7{left:69%;font-size:24px;animation-delay:1.2s;animation-duration:4.6s}
.shroom8{left:78%;font-size:32px;animation-delay:4.4s;animation-duration:5s}
.shroom9{left:87%;font-size:20px;animation-delay:2s;animation-duration:5.4s}
/* 火把 */
.torch-deco{position:fixed;bottom:35px;left:35px;font-size:30px;animation:fireGlow 3s ease-in-out infinite;z-index:9999}
/* 太阳历 */
.sundial-deco{position:fixed;top:75px;right:30px;font-size:22px;opacity:0.06;animation:sundialRotate 30s linear infinite;z-index:9999;pointer-events:none}
/* 登录/注册 */
.login-page{display:flex!important;align-items:center!important;justify-content:center!important;min-height:100vh!important}
.login-box{width:320px;text-align:center}
.login-title{font-size:28px;font-weight:700;color:var(--brand);margin-bottom:2px;letter-spacing:-.5px}
.login-subtitle{font-size:16px;font-weight:400;color:var(--text2);margin-bottom:20px}
.login-welcome{font-size:14px;color:var(--text2);margin-bottom:16px}
.login-box .login-field{width:100%!important;padding:10px 14px!important;border:1px solid var(--border)!important;border-radius:10px!important;font-size:14px!important;background:var(--bg)!important;margin-bottom:8px!important}
.login-box .login-field:focus{border-color:var(--brand)!important}
.login-btn{width:100%!important;padding:10px!important;background:var(--brand)!important;color:#FFF!important;border:none!important;border-radius:10px!important;font-size:15px!important;font-weight:500!important;cursor:pointer!important;margin-top:4px!important}
.login-btn:hover{background:#5B3D78!important}
.login-msg{font-size:12px;color:#c33;text-align:center;margin:4px 0;min-height:18px}
.login-msg.ok{color:#2E7D32}
.login-reglink{font-size:13px;color:var(--text2);margin-top:12px;text-align:center}
.reg-link{color:#36c;cursor:pointer;font-weight:500;text-decoration:underline}
.reg-link:hover{color:#1a4fa0}
.reg-link-btn{color:#3366CC!important;background:none!important;border:none!important;text-decoration:underline!important;padding:0!important;font-size:13px!important;font-weight:500!important;cursor:pointer!important;box-shadow:none!important;min-width:0!important;width:auto!important;height:auto!important;border-radius:0!important}
.reg-link-btn:hover{color:#1a4fa0!important;background:none!important;transform:none!important;box-shadow:none!important}
/* 导航 */
.navbar{display:flex;align-items:center;justify-content:space-between;padding:4px 16px;border-bottom:1px solid var(--border);background:rgba(255,255,255,0.6);flex-shrink:0}
.nav-left{display:flex;align-items:center;gap:8px}
.nav-logo{width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,var(--brand),var(--brand-light));display:flex;align-items:center;justify-content:center;font-size:14px;color:white}
.nav-title{font-size:34px;font-weight:400;color:var(--brand);letter-spacing:3px;font-family:'ZCOOL KuaiLe','Noto Serif SC',serif;line-height:1.15}
.nav-title-sub{font-size:14px;color:var(--text2);font-family:'Noto Serif SC',serif}
.nav-right{display:flex;align-items:center;gap:12px}
.nav-stat{font-size:12px;color:var(--text2);display:flex;align-items:center;gap:4px}
.nav-dot{width:5px;height:5px;border-radius:50%;background:var(--green);box-shadow:0 0 0 2px var(--green-bg);animation:pulse 2.5s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.8);opacity:.2}}
/* 主布局 */
.main-page{display:flex!important;flex-direction:column!important;flex:1!important;height:100vh!important;overflow:hidden!important;width:100%!important}
.app-wrap{display:flex!important;flex:1!important;min-height:0!important;padding:4px 6px!important;gap:10px!important}
.sidebar{width:14%!important;min-width:120px!important;max-width:155px!important;flex-shrink:0!important;padding-right:2px!important}
.sb-header{font-size:12px;font-weight:600;color:var(--text3);text-transform:uppercase;margin-bottom:6px;padding:0 0 0 4px}
.sb-grid{display:flex;flex-direction:column;gap:2px;margin-bottom:10px}
.sb-item{display:flex;align-items:center;gap:4px;padding:3px 0 3px 6px;border-radius:4px;font-size:12px;color:var(--text2);cursor:pointer;transition:all .12s ease}
.sb-item:hover{background:var(--brand-bg);color:var(--brand)}
.sb-icon{font-size:13px;width:16px;text-align:center}
.sb-footer{font-size:10px;color:var(--text3);padding:5px 0 3px 6px;border-top:1px solid var(--border);margin-top:4px;line-height:1.4}
.chat-area{flex:1!important;min-width:0!important;display:flex!important;flex-direction:column!important}
/* 历史记录 */
.hist-header{font-size:11px;font-weight:600;color:var(--text3);text-transform:uppercase;margin-bottom:4px;padding:0 0 0 6px;margin-top:6px}
.hist-empty{font-size:11px;color:var(--text3);padding:4px 6px;text-align:left}
.hist-item{display:flex;align-items:center;padding:3px 0 3px 6px;border-radius:4px;font-size:11px;color:var(--text2);cursor:pointer;transition:all .12s ease;margin-bottom:2px}
.hist-item:hover{background:var(--brand-bg);color:var(--brand)}
.hist-title{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hist-del{font-size:10px;color:var(--text3);padding:0 4px;border-radius:3px;opacity:0;transition:opacity .12s}
.hist-item:hover .hist-del{opacity:.6}.hist-del:hover{opacity:1!important;color:#c33!important}
.hist-new-btn2{width:100%!important;padding:5px!important;background:var(--brand-bg)!important;color:var(--brand)!important;border:1px dashed var(--brand-light)!important;border-radius:6px!important;font-size:12px!important;font-weight:500!important;cursor:pointer!important;margin-top:3px!important}
.hist-new-btn2:hover{background:rgba(111,74,142,0.08)!important}
.logout-btn{width:100%!important;padding:5px!important;background:transparent!important;color:var(--text3)!important;border:1px solid var(--border)!important;border-radius:6px!important;font-size:11px!important;margin-top:6px!important}
.logout-btn:hover{color:#c33!important;border-color:#c33!important}
/* 欢迎页 */
.welcome-page{display:flex!important;align-items:center!important;justify-content:center!important;height:100vh!important;width:100%!important;overflow:hidden!important}
.welcome-inner{text-align:center;max-width:620px;padding:30px 24px}
.wel-icon{font-size:64px;margin-bottom:12px}
.wel-title{font-size:30px;font-weight:700;color:var(--brand);margin-bottom:6px;font-family:'ZCOOL KuaiLe',serif}
.wel-subtitle{font-size:18px;color:var(--text);margin-bottom:20px}
.wel-desc{font-size:14px;color:var(--text2);line-height:2;margin-bottom:20px}
.wel-desc b{color:var(--brand)}
.wel-start-hint{font-size:14px;color:var(--text3);margin-bottom:20px}
.wel-start-btn{font-size:18px!important;padding:12px 44px!important;background:linear-gradient(135deg,var(--brand),var(--brand-light))!important;color:#FFF!important;border:none!important;border-radius:16px!important;font-weight:600!important;cursor:pointer!important;box-shadow:0 6px 24px rgba(111,74,142,0.25)!important;transition:all .3s ease!important}
.wel-start-btn:hover{transform:translateY(-3px)!important;box-shadow:0 10px 36px rgba(111,74,142,0.35)!important}
/* 欢迎与聊天 */
.welcome-card{display:flex;gap:10px;padding:12px 16px 8px;flex-shrink:0;background:rgba(111,74,142,0.02);border-bottom:1px solid var(--border);margin:0 0 6px}
.welcome-avatar{font-size:34px;flex-shrink:0;margin-top:2px}
.welcome-title{font-size:16px;font-weight:600;color:var(--brand);margin-bottom:6px}
.welcome-sub{font-size:13px;color:var(--text2);line-height:1.7;margin-bottom:6px}
.welcome-tip{font-size:12px;color:var(--text3);font-style:italic}
.chip-bar{display:flex;flex-wrap:wrap;gap:3px;padding:0 12px 4px;justify-content:center;flex-shrink:0;margin-bottom:2px}
.chip{display:inline-flex;align-items:center;gap:2px;padding:2px 7px;background:var(--brand-bg);border:1px solid var(--border);border-radius:10px;font-size:9px;color:var(--text2);cursor:pointer;transition:all .15s ease}
.chip:hover{background:rgba(111,74,142,0.07);border-color:var(--brand-light);color:var(--brand)}
.chip-ico{font-size:10px}
.chat-wrapper{flex:1!important;display:flex!important;flex-direction:column!important;min-height:0!important}
.user-wrap{background:rgba(111,74,142,0.06)!important;border:1px solid rgba(111,74,142,0.08)!important;border-radius:14px 14px 4px 14px!important;margin:6px 0!important;padding:9px 14px!important;color:var(--text)!important;font-size:13px!important;line-height:1.65!important;max-width:85%!important;float:right!important;clear:both!important}
.bot-wrap{background:rgba(247,244,249,0.6)!important;border:1px solid var(--border)!important;border-left:3px solid var(--brand-light)!important;border-radius:14px 14px 14px 4px!important;margin:6px 0!important;padding:9px 14px!important;color:var(--text)!important;font-size:13px!important;line-height:1.65!important;max-width:100%!important;clear:both!important}
.textbox-wrap{background:var(--bg)!important;border:1.5px solid var(--border)!important;border-radius:28px!important;padding:0 4px 0 18px!important;display:flex!important;align-items:center!important;margin:0 16px 10px!important}
.textbox-wrap:focus-within{border-color:var(--brand)!important;box-shadow:0 0 0 4px rgba(111,74,142,0.08)!important}
input,textarea{background:transparent!important;color:var(--text)!important;font-size:14px!important;border:none!important;padding:10px 0!important}
.message-wrap{flex:1!important;overflow-y:auto!important;padding:4px 16px 0!important}
footer{display:none!important}
/* 文档弹窗 */
.doc-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.3);z-index:999;align-items:center;justify-content:center}
.doc-overlay.active{display:flex}
.doc-modal{background:var(--card);border-radius:16px;max-width:700px;width:90%;max-height:80vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,.1)}
.doc-modal-head{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid var(--border)}
.doc-modal-title{font-size:16px;font-weight:600;color:var(--text)}
.doc-modal-close{background:none!important;border:none!important;font-size:18px!important;color:var(--text3)!important;cursor:pointer!important;padding:4px!important}
.doc-modal-body{padding:20px;overflow-y:auto;font-size:13px;line-height:1.7}
"""

def build_ui():
    with gr.Blocks(title="楚雄师范学院 · 校园智能助手", css=CUSTOM_CSS, theme=gr.themes.Soft()) as demo:
        gr.HTML("""<div class="deco-bg"><span class="bg-petal">🌺</span><span class="bg-petal">🌸</span>
        <span class="bg-petal">🌺</span><span class="bg-petal">🌸</span><span class="bg-petal">🌺</span>
        <span class="bg-petal">🌸</span><span class="bg-petal">🌺</span><span class="bg-petal">🌸</span>
        <span class="bg-petal">🌺</span><span class="bg-petal">🌸</span></div>
        <div class="deco-bottom">
        <span class="yuanmou-man yuanmou1">🗿</span>
        <span class="yuanmou-man yuanmou2">🗿</span>
        <span class="yuanmou-man yuanmou3">🗿</span>
        <span class="shroom shroom1">🍄</span><span class="shroom shroom2">🍄</span>
        <span class="shroom shroom3">🍄</span><span class="shroom shroom4">🍄</span>
        <span class="shroom shroom5">🍄</span><span class="shroom shroom6">🍄</span>
        <span class="shroom shroom7">🍄</span><span class="shroom shroom8">🍄</span>
        <span class="shroom shroom9">🍄</span>
        <span class="torch-deco">🔥</span>
        <span class="sundial-deco">☀️</span></div>""")

        user_state = gr.State(None)
        convs_state = gr.State([])
        chat_state = gr.State([])

        # ======== 登录页面 ========
        with gr.Column(visible=True, elem_classes="login-page") as login_page:
            with gr.Column(elem_classes="login-box"):
                gr.HTML('<div class="login-title">楚雄师范学院</div>')
                gr.HTML('<div class="login-subtitle">校园智能助手</div>')
                gr.HTML('<div class="login-welcome">欢迎回来，请登录</div>')
                login_user = gr.Textbox(label="", placeholder="用户名", elem_classes="login-field", container=False)
                login_pass = gr.Textbox(label="", placeholder="密码", type="password", elem_classes="login-field", container=False)
                login_msg = gr.HTML('<div class="login-msg"></div>')
                login_btn_submit = gr.Button("登录", elem_classes="login-btn")
                gr.HTML('<div class="login-reglink">还没有账号？</div>')
                to_reg_btn = gr.Button("注册账号", variant="link", size="sm", elem_classes="reg-link-btn")

        # ======== 注册页面 ========
        with gr.Column(visible=False, elem_classes="login-page") as reg_page:
            with gr.Column(elem_classes="login-box"):
                gr.HTML('<div class="login-title">楚雄师范学院</div>')
                gr.HTML('<div class="login-subtitle">校园智能助手</div>')
                gr.HTML('<div class="login-welcome">创建你的专属账号</div>')
                reg_user = gr.Textbox(label="", placeholder="用户名（至少2位）", elem_classes="login-field", container=False)
                reg_pass = gr.Textbox(label="", placeholder="密码（至少3位）", type="password", elem_classes="login-field", container=False)
                reg_msg = gr.HTML('<div class="login-msg"></div>')
                reg_btn_submit = gr.Button("注册", elem_classes="login-btn")
                gr.HTML('<div class="login-reglink">已有账号？</div>')
                to_log_btn = gr.Button("返回登录", variant="link", size="sm", elem_classes="reg-link-btn")

        # ======== 欢迎页面（登录后先显示） ========
        with gr.Column(visible=False, elem_classes="welcome-page") as welcome_page:
            with gr.Column(elem_classes="welcome-inner"):
                gr.HTML('<div class="wel-icon">🎓</div>')
                gr.HTML('<div class="wel-title">同学你好呀！👋</div>')
                gr.HTML('<div class="wel-subtitle">欢迎来到楚雄师范学院校园智能助手</div>')
                gr.HTML('<div class="wel-desc">我是你的专属校园AI小助手，知识库里有10篇校园文档、200条知识片段。<br><br>📚 无论是<b>图书馆几点开门</b>、🏠 <b>宿舍几点关门</b>、🍜 <b>食堂用餐</b><br>🎓 <b>奖学金怎么申请</b>、📖 教务选课、🌐 校园网络、🏥 校医院、🧠 心理咨询<br><br>关于校园生活的任何问题，随时问我！我会基于知识库给你准确、有据可依的答案。</div>')
                gr.HTML('<div class="wel-start-hint">准备好了吗？点击下方按钮开始咨询～</div>')
                start_btn = gr.Button("🚀 开始咨询", elem_classes="wel-start-btn")

        # ======== 主页面（点击开始咨询后） ========
        with gr.Column(visible=False, elem_classes="main-page") as main_page:
            gr.HTML(f"""<div class="navbar"><div class="nav-left">
            <div class="nav-logo">🎓</div><div class="nav-title">楚雄师范学院</div><div class="nav-title-sub">校园智能助手</div>
            </div><div class="nav-right">
            <div class="nav-stat">📚 {DOC_COUNT} 条知识</div>
            <div class="nav-stat"><span class="nav-dot"></span> 在线</div>
            </div></div>""")

            with gr.Row(elem_classes="app-wrap"):
                with gr.Column(elem_classes="sidebar", scale=1):
                    gr.HTML(build_sidebar_html())
                    gr.HTML('<div class="hist-header">对话历史</div>')
                    hist_html = gr.HTML('<div class="hist-empty">暂无历史对话</div>')
                    newchat_btn = gr.Button("➕ 新对话", elem_classes="hist-new-btn2")
                    logout_btn = gr.Button("退出登录", elem_classes="logout-btn")

                with gr.Column(elem_classes="chat-area", scale=9):
                    gr.HTML(build_welcome_html())
                    gr.HTML(build_chips_html())
                    with gr.Column(elem_classes="chat-wrapper"):
                        chat = gr.ChatInterface(fn=respond, title="", description="")
                    gr.HTML(build_modal_html())

        # Bridge 组件
        convid_input = gr.Textbox(visible=False, elem_id="convIdBridge")
        load_trigger = gr.Button("加载", visible=False, elem_id="loadTrigger")
        del_trigger = gr.Button("删除", visible=False, elem_id="delTrigger")

        # ======== 登录逻辑 ========
        def on_login(user, pwd):
            if not user or not pwd:
                return '<div class="login-msg">请输入用户名和密码</div>', gr.update(), gr.update(), gr.update(), gr.update()
            ok, msg, uid = auth.login(user, pwd)
            if not ok:
                return f'<div class="login-msg">{msg}</div>', gr.update(), gr.update(), gr.update(), gr.update()
            SESSION["user_id"] = uid; SESSION["username"] = user
            cid = auth.create_conversation(uid, "新对话")
            SESSION["conv_id"] = cid; SESSION["messages"] = []
            convs = auth.get_user_conversations(uid)
            return '<div class="login-msg"></div>', gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), convs

        def on_register(user, pwd):
            ok, msg = auth.register(user, pwd)
            if ok:
                return '<div class="login-msg ok">注册成功，请登录</div>', gr.update(visible=True), gr.update(visible=False)
            return f'<div class="login-msg">{msg}</div>', gr.update(), gr.update()

        login_btn_submit.click(on_login, [login_user, login_pass], [login_msg, login_page, reg_page, welcome_page, main_page, convs_state])
        reg_btn_submit.click(on_register, [reg_user, reg_pass], [reg_msg, login_page, reg_page])

        # ======== 登出/切换 ========
        start_btn.click(lambda: (gr.update(visible=False), gr.update(visible=True)), None, [welcome_page, main_page])
        to_reg_btn.click(lambda: (gr.update(visible=False), gr.update(visible=True)), None, [login_page, reg_page])
        to_log_btn.click(lambda: (gr.update(visible=True), gr.update(visible=False)), None, [login_page, reg_page])
        def refresh_hist(convs):
            if not convs:
                return '<div class="hist-empty">暂无历史对话</div>'
            html = ''
            for c in convs[:5]:
                cid = c["id"]
                title = c.get("title", "新对话")[:25]
                safe = title.replace("'","\\'")
                html += f'<div class="hist-item" data-id="{cid}"><span class="hist-title">{safe}</span><span class="hist-del" data-id="{cid}">x</span></div>'
            return html

        convs_state.change(refresh_hist, [convs_state], [hist_html])

        # ======== 新对话 ========
        def do_new_chat():
            if not SESSION["user_id"]: return gr.update(), []
            cid = auth.create_conversation(SESSION["user_id"], "新对话")
            SESSION["conv_id"] = cid; SESSION["messages"] = []
            return auth.get_user_conversations(SESSION["user_id"]), []

        newchat_btn.click(do_new_chat, None, [convs_state, chat_state])

        # ======== 加载/删除对话 ========
        def do_load_conv(cid_str):
            if not cid_str or not SESSION["user_id"]: return [], gr.update(), gr.update()
            try: cid = int(cid_str)
            except: return [], gr.update(), gr.update()
            conv = auth.load_conversation(cid)
            if not conv: return [], gr.update(), gr.update()
            SESSION["conv_id"] = cid; SESSION["messages"] = conv["messages"]
            history = []
            msgs = conv["messages"]
            for i in range(0, len(msgs)-1, 2):
                if i+1 < len(msgs) and msgs[i]["role"] == "user":
                    history.append([msgs[i]["content"], msgs[i+1]["content"]])
            return history, auth.get_user_conversations(SESSION["user_id"]), gr.update()

        def do_del_conv(cid_str):
            if not cid_str or not SESSION["user_id"]: return gr.update()
            try: cid = int(cid_str)
            except: return gr.update()
            auth.delete_conversation(cid)
            if SESSION["conv_id"] == cid: SESSION["conv_id"] = None; SESSION["messages"] = []
            return auth.get_user_conversations(SESSION["user_id"])

        load_trigger.click(do_load_conv, [convid_input], [chat_state, convs_state, chat_state])
        del_trigger.click(do_del_conv, [convid_input], [convs_state])

        # ======== 退出登录 ========
        def do_logout():
            SESSION["user_id"] = None; SESSION["username"] = None
            SESSION["conv_id"] = None; SESSION["messages"] = []
            return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update()

        logout_btn.click(do_logout, None, [login_page, welcome_page, main_page, reg_page, convs_state])

    return demo

if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="127.0.0.1", server_port=7860, share=False, show_error=True,
        css=CUSTOM_CSS, theme=gr.themes.Soft(),
        js="""window.openDoc=function(l,t){var b=document.getElementById('docBody'),s=document.getElementById('doc-'+l);if(b&&s){b.innerHTML=s.innerHTML;document.getElementById('docTitle').textContent='📄 '+t;document.getElementById('docOverlay').classList.add('active');b.scrollTop=0;}};window.closeDoc=function(){document.getElementById('docOverlay').classList.remove('active');};document.addEventListener('keydown',function(e){if(e.key==='Escape')window.closeDoc();});if(!window._histBound){window._histBound=true;document.addEventListener('click',function(e){var t=e.target.closest('.hist-item');if(t&&!e.target.closest('.hist-del')){var id=t.getAttribute('data-id');if(id){var i=document.getElementById('convIdBridge');if(i){i.value=id;i.dispatchEvent(new Event('input',{bubbles:true}));var b=document.getElementById('loadTrigger');if(b)b.click();}}}});document.addEventListener('click',function(e){var d=e.target.closest('.hist-del');if(d){e.stopPropagation();var id=d.getAttribute('data-id');if(id&&confirm('确定删除此对话？')){var i=document.getElementById('convIdBridge');if(i){i.value=id;i.dispatchEvent(new Event('input',{bubbles:true}));var b=document.getElementById('delTrigger');if(b)b.click();}}}});}""",
    )
