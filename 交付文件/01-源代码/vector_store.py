"""
向量存储与检索模块
使用 ChromaDB 管理文档向量，支持写入和语义检索。
"""

import chromadb
from api_client import get_embeddings

# 批量 Embedding 的每批最大条数（避免单次请求过大）
EMBEDDING_BATCH_SIZE = 10


def create_vector_store(db_path: str = "./chroma_db", collection_name: str = "campus") -> chromadb.Collection:
    """
    创建或获取 ChromaDB 持久化集合。
    数据存在本地 db_path 目录，重启不丢失。
    """
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name=collection_name)
    return collection


def add_documents(collection: chromadb.Collection, documents: list[str], metadatas: list[dict] = None):
    """
    将文档批量 Embedding 后写入 ChromaDB。
    写入前清空旧数据，确保每次重建都是干净的。

    参数:
        collection: ChromaDB 集合对象
        documents: 文本片段列表
        metadatas: 每条文档对应的元数据（可选）
    """
    if not documents:
        return

    # 清空旧数据
    try:
        existing = collection.get()
        if existing and existing.get("ids"):
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    # 批量 Embedding + 分批写入
    for i in range(0, len(documents), EMBEDDING_BATCH_SIZE):
        batch_docs = documents[i:i + EMBEDDING_BATCH_SIZE]
        batch_meta = metadatas[i:i + EMBEDDING_BATCH_SIZE] if metadatas else None

        embeddings = get_embeddings(batch_docs)
        ids = [f"doc_{i + j}" for j in range(len(batch_docs))]

        add_kwargs = {
            "documents": batch_docs,
            "embeddings": embeddings,
            "ids": ids,
        }
        if batch_meta:
            add_kwargs["metadatas"] = batch_meta

        collection.add(**add_kwargs)


def search(collection: chromadb.Collection, query: str, n_results: int = 3,
           distance_threshold: float = 2.0) -> list[dict]:
    """
    语义检索：输入自然语言查询，返回最相似的文档片段。

    参数:
        collection: ChromaDB 集合
        query: 查询文本
        n_results: 返回结果数量
        distance_threshold: 距离阈值，超过此值的结果视为不相关，会被过滤

    返回:
        [{"content": str, "metadata": dict | None, "distance": float}, ...]
    """
    query_vector = get_embeddings([query])[0]

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    if not results["ids"] or not results["ids"][0]:
        return output

    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i] if results["distances"] else float("inf")
        # 距离太大说明不相关，跳过
        if distance > distance_threshold:
            continue
        output.append({
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i] if results["metadatas"] else None,
            "distance": round(distance, 3),
        })

    return output


def get_collection_stats(collection: chromadb.Collection) -> dict:
    """获取集合的统计信息。"""
    data = collection.get()
    count = len(data.get("ids", []))
    return {"document_count": count}
