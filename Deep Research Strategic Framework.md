Strategic Framework for Oncological Intelligence: Data Acquisition and Curation for the OncoAgent Triage System
The emergence of large language models (LLMs) has fundamentally altered the trajectory of clinical decision support systems, particularly within the high-stakes domain of oncology. The development of OncoAgent, a specialized Llama-3-8B system, requires an intricate data strategy that balances the depth of medical knowledge with the agility required for early-stage triage. This project necessitates a dual-pathway approach: utilizing Retrieval-Augmented Generation (RAG) to ground the model in the latest clinical practice guidelines and employing Supervised Fine-Tuning (SFT) to instill the procedural reasoning capabilities required for effective patient assessment.[1, 2, 3] The architecture focuses on the 8-billion parameter variant of Llama-3, chosen for its favorable balance of computational efficiency and latent reasoning capacity, which can be further enhanced through Parameter-Efficient Fine-Tuning (PEFT) such as LoRA and QLoRA.[2, 4, 5]
The Epistemic Core: Clinical Practice Guidelines for RAG
The primary challenge in oncological triage is the rapid evolution of "ground truth." Recommendations for staging, biomarker testing, and therapeutic interventions are updated frequently, rendering static training data obsolete within months. A RAG-based architecture addresses this by treating external guidelines as a "dynamic brain," allowing OncoAgent to query the National Comprehensive Cancer Network (NCCN), the European Society for Medical Oncology (ESMO), and the American Society of Clinical Oncology (ASCO) in real-time.[6, 7, 8] The efficacy of such a system is contingent upon the conversion of these complex, often visual, guidelines into a machine-actionable corpus.[9, 10, 11]
Strategic Sourcing of Clinical Guidelines
Identifying the optimal sources for RAG involves prioritizing repositories that provide high-density evidentiary support in formats that can be parsed with high fidelity. The NCCN Guidelines are widely considered the gold standard for algorithmic oncology, structured around clinical flowcharts and treatment pathways for over 60 cancer types.[6, 10] For OncoAgent, these must be acquired through structured digital tools like the NCCN Guidelines Navigator, which allows for a more granular navigation of nodes compared to traditional PDFs.[6, 8] ESMO provides similar value through its Clinical Practice Guidelines (CPGs) and Pocket Guidelines, which are often condensed into slide sets—highly useful for RAG as they present information in a concise, structured manner that minimizes the noise inherent in full-length review papers.[12, 13, 14]
Repository
Content Type
Processing Format
Clinical Application
NCCN Clinical Guidelines
Algorithmic Flowcharts
JSON-structured visual nodes
Definitive treatment pathways and staging [6, 9]
ESMO Pocket Guidelines
Condensed Recommendations
Text-extracted PDF/Slide Sets
Rapid bedside reference and follow-up [12, 14]
ASCO Guidelines
Topic-Specific Deep Dives
Citation-linked Vertex AI/Gemini
High-level evidence synthesis and trial data [1, 7]
PubMed Central (PMC)
Peer-Reviewed Case Reports
XML/JSON via PMC-Patients
Real-world evidence and rare case mapping [15, 16]
The process of vectorizing these sources requires a transition from raw text extraction to "agentic" or "graph-based" retrieval. Traditional RAG systems often struggle with the non-linear logic of oncology guidelines. Agentic-RAG addresses this by using a multi-step LLM process to select relevant clinical titles, retrieve matching content, and iteratively refine recommendations based on "insufficiency checks".[11, 17, 18] Graph-RAG further enhances this by mapping the guideline corpus into a medical knowledge graph, where entities (e.g., "Stage IIA", "HER2 Status") and their relationships (e.g., "indicates", "contraindicates") are represented as nodes and edges.[9, 10] This structured approach has demonstrated a 100% adherence rate in NCCN-guided breast cancer planning, significantly outperforming standard GPT-4 benchmarks.[9, 11, 17]
Advanced Parsing and Data Representation
Converting the visual complexity of oncological guidelines into machine-readable formats is a significant hurdle. Much of the information in NCCN documents resides in flowcharts and tables, which traditional OCR tools often fail to capture contextually.[9, 18, 19] A robust engineering pipeline for OncoAgent utilizes specialized parsers such as pdf2json or PyMuPDF combined with bounding-box clustering to identify flowchart nodes and their logical transitions.[9, 20, 21]
The resulting data representation should follow a document schema that preserves metadata critical for retrieval. Each JSON record should include a page_id, a visual_type (categorized as flowchart, table, or text), and a list of identified entities (e.g., SNOMED CT or NCCN-specific ontologies).[9] For Graph-RAG implementations, text chunks are parsed to extract medical triples (head, relation, tail), which are then grouped into "clinical subgraphs" using algorithms like Louvain community detection.[9, 10] This ensures that when a query regarding "hormone-receptor-positive adjuvant chemotherapy" is received, the retriever can access a pre-summarized community of related nodes rather than a disconnected set of text fragments.[9, 10]
Semantic Partitioning Strategies for Clinical Context
The quality of a RAG system's output is directly proportional to its chunking strategy. In oncology, where a single qualifier (e.g., "if ECOG > 2") can change a treatment path from curative to palliative, losing context during document splitting is unacceptable.[22, 23, 24] Naive chunking, which splits text based on fixed character counts, often severs these critical logical links, leading to fragmented information retrieval and hallucinations.[22, 23]
The Adaptive Semantic Chunking Method (ASCM)
The Adaptive Semantic Chunking Method (ASCM) represents the state-of-the-art for clinical RAG. Unlike fixed-window strategies, ASCM formalizes the splitting process as a shortest-path problem in a directed acyclic graph (DAG).[23, 25] It employs a multi-component coherence function that evaluates the continuity of semantic, structural, and medical analysis across potential boundaries.[25] By identifying natural breakpoints such as paragraphs, headers, and bulleted lists, ASCM creates variable-sized chunks that maximize token usage without splitting logical units.[24, 25]
Chunking Strategy
Mechanism
Advantage
Disadvantage
Fixed-Size
Split by token/char count
Simple, efficient
Loss of contextual logic [22, 23]
Recursive
Split by prioritized delimiters
Preserves paragraphs
May still split long clinical tables [22, 23]
Semantic
Group by sentence similarity
High topic coherence
Computationally expensive [22, 23]
Adaptive (ASCM)
DAG-based optimal partitioning
Preserves medical entity links
Requires domain-specific heuristics [23, 25]
Implementation details for medical RAG often involve a "500-word cap" to ensure that specific elements—such as dosages, timing, and safety qualifiers—remain within a single retrievable span.[23] Furthermore, an "agentic chunker" approach can be used to generate concise micro-headers for each segment. Using a high-level model like Gemini 1.0 Pro, each chunk is prepended with a 5-15 word "gist" (e.g., "Initial Workup for Suspected Lung Cancer") which is treated as part of the content for vector indexing.[23] This technique ensures that even if a chunk is retrieved in isolation, its overarching clinical purpose is explicitly defined, reducing the likelihood of the LLM misinterpreting the retrieved data.[23]
Curation of Supervised Fine-Tuning Corpora
While RAG provides the knowledge base, Supervised Fine-Tuning (SFT) is necessary to train Llama-3-8B in the "language" of oncology—transforming unstructured clinical notes into structured reasoning and diagnosis.[2, 4, 26] The goal is to move the model from a general-purpose text generator to a specialized clinical agent capable of "Chain-of-Thought" (CoT) reasoning over longitudinal patient data.[2, 27, 28]
Viable Alternatives to MIMIC-IV
The MIMIC-IV database, while comprehensive, often presents significant hurdles due to its credentialing and ethical approval requirements.[16, 29] For rapid development, particularly in a hackathon setting, the OncoAgent strategy leverages open-access datasets that provide similar or superior utility for oncological reasoning without the weeks-long approval delay.
PMC-Patients is perhaps the most valuable public alternative, containing 167,000 patient summaries extracted from open-access case reports in PubMed Central.[15, 16, 29] This dataset is particularly rich because case reports, unlike routine EHR notes, are expertly written to highlight diagnostic challenges and clinical rationales.[16, 30, 31] It includes 3.1 million patient-article relevance annotations and 293,000 patient-patient similarity annotations, making it ideal for training models to retrieve relevant literature based on a new patient's history.[16, 29, 30]
Dataset
Repository (HF/PhysioNet)
Structure
Clinical Aportation
PMC-Patients
zhengyun21/PMC-Patients
Unstructured Note → Relevant Article
Longitudinal context and similarity [29, 32]
MedQA (USMLE)
inspect_evals/medqa
MCQ → Explanation
Board-level diagnostic knowledge [33, 34]
CancerGUIDE
microsoft/CancerGUIDE
Synthetic Note → NCCN Label
Guideline-aligned treatment planning [35]
RJUA-QA
Hugging Face
Question → Context → Answer
Evidence-based urology/oncology [29]
MedBullets
Hugging Face
Clinical MCQ → Expert Reasoning
Step-by-step reasoning for USMLE 2/3 [29]
ChatDoctor
GitHub/HF
Dialogue → Diagnosis
Conversational triage and interaction [36]
MedQA and MedBullets are essential for instilling the "doctor's perspective." These datasets are derived from professional medical board exams (e.g., USMLE) and require models to solve complex, multi-step clinical problems.[29, 33, 34] MedQA provides 12,723 English-language questions, while MedBullets adds thousands more with detailed expert-written explanations.[29, 34] Training on these datasets enables Llama-3 to move beyond simple keyword matching and begin performing the "deductive leaps" required for early-stage triage.[2, 26, 37]
Multi-Task Learning and Encoding
A high-yield strategy for oncological triage is to repurpose the Llama-3-8B model as a multi-task discriminative encoder. This involves replacing the standard causal language modeling head with parallel classification layers tailored to specific clinical tasks, such as T-stage, N-stage, M-stage, and biomarker status (e.g., ER/PR/HER2 for breast cancer).[4] Experimental results show that models fine-tuned in this multi-task framework achieve a Macro F1 score of 0.976, resolving complex contextual ambiguities that rule-based pipelines often miss.[4] This "inductive transfer" allows the model to leverage common features across different staging tasks, improving overall efficiency and accuracy.[4]
Synthetic Data Generation: The "Hackathon Cheat-Code"
The primary bottleneck in clinical AI is the scarcity of "gold-standard" expert-annotated data. In a time-limited environment, the OncoAgent strategy utilizes the Temporal-Causal Chain-of-Thought (OncoCoT) framework to generate thousands of high-fidelity synthetic clinical records.[27, 28] This framework uses frontier models like GPT-4o or Claude 3.5 as "expert simulators" to produce clinical histories that are not only anatomically correct but also causally coherent over time.[28]
Temporal-Causal Chain-of-Thought (OncoCoT) Methodology
Traditional medical QA datasets are often "single-time-point" entries, failing to capture the evolving nature of clinical decision-making. The OncoCoT approach overcomes this by analyzing real-world clinical timelines to identify critical decision nodes: examination, diagnosis, and treatment.[28]
The methodology proceeds in three phases:
Timeline Extraction: Extracting a sequence of medical events from a seed case (e.g., real case reports from PMC-Patients).
Causality-Aware Simulation: Simulating patient-clinician interactions at specific timepoints, where each decision (e.g., ordering a biopsy) is constrained by subsequent outcomes (e.g., the biopsy result).[28]
Refinement via Future Nodes: Using future nodes in the clinical timeline as logical constraints to refine the reasoning paths of earlier nodes.[28] For instance, if a patient is eventually diagnosed with metastatic lung cancer, the initial reasoning at the "triage" stage must reflect the suspicious features (e.g., persistent cough, weight loss) that make such a diagnosis plausible.[28]
This "looking-back-to-reason-forward" approach ensures that the synthetic data possesses the internal consistency required for medical training.[27, 28] It allows for the generation of thousands of patient "trajectories" that are concordant with NCCN guidelines, even when the underlying training data is sparse.[35, 38]
Data Cleaning and PII Redaction
Even in synthetic or de-identified datasets, data hygiene is paramount. A robust curation pipeline utilizing tools like NVIDIA NeMo Curator is employed to unify Unicode formatting, redact any residual personally identifiable information (PII), and filter out "noisy" records (e.g., notes that are too short or contain duplicate content).[39] This process is formalized into JSONL formats, where each entry is structured as a prompt containing instructions, clinical inputs, and reasoned outputs.[36, 39]
For oncology, "note bloat"—the presence of redundant, auto-populated text in EHRs—is a significant concern. Techniques such as TRACE (Text Reduction for Augmented Clinical Efficiency) can be applied to remove up to 47.3% of chart text while preserving the clinically meaningful signals.[40] This reduction is critical for the 8B parameter Llama-3 model, as it minimizes the "distraction" from irrelevant text and focuses the model's attention on diagnostic-relevant tokens.[40]
Data Sourcing Masterplan for OncoAgent
The following masterplan outlines the exact strategy for acquiring and curating the datasets necessary for the OncoAgent triage system.
Category
Dataset / Tool Name
Repository / Access Point
Utility for OncoAgent
RAG Source
NCCN Guidelines
nccn.org/guidelines
Primary "Brain" for treatment paths [6, 9]
RAG Source
ESMO CPG Slide Sets
esmo.org/guidelines
Structural logic and tables [12, 14]
SFT Data
PMC-Patients
zhengyun21/PMC-Patients (HF)
Reasoning over long histories [16, 29]
SFT Data
CancerGUIDE
microsoft/CancerGUIDE (HF)
Guideline-adherent treatment [35]
SFT Data
MedQA
inspect_evals/medqa (HF)
Professional-level medical knowledge [33, 37]
SFT Data
MedBullets
Hugging Face
Detailed clinical reasoning traces [29]
SFT Data
RJUA-QA
Hugging Face
Expert evidence-based urology [29]
SFT Data
MedNLI
PhysioNet
Logical consistency evaluation [29]
Processing
pdf2json
npm pdf2json
PDF-to-JSON visual node extraction [20]
Processing
NeMo Curator
NVIDIA/NeMo-Curator
PII redaction and Unicode cleanup [39]
The masterplan emphasizes the use of Hugging Face repositories for immediate accessibility, bypassing the lengthy credentialing of databases like MIMIC-IV. The "LungCURE" and "OncoCoT" frameworks provide the methodological backbone for ensuring the data is not just voluminous, but clinically valid and causally structured.[28, 41]
The Master Prompt for Synthetic Clinical Reasoning Data
To generate the high-fidelity synthetic data required for the OncoAgent triage model, the following master prompt is designed for use with a frontier LLM (e.g., GPT-4o or Claude 3.5). This prompt utilizes the OncoCoT methodology to ensure temporal and causal rigor.
OncoAgent Master Prompt Template
MISSION
Act as a Senior Oncologist and a Data Engineer. Your objective is to generate a high-fidelity, longitudinal clinical case for training a triage AI. The output must be a structured JSONL record that reflects an evidence-based diagnostic trajectory.
METHODOLOGY: ONCOCOT (TEMPORAL-CAUSAL CHAIN-OF-THOUGHT)
Initialize Timeline: Define a patient presenting for early-stage triage (T0).
Assign Future Outcome: Pre-determine the definitive diagnosis and AJCC 8th Edition staging (e.g., Stage IIB Non-Small Cell Lung Cancer).
Reason Backward: Based on the future diagnosis, define the "vague symptoms" and "red flags" that should have been observed at T0.
Construct Decision Nodes: Generate the reasoning for Examination (T0), Diagnosis (T1), and Treatment (T2).
CASE ATTRIBUTES
Patient Note: Include age, sex, race, detailed smoking history (pack-years), comorbidities (e.g., COPD, diabetes), and symptoms (e.g., persistent cough, hemoptysis).
Staging: TNM score based on NCCN guidelines.
Biomarkers: Include relevant status (e.g., EGFR mutation, PD-L1 level).
OUTPUT SCHEMA
{ "patient_uid": "SYN-ONCO-", "clinical_note": "", "onco_cot_reasoning": { "timeline_t0": "Examination:", "timeline_t1": "Diagnosis:", "timeline_t2": "Treatment:" }, "nccn_label": "", "evidence_anchor": "NCCN NSCLC Guidelines v2024, Page [X]" }
CONSTRAINTS
Do not use real PII.
Ensure anatomical and clinical accuracy (e.g., do not suggest surgery for Stage IV without a palliative rationale).
Use a diverse set of patient demographics to avoid model bias.
This prompt is engineered to produce the "Rationale-enriched synthetic datasets" required for LoRA-based fine-tuning.[42, 43] By forcing the generator to "reason backward" from a known outcome, the resulting data avoids the logical gaps common in naive synthetic generation, where symptoms and final diagnoses may be disconnected.[28]
Implementation Strategy for Llama-3-8B
The technical implementation of the OncoAgent model utilizes Parameter-Efficient Fine-Tuning (PEFT) on the 8B variant of Llama-3. This approach is dictated by the need for high-performance reasoning on constrained hardware.
Fine-Tuning Configuration
Llama-3-8B is fine-tuned using LoRA adapters specifically on the query and value projection layers.[2, 4] The use of LoRA reduces the number of trainable parameters by up to 900%, allowing for rapid experimentation with the curated datasets.[5]
Hyperparameter
Value
Rationale
LoRA Rank (r)
16 - 128
Balance between model flexibility and memory [5, 26]
LoRA Alpha (α)
32
Typical scaling factor for weight updates [2]
Learning Rate
3×10 
−5
 
Optimized for clinical domain adaptation [26]
Batch Size
2 - 8
Managed via gradient accumulation for small-GPU setups [2]
Training Epochs
4
Sufficient for convergence on medical reasoning tasks [2, 4]
Temperature
0.1
Minimizes stochastic variance in medical outputs [26]
The model's performance is evaluated using metrics that go beyond simple token accuracy. "Path Overlap" and "Treatment Match" are used to assess adherence to NCCN guidelines, while "mGPS" (modified Generative Performance Score) is used to deduplicate hallucinations and measure guideline concordance.[7, 35, 38] This evaluation framework ensures that OncoAgent is not just generating "plausible" text, but is delivering "clinically valid" guidance that aligns with the specialized consensus of oncology practitioners.[1, 2, 7]
Optimizing Retrieval for Early Triage
The triage phase of oncology is the most critical point for intervention. Delays in diagnosis can significantly reduce the 5-year survival rate, particularly in lung cancer, where nearly 30% of patients die within 90 days of diagnosis.[44, 45] OncoAgent's data strategy is specifically tuned to recognize "suspicious X-rays" and "high-risk patient histories" that require immediate acceleration to CT imaging or biopsy.[41, 44, 45]
LungCURE and Radiology Integration
The OncoAgent strategy integrates the "LungCURE" methodology, which uses AI to triage scans immediately after capture.[44, 45] By sourcing datasets that include pairs of chest radiographs and final diagnoses (e.g., M4CXR), the model learns to identify "subtle pulmonary nodules" (6-10mm) and flag them for urgent review.[41, 46] This AI-driven approach has been shown to halve the time from X-ray to diagnosis from 60 days to 30 days in NHS pilot studies.[44, 45]
The RAG component is augmented with specialized radiology guidelines, such as Lung-RADS and the Fleischner guidelines, which provide the rules for nodule follow-up.[41] When a patient summary is processed, the system performs a similarity search across these guidelines to determine if the findings meet the threshold for intervention.[23, 41]
Contextual Retrieval and Metadata Enrichment
To prevent the "context rot" that often plagues medical RAG, OncoAgent employs "Contextual Retrieval." This involves pairing each chunk with a summary of the entire document, which is then sent to an LLM to generate a context-enriched version of the chunk.[47] For example, a chunk detailing "dosage for adjuvant cisplatin" is enriched with the metadata "Standard of care for Stage IIA NSCLC following R0 resection".[4, 47] This enrichment makes the chunk vectors more informative and semantically accurate during similarity search, ensuring that the retriever does not pull recommendations from the "Advanced Stage" section of the guidelines when the patient is "Early Stage".[4, 47]
Conclusion: Designing the OncoAgent Ecosystem
The design of the OncoAgent data strategy represents a move toward "Precision AI" in medicine. By meticulously sourcing clinical practice guidelines from NCCN, ESMO, and ASCO, the system ensures its knowledge is anchored in global expert consensus.[1, 6, 7, 48] The use of the Adaptive Semantic Chunking Method (ASCM) preserves the dense logical structure of these guidelines, while open datasets like PMC-Patients and CancerGUIDE provide the necessary training signals for complex reasoning.[23, 25, 29, 35]
Furthermore, the OncoCoT framework enables the generation of high-fidelity synthetic data, bypassing the ethical and logistical bottlenecks of traditional clinical databases.[27, 28] When combined with parameter-efficient fine-tuning on Llama-3-8B, these strategies create a triage agent that is accurate, evidence-based, and highly responsive to the temporal-causal nature of cancer care.[2, 4, 5, 26] The ultimate objective is to provide oncologists with a "trusted colleague" in the triage room—an assistant capable of synthesizing vast amounts of data into actionable insights, thereby accelerating the pathway from first symptom to definitive cure.[1, 41, 45, 49]
--------------------------------------------------------------------------------
AI in Oncology Clinical Decision Support | Cancerworld Magazine, https://cancerworld.net/ai-in-oncology-clinical-decision-support/
UltimateMedLLM-Llama3-8B: Fine-tuning Llama 3 for Medical Question-Answering - Stanford University, https://web.stanford.edu/class/archive/cs/cs224n/cs224n.1254/final-reports/256847341.pdf
Augmenting Large Language Models With National Comprehensive Cancer Network Guidelines for Improved and Standardized Adjuvant Therapy Recommendations in Postoperative Breast Cancer Cases - ASCO Publications, https://ascopubs.org/doi/10.1200/CCI-24-00243
Multi-Task LLM with LoRA Fine-Tuning for Automated Cancer Staging and Biomarker Extraction - arXiv, https://arxiv.org/html/2604.13328v1
Modern Approaches to LLaMA Fine-Tuning: Parameter-Efficient Methods for Targeted Domain - ResearchGate, https://www.researchgate.net/publication/400600690_Modern_Approaches_to_LLaMA_Fine-Tuning_Parameter-Efficient_Methods_for_Targeted_Domain
NCCN Guidelines Navigator, https://www.nccn.org/guidelines/nccn-guidelines-navigator
Source matters: Performance of guideline-anchored RAG versus broad evidence LLMs in GI oncology. - ASCO, https://www.asco.org/abstracts-presentations/255993/abstract
Recently Updated Guidelines - NCCN, https://www.nccn.org/guidelines/recently-published-guidelines
Personalized RAG++ for Clinical Decision Support - Emergent Mind, https://www.emergentmind.com/topics/personalized-rag
Developing an Artificial Intelligence Tool for Personalized Breast Cancer Treatment Plans based on the NCCN Guidelines - ResearchGate, https://www.researchgate.net/publication/389315352_Developing_an_Artificial_Intelligence_Tool_for_Personalized_Breast_Cancer_Treatment_Plans_based_on_the_NCCN_Guidelines
BPI25-012: Developing an Artificial Intelligence Tool for Personalized Breast Cancer Treatment Plans Based on the NCCN Guidelines in - JNCCN, https://jnccn.org/view/journals/jnccn/23/3.5/article-BPI25-012.xml?print
ESMO Clinical Practice Guidelines: Guidelines Slide Sets, https://www.esmo.org/guidelines/guidelines-slide-sets
Guidelines | ESMO, https://www.esmo.org/guidelines
ESMO Open: Frequently Asked Questions, https://www.esmo.org/about-esmo/discover-esmo-journals/esmo-open/frequently-asked-questions
PMC-Patients-Dataset for Clinical Decision Support - Kaggle, https://www.kaggle.com/datasets/priyamchoksi/pmc-patients-dataset-for-clinical-decision-support
A large-scale dataset of patient summaries for retrieval-based clinical decision support systems - PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC10728216/
[2502.15698] Developing an Artificial Intelligence Tool for Personalized Breast Cancer Treatment Plans based on the NCCN Guidelines - arXiv, https://arxiv.org/abs/2502.15698
Developing an Artificial Intelligence Tool for Personalized Breast Cancer Treatment Plans based on the NCCN Guidelines - arXiv, https://arxiv.org/html/2502.15698v1
PDF to JSON Converter Guide: Best Methods October 2025, https://www.extend.ai/resources/pdf-to-json-converter-guide
pdf2json - NPM, https://www.npmjs.com/package/pdf2json
A Practical Guide to PDF to JSON Conversion for Automation - DigiParser, https://www.digiparser.com/blog/pdf-to-json
Best Chunking Strategies for RAG Pipelines - Redis, https://redis.io/blog/chunking-strategy-rag-pipelines/
Comparative Evaluation of Advanced Chunking for Retrieval ..., https://pmc.ncbi.nlm.nih.gov/articles/PMC12649634/
RAG 2.0 : Advanced Chunking Strategies with Examples. | by Vishal Mysore - Medium, https://medium.com/@visrow/rag-2-0-advanced-chunking-strategies-with-examples-d87d03adf6d1
Adaptive Semantic Chunking Method for Medical Retrieval-Augmented Generation Systems, https://openreview.net/forum?id=9ph0YwPFR4
Classifying American Society of Anesthesiologists Physical Status With a Low-Rank–Adapted Large Language Model: Development and Validation Study - Journal of Medical Internet Research, https://www.jmir.org/2026/1/e89540/PDF
OncoCoT: A Temporal-causal Chain-of-Thought Dataset for Oncologic Decision-Making | Proceedings of the AAAI Conference on Artificial Intelligence, https://ojs.aaai.org/index.php/AAAI/article/view/40724
OncoCoT: A Temporal-causal Chain-of-Thought Dataset for Oncologic Decision-Making - AAAI Publications, https://ojs.aaai.org/index.php/AAAI/article/view/40724/44685
Daily Papers - Hugging Face, https://huggingface.co/papers?q=JAMA%20Clinical%20Challenge
PMC-Patients Homepage, https://pmc-patients.github.io/
PMC-Patients: A Large-scale Dataset of Patient Summaries and Relations for Benchmarking Retrieval-based Clinical Decision Support Systems. - GitHub, https://github.com/pmc-patients/pmc-patients
zhengyun21/PMC-Patients-ReCDS · Datasets at Hugging Face, https://huggingface.co/datasets/zhengyun21/PMC-Patients-ReCDS
MedQA: Medical exam Q&A benchmark - GitHub Pages, https://ukgovernmentbeis.github.io/inspect_evals/evals/knowledge/medqa/
MedQA.md - openmedlab/Awesome-Medical-Dataset - GitHub, https://github.com/openmedlab/Awesome-Medical-Dataset/blob/main/resources/MedQA.md
microsoft/CancerGUIDE · Datasets at Hugging Face, https://huggingface.co/datasets/microsoft/CancerGUIDE
Medical LLMs: Fine-Tuning vs. Retrieval-Augmented Generation - PMC, https://pmc.ncbi.nlm.nih.gov/articles/PMC12292519/
MedExQA: Medical Question Answering Benchmark with Multiple Explanations - arXiv, https://arxiv.org/html/2406.06331v2
CancerGUIDE: Cancer Guideline Understanding via Internal Disagreement Estimation - Microsoft Research, https://www.microsoft.com/en-us/research/publication/cancerguide-cancer-guideline-understanding-via-internal-disagreement-estimation/
Curating Custom Datasets for LLM Parameter-Efficient Fine-Tuning with NVIDIA NeMo Curator | NVIDIA Technical Blog, https://developer.nvidia.com/blog/curating-custom-datasets-for-llm-parameter-efficient-fine-tuning-with-nvidia-nemo-curator/
Computers and Society - arXiv, https://arxiv.org/list/cs.CY/new
Qure.ai: AI Healthcare Solutions in USA, https://www.qure.ai/
A Synthetic Data Generation Framework with Chain-of-Thought Reasoning - IBM Research, https://research.ibm.com/publications/a-synthetic-data-generation-framework-with-chain-of-thought-reasoning
GitHub - inclusionAI/PromptCoT: A unified suite for generating elite reasoning problems and training high-performance LLMs, including pioneering attention-free architectures, https://github.com/inclusionAI/PromptCoT
Qure.ai - SBRI Healthcare, https://sbrihealthcare.co.uk/nhs-cancer-programme/case-studies/qure-ai
LungIMPACT: impact of immediate AI enabled patient triage to chest CT on the lung cancer pathway - YouTube, https://www.youtube.com/watch?v=b9k-TSmPuUQ
Daily Papers - Hugging Face, https://huggingface.co/papers?q=Clinical%20accuracy
Chapter 2: The Technical Foundations of Text-Only RAG | by Marc Haraoui | Medium, https://medium.com/@marcharaoui/chapter-2-the-technical-foundations-of-text-only-rag-3e462eb5307e
Source matters: Performance of guideline-anchored RAG versus broad evidence LLMs in GI oncology. - ASCO Publications, https://ascopubs.org/doi/10.1200/JCO.2026.44.2_suppl.805
India AI - NCG CATCH Grant Awards 2026 - National Cancer Grid, https://www.ncgindia.org/ncg-catch-grant
