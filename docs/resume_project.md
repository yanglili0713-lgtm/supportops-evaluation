**SupportOps-RAG：面向客服/运维工单的检索增强问答与故障诊断系统**
技术栈：Python / BM25 / BGE Embedding / FAISS-HNSW / Hybrid Retrieval / Cross-Encoder Reranker / Agentic Planner / Evaluation / Trace

* 项目介绍：构建面向客服知识库、产品文档与运维工单的检索增强问答与故障诊断系统，针对长文档切分、关键词与语义错配、证据不足导致的错误自信回答及多文档故障定位困难，设计混合检索、证据重排、可控检索决策与可追踪评测机制，提升系统证据召回、拒答可靠性与诊断可解释性。
* 评测链路：基于 SupportOpsBench seed 构建统一评测流程，覆盖意图路由、知识检索、多文档诊断、无答案拒答、证据溯源和安全边界等任务；同时支持 BANKING77 官方数据集加载与评测流程，并提供离线 sample fallback 用于 smoke test。
* 检索策略与真实指标：实现 BM25、Dense Retrieval、FAISS-HNSW、Hybrid Retrieval、Hybrid + Cross-Encoder Reranker、Planner-RAG 等策略；BM25、Dense、Hybrid、Hybrid reranker 已完成本地 seed 评测与 trace 落盘，便于按 MRR@10、Top-1 evidence precision 和 P95 latency 做对比分析。
* refusal / verifier 指标：设计 refusal policy 与 verifier 检查，对 no-answer 场景和低置信证据进行过滤；在本地 seed 评测中，no-answer refusal accuracy 为 0.95，refusal F1 为 0.80。
* trace / ablation / failure analysis：构建 JSONL trace、failure case report 和 ablation summary，支持 BM25、Dense、Hybrid、Hybrid without reranker、Hybrid with reranker、Planner-RAG 等消融，以及 top-k 和 chunk size 对照，便于回放检索失败、误拒答和 planner 误路由。通过 alpha sweep 与 failure report 分析 BM25 + Dense 线性融合在强关键词 hard-negative 场景下的排序退化问题。
* 可视化展示：基于 Streamlit 构建本地可视化 Demo，支持检索策略切换、Top-k evidence 展示、trace 回放、评测指标看板与失败案例分析，便于系统演示与误差定位。

补充评测：在 BANKING77 官方全量 test split（train=10003，test=3080）上，TF-IDF + LogisticRegression router 达到 Accuracy 0.8929、Macro-F1 0.8940，显著优于 rule baseline 的 0.2951 / 0.2933；该结果用于支撑客服意图识别与 router 评测链路。

