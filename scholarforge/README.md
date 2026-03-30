# ScholarForge

**Academic Research & Knowledge Pipeline** — the definitive tool for harvesting academic literature from 20 free sources and building AI-ready knowledge datasets for book writing, research, and LLM workflows.

```
███████╗ ██████╗██╗  ██╗ ██████╗ ██╗      █████╗ ██████╗ ███████╗
██╔════╝██╔════╝██║  ██║██╔═══██╗██║     ██╔══██╗██╔══██╗██╔════╝
███████╗██║     ███████║██║   ██║██║     ███████║██████╔╝█████╗
╚════██║██║     ██╔══██║██║   ██║██║     ██╔══██║██╔══██╗██╔══╝
███████║╚██████╗██║  ██║╚██████╔╝███████╗██║  ██║██║  ██║███████╗
╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝

     ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
     ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
     █████╗  ██║   ██║██████╔╝██║  ███╗█████╗
     ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
     ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
     ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
```

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Zero mandatory deps](https://img.shields.io/badge/deps-zero%20mandatory-brightgreen.svg)]()
[![Sources](https://img.shields.io/badge/sources-20%20APIs-orange.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

---

## What is ScholarForge?

ScholarForge is a **single Python script** that combines two powerful research workflows:

| Mode | What it does |
|---|---|
| **harvest** | Searches **20 academic APIs simultaneously**, scores by relevance, downloads open-access PDFs/EPUBs |
| **forge** | Scans a folder of documents, extracts all text, exports a structured knowledge dataset for AI/LLM use |
| **pipeline** | Runs both stages back-to-back: search → download → chunk → export |

Designed for **researchers, authors, and academics** who want to build a comprehensive personal library around any topic — with zero friction and zero cost.

---

## Features

### Harvest
- Queries **20 academic sources simultaneously** — books, papers, preprints, theses, datasets
- No book/paper split — searches everything at once
- **Exact-phrase + broad query** per subject for maximum recall
- **Unicode-aware relevance scoring** with accent-normalised matching (Greek, Cyrillic, CJK)
- Automatic deduplication by DOI + title + year
- Exponential back-off retries on rate-limits (429/5xx)
- Full **contextual inline help** — press `h` at any prompt for detailed explanations

### Forge
- Reads **12+ file formats**: PDF, DOCX, TXT, Markdown, HTML, XML, JSON, CSV, TSV, RTF, YAML, TeX
- Semantic chunking with paragraph/sentence boundary snapping
- Language detection (English, Greek, German, French, Spanish)
- Exports `knowledge_dataset.jsonl` (AI-ready chunks), `knowledge_sources.csv`, `knowledge_corpus.md`, `knowledge_summary.json`

### General
- Beautiful ASCII UI: progress bars with ETA, spinners, tables, colour-coded status
- Fully interactive wizard OR fully non-interactive via flags
- Windows, macOS, Linux
- Zero mandatory dependencies

---

## Installation

```bash
git clone https://github.com/AnastasiosPapalias/scholarforge.git
cd scholarforge
pip install pypdf python-docx   # optional but recommended
```

---

## Quick Start

```bash
# Interactive — just run it
python scholarforge.py

# Harvest (searches all 20 sources)
python scholarforge.py harvest \
  --subjects "quantum mechanics, wave-particle duality" \
  --output ./my_library

# Greek subjects fully supported
python scholarforge.py harvest \
  --subjects "καβείρια μυστήρια, Samothrace, Kabeiroi" \
  --output ./kabeiroi_research

# Forge a folder of documents
python scholarforge.py forge /path/to/documents --output ./knowledge_export

# Full pipeline
python scholarforge.py pipeline \
  --subjects "Byzantine music, neumes" \
  --output ./byzantine_research

# Get detailed help for any field
python scholarforge.py --explain min_score
python scholarforge.py --explain subjects
```

---

## Academic Sources (20 total)

### Metadata & Citation Backbone
| Source | Coverage | Free PDF |
|---|---|---|
| [OpenAlex](https://openalex.org) | 250M+ works, all disciplines | ✅ OA filter |
| [Crossref](https://www.crossref.org) | 150M+ DOI metadata | ✅ When available |
| [Semantic Scholar](https://www.semanticscholar.org) | 200M+ papers + AI ranking | ✅ When available |

### OA-First Search Engines
| Source | Coverage | Free PDF |
|---|---|---|
| [OA.mg](https://oa.mg) | 250M+ OA papers | ✅ Always |
| [CORE](https://core.ac.uk) | 260M+ full-text from repositories | ✅ Always |
| [DOAJ](https://doaj.org) | Peer-reviewed OA journals only | ✅ Always |
| [Paperity](https://paperity.org) | 100% OA journals aggregator | ✅ Always |

### Preprint & Discipline Repositories
| Source | Coverage | Free PDF |
|---|---|---|
| [arXiv](https://arxiv.org) | 2M+ preprints: physics, CS, maths, bio | ✅ Always |
| [SSRN](https://ssrn.com) | Economics, law, finance, social sciences | ✅ Most |

### Biomedical Full-Text
| Source | Coverage | Free PDF |
|---|---|---|
| [PubMed](https://pubmed.ncbi.nlm.nih.gov) | 35M+ biomedical citations | ✅ Via PMC |
| [PMC Full-Text](https://pmc.ncbi.nlm.nih.gov) | NIH full-text archive | ✅ Always |
| [Europe PMC](https://europepmc.org) | 40M+ life sciences + books + theses | ✅ Many |

### Open Repositories
| Source | Coverage | Free PDF |
|---|---|---|
| [Zenodo](https://zenodo.org) | CERN open archive: datasets, theses, reports | ✅ Always |
| [Figshare](https://figshare.com) | Papers, datasets, posters, theses, code | ✅ Always |
| [HAL](https://hal.science) | 4.4M+ papers, strong in humanities | ✅ OA filter |
| [OpenAIRE](https://openaire.eu) | EU-funded research, institutional repos | ✅ Many |

### Books & General
| Source | Coverage | Free PDF |
|---|---|---|
| [Google Books](https://books.google.com) | Largest book index | Preview/OA |
| [Internet Archive](https://archive.org) | Books, documents, historical texts | ✅ Many |
| [Open Library](https://openlibrary.org) | 20M+ books | ✅ Public domain |

### Theses
| Source | Coverage | Free PDF |
|---|---|---|
| [EThOS / DART-Europe](https://ethos.bl.uk) | UK & European doctoral theses | ✅ Many |

---

## Output Structure

### Harvest
```
./my_library/
├── downloads/          ← Downloaded PDFs, EPUBs, HTMLs
├── metadata/
│   ├── filtered_records.jsonl
│   ├── filtered_records.csv
│   ├── raw_records.jsonl
│   └── <source>.jsonl  (one per source)
└── reports/
    ├── harvest_summary.json
    ├── manual_search_links.txt
    ├── errors.txt
    └── failed_downloads.txt
```

### Forge
```
./knowledge_export/
├── knowledge_dataset.jsonl   ← AI-ready chunks
├── knowledge_sources.csv
├── knowledge_corpus.md
└── knowledge_summary.json
```

### Chunk format
```json
{
  "source_path": "/path/to/file.pdf",
  "file_name": "paper.pdf",
  "extension": ".pdf",
  "page": 3,
  "chunk_index": 2,
  "text": "The mysteries of Samothrace...",
  "char_count": 3412,
  "word_count": 578,
  "text_sha256": "a3f9...",
  "language_hint": "en"
}
```

---

## CLI Reference

```
python scholarforge.py [--version] [--no-banner] [--no-color]
                       [--verbose] [--deps] [--explain FIELD]
                       MODE [options]

Modes:
  harvest    Search all 20 APIs and download documents
  forge      Build knowledge dataset from a document folder
  pipeline   Harvest then forge in sequence

harvest options:
  --subjects, -s      Comma-separated subjects (Unicode supported)
  --output, -o        Output directory
  --max-results N     Max results per source per query (default: 25)
  --min-score SCORE   Minimum relevance score (default: 10.0)
  --max-downloads N   Max documents to download (default: 100)
  --no-download       Skip downloading (metadata-only run)

forge options:
  DIR                 Source folder to scan
  --output, -o        Output directory
  --chunk-size N      Characters per chunk (default: 3500)
  --overlap N         Overlap between chunks (default: 350)
  --extensions EXT…   Whitelist of extensions, e.g. pdf txt docx
  --include-hidden    Also scan hidden files

--explain FIELD:
  subjects, max_results, min_score, max_downloads, chunk_size, overlap
```

---

## LLM / RAG Integration

```python
import json, chromadb

client = chromadb.Client()
col    = client.create_collection("my_research")

with open("knowledge_dataset.jsonl") as f:
    for i, line in enumerate(f):
        chunk = json.loads(line)
        col.add(
            documents=[chunk["text"]],
            metadatas=[{"source": chunk["file_name"], "page": chunk["page"]}],
            ids=[f"chunk_{i}"]
        )
```

---

## Requirements

- **Python 3.8+** (zero mandatory third-party packages)
- `pip install pypdf` — PDF extraction
- `pip install python-docx` — DOCX extraction

```bash
python scholarforge.py --deps   # check status
```

---

## Changelog

### v3.3.0 (2026-03-30)
- **+7 new sources** → 20 total: Figshare, HAL, SSRN, Paperity, PMC Full-Text, OA.mg, EThOS/DART-Europe
- Sources grouped by type in UI

### v3.2.0
- Removed book/paper mode — all sources always active
- Added arXiv, Europe PMC, Zenodo, CORE, DOAJ, OpenAIRE (13 total)

### v3.1.0
- Fixed summary box overflow for long paths/source lists
- Full Unicode support + accent-normalised matching
- Inline `h` help at every prompt; `--explain FIELD` CLI flag
- Pipeline mode: full harvest + forge configuration

### v3.0.0
- Initial release: combined bibliography_harvester + build_knowledge_dataset
- Interactive ASCII wizard

---

## Author

**Anastasios Papalias** · [github.com/AnastasiosPapalias](https://github.com/AnastasiosPapalias)

## License

MIT — see [LICENSE](LICENSE)
