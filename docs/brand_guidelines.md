# OncoAgent — Brand Guidelines

> **Version:** 1.0 · **Date:** 2026-05-05 · **AMD Developer Hackathon 2026**

---

## 1. Brand Essence

### 1.1 Mission Statement

**OncoAgent democratizes clinical oncology intelligence.** We build open-source, privacy-first AI systems that empower primary care physicians with evidence-based oncological triage — grounded in NCCN/ESMO guidelines, running locally on AMD Instinct™ MI300X hardware.

### 1.2 Brand Promise

> *"In medicine, saying 'I don't know' is safer than guessing."*

Every recommendation is traceable. Every source is cited. Every hallucination is blocked. OncoAgent delivers **radical transparency** in clinical AI.

### 1.3 Brand Pillars

| Pillar | Description |
|--------|-------------|
| **Clinical Safety** | Zero-hallucination policy. Anti-fabrication gates at every node. |
| **Radical Transparency** | Every recommendation shows its source, page, and confidence score. |
| **Open Source** | 100% open-source. Life-saving intelligence belongs to humanity. |
| **Privacy First** | Runs locally on AMD MI300X. Zero patient data leaves the hospital. |
| **Evidence-Based** | Grounded exclusively in NCCN/ESMO peer-reviewed clinical guidelines. |

### 1.4 Brand Personality

OncoAgent speaks as a **trusted clinical colleague** — not a chatbot, not a search engine.

- **Authoritative** — Backed by peer-reviewed oncology guidelines
- **Transparent** — Always shows its work and admits uncertainty
- **Precise** — Clinical-grade language, zero ambiguity
- **Humble** — Refuses to answer when evidence is insufficient
- **Compassionate** — Ultimately serves patient outcomes

### 1.5 Tagline Options

| Context | Tagline |
|---------|---------|
| Primary | **"Clinical Intelligence. Open Source. Zero Hallucinations."** |
| Technical | **"SOTA RAG. Local Inference. Evidence-Grounded Oncology."** |
| Emotional | **"Because every hour counts in oncology."** |
| Hackathon | **"Democratizing Oncology with AMD Instinct™"** |

---

## 2. Visual Identity

### 2.1 Logo Concept

The OncoAgent logo combines three symbolic elements:

1. **DNA Helix** — Represents the biological/oncological domain
2. **Neural Network Nodes** — Represents the multi-agent AI architecture
3. **Shield Outline** — Represents clinical safety and patient protection

**Logo Mark:** A stylized double-helix merging into interconnected neural nodes, enclosed within a subtle shield silhouette.

**Wordmark:** "OncoAgent" set in **Outfit Bold**, with "Onco" in Primary Teal and "Agent" in Midnight Navy.

### 2.2 Logo Usage Rules

| ✅ Do | ❌ Don't |
|-------|----------|
| Use on solid backgrounds (white, navy, dark) | Stretch, rotate, or skew the logo |
| Maintain minimum clear space (1x logo height) | Place on busy photographic backgrounds |
| Use the monochrome version on dark backgrounds | Change the logo colors arbitrarily |
| Scale proportionally | Add drop shadows or effects |

### 2.3 Logo Variants

| Variant | Use Case |
|---------|----------|
| **Full Color** | Primary usage on light backgrounds |
| **Dark Mode** | White wordmark + teal icon on dark backgrounds |
| **Monochrome** | Single-color contexts (printing, embossing) |
| **Icon Only** | Favicons, app icons, social media avatars |

---

## 3. Color System

### 3.1 Primary Palette

```
┌─────────────────────────────────────────────────────┐
│  PRIMARY TEAL        │  DARK TEAL          │  LIGHT TEAL        │
│  #0D9488             │  #0F766E            │  #5EEAD4           │
│  rgb(13, 148, 136)   │  rgb(15, 118, 110)  │  rgb(94, 234, 212) │
│  ██████████          │  ██████████         │  ██████████        │
│  Buttons, links,     │  Hover states,      │  Highlights,       │
│  active states       │  headers            │  badges, tags      │
└─────────────────────────────────────────────────────┘
```

### 3.2 Secondary Palette

```
┌─────────────────────────────────────────────────────┐
│  MIDNIGHT NAVY       │  SLATE               │  STEEL             │
│  #0F172A             │  #334155             │  #64748B           │
│  rgb(15, 23, 42)     │  rgb(51, 65, 85)     │  rgb(100, 116, 139)│
│  ██████████          │  ██████████          │  ██████████        │
│  Backgrounds, text,  │  Secondary text,     │  Captions,         │
│  headers             │  borders             │  placeholders      │
└─────────────────────────────────────────────────────┘
```

### 3.3 Accent & Semantic Colors

```
┌──────────────────────────────────────────────────────────────────┐
│  AMBER HOPE   │  SUCCESS      │  ERROR        │  WARNING        │
│  #F59E0B      │  #22C55E      │  #EF4444      │  #F97316        │
│  Highlights,  │  Validated ✅ │  Rejected ❌  │  Low Conf. ⚠️   │
│  CTAs, hope   │  Safe results │  Hallucination│  Needs review   │
│               │               │  detected     │                 │
└──────────────────────────────────────────────────────────────────┘
```

### 3.4 Neutral Scale

| Token | Hex | Usage |
|-------|-----|-------|
| `--white` | `#FFFFFF` | Page backgrounds |
| `--gray-50` | `#F8FAFC` | Subtle backgrounds |
| `--gray-100` | `#F1F5F9` | Card backgrounds |
| `--gray-300` | `#CBD5E1` | Borders, dividers |
| `--gray-500` | `#64748B` | Secondary text |
| `--gray-700` | `#334155` | Primary body text |
| `--gray-900` | `#0F172A` | Headings, emphasis |

### 3.5 Color Accessibility

All color combinations must meet **WCAG 2.1 AA** contrast ratios:
- **Normal text:** Minimum 4.5:1
- **Large text:** Minimum 3:1
- **UI components:** Minimum 3:1

| Combination | Ratio | Pass? |
|-------------|-------|-------|
| White text on Primary Teal (#0D9488) | 4.6:1 | ✅ AA |
| White text on Midnight Navy (#0F172A) | 17.1:1 | ✅ AAA |
| Midnight Navy on White | 17.1:1 | ✅ AAA |
| Primary Teal on Gray-50 | 4.5:1 | ✅ AA |

---

## 4. Typography

### 4.1 Font Stack

| Role | Font Family | Weight | Fallback |
|------|-------------|--------|----------|
| **Headings** | Outfit | Bold (700), SemiBold (600) | system-ui, sans-serif |
| **Body** | Inter | Regular (400), Medium (500) | system-ui, sans-serif |
| **Monospace** | JetBrains Mono | Regular (400) | monospace |
| **Medical Terms** | Inter | Medium Italic (500i) | system-ui, sans-serif |

### 4.2 Type Scale

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| H1 | 48px / 3rem | Outfit Bold | 1.1 | Page titles |
| H2 | 36px / 2.25rem | Outfit SemiBold | 1.2 | Section headers |
| H3 | 24px / 1.5rem | Outfit SemiBold | 1.3 | Subsections |
| H4 | 20px / 1.25rem | Inter Medium | 1.4 | Card headers |
| Body | 16px / 1rem | Inter Regular | 1.6 | Paragraph text |
| Caption | 14px / 0.875rem | Inter Regular | 1.5 | Labels, metadata |
| Small | 12px / 0.75rem | Inter Medium | 1.4 | Badges, footnotes |
| Code | 14px / 0.875rem | JetBrains Mono | 1.5 | Code blocks, metrics |

### 4.3 Google Fonts Import

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&family=Outfit:wght@600;700&display=swap');
```

---

## 5. Voice & Tone

### 5.1 Writing Principles

| Principle | Description | Example |
|-----------|-------------|---------|
| **Clinical Precision** | Use exact medical terminology | ✅ "Stage IIIA NSCLC" · ❌ "Advanced lung cancer" |
| **Transparent Uncertainty** | Explicitly state limitations | ✅ "Insufficient evidence in provided guidelines" |
| **Source Attribution** | Always cite guideline sources | ✅ "Per NCCN NSCLC v2024, Page 42" |
| **Action-Oriented** | Guide next steps clearly | ✅ "Recommend CT scan within 14 days" |
| **Zero Speculation** | Never invent or extrapolate | ❌ "This could potentially be..." |

### 5.2 Tone by Context

| Context | Tone | Example |
|---------|------|---------|
| **Clinical Output** | Authoritative, precise, cited | "Based on NCCN Guidelines (Page 42): First-line therapy for Stage IIIA..." |
| **Safety Rejection** | Firm, protective, transparent | "❌ Rejected: Insufficient evidence in clinical guidelines." |
| **UI Labels** | Clear, concise, bilingual | "Generate Recommendation / Generar Recomendación" |
| **Social Media** | Enthusiastic, technical, authentic | "🧬 Just ingested 70+ clinical guidelines into ChromaDB!" |
| **Documentation** | Professional, structured, thorough | Standard technical documentation voice |
| **Error Messages** | Empathetic, actionable, safe | "Inference system error. No recommendation generated." |

### 5.3 Anti-Hallucination Language

The following phrase is the **canonical safety response** when evidence is insufficient:

> **"Información no concluyente en las guías provistas."**
>
> (English: "Inconclusive information in the provided guidelines.")

This phrase must NEVER be modified or softened. It is the system's safety valve.

---

## 6. Iconography & Visual Elements

### 6.1 Icon Style

- **Style:** Outlined, 1.5px stroke weight
- **Grid:** 24×24px base grid
- **Corner radius:** 2px on geometric shapes
- **Aesthetic:** Medical meets technology — clean, precise, trustworthy

### 6.2 Core Icons

| Icon | Usage | Suggested Source |
|------|-------|-----------------|
| 🧬 DNA Helix | Oncology, biology | Custom SVG |
| 🛡️ Shield Check | Safety validation (PASS) | Lucide Icons |
| ❌ Shield X | Safety rejection (FAIL) | Lucide Icons |
| 📊 Bar Chart | RAG confidence metrics | Lucide Icons |
| 📚 Book Open | Retrieved sources/guidelines | Lucide Icons |
| 🔍 Search | RAG retrieval process | Lucide Icons |
| ⚡ Zap | AMD/ROCm performance | Lucide Icons |
| 🏥 Hospital | Clinical context | Lucide Icons |

### 6.3 Emoji Usage in Social Media

Approved emoji set for brand consistency:

| Emoji | Meaning |
|-------|---------|
| 🧬 | Oncology / DNA / Biology |
| 🧠 | AI / Intelligence / Reasoning |
| 🛡️ | Safety / Anti-hallucination |
| 🚀 | Milestone / Launch / Progress |
| ⚡ | Performance / AMD / Speed |
| 📊 | Metrics / Data / Results |
| 🏥 | Healthcare / Clinical |
| 🔬 | Research / SOTA |
| 💻 | Code / Engineering |
| 🌍 | Open Source / Global |

---

## 7. UI Design System

### 7.1 Gradio Theme Configuration

```python
import gradio as gr

ONCOAGENT_THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.teal,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.gray,
    font=[
        gr.themes.GoogleFont("Inter"),
        "system-ui",
        "sans-serif",
    ],
    font_mono=[
        gr.themes.GoogleFont("JetBrains Mono"),
        "monospace",
    ],
)
```

### 7.2 Component Patterns

#### Safety Status Badge

| State | Icon | Color | Label |
|-------|------|-------|-------|
| Validated | ✅ | `#22C55E` | "Validated against clinical oncology guidelines" |
| Rejected (No evidence) | ❌ | `#EF4444` | "Rejected: Insufficient evidence in clinical guidelines" |
| Rejected (Low confidence) | ⚠️ | `#F97316` | "Rejected: Low retrieval confidence (X.XX)" |
| Rejected (Hallucination) | ❌ | `#EF4444` | "Rejected: Hallucination detected (unsupported claims)" |
| System Error | ❌ | `#64748B` | "Rejected: Safety validation failed due to system error" |

#### RAG Confidence Display

```
📊 RAG Confidence Score: 0.8742 | 📚 Sources Retrieved: 5
```

Always display both metrics together. The confidence score uses 4 decimal places.

### 7.3 Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  🧬 OncoAgent: Clinical Oncology Decision Support       │
│  Description text...                                     │
├──────────────────────────┬──────────────────────────────┤
│                          │                              │
│  Clinical History Input  │  Safety Validation Status    │
│  [Textarea - 10 lines]  │  ┌──────────────────────┐   │
│                          │  │ ✅ / ❌ Status Badge  │   │
│  [Clear] [Generate ▶]   │  └──────────────────────┘   │
│                          │                              │
│                          │  Extracted Entities          │
│                          │  • Cancer Type: ...          │
│                          │  • Stage: ...                │
│                          │  • Mutations: ...            │
│                          │                              │
│                          │  Retrieved Sources           │
│                          │  📊 Confidence | 📚 Count   │
│                          │  - Source 1 (Page X)         │
│                          │  - Source 2 (Page Y)         │
│                          │                              │
│                          │  Clinical Recommendation     │
│                          │  [Full recommendation text]  │
│                          │                              │
└──────────────────────────┴──────────────────────────────┘
```

---

## 8. Social Media & Content Guidelines

### 8.1 Platform Strategy

| Platform | Tone | Content Type | Frequency |
|----------|------|--------------|-----------|
| **X/Twitter** | Technical, Build-in-Public | Threads (4-5 tweets), metrics, code screenshots | Daily |
| **LinkedIn** | Professional, Strategic | Long-form milestone posts, architecture decisions | 2-3x/week |
| **Instagram/TikTok** | Visual, Dynamic | Slides, code recordings, B-roll | 1-2x/week |

### 8.2 Hashtag Strategy

**Primary (Always use):**
`#AMDHackathon` `#HealthTech` `#ROCm`

**Secondary (Rotate):**
`#OpenSource` `#BuildInPublic` `#AI` `#Llama31` `#LangGraph` `#OncoAgent`

**Topical (When relevant):**
`#MedicalAI` `#CrossEncoder` `#HyDE` `#AntiHallucination` `#RAG`

### 8.3 Content Pillars

| Pillar | % of Content | Examples |
|--------|-------------|---------|
| **Technical Build** | 40% | Architecture decisions, code walkthroughs, RAG pipeline details |
| **Failure Stories** | 20% | "Fracaso del Día" — honest debugging stories |
| **Mission & Vision** | 20% | Open-source philosophy, patient privacy, democratization |
| **Metrics & Results** | 20% | Benchmark numbers, ingestion stats, confidence scores |

### 8.4 Visual Content Suggestions

| Type | Description |
|------|-------------|
| **Code Screenshots** | Dark theme, syntax highlighted, key lines annotated |
| **Architecture Diagrams** | Mermaid or draw.io, brand colors |
| **Terminal Recordings** | asciinema captures of ingestion/training |
| **Before/After** | Side-by-side comparisons of improvements |
| **Metric Cards** | Styled cards with key performance numbers |

### 8.5 Account Mentions

Always mention ecosystem partners when relevant:

| Partner | Handle |
|---------|--------|
| lablab.ai | `@lablabai` |
| AMD | `@AIatAMD` / `@AMD` |
| Hugging Face | `@huggingface` |

---

## 9. Partner & Co-Branding

### 9.1 Technology Partners

| Partner | Relationship | Logo Usage |
|---------|-------------|------------|
| **AMD** | Hardware sponsor (MI300X) | Use "AMD Instinct™" with ™ symbol |
| **lablab.ai** | Hackathon organizer | Per lablab.ai brand guidelines |
| **Hugging Face** | Model hosting & datasets | Per HF brand guidelines |
| **Meta (Llama)** | Base model provider | Use "Meta-Llama-3.1-8B-Instruct" full name |

### 9.2 Co-Branding Rules

- OncoAgent logo always appears **first** (leftmost or topmost)
- Partner logos are separated by a vertical divider (`|`)
- Use the phrase: *"Powered by AMD Instinct™ MI300X"*
- Never imply that partners endorse OncoAgent's medical outputs

### 9.3 Required Disclaimers

All public-facing materials must include:

> **⚠️ Disclaimer:** OncoAgent is an AI research prototype developed for the AMD Developer Hackathon 2026. It is NOT a certified medical device. Clinical decisions must always be made by qualified healthcare professionals. This system is designed as a decision-support tool, not a replacement for clinical judgment.

---

## 10. File Naming & Asset Organization

### 10.1 Asset Directory Structure

```
docs/
├── brand_guidelines.md          # This file (EN)
├── brand_guidelines.es.md       # Spanish version
└── assets/
    └── brand/
        ├── logo/
        │   ├── oncoagent_logo_full_color.svg
        │   ├── oncoagent_logo_dark_mode.svg
        │   ├── oncoagent_logo_monochrome.svg
        │   └── oncoagent_icon_only.svg
        ├── colors/
        │   └── color_palette.svg
        ├── typography/
        │   └── type_specimen.svg
        └── social/
            ├── twitter_header.png    (1500×500)
            ├── linkedin_banner.png   (1584×396)
            └── avatar.png            (400×400)
```

### 10.2 Naming Convention

All brand assets follow `snake_case` naming:
- `oncoagent_logo_full_color.svg`
- `social_post_rag_pipeline.png`
- `diagram_langgraph_architecture.svg`

---

## 11. CSS Design Tokens

```css
:root {
  /* --- Primary --- */
  --color-primary: #0D9488;
  --color-primary-dark: #0F766E;
  --color-primary-light: #5EEAD4;

  /* --- Secondary --- */
  --color-secondary: #0F172A;
  --color-secondary-light: #334155;
  --color-secondary-muted: #64748B;

  /* --- Accent --- */
  --color-accent: #F59E0B;
  --color-accent-dark: #D97706;

  /* --- Semantic --- */
  --color-success: #22C55E;
  --color-error: #EF4444;
  --color-warning: #F97316;
  --color-info: #3B82F6;

  /* --- Neutrals --- */
  --color-white: #FFFFFF;
  --color-gray-50: #F8FAFC;
  --color-gray-100: #F1F5F9;
  --color-gray-300: #CBD5E1;
  --color-gray-500: #64748B;
  --color-gray-700: #334155;
  --color-gray-900: #0F172A;

  /* --- Typography --- */
  --font-heading: 'Outfit', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* --- Spacing --- */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  /* --- Border Radius --- */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* --- Shadows --- */
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 6px rgba(15, 23, 42, 0.07);
  --shadow-lg: 0 10px 15px rgba(15, 23, 42, 0.1);
}
```

---

## 12. Internationalization (i18n)

### 12.1 Language Strategy

| Layer | Primary Language | Secondary Language |
|-------|-----------------|-------------------|
| **Source Code** | English | — |
| **UI (Default)** | English | Spanish |
| **Documentation** | English (`.md`) | Spanish (`.es.md`) |
| **Social Media** | Spanish | English |
| **Clinical Output** | Spanish | English |

### 12.2 i18n Architecture

All UI strings are stored in a centralized dictionary (see `ui/app.py`):

```python
I18N = {
    "en": { "title": "OncoAgent: Clinical Oncology Decision Support", ... },
    "es": { "title": "OncoAgent: Soporte de Decisión en Oncología Clínica", ... },
}
```

New languages can be added by extending this dictionary without modifying component logic.

---

*Built with ❤️ and AMD Instinct™ MI300X for the AMD Developer Hackathon 2026.*
