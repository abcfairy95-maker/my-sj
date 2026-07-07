"""
auth.py — 用户认证 + 对话历史存储
SQLite 数据库，users 表 + conversations 表
"""
import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "app_data.db")

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """创建用户表和对话历史表"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT DEFAULT '新对话',
            messages TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def register(username: str, password: str) -> tuple[bool, str]:
    """注册新用户，返回(成功, 消息)"""
    if not username.strip() or len(username.strip()) < 2:
        return False, "用户名至少2个字符"
    if not password or len(password) < 3:
        return False, "密码至少3个字符"
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username.strip(), _hash_password(password))
        )
        conn.commit()
        return True, "注册成功，请登录"
    except sqlite3.IntegrityError:
        return False, "用户名已存在"
    finally:
        conn.close()

def login(username: str, password: str) -> tuple[bool, str, int | None]:
    """登录验证，返回(成功, 消息, user_id)"""
    conn = get_db()
    row = conn.execute(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (username.strip(),)
    ).fetchone()
    conn.close()
    if not row:
        return False, "用户名不存在", None
    if row["password_hash"] != _hash_password(password):
        return False, "密码错误", None
    return True, "登录成功", row["id"]

def create_conversation(user_id: int, title: str = "新对话") -> int:
    """创建新对话，返回 conversation_id"""
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
        (user_id, title)
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid

def save_conversation(conv_id: int, messages: list, title: str = None):
    """保存对话消息"""
    import json
    conn = get_db()
    data = json.dumps(messages, ensure_ascii=False)
    if title:
        conn.execute(
            "UPDATE conversations SET messages=?, title=?, updated_at=datetime('now','localtime') WHERE id=?",
            (data, title, conv_id)
        )
    else:
        conn.execute(
            "UPDATE conversations SET messages=?, updated_at=datetime('now','localtime') WHERE id=?",
            (data, conv_id)
        )
    conn.commit()
    conn.close()

def load_conversation(conv_id: int) -> dict | None:
    """加载对话，返回 {id, title, messages, created_at}"""
    import json
    conn = get_db()
    row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "messages": json.loads(row["messages"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }

def get_user_conversations(user_id: int) -> list[dict]:
    """获取用户的所有对话列表"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [{
        "id": r["id"],
        "title": r["title"],
        "created_at": r["created_at"],
        "updated_at": r["updated_at"],
    } for r in rows]

def delete_conversation(conv_id: int):
    """删除对话"""
    conn = get_db()
    conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()

# 启动时初始化
init_db()
