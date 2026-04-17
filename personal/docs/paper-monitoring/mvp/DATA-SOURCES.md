# Data Source Specification -- Paper Monitoring

> **Status**: Updated for MVP
> **Author**: Architect Agent
> **Last Updated**: 2026-04-17
> **Phase**: MVP
> **Depends on**: PRD.md (MVP), TDD.md (MVP)

---

## Data Sources

### Source 1: arXiv API (Primary -- Weekly Pipeline + Seeding)

| Field | Detail |
|-------|--------|
| **Type** | REST API |
| **URL / Endpoint** | `https://export.arxiv.org/api/query` |
| **Authentication** | None required |
| **Rate Limits** | 3-second courtesy delay between sequential requests (arXiv's stated policy) |
| **Cost** | Free, no API key |
| **Data Format** | Atom XML |
| **Update Frequency** | Real-time (papers indexed same-day; confirmed 2026-04-13T17:59:49Z) |
| **Reliability** | High (arXiv is a stable, long-running academic service) |

**Usage in the System**:

- **Weekly pipeline (Phase 2)**: Fetches the past 7 days of papers across five categories: `cs.LG`, `cs.AI`, `cs.CL`, `cs.CV`, `stat.ML`. Expected weekly volume: ~800--1,200 raw papers with significant cross-category overlap. Deduplicated by arXiv ID before processing.
- **Seeding (Phase 1)**: Fetches individual landmark papers and survey papers by arXiv ID using the same endpoint. Also used by the manual `seed.py --arxiv-id <id>` CLI for adding new survey papers to the knowledge bank.

**Query Construction**:

```
# Weekly fetch (one query per category)
GET https://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&sortOrder=descending&start=0&max_results=500

# Single paper by ID (seeding)
GET https://export.arxiv.org/api/query?id_list=1706.03762

# Batch fetch by IDs (seeding)
GET https://export.arxiv.org/api/query?id_list=1706.03762,1810.04805,2005.14165&max_results=50
```

**Sample Response** (confirmed live, 2026-04-13):

```xml
<entry>
  <id>http://arxiv.org/abs/2604.11805v1</id>
  <title>Solving Physics Olympiad via Reinforcement Learning on Physics Simulators</title>
  <published>2026-04-13T17:59:40Z</published>
  <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
  <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
  <summary>We have witnessed remarkable advances in LLM reasoning capabilities...
    [full abstract, avg ~300-400 words]
  </summary>
  <author><name>Mihir Prabhudesai</name></author>
  <author><name>Deepak Pathak</name></author>
  <arxiv:comment>Project Webpage - https://sim2reason.github.io/</arxiv:comment>
</entry>
```

**Field Mapping to Internal Pydantic Model (`ArxivPaper`)**:

| XML Path | `ArxivPaper` Field | Transformation |
|----------|-------------------|----------------|
| `<id>` | `arxiv_id` | Extract ID from URL: `http://arxiv.org/abs/2604.11805v1` -> `2604.11805` (strip version suffix and URL prefix) |
| `<title>` | `title` | Strip whitespace and normalize newlines |
| `<summary>` | `abstract` | Strip whitespace and normalize newlines |
| `<author><name>` | `authors` | Collect all `<author>` children into `list[str]` |
| `<category>` (first) | `primary_category` | First `<category term="...">` value, e.g. `cs.LG` |
| `<category>` (all) | `all_categories` | All `<category term="...">` values as `list[str]` |
| `<published>` | `published_date` | Parse ISO 8601 timestamp, store as `YYYY-MM-DD` date string |
| `<updated>` | `updated_date` | Parse ISO 8601 timestamp, store as `YYYY-MM-DD` date string. May differ from `published_date` for revised papers |
| `<id>` | `arxiv_url` | Construct: `https://arxiv.org/abs/{arxiv_id}` |
| `<id>` | `pdf_url` | Construct: `https://arxiv.org/pdf/{arxiv_id}` |
| `<arxiv:comment>` | `comment` | Raw text, or `None` if absent. Often contains links to code repos or project pages |

**Known Limitation -- Date-Range Query Parameters Are Broken**:

The arXiv API documents a `submittedDate:[YYYYMMDD TO YYYYMMDD]` range query syntax. In live testing (confirmed 2026-04-13), this consistently returns 0 results. This is a known arXiv API quirk.

**Workaround (implemented in `ArxivFetcher`)**:

1. Query with `sortBy=submittedDate` and `sortOrder=descending` -- this reliably returns papers in reverse chronological order.
2. Paginate through results (up to 500 per page), respecting the 3-second delay between requests.
3. Filter by `published` date in Python post-processing: keep only papers where `published_date >= (today - 30 days)` (configurable via `arxiv_lookback_days`, default 30 — extended from 7 in PoC for fairer upvote scoring).
4. Stop pagination once the fetcher encounters papers older than the lookback window.

This workaround fetches more data than strictly necessary but is reliable. The over-fetch is bounded by the stop condition in step 4.

**Rate Limiting Strategy**:

- **Delay**: `time.sleep(3.0)` between every sequential HTTP request to the arXiv API. This is arXiv's documented courtesy requirement, not a hard enforcement -- but violating it risks IP-level throttling.
- **Retry on server error**: Retry up to 3 times with exponential backoff (3s, 9s, 27s) on HTTP 5xx or connection errors.
- **Abort on client error**: Log and abort on HTTP 4xx (indicates a query construction bug).
- **Skip on malformed XML**: Log a warning and skip any entry that fails XML parsing; continue with remaining entries.
- **Configurable**: The delay (`arxiv_fetch_delay`) and page size (`arxiv_max_results_per_category`) are defined in `config.py`.

**Deduplication**:

Papers cross-listed across multiple categories (e.g., a paper in both `cs.LG` and `cs.AI`) will appear in multiple category fetches. ArxivFetcher deduplicates by `arxiv_id` before returning, keeping the first occurrence.

**Fallback Strategy**:

arXiv is the primary and sole source of paper metadata. If the arXiv API is entirely unreachable after all retries, the weekly pipeline aborts and logs the failure to the `weekly_runs` table. The digest for that week is not generated. This is an acceptable failure mode -- arXiv outages are rare (minutes, not hours) and a missed week is recoverable.

---

### Source 2: HuggingFace Daily Papers API (Secondary -- Pre-Filter Signal)

| Field | Detail |
|-------|--------|
| **Type** | REST API |
| **URL / Endpoint** | `https://huggingface.co/api/daily_papers` (daily listing), `https://huggingface.co/api/papers/{arxiv_id}` (single lookup) |
| **Authentication** | None required |
| **Rate Limits** | Not documented; no rate limit errors observed in testing. 1-second delay applied as conservative measure. |
| **Cost** | Free, no API key |
| **Data Format** | JSON |
| **Update Frequency** | Daily (community-submitted and HF-curated) |
| **Reliability** | Medium (undocumented API, no SLA; supplementary signal so failure is non-blocking) |

**Usage in the System**:

- **Weekly pipeline (Phase 2)**: After ArxivFetcher returns the raw paper list, HuggingFaceFetcher provides community upvote counts for papers that appear on HF Daily Papers. The `upvotes` field is the primary pre-filter signal used by PreFilter to reduce ~800--1,200 raw papers to the top 50--100 candidates for Ollama classification.
- **Not used in seeding (Phase 1)**: Landmark papers and surveys are fetched directly by arXiv ID; HF community signal is irrelevant for seeding.

**Query Construction**:

```
# Fetch all papers for a specific date
GET https://huggingface.co/api/daily_papers?date=2026-04-13

# Fetch 7 days (called once per day in the lookback window)
GET https://huggingface.co/api/daily_papers?date=2026-04-13
GET https://huggingface.co/api/daily_papers?date=2026-04-12
... (7 calls total)

# Look up a single paper by arXiv ID
GET https://huggingface.co/api/papers/2604.11521
```

**Sample Response** (confirmed live, 2026-04-13):

```json
{
  "paper": {
    "id": "2604.11521",
    "title": "Continuous Adversarial Flow Models",
    "upvotes": 1,
    "ai_keywords": [
      "continuous-time flow models",
      "adversarial objective",
      "learned discriminator",
      "flow matching"
    ],
    "ai_summary": "Continuous adversarial flow models improve image generation...",
    "publishedAt": "2026-04-13T00:00:00.000Z"
  },
  "numComments": 1,
  "submittedBy": { "...": "..." }
}
```

**Field Mapping to Internal Pydantic Model (`HFPaper`)**:

| JSON Path | `HFPaper` Field | Transformation |
|-----------|----------------|----------------|
| `paper.id` | `arxiv_id` | Direct string, e.g. `"2604.11521"` |
| `paper.title` | `title` | Direct string |
| `paper.upvotes` | `upvotes` | Integer. Range observed: 0--216 on a single day. Most papers have 1--5; high-signal papers reach 50--200+. |
| `paper.ai_keywords` | `ai_keywords` | `list[str]`, HF-generated. Useful for enrichment but not used in classification (Ollama extracts its own concepts). |
| `paper.ai_summary` | `ai_summary` | One-sentence HF-generated summary. Not used directly; Ollama generates its own summary. |
| `numComments` | `num_comments` | Integer. Discussion activity signal, stored but not currently used in scoring. |

**Fields Not Mapped (Intentionally Ignored)**:

| JSON Path | Reason |
|-----------|--------|
| `paper.publishedAt` | Already have `published_date` from arXiv, which is authoritative |
| `paper.summary` | This is the arXiv abstract re-hosted by HF; already fetched from arXiv |
| `paper.authors` | Already fetched from arXiv |
| `submittedBy` | Who submitted the paper to HF Daily. Not relevant to our pipeline. |

**Integration Pattern**:

HuggingFaceFetcher returns a `dict[str, HFPaper]` keyed by arXiv ID. The PreFilter joins this dict against the ArxivPaper list:

- Papers found in HF: `upvotes` field is populated from HF data.
- Papers not found in HF: `upvotes` defaults to 0. These papers still enter the pre-filter pool via their category priority score.

This ensures the HF signal boosts community-validated papers without excluding niche papers that the HF community did not submit.

**Volume**: 29--50 papers per day on HF Daily Papers. Over a 7-day window, this yields ~200--350 papers. Most of these will overlap with the arXiv fetch; the ones that don't are ignored (we use HF only for upvote enrichment, not as a paper source).

**Rate Limiting Strategy**:

- **Delay**: `time.sleep(1.0)` between sequential API calls. Conservative; no documented limit exists, but the API is undocumented and a courtesy delay is appropriate.
- **Configurable**: The delay (`hf_fetch_delay`) is defined in `config.py`.

**Fallback Strategy**:

HuggingFace data is supplementary. If the HF API is entirely unreachable or returns errors, the pipeline continues with `upvotes=0` for all papers. The PreFilter falls back to category priority scoring only. The digest will still be generated but may include slightly different papers than if HF signal were available. This degradation is logged as a warning but does not abort the pipeline.

---

### Source 3: Seeding Sources (One-Time, Phase 1)

These sources are used exclusively during the knowledge bank seeding phase and the manual `seed.py --arxiv-id <id>` CLI. They are not part of the weekly pipeline.

#### 3a. Landmark Papers (via arXiv API)

| Field | Detail |
|-------|--------|
| **Type** | REST API (same arXiv endpoint as Source 1) |
| **URL / Endpoint** | `https://export.arxiv.org/api/query?id_list={arxiv_id}` |
| **Authentication** | None |
| **Cost** | Free |
| **Data Format** | Atom XML |
| **Volume** | 17 papers (one-time fetch) |

**Paper List**:

| Paper | arXiv ID | Foundational Concept |
|-------|----------|---------------------|
| Attention Is All You Need (Transformer) | `1706.03762` | Transformer architecture, self-attention |
| BERT: Pre-training of Deep Bidirectional Transformers | `1810.04805` | Pre-training for NLP, masked language modeling |
| Language Models are Few-Shot Learners (GPT-3) | `2005.14165` | Few-shot learning, scaling |
| Deep Residual Learning (ResNet) | `1512.03385` | Residual connections, deep networks |
| Batch Normalization | `1502.03167` | Training stability, normalization |
| Efficient Estimation of Word Representations (Word2Vec) | `1301.3781` | Word embeddings, distributed representations |
| Generative Adversarial Nets (GAN) | `1406.2661` | Adversarial training, generative models |
| Auto-Encoding Variational Bayes (VAE) | `1312.6114` | Variational inference, latent spaces |
| Denoising Diffusion Probabilistic Models (DDPM) | `2006.11239` | Diffusion models, denoising |
| LoRA: Low-Rank Adaptation | `2106.09685` | Parameter-efficient fine-tuning |
| Proximal Policy Optimization (PPO) | `1707.06347` | Policy gradient methods, RLHF |
| Llama 2: Open Foundation and Fine-Tuned Chat Models | `2307.09288` | Open LLMs, RLHF alignment |
| Mamba: Linear-Time Sequence Modeling with Selective State Spaces | `2312.00752` | State space models |
| FlashAttention: Fast and Memory-Efficient Exact Attention | `2205.14135` | Efficient attention, IO-aware algorithms |
| Learning Transferable Visual Models From Natural Language Supervision (CLIP) | `2103.00020` | Vision-language pre-training, contrastive learning |
| A Survey of Reinforcement Learning from Human Feedback (RLHF) | `2307.01852` | RLHF overview |
| Scaling Laws for Neural Language Models | `2001.08361` | Neural scaling laws |

**Processing approach**: Fetch all 17 papers via a single batch API call (`id_list=1706.03762,1810.04805,...`). Extract title + abstract for each. Pass each to `OllamaClassifier.extract_concepts()` to populate the knowledge bank with foundational concepts. Create `INTRODUCES` edges from each paper node to its extracted concept nodes.

**Rate limiting**: Single batch call, then one Ollama inference per paper. The 3-second arXiv delay applies between paginated requests if the batch exceeds the page size, but 17 papers will fit in a single response.

#### 3b. Survey Papers (via arXiv API)

| Field | Detail |
|-------|--------|
| **Type** | REST API (same arXiv endpoint as Source 1) |
| **URL / Endpoint** | `https://export.arxiv.org/api/query?id_list={arxiv_id}` |
| **Authentication** | None |
| **Cost** | Free |
| **Data Format** | Atom XML |
| **Volume** | 10 papers (one-time fetch) |

**Paper List**:

| Domain | Paper | arXiv ID |
|--------|-------|----------|
| NLP / LLMs | A Survey of Large Language Models | `2303.18223` |
| Computer Vision | An Image is Worth 16x16 Words (ViT) | `2010.11929` |
| Reinforcement Learning | Deep Reinforcement Learning: An Overview | `1701.07274` |
| Graph Neural Networks | A Comprehensive Survey on Graph Neural Networks | `1901.00596` |
| Federated Learning | Communication-Efficient Learning of Deep Networks | `1602.05629` |
| Multimodal ML | Multimodal Machine Learning: A Survey and Taxonomy | `2209.03430` |
| Efficient Deep Learning | Efficient Deep Learning: A Survey | `2106.08962` |
| Explainability | A Survey of Methods for Explaining Black Box Models (XAI) | `1802.01528` |
| Prompt Engineering | Pre-train, Prompt, and Predict: A Systematic Survey | `2107.13586` |

**Note**: The research report recommended a 10th survey for MLOps (referencing Chip Huyen's work), but no arXiv ID was identified. This domain gap is accepted for the PoC. If a suitable MLOps survey is found, it can be added via `python seed.py --arxiv-id <id>`.

**Processing approach**: Same as landmark papers -- batch fetch via arXiv API, extract concepts via Ollama. Survey papers produce broader, domain-spanning concept maps compared to the narrower concepts from landmark papers.

#### 3c. Textbooks (via PDF Download)

| Field | Detail |
|-------|--------|
| **Type** | PDF file download (one-time, manual or scripted) |
| **URL** | See table below |
| **Authentication** | None (all freely and legally available) |
| **Cost** | Free |
| **Data Format** | PDF (digital-native, clean text layers) |
| **Library** | PyMuPDF (`fitz`) for text extraction |

**Textbook List (MVP — 5 books)**:

| Textbook | URL | Chapters to Process | Status |
|----------|-----|---------------------|--------|
| Murphy -- *Probabilistic Machine Learning: An Introduction* (2022) | https://probml.github.io/pml-book/ | All 23 chapters | PDF downloaded, 3 chapters seeded in PoC, 20 remaining |
| Sutton & Barto -- *Reinforcement Learning: An Introduction* (2nd ed., 2020) | http://incompleteideas.net/book/the-book-2nd.html | 15 chapters (skip Psychology/Neuroscience) | PDF downloaded, 3 chapters seeded in PoC, 12 remaining |
| Hastie, Tibshirani, Friedman -- *Elements of Statistical Learning* (2009) | Author's Google Drive link | All 17 chapters | PDF downloaded in PoC |
| Bishop -- *Pattern Recognition and Machine Learning* (2006) | Microsoft Research | All 14 chapters | PDF downloaded in PoC |
| Zhang et al. -- *Dive into Deep Learning* (2023) | https://d2l.ai/ | 17 key chapters (skip Builders Guide, Computational Performance, Appendices) | PDF downloaded in PoC, Goodfellow substitute |

**Dropped from PoC list**: Goodfellow *Deep Learning* — MIT Press forbids PDF distribution; HTML-only format unsuitable for PdfExtractor.

**Processing approach**:

1. Download PDFs manually to `data/textbooks/`. These files are gitignored.
2. `PdfExtractor.extract_chapters()` extracts text per chapter using TOC-verified page ranges.
3. Each extracted chapter is chunked to ~3000 words and passed to `ConceptExtractor` via `LLMClient`.
4. Source-type-aware prompts: textbook_chapter extracts 5-15 concepts per chunk.
5. Chapter page ranges are configured in `TEXTBOOK_CONFIGS` in `seed.py`, TOC-derived and 0-indexed.
6. Expected noise: headers, footers, figure captions, equation formatting artifacts. Ollama handles noisy input well with schema-constrained output.

**Field Mapping to Processing Input**:

| Extraction Field | Usage |
|-----------------|-------|
| Chapter text (raw string from PyMuPDF) | Input to `OllamaClassifier.extract_concepts()` |
| Source description (e.g., "Goodfellow et al. Deep Learning, Ch. 3: Probability") | Stored as `seeded_from` in concept node properties for provenance |

**Fallback Strategy**:

If a textbook PDF is unavailable (URL changed, download fails), the seeding phase proceeds without it. The affected domain's concepts will have less coverage in the knowledge bank. Gaps can be identified during the first 4 weekly runs by reviewing unmatched concept names in ConceptLinker logs, then backfilled with additional survey papers via `seed.py --arxiv-id`.

---

### Source 4: Excluded Sources

These sources were evaluated during the research phase and excluded from the PoC. The reasons are documented here for future reference.

#### 4a. Papers with Code

| Field | Detail |
|-------|--------|
| **Status** | API deprecated; redirects to HuggingFace |
| **Evidence** | `paperswithcode.com/api/v1/` returns HTTP 302, redirecting to `https://huggingface.co/papers/trending` (confirmed 2026-04-14) |
| **What it offered** | Benchmark leaderboard links, code repository associations, state-of-the-art tracking by task |
| **Why excluded** | API no longer functional. The HuggingFace Daily Papers API (Source 2) is the successor for community paper discovery. Benchmark/code data is still browsable on the website but not programmatically accessible without scraping (ToS risk). |
| **Revisit trigger** | If HuggingFace exposes benchmark/code-link data via their API in the future, consider integrating it. |

#### 4b. Semantic Scholar

| Field | Detail |
|-------|--------|
| **Status** | Partially viable but excluded from PoC |
| **URL** | `https://api.semanticscholar.org/graph/v1/` |
| **Evidence** | HTTP 429 returned on the second sequential unauthenticated request (confirmed in testing). Free API key available via web form for ~100 req/s. |
| **What it offers** | `citationCount`, `influentialCitationCount`, `fieldsOfStudy`, cross-paper reference graph |
| **Why excluded** | (1) Rate-limited to the point of being unreliable without an API key, violating the zero-dependency PoC approach. (2) Citation counts are near-zero for papers less than ~6 months old, making it useless for the weekly digest of new papers. (3) Obtaining a free API key is a 5-minute form but adds a credential management concern. |
| **Revisit trigger** | If the project adds citation-velocity enrichment for older papers (e.g., re-scoring papers from 6+ months ago), apply for the free S2 API key and add an S2 integration module. |

#### 4c. Google Scholar

| Field | Detail |
|-------|--------|
| **Status** | Not viable |
| **Evidence** | No public API exists. Scraping is actively blocked and violates Google's Terms of Service. |
| **What it offers** | Citation counts (the most comprehensive citation database) |
| **Why excluded** | No programmatic access path that doesn't violate ToS. |
| **Revisit trigger** | None foreseeable. Google Scholar has never offered a public API. |

#### 4d. OpenReview

| Field | Detail |
|-------|--------|
| **Status** | Partially viable but excluded from PoC |
| **URL** | `https://api2.openreview.net/` |
| **Evidence** | HTTP 403 for unauthenticated access to ICLR 2024 submissions (confirmed in testing). Free registration required. |
| **What it offers** | Access to ICLR, NeurIPS, ICML paper decisions, peer review scores, reviewer comments |
| **Why excluded** | (1) Requires registration (credential management). (2) arXiv already captures most conference papers as preprints, so the incremental value is peer review metadata, not paper discovery. (3) Low priority for the PoC's core use case of weekly monitoring. |
| **Revisit trigger** | If the user wants to incorporate conference acceptance decisions or review quality signals into the tier classification, register for OpenReview and add an integration module. |

---

## Data Quality Considerations

### arXiv Data Quality

- **Missing abstracts**: Rare but possible for withdrawn papers. ArxivFetcher logs a warning and skips papers with empty `<summary>` elements.
- **Duplicate entries from cross-listing**: A paper listed in both `cs.LG` and `cs.AI` appears in both category queries. Deduplicated by arXiv ID before any downstream processing.
- **Version suffixes**: The `<id>` field includes version (e.g., `2604.11805v1`). The fetcher strips the version suffix to produce a canonical `arxiv_id` used as the deduplication key and node ID.
- **Title/abstract encoding**: arXiv XML uses standard UTF-8 encoding. LaTeX math notation appears as raw LaTeX in titles and abstracts (e.g., `$O(n \log n)$`). This is passed directly to Ollama, which handles LaTeX notation in prompts without issues.
- **Publication date semantics**: The `<published>` field reflects when the paper was first submitted to arXiv, not when it was published at a conference. For weekly monitoring, this is the correct date to filter on.
- **Category assignment**: Authors self-assign categories. Some papers are miscategorized. The pre-filter's category priority scoring mitigates this by not relying solely on category for importance.

### HuggingFace Data Quality

- **Coverage gap**: HF Daily Papers covers 29--50 papers/day vs. ~150--200+ new ML papers/day on arXiv. This is by design -- HF is used as a quality signal, not a complete source. Papers not on HF receive `upvotes=0` and are still eligible via category priority.
- **Community bias**: HF upvotes skew toward trendy/viral topics (LLMs, image generation) and may underweight niche but important work (e.g., theoretical ML, federated learning). Mitigated by the category priority score in PreFilter, which ensures representation across all five monitored categories.
- **Upvote count instability**: Upvote counts may change between the time the pipeline fetches them and the time the user reads the digest. This is acceptable -- the count is used as a relative ranking signal, not an absolute metric.
- **Undocumented API**: The HF Daily Papers API is not officially documented. Endpoint behavior, response schema, or availability could change without notice. The Pydantic model validation will catch schema changes; if the API breaks, the pipeline degrades gracefully (falls back to category-only scoring).

### Textbook PDF Quality

- **Extraction noise**: PyMuPDF (fitz) extracts text reliably from digital-native PDFs but produces artifacts from figure captions, headers/footers, page numbers, and mathematical equations. Acceptable for PoC -- Ollama handles noisy input well enough for concept extraction.
- **Chapter boundary detection**: Page ranges for chapters must be manually specified in the seeding configuration. There is no automatic chapter detection.
- **Encoding**: All target textbooks are modern, digital-native PDFs with clean Unicode text layers. No OCR-dependent sources.

### Ollama Output Quality

- **JSON compliance**: Ollama's `format="json"` parameter forces JSON output mode, but the structure may not always match the expected schema. Validated by Pydantic; retry logic (up to 3 attempts) handles most transient failures.
- **Tier 1/2 ambiguity**: The 7B model (`qwen2.5:7b`) struggles more with the T1/T2 distinction than larger models. Mitigated with 3--5 few-shot examples of known T1 and T2 papers in the system prompt. A 20-paper eval set with human-assigned tiers is planned for validation.
- **Concept name consistency**: Different Ollama calls may produce slightly different names for the same concept (e.g., "attention mechanism" vs. "self-attention"). ConceptLinker uses fuzzy matching (threshold 0.85) to handle minor variations. The controlled vocabulary from seeding anchors the canonical names.

---

## Data Privacy & Compliance

### No PII Collected

The system processes only publicly available academic metadata:

- Paper titles, authors, abstracts, and categories from arXiv (public)
- Community upvote counts from HuggingFace (public)
- Freely available textbook content (published with open access by their authors)

No personally identifiable information is collected, processed, or stored beyond author names that are already part of the public academic record.

### Terms of Service Compliance

| Source | ToS Status |
|--------|-----------|
| **arXiv API** | arXiv permits automated access via their API. The 3-second courtesy delay between requests satisfies their usage policy. Bulk redistribution of content is not planned. |
| **HuggingFace API** | No published API ToS for the daily papers endpoint (undocumented API). Usage is limited to personal, non-commercial enrichment of publicly available paper metadata. Conservative rate limiting (1s delay) applied. |
| **Textbook PDFs** | All four textbooks are freely and legally distributed by their authors/publishers at the listed URLs. Downloaded for personal knowledge extraction, not redistribution. |
| **Google Scholar** | Excluded specifically because scraping violates ToS. |
| **Papers with Code** | Excluded because the API is deprecated. No scraping of the website. |

### Data Storage

- All data is stored locally in a SQLite database on the user's iMac. No cloud storage, no network access to the database.
- The `data/` directory (containing the SQLite database, logs, and downloaded PDFs) is gitignored.
- Generated HTML digests are gitignored (generated artifacts).
- No secrets or API keys are required or stored by the PoC.

---

## Integration Summary

The following table shows how each data source connects to the system components defined in the TDD:

| Source | Component | When Used | Data Direction | Failure Impact |
|--------|-----------|-----------|---------------|----------------|
| arXiv API | `ArxivFetcher` | Weekly (Phase 2) + Seeding (Phase 1) | arXiv -> ArxivPaper -> GraphStore | **Pipeline abort** (primary source) |
| HuggingFace API | `HuggingFaceFetcher` | Weekly (Phase 2) | HF -> HFPaper -> PreFilter | **Graceful degradation** (falls back to category-only scoring) |
| Landmark papers | `ArxivFetcher.fetch_batch()` | Seeding (Phase 1, one-time) | arXiv -> ArxivPaper -> OllamaClassifier -> GraphStore | Seeding is incomplete; retry manually |
| Survey papers | `ArxivFetcher.fetch_batch()` | Seeding (Phase 1, one-time) | arXiv -> ArxivPaper -> OllamaClassifier -> GraphStore | Seeding is incomplete; retry manually |
| Textbook PDFs | `PdfExtractor` | Seeding (Phase 1, one-time) | PDF -> ChapterText -> OllamaClassifier -> GraphStore | Reduced concept coverage; backfill with surveys |
