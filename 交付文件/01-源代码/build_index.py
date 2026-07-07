from document_loader import load_and_split
from vector_store import create_vector_store, add_documents, get_collection_stats

CHUNK_SIZE = 300
OVERLAP = 50

print("=" * 50)
print("  知识库索引构建工具")
print("=" * 50)

print("\n[1/3] 加载文档...")
chunks, sources = load_and_split("docs", chunk_size=CHUNK_SIZE, overlap=OVERLAP)
print(f"  → 从 docs/ 加载 10 篇文档，切分为 {len(chunks)} 个片段")
print(f"  → 片段平均长度: {sum(len(c) for c in chunks)//len(chunks)} 字")

print("\n[2/3] 构建向量库...")
collection = create_vector_store()

print("\n[3/3] 写入 ChromaDB...")
metadatas = [{"source": s} for s in sources]
add_documents(collection, chunks, metadatas=metadatas)
stats = get_collection_stats(collection)
print(f"  → 向量库已就绪，共 {stats['document_count']} 条")

print("\n✅ 索引构建完成！运行 python rag_agent.py 开始对话")
print(f"  或运行 python app.py 启动 Web 界面")
