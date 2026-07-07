# 🏫 楚雄师范学院校园智能问答助手

## 基于大模型与RAG的智能问答Agent搭建

---

## 📋 项目概述

本项目为楚雄师范学院搭建了一套基于 **RAG（检索增强生成）** 技术的校园智能问答系统。系统能够准确回答校园生活、教务管理、图书馆服务、奖助政策等方面的常见问题，有效解决大模型"幻觉"问题。

- **实训时间**：2026年7月6日 14:30 — 7月7日 17:15
- **核心链路**：API接入 → 知识库构建 → Embedding → 向量检索 → Agent搭建 → Web交付

---

## 🏗 系统架构

```
用户 ←→ Gradio Web界面 ←→ RAG Agent
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              DeepSeek API  Qwen Embedding  ChromaDB
              (对话生成)    (文本向量化)    (向量存储+检索)
```

### RAG 工作流程

```
用户提问："图书馆周末几点开门？"
         │
         ▼
   ① 检索 (Retrieval)
   问题 → Embedding → 向量 → ChromaDB 语义检索 Top 3
         │
         ▼
   ② 增强 (Augmentation)
   检索结果 + 用户问题 → 拼接 Prompt
         │
         ▼
   ③ 生成 (Generation)
   DeepSeek 基于文档回答："周六日 09:00-21:00"
   📚 参考来源：图书馆使用指南.md
```

---

## 🛠 技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| 大模型 | **DeepSeek Chat** | 国产性价比最优，¥1/百万token |
| Embedding | **Qwen Embedding**（阿里云） | 免费额度百万token，1024维 |
| 向量数据库 | **ChromaDB** | pip安装即用，Pythonic API |
| Web界面 | **Gradio** | 专为AI Demo设计，3行代码出界面 |
| 开发环境 | **VS Code + Qoder CLI** | AI辅助编程 |

---

## 📁 项目文件结构

```
workspace/
├── api_client.py          # DeepSeek + Qwen Embedding API 封装
├── document_loader.py     # 文档加载 + 300字切片
├── vector_store.py        # ChromaDB 向量写入 + 语义检索
├── rag_agent.py           # RAG Agent 组装 + CLI对话 + 多轮对话
├── app.py                 # Gradio Web 界面（精美CSS主题）
├── build_index.py         # 知识库索引一键构建
├── requirements.txt       # Python 依赖
├── docs/                  # 10篇校园知识文档（Markdown）
├── chroma_db/             # 向量数据库持久化存储
├── 交付文件/               # PPT内容大纲（Markdown）
├── 交付文件_docx/          # PPT内容（Word文档）
├── 交付文件_pptx/          # 答辩演示PPT
└── 验收结果/               # 验收文档
```

---

## 📚 知识库设计

### 文档覆盖（10篇，约4.1万字）

| 文档 | 内容范围 | 字数 |
|------|---------|------|
| 校园生活指南.md | 宿舍管理、食堂、校园卡、运动场地 | 5,927 |
| 教务学籍管理.md | 选课、考试、成绩、辅修、毕业论文 | 5,870 |
| 图书馆使用指南.md | 开放时间、借阅规则、电子资源、自习 | 4,820 |
| 学生奖助政策.md | 奖学金、助学金、勤工助学、评优 | 5,120 |
| 校园安全与应急.md | 保卫处、校医院、心理咨询、消防 | 5,240 |
| 校园交通与出行指南.md | 校内外交通、公交、停车、出行 | 4,220 |
| 信息技术与网络服务指南.md | WiFi、VPN、一卡通、打印服务 | 5,040 |
| 学生社团与组织指南.md | 学生会、60+社团、综合测评 | 5,230 |
| 新生入学指南.md | 报到流程、军训、入学教育、防骗 | 4,850 |
| 毕业与就业指南.md | 毕业条件、就业服务、考研、校友 | 4,320 |

### 切片策略
- **chunk_size**：300 字符
- **overlap**：50 字符（防止关键信息被切断）
- **切片数量**：181 个片段
- **平均长度**：275 字/片段

---

## 🚀 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置 API Key
编辑 `api_client.py`，填入你的 API Key：
```python
DEEPSEEK_API_KEY = "sk-xxxxxxxx"   # 从 platform.deepseek.com 获取
QWEN_API_KEY = "sk-xxxxxxxx"       # 从 dashscope.aliyun.com 获取
```

### 3. 构建知识库索引
```bash
python build_index.py
```

### 4. 启动 CLI 对话
```bash
python rag_agent.py
```

### 5. 启动 Web 界面
```bash
python app.py
# 浏览器打开 http://127.0.0.1:7861
```

---

## ✅ 测试结果

42 个问答场景全部通过，通过率 **100%**：

| 类别 | 测试问题 | 结果 |
|------|---------|:--:|
| 宿舍生活 | 宿舍晚上几点关门？可以用电饭煲吗？ | ✅ |
| 食堂 | 食堂可以用现金吗？有什么好吃的？ | ✅ |
| 图书馆 | 周末几点开门？怎么续借？怎么预约座位？ | ✅ |
| 奖助学金 | 国家奖学金多少钱？助学金怎么申请？ | ✅ |
| 教务选课 | 怎么选课？转专业条件？怎么查成绩？ | ✅ |
| 考试毕业 | 期末考试什么时候？毕业论文答辩？ | ✅ |
| 信息技术 | 校园网怎么连？VPN怎么用？校园卡丢了？ | ✅ |
| 交通出行 | 校内怎么坐车？学校附近有什么？ | ✅ |
| 社团活动 | 怎么加入社团？综合测评怎么算？ | ✅ |
| 安全医疗 | 校医院在哪？保卫处电话？心理咨询？ | ✅ |
| 新生入学 | 报到要带什么？军训多久？ | ✅ |
| 毕业就业 | 档案去哪了？考研怎么准备？ | ✅ |

---

## 🐛 Debug 案例

开发过程中解决的 4 个典型问题：

1. **split_text 死循环** — 切片到最后一段时无限循环，加 `if end == text_len: break` 解决
2. **Qwen Embedding 批量超限** — API限制一次最多10条，将 `EMBEDDING_BATCH_SIZE` 从100改为10
3. **Gradio 6.x API 不兼容** — theme/css参数位置变了，调整到 `launch()` 方法中
4. **参考来源不显示** — `build_index.py` 写入时未传 `metadatas`，修复 `load_and_split()` 返回来源信息

---

## 🎓 技术复盘

| 能力 | 体现 |
|------|------|
| 大模型 API 调用 | DeepSeek Chat + Qwen Embedding，含重试和错误处理 |
| RAG 原理 | 检索→增强→生成完整链路 |
| Prompt Engineering | 角色设定 + 引用约束 + 兜底策略 |
| 向量数据库 | ChromaDB 写入、索引、语义检索、距离过滤 |
| AI 辅助开发 | 全部模块由 AI 生成，人负责调试集成 |
| Web 应用 | Gradio + 自定义CSS主题 + 多轮对话 |

---

## 📖 拓展学习路径

1. **框架化开发** — 用 LangChain 或 LlamaIndex 重构
2. **多模态 RAG** — 检索文字 + 图片 + 表格
3. **Agentic RAG** — AI 自主决定检索策略
4. **Graph RAG** — 知识图谱跨文档推理
5. **评估与优化** — RAGAS 量化评估检索和生成质量
