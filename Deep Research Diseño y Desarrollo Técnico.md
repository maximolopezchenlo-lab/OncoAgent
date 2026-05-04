Technical Design Document for OncoAgent: A Multi-Agent System for Early Oncology Detection on AMD Instinct MI300X Infrastructure
The convergence of multi-agent systems and high-performance hardware acceleration represents the next frontier in clinical decision support. The OncoAgent project is designed to address the critical challenge of early cancer detection by extracting actionable insights from unstructured clinical narratives. The technical architecture defined in this document prioritizes stateful orchestration, domain-specific fine-tuning on AMD Instinct MI300X accelerators, and the integration of guideline-anchored retrieval systems to ensure clinical safety and precision. This report provides a comprehensive technical roadmap for implementing OncoAgent within a ROCm-powered environment, bridging the gap between raw medical text and evidence-based oncology recommendations.
Multi-Agent Workflow Orchestration and State Management
The design of a clinical multi-agent system requires a departure from linear, deterministic pipelines toward stateful, iterative workflows. In the OncoAgent architecture, the interaction between agents is modeled as a directed graph where nodes represent specialized functions and edges define the logic for state transitions. The primary orchestration challenge involves managing the transition from an initial triage phase to a deep-dive oncological analysis while maintaining a complete audit trail of the reasoning process.[1, 2]
Comparative Analysis of Agentic Frameworks
The selection of an orchestration framework dictates the system's ability to handle complex, cyclical reasoning patterns. A comparative analysis of leading frameworks reveals distinct trade-offs in terms of control, scalability, and clinical reliability.
Framework
Core Philosophy
Memory Mechanism
Best For
Clinical Suitability
LangGraph
Graph-based state machines
Persistent checkpoints
Stateful, cyclical workflows
High (Deterministic transitions)
CrewAI
Role-based collaboration
RAG-supported role memory
Sequential, pipeline tasks
Medium (Opinionated structure)
AutoGen
Conversational loops
Conversation history
Code generation & chat
Low (Potential for runaway loops)
For OncoAgent, LangGraph is the recommended framework. Unlike simpler alternatives, LangGraph represents workflows as stateful graphs where every step is a node and every transition is an edge governed by conditional logic.[1, 3] This is particularly critical in oncology, where a specialist agent may need to loop back to the triage agent to request additional information—such as missing laboratory values or clarification on symptoms—before finalizing a risk score.[4, 5] LangGraph’s ability to persist state through checkpoints ensures that the system can recover from failures and provides a mechanism for human-in-the-loop (HITL) validation, which is a regulatory necessity in HealthTech.[1, 6]
Interaction Logic: The Router-Specialist Handoff
The OncoAgent workflow begins with the Router Agent, acting as a clinical triage system. Its primary responsibility is the analysis of raw input text—such as pathology reports, radiology impressions, or physician notes—to determine the urgency and the specific oncological specialty required.[7, 8]
The handoff mechanism between the Router and the Specialist Agent is governed by a strict state schema. The Router performs intent classification and entity extraction, populating a TypedDict state object that is passed to the Specialist.[5, 9] This interaction is not a one-way transfer; the Specialist Agent can invoke a "request_info" event if the triage data is insufficient to reach a staging conclusion.[10]
The coordination logic emphasizes augmentation over replacement. The system follows a two-phase assessment: autonomous intake followed by collaborative acuity assessment.[8, 11] During the handoff, "Key Detail Preservation" is the primary metric, ensuring that critical data like tumor size markers, TNM staging fragments, and patient comorbidities are carried forward without loss.[12, 13]
Agent Category
Model Size (Rec.)
Primary Responsibility
Key Output
Triage (Router)
7B - 8B
Intent classification, urgency scoring
Structured Triage Summary
Specialist (Oncology)
70B - 405B
Clinical reasoning, staging alignment
Risk Assessment & Justification
Coordinator
8B
Graph orchestration, task routing
State Transition Signal
The Specialist Agent implements the American Joint Committee on Cancer (AJCC) or NCCN staging logic, which requires analyzing the "T" (tumor size), "N" (node involvement), and "M" (metastasis) parameters from the text.[13, 14, 15] The interaction is formalized such that the Specialist only proceeds if the Router provides enough granular data; otherwise, a recursive loop is triggered to query the physician or external electronic health records (EHR).[5, 11]
Specialized Fine-Tuning Strategy for Clinical Oncology
Standard open-source models like Llama 3.1 possess broad knowledge but lack the specific reasoning patterns required to justify a high-stakes cancer risk assessment. The OncoAgent strategy employs intensive fine-tuning to internalize clinical causality and ensure that the model’s outputs are traceable to medical evidence.[16, 17, 18]
Pipeline for AMD Instinct MI300X
The AMD Instinct MI300X, with its 192GB of HBM3 memory, provides the necessary headroom for fine-tuning high-parameter models like Llama 3-70B or even 405B using Parameter-Efficient Fine-Tuning (PEFT).[19, 20] The training pipeline is optimized for the ROCm 6.2 ecosystem, utilizing the high memory bandwidth to process long-context clinical documents without aggressive truncation.[21, 22]
The implementation utilizes QLoRA (Quantized Low-Rank Adaptation), which quantizes the base model to 4-bit NormalFloat (NF4) while training low-rank adapter matrices.[23, 24] This approach minimizes VRAM usage while maintaining the expressive power needed for medical Q&A. The training configuration prioritizes the projection layers (q_proj, v_proj, k_proj, o_proj) to capture the intricate linguistic patterns of radiology and pathology reports.[17, 25]
Dataset Ingestion and Clinical Justification Schema
The model must be taught to "think" like an oncologist. This requires a JSONL dataset where each entry includes a detailed reasoning trace. The OncoAgent dataset architecture is derived from frameworks like OncoCoT, which simulate the spatiotemporal decision-making process of real-world oncology boards.[14, 18]
The JSONL structure must follow a prompt/completion format that emphasizes causality. The thought field is critical for teaching the model the intermediate steps of clinical reasoning, such as identifying a spiculated mass and correlating it with hilar lymphadenopathy before concluding a high risk of malignancy.[18, 26]
Representative JSONL Schema for Clinical Reasoning:
{
  "case_metadata": {
    "age": 62,
    "gender": "Female",
    "imaging_type": "Chest CT"
  },
  "prompt": "Analyze the CT report: '2.5 cm spiculated mass in the left upper lobe with associated pleural thickening and enlarged mediastinal lymph nodes (1.2 cm)'. Provide a malignancy risk assessment with clinical justification.",
  "thought": "1. Identify lesion characteristics: 2.5 cm mass is T1c/T2a. 2. Morphology: 'Spiculated' is highly indicative of malignancy. 3. Node involvement: Mediastinal nodes (1.2 cm) suggest N2 involvement. 4. Correlate findings: T2aN2 staging points to Stage IIIA, which carries high risk and requires surgical consultation.",
  "completion": {
    "risk_score": 0.85,
    "assessment": "High suspicion for lung malignancy (likely Stage IIIA).",
    "justification": "Risk based on spiculated mass morphology and suspicious mediastinal lymphadenopathy consistent with nodal involvement.",
    "citations":
  }
}
This structure forces the model to internalize "Clinical Logic-Constrained Rethinking," where it must re-evaluate its initial diagnosis based on the full longitudinal outcome of the case, effectively reducing the probability of premature or incorrect assessments.[18]
ROCm Software Stack for Efficient Fine-Tuning
Executing this pipeline on AMD hardware requires a specific set of libraries adapted for the ROCm backend. The primary goal is to bypass the "NVIDIA presumption" often baked into ML libraries.[27]
Library / Tool
Version / Source
Function
ROCm PyTorch
2.5.0+ (Nightly/Release)
Core tensor computations
bitsandbytes-rocm
ROCm fork (from source)
8-bit/4-bit quantization [28, 29]
Unsloth [amd]
pip install unsloth[amd]
2x faster training for Llama 3 [25]
FlashAttention-2
AMD-optimized (CK/Triton)
O(n) memory attention mechanisms [19, 30]
Hugging Face Optimum
Optimum-AMD
Hardware-specific optimizations
Axolotl (ROCm)
Manual dependency override
High-level training orchestration [27]
The installation of bitsandbytes is the most critical step. Since the mainstream version is CUDA-centric, the ROCm fork must be compiled with cmake -DCOMPUTE_BACKEND=hip -DHIP_TARGETS=gfx942 to ensure the quantization kernels are correctly generated for the MI300X architecture.[27, 29] Furthermore, the environment variable HSA_OVERRIDE_GFX_VERSION=9.4.2 must be set to ensure that compiled kernels are compatible with the specific hardware revisions of the Instinct series.[25]
Retrieval-Augmented Generation for Clinical Guidelines
A fundamental architectural decision in OncoAgent is the rejection of a "weights-only" approach for the Specialist Agent. While fine-tuning teaches the model how to reason and how to speak the language of oncology, it cannot guarantee up-to-date adherence to clinical practice guidelines (CPG) which change frequently. Therefore, the Specialist Agent is acoupled to a Guideline-Anchored RAG system.[31, 32, 33]
RAG vs. Fine-Tuning Analysis
The decision to use a hybrid architecture (FT+RAG) is based on the necessity for "groundedness" and "traceability." Clinical guidelines from the NCCN or ESMO are the gold standard for evidence-based care. Fine-tuning alone can lead to "confident hallucinations," where the model speaks with clinical authority but provides outdated or incorrect treatment regimens.[31, 33]
Feature
Fine-Tuning Only
Guideline-Anchored RAG
Hybrid (OncoAgent)
Knowledge Recency
Stale (at time of train)
Real-time updates
Best of both worlds
Traceability
None (internal weights)
Explicit citations
High (Weights + Citations)
Hallucination Risk
ConfidentFabrications
Retrieval Failure
Minimized via cross-check
Cost
High (Periodic retuning)
Low (Database update)
Balanced
The OncoAgent system uses RAG for "open-book" exam capabilities, allowing the specialist to consult trusted references on-the-fly.[32] This is particularly critical for oncology, where biomarkers and newly approved drugs emerge monthly.
Vector Database and Parsing Architecture
Oncology guidelines are notoriously difficult to ingest because they are structured as complex flowcharts and decision trees. A "naive RAG" approach that chunks text into arbitrary 512-token segments will fail to capture the hierarchical logic of these documents.[34, 35]
The OncoAgent RAG architecture implements a structured ingestion pipeline:
JSON Parsing: Guidelines (NCCN/ESMO) are parsed into JSON records that capture nodes (patient profiles) and edges (recommended treatments). The schema includes page_id, visual_type (flowchart/table/text), and entities.[34, 36]
Semantic/Structure-Based Chunking: The system uses recursive chunking that respects the structure of the flowchart. Each chunk represents a complete decision node, ensuring that the retriever provides a meaningful clinical context rather than a fragmented text snippet.[35, 37]
Embedding & Retrieval: Using a domain-specific embedding model (e.g., MedCPT), JSON objects are stored in a vector database like Qdrant or FAISS. The retrieval is optimized using a cosine similarity score:
retrieval_score(q,d)= 
∥E(q)∥∥E(d)∥
E(q)⋅E(d)
​
 
where E is the embedding function.[34]
Agentic Refinement (Insufficiency Loop): The Specialist Agent performs an "Insufficiency Check." After retrieving the guidelines and generating a plan, a secondary LLM call evaluates the plan against a checklist: Does it follow the correct sequencing? Are there references present? If the assessment is "Insufficient," the RAG query is rewritten and executed again.[34, 36]
Infrastructure and Serving on AMD Instinct MI300X
The deployment phase of OncoAgent focuses on maximizing the throughput of the fine-tuned Specialist model and ensuring that the entire multi-agent system is scalable and easily accessible for clinical prototyping.
Repository Structure and vLLM Serving
The model serving layer utilizes vLLM, which is the industry standard for high-throughput inference on AMD GPUs. vLLM implements PagedAttention, which partitions the Key-Value (KV) cache into non-contiguous memory blocks, effectively eliminating memory waste.[21, 38, 39]
Recommended Repository Structure: /OncoAgent ├── /agents │ ├── triage_agent.py # Router logic (LangGraph nodes) │ ├── oncology_agent.py # Specialist logic + RAG integration │ └── validator_agent.py # Safety/Insufficiency check nodes ├── /infra │ ├── Dockerfile.rocm # AMD optimized build │ ├── vllm_config.yaml # Tensor/Pipeline parallelism settings │ └── serve_api.py # FastAPI wrapper for MAS ├── /finetuning │ ├── dataset.jsonl # Structured reasoning data │ └── train_qlora.py # ROCm-specific training script ├── /rag_store │ ├── ingest_nccn.py # PDF-to-JSON guideline parser │ └── vector_index/ # Persistence for Qdrant/FAISS └── README.md # TDD and deployment guide
To serve a 70B parameter oncology specialist on the MI300X, the system utilizes Tensor Parallelism (TP) to shard the model weights across the 8 GPUs typically found in an MI300X node.[19, 40] For extremely high concurrency, Data Parallelism (DP) is combined with Expert Parallelism (EP) if a Mixture-of-Experts (MoE) architecture like Mixtral is selected.[41]
Hardware Optimization for MI300X
The MI300X benefits from specific kernel-level optimizations that must be enabled during deployment.
FP8 Quantization: Using fp8 for weights and the KV cache can improve throughput by up to 1.6x.[21, 42] AMD provides pre-built "Quark" quantized models on Hugging Face specifically for the MI300X.[21]
Skinny GEMM: Optimization for low-batch decoding, allowing matrix multiplications to process faster for real-time clinician chat interfaces.[43, 44]
FlashAttention-2: Integrating Triton-based FlashAttention kernels allows the specialist to handle long clinical reports with quadratic complexity reduction.[30, 38, 42]
vLLM Launch Command for OncoAgent:
export MODEL="/app/models/OncoAgent-70B-FT"
vllm serve $MODEL \
  --tensor-parallel-size 8 \
  --max-model-len 32768 \
  --quantization fp8 \
  --kv-cache-dtype fp8 \
  --enforce-eager \
  --device cuda \
  --host 0.0.0.0 --port 8000
Note: cuda is aliased to ROCm in these environments.[38, 45]
Packaging as a Hugging Face Space
For the prototype to be functional as a "Space" on Hugging Face, it must be containerized using a Docker image that includes the full ROCm stack. Hugging Face Spaces support Docker as a primary SDK.[46]
Steps for Space Configuration:
Metadata: Set sdk: docker in the README.md YAML block.
Base Image: Use rocm/vllm:rocm6.2_mi300_ubuntu20.04_py3.9_vllm_0.6.4 for maximum compatibility with MI300X.[43]
Hardware Selection: Request the "AMD Instinct MI300X" hardware flavor in the Space settings.[47]
Security: Use Hugging Face Secrets to manage HF_TOKEN for accessing gated models like Llama 3.1.[46, 48]
Exposed Port: Set app_port: 7860 in the metadata to align with the frontend (Streamlit or FastAPI).[46]
Clinical Safety and Explainability Framework
The deployment of OncoAgent is not merely a technical task but a clinical safety imperative. The architecture includes specific layers to ensure that every recommendation is explainable and verifiable by a human oncologist.
The "Thought" Prompting and Traceability
The Specialist Agent is prompted using Chain-of-Thought (CoT) with Self-Consistency.[17, 49] By forcing the model to show its work—breaking down the staging logic step-by-step—the system provides a "defensive prompt scaffold" that reduces hallucinations.[49] The final output is structured to include:
Clinical Summary: A high-level assessment of the risk.
Reasoning Steps: The intermediate logic applied to the patient's data.
Guideline Citations: Direct links to the retrieved NCCN/ESMO passages.[26, 34]
Evaluation Metrics for Oncology Agents
The system's performance is measured using a specialized "mGPS" (modified Generative Performance Score), which combines Guideline Concordance with Hallucination Severity.[33]
Metric
Definition
Target
mGPS
Weighted score of concordance and factuality
> 0.75
TNM Accuracy
Consistency with ground-truth staging [14]
> 90%
Hallucination Rate
Frequency of medically incorrect claims
< 1%
Latency (TTFT)
Time to first reasoning token
< 2.0s
Recall@5 (RAG)
Retrieval accuracy of correct guideline node
> 95%
Human-in-the-Loop (HITL) Integration
LangGraph allows the insertion of "Interrupt" nodes. In high-risk scenarios—such as when the Specialist Agent recommends a high-toxicity chemotherapy regimen—the graph state is paused. A clinician must review the "Thought Trace" and the "RAG Citations" in a specialized UI (e.g., Streamlit) and either "Approve," "Modify," or "Reject" the plan before the state proceeds to the final report generation node.[5, 10]
Riesgos Técnicos y Mitigaciones
The development of OncoAgent on AMD's cutting-edge Instinct infrastructure involves several non-trivial technical risks. These must be managed through proactive architectural decisions and environment tuning.
Hardware and Infrastructure Risks
The MI300X is a powerful but complex accelerator. Driver-level issues and memory fragmentation are the primary bottlenecks.
GPU Recovery Failures: Earlier versions of ROCm experienced error recovery failures on the MI300X when encountering uncorrectable memory errors.[50, 51]
Mitigation: Ensure the infrastructure is running ROCm 6.2.2 or later, which specifically addresses the MI300X recovery state.[51] Implement automated node health checks using amd-smi monitor to detect and restart "stuck" kernels.
VRAM Fragmentation and Preemption: In high-concurrency environments, vLLM can preempt requests if the KV cache fills up, leading to high latency spikes.[40]
Mitigation: Increase gpu_memory_utilization (e.g., to 0.95) and decrease max_num_seqs to provide more breathing room for long-context clinical tasks.[40] Use Tensor Parallelism (TP=8) to shard model weights, freeing up more memory per GPU for the KV cache.
Kernel Compilation Time: JIT compilation of Triton or CK kernels can lead to long startup times, which may trigger timeouts in cloud environments like Hugging Face Spaces.[40, 52]
Mitigation: Use pre-compiled GEMM tables and set HSA_NO_SCRATCH_RECLAIM=1 to optimize kernel memory management.[19, 47] Pre-warm the vLLM server by running a dummy inference request during the container initialization phase.[53]
Multi-Agent Coordination Risks
Agentic systems introduce failure modes that are absent in single-model deployments, particularly concerning "cascading errors".[54]
Hallucination Propagation: A mistake by the Router (e.g., misidentifying "no tumor" as "tumor") is treated as ground truth by the Specialist, leading to a disastrously wrong clinical assessment.[54, 55]
Mitigation: Implement "Output Validation" at every handoff. Run a secondary, lightweight schema check and range check on the Router’s output before the Specialist consumes it.[54] Use a dedicated "Validator Agent" to cross-reference the specialist's staging against the original raw text.[34]
Context Dilution and Window Limits: As agents pass messages back and forth, earlier critical clinical context (like patient age or comorbidities) may drop out of the context window.[54, 56]
Mitigation: Use a "Stateful Persistence" model in LangGraph where core patient demographics are pinned in a special "Profile" field that is prepended to every agent prompt, regardless of the conversation history length.[9, 18]
Emergent Agency and Loops: Peer-to-peer agents can converge on a hallucinated consensus or enter infinite negotiation loops.[55, 56]
Mitigation: Prioritize a hierarchical architecture (Router-Specialist) over peer-to-peer swarms. Define explicit max_steps for every graph traversal and use a "Supervisor" node to terminate any workflow that exceeds a complexity threshold.[7, 56]
ROCm Compatibility Risks
The "NVIDIA-first" nature of many ML libraries creates friction for AMD developers.
Library Version Drift: Specific versions of transformers or accelerate may break ROCm support if updated carelessly.[27]
Mitigation: Use "Pinned Dependencies" in the repository. Provide a validated Docker image where the versions of ROCm, PyTorch, and bitsandbytes are locked.[27, 43]
Quantization Bugs: Versions of bitsandbytes earlier than 0.49.2 have been known to cause 4-bit decode NaN bugs on AMD GPUs.[25]
Mitigation: Exclusively use the rocm_enabled branch of the official ROCm bitsandbytes repository and verify the installation version (target 0.42.0+ for ROCm 6.2) before starting the training loop.[28, 29]
By following this technical design, OncoAgent will leverage the massive compute power of the AMD Instinct MI300X to provide a scalable, safe, and highly accurate cancer detection service that remains grounded in the latest oncological evidence. The combination of stateful LangGraph orchestration and guideline-anchored RAG ensures that the system is not just a technological prototype but a reliable tool for clinical professionals.
--------------------------------------------------------------------------------
LangChain vs CrewAI vs AutoGen - Which to Use (2026) - Blogs - Trixly AI Solutions, https://www.trixlyai.com/blogs/langchain-vs-crewai-vs-autogen-which-ai-agent-framework-should-you-actually-use
README.md - langchain-ai/langgraph-example - GitHub, https://github.com/langchain-ai/langgraph-example/blob/main/README.md
LangGraph: Build Stateful AI Agents in Python, https://realpython.com/langgraph-python/
Build a custom RAG agent with LangGraph - Docs by LangChain, https://docs.langchain.com/oss/python/langgraph/agentic-rag
Building a clinical intake assistant using LangGraph | by Wang ..., https://medium.com/@wangjunwei38/building-a-clinical-intake-assistant-using-langgraph-d602607bd7ed
Comparing Popular AI Agent Frameworks: LangChain, AutoGen, and CrewAI – Which is the Best Choice for You? - Bestarion, https://bestarion.com/langchain-vs-autogen-vs-crewai/
How to Build Multi-Agent AI Systems for Complex Workflows | Team 400 Blog, https://team400.ai/blog/2026-04-23-build-multi-agent-ai-systems-workflows
ED-Triage-Agent: A Framework for Human-AI Collaborative Emergency Triage | medRxiv, https://www.medrxiv.org/content/10.64898/2026.02.17.26346501v1.full-text
Day 3 - Building an agent with LangGraph - Kaggle, https://www.kaggle.com/code/markishere/day-3-building-an-agent-with-langgraph
Microsoft Agent Framework Workflows Orchestrations - Handoff, https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/handoff
AI Telehealth Patient Routing Agent | Cassidy AI, https://www.cassidyai.com/solutions/ai-telehealth-patient-routing-agent
Triage & Routing - microsoft/ai-agent-eval-scenario-library - GitHub, https://github.com/microsoft/ai-agent-eval-scenario-library/blob/main/business-problem-scenarios/triage-and-routing.md
\benchmarkname: Benchmarking Multimodal Real-World Clinical Reasoning for Precision Lung Cancer Diagnosis and Treatment - arXiv, https://arxiv.org/html/2604.06925v2
\benchmarkname: Benchmarking Multimodal Real-World Clinical Reasoning for Precision Lung Cancer Diagnosis and Treatment - arXiv, https://arxiv.org/html/2604.06925v1
Clinical reasoning from real-world oncology reports using large language models - PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC12615922/
Fine-Tuning Llama 3: Enhancing Accuracy in Medical Q&A With ..., https://labelstud.io/blog/fine-tuning-llama-3-enhancing-accuracy-in-medical-q-and-a-with-llms/
UltimateMedLLM-Llama3-8B: Fine-tuning Llama 3 for Medical Question-Answering - Stanford University, https://web.stanford.edu/class/archive/cs/cs224n/cs224n.1254/final-reports/256847341.pdf
OncoCoT: A Temporal-causal Chain-of-Thought ... - AAAI Publications, https://ojs.aaai.org/index.php/AAAI/article/view/40724/44685
Using AMD ROCm™ vLLM Docker Image with AMD Instinct™ MI300X, https://www.amd.com/en/developer/resources/technical-articles/how-to-use-prebuilt-amd-rocm-vllm-docker-image-with-amd-instinct-mi300x-accelerators.html
powderluv/vllm-docs: Documentation for vLLM Dev Channel releases - GitHub, https://github.com/powderluv/vllm-docs
AMD Instinct MI300X workload optimization — ROCm Documentation, https://rocm.docs.amd.com/en/docs-6.4.1/how-to/rocm-for-ai/inference-optimization/workload.html
Coding Agents on AMD GPUs: Fast LLM Pipelines for Developers - ROCm™ Blogs, https://rocm.blogs.amd.com/artificial-intelligence/coding-agent/README.html
Fine-Tuning LLaMA 3.1 on Your Custom Dataset: A Comprehensive Guide | by Ujwal Tewari | Medium, https://medium.com/analytics-vidhya/fine-tuning-llama-3-1-on-your-custom-dataset-a-comprehensive-guide-e5944dd6b5ef
Enhancing LLM Accessibility: A Deep Dive into QLoRA Through Fine-tuning Llama Model on a single AMD GPU, https://rocm.blogs.amd.com/artificial-intelligence/llama-Qlora/README.html
Fine-tuning LLMs on AMD GPUs with Unsloth Guide, https://unsloth.ai/docs/get-started/install/amd
AI-assisted protocol information extraction for improved accuracy and efficiency in clinical trial workflows - arXiv, https://arxiv.org/html/2602.00052v2
Practical AI with AMD Instinct MI300X - Eric Hartford, https://erichartford.com/practical-ai-with-amd-instinct-mi300x
Fine-tuning Llama-3.1 with QLoRA - ROCm Documentation - AMD, https://rocm.docs.amd.com/projects/ai-developer-hub/en/v5.1/notebooks/fine_tune/QLoRA_Llama-3.1.html
Fine-tuning and inference using a single GPU - ROCm Documentation - AMD, https://rocm.docs.amd.com/en/latest/how-to/rocm-for-ai/fine-tuning/single-gpu-fine-tuning-and-inference.html
vLLM V1 performance optimization — ROCm Documentation, https://rocm.docs.amd.com/en/latest/how-to/rocm-for-ai/inference-optimization/vllm-optimization.html
Fine-Tuning vs. RAG for Medical AI: A Builder's Honest Guide | by Amrita Sarkar | Apr, 2026, https://pub.towardsai.net/fine-tuning-vs-rag-for-medical-ai-a-builders-honest-guide-4efe723f2e57
Development of a RAG-based Expert LLM for Clinical Support in Radiation Oncology, https://www.medrxiv.org/content/10.1101/2025.09.16.25335813v1.full-text
Source matters: Performance of guideline-anchored RAG versus broad evidence LLMs in GI oncology. - ASCO, https://www.asco.org/abstracts-presentations/255993/abstract
Personalized RAG++ for Clinical Decision Support - Emergent Mind, https://www.emergentmind.com/topics/personalized-rag
Best Chunking Strategies for RAG Pipelines - Redis, https://redis.io/blog/chunking-strategy-rag-pipelines/
Developing an Artificial Intelligence Tool for Personalized Breast Cancer Treatment Plans based on the NCCN Guidelines - arXiv, https://arxiv.org/html/2502.15698v1
Chunking strategies for RAG tutorial using Granite - IBM, https://www.ibm.com/think/tutorials/chunking-strategies-for-rag-with-langchain-watsonx-ai
Running vLLM in Docker with AMD ROCm and the Continue.dev CLI | TinyComputers.io, https://tinycomputers.io/posts/running-vllm-in-docker-with-amd-rocm-and-the-continuedev-cli.html
Efficient LLM Agent Serving with vLLM: A Deep Dive into Research Agent Benchmarking | by Madhur Prashant | Medium, https://medium.com/@madhur.prashant7/efficient-llm-agent-serving-with-vllm-a-deep-dive-into-research-agent-benchmarking-3c07c563228a
Optimization and Tuning - vLLM, https://docs.vllm.ai/en/stable/configuration/optimization/
The vLLM MoE Playbook: A Practical Guide to TP, DP, PP and Expert Parallelism, https://rocm.blogs.amd.com/software-tools-optimization/vllm-moe-guide/README.html
ROCm 6.2.0 Release #3502, https://github.com/ROCm/ROCm/discussions/3502
AI Inference on AMD MI300X with vLLM Docker Image Validation, https://www.amd.com/en/developer/resources/technical-articles/ai-inference-on-amd-mi300x-with-vllm-docker-image-validation.html
Creating custom kernels for the AMD MI300 - Hugging Face, https://huggingface.co/blog/mi300kernels
Deploying your model - ROCm Documentation - AMD, https://rocm.docs.amd.com/en/docs-7.0.0/how-to/rocm-for-ai/inference/deploy-your-model.html
Docker Spaces - Hugging Face, https://huggingface.co/docs/hub/spaces-sdks-docker
Getting Started with AMD Instinct MI300X on Azure, https://instinct.docs.amd.com/projects/instinct-azure/latest/mi300x.html
Running inference with Hugging Face Transformers - ROCm Documentation - AMD, https://rocm.docs.amd.com/projects/ai-developer-hub/en/latest/notebooks/inference/1_inference_ver3_HF_transformers.html
The Prompt Engineering Cheat Sheet: How to Write Better AI Prompts - eWeek, https://www.eweek.com/news/prompt-engineering-cheat-sheet-guide/
AMD ROCm 6.2.2 Released To Fix Instinct MI300X Error Recovery Failure - Phoronix, https://www.phoronix.com/news/AMD-ROCm-6.2.2
ROCm 6.2.2 release notes, https://rocm.docs.amd.com/en/docs-6.2.2/about/release-notes.html
AMD Instinct MI300X workload optimization - ROCm Documentation, https://rocm.docs.amd.com/en/latest/how-to/rocm-for-ai/inference-optimization/workload.html
Installation with ROCm - vLLM, https://docs.vllm.ai/en/v0.6.6/getting_started/amd-installation.html
Multi-Agent AI Systems: Architecture & Failure Modes | Augment Code, https://www.augmentcode.com/guides/multi-agent-ai-systems
Architecture Matters for Multi-Agent Security - arXiv, https://arxiv.org/html/2604.23459v1
Why Multi-Agent Systems Fail at Scale (And Why Simplicity Always Wins) | by Bijit Ghosh, https://medium.com/@bijit211987/why-multi-agent-systems-fail-at-scale-and-why-simplicity-always-wins-7490f9002a9b
