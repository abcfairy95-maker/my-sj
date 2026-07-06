"""
API 客户端模块
封装 DeepSeek 对话 API 和 Qwen Embedding API 调用。
"""

import time
import requests

# ============================================================
# API 配置 —— 请在此填入你的 API Key
# ============================================================
DEEPSEEK_API_KEY = "sk-your-deepseek-api-key-here"  # 请替换为你的 DeepSeek API Key
QWEN_API_KEY = "sk-your-qwen-api-key-here"          # 请替换为你的阿里云 Qwen API Key

# API 端点
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/v1/chat/completions"
QWEN_EMBEDDING_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"

# 超时与重试配置
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒

# 复用连接池，减少 TCP 握手开销
_session = requests.Session()
_session.headers.update({"Content-Type": "application/json"})


def _retry_request(method: str, url: str, **kwargs) -> requests.Response:
    """带重试的 HTTP 请求，指数退避。"""
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = _session.request(method, url, timeout=TIMEOUT, **kwargs)
            if resp.status_code < 500:
                return resp
            # 5xx 服务端错误，重试
            last_exc = requests.HTTPError(f"{resp.status_code}: {resp.text[:200]}")
        except (requests.Timeout, requests.ConnectionError) as e:
            last_exc = e
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY * attempt)
    raise last_exc or RuntimeError("请求失败，已达最大重试次数")


def call_deepseek(prompt: str, system_prompt: str = "") -> str:
    """
    调用 DeepSeek Chat API，返回文本回复。
    
    参数:
        prompt: 用户输入内容
        system_prompt: 系统级指令（角色设定）
    
    返回:
        模型的文本回复
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    resp = _retry_request(
        "POST",
        DEEPSEEK_CHAT_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2048,
        },
    )
    data = resp.json()
    if "choices" not in data or not data["choices"]:
        raise ValueError(f"DeepSeek 返回异常: {data}")
    return data["choices"][0]["message"]["content"].strip()


def get_embedding(text: str) -> list[float]:
    """获取单条文本的 Embedding 向量。"""
    return get_embeddings([text])[0]


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    批量获取多条文本的 Embedding 向量。
    一次请求处理多条，避免逐条调用的网络开销。
    
    参数:
        texts: 文本列表
    
    返回:
        向量列表，每个向量为浮点数列表
    """
    if not texts:
        return []

    resp = _retry_request(
        "POST",
        QWEN_EMBEDDING_URL,
        headers={"Authorization": f"Bearer {QWEN_API_KEY}"},
        json={
            "model": "text-embedding-v3",
            "input": texts,
        },
    )
    data = resp.json()
    if "data" not in data:
        raise ValueError(f"Embedding API 返回异常: {data}")
    # 按 index 排序确保顺序
    sorted_items = sorted(data["data"], key=lambda x: x["index"])
    return [item["embedding"] for item in sorted_items]


# ============================================================
# 快速自检
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("API 客户端自检")
    print("=" * 50)

    # 1. DeepSeek 对话测试
    print("\n[1/2] 测试 DeepSeek 对话...")
    try:
        reply = call_deepseek("用一句话介绍 RAG 技术")
        print(f"DeepSeek 回复: {reply}")
    except Exception as e:
        print(f"DeepSeek 调用失败: {e}")

    # 2. Embedding 测试
    print("\n[2/2] 测试 Qwen Embedding...")
    try:
        vec = get_embedding("你好世界")
        print(f"向量维度: {len(vec)}")
        print(f"前 5 个值: {[round(v, 4) for v in vec[:5]]}")
    except Exception as e:
        print(f"Embedding 调用失败: {e}")
