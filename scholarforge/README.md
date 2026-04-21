# ScholarForge

**Provenance-first scholarly research workspace** — harvest academic literature from 20 free sources, build trustworthy corpora, and prepare writing-ready exports.

```
███████╗ ██████╗██╗  ██╗ ██████╗ ██╗      █████╗ ██████╗ 
██╔════╝██╔════╝██║  ██║██╔═══██╗██║     ██╔══██╗██╔══██╗
███████╗██║     ███████║██║   ██║██║     ███████║██████╔╝
╚════██║██║     ██╔══██║██║   ██║██║     ██╔══██║██╔══██╗
███████║╚██████╗██║  ██║╚██████╔╝███████╗██║  ██║██║  ██║
╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝

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

ScholarForge is a terminal-based scholarly research workbench. It is **not** an AI agent wrapper and **not** a generic search tool. It is a calm, scholar-first workspace designed for researchers, students, and authors.

**What it does:**

| Command | What it does |
|---|---|
| `scholarforge new` | Create a research project (wizard guides you step by step) |
| `scholarforge search` | Paste a title or question → expands to queries → harvests 20 APIs |
| `scholarforge import` | Copy your own documents into the project corpus |
| `scholarforge build` | Extract and chunk all corpus documents into a knowledge dataset |
| `scholarforge export` | Export bibliography as BibTeX, CSL-JSON, or annotated Markdown |
| `scholarforge review-project` | Terminal report of your project state |

**Key differentiators:**
- Natural-language search — paste a full research title or question, no keyword tuning needed
- Trust labels on every record (peer-reviewed, preprint, grey literature)
- Humanities-friendly, not STEM-only
- Multilingual (Unicode + accent-stripped matching + domain lexicons)
- Writing-readiness: BibTeX, CSL-JSON, annotated literature-review Markdown
- Zero mandatory dependencies

---

## Installation

### Requirements
- Python 3.8 or newer ([download here](https://www.python.org/downloads/))
- Git ([download here](https://git-scm.com/downloads))

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/AnastasiosPapalias/Python.git
cd Python/scholarforge

# 2. Install ScholarForge (editable install — recommended)
pip install -e .

# 3. Optional: install PDF and DOCX support
pip install pypdf python-docx

# 4. Verify
scholarforge --version
```

After installation, the `scholarforge` command is available anywhere in your terminal.

---

## Quick Start

### Beginner path (wizard)

Just run:

```bash
mkdir my-research
scholarforge new my-research
```

The wizard will ask you plain-English questions — no jargon. Press Enter to accept any default.

Then search:

```bash
scholarforge search --project my-research "effects of microplastics on marine invertebrates"
```

### Power-user path (flags)

```bash
# Create project without wizard
scholarforge new --skip-wizard --name marine-plastics --kind thesis my-research

# Search with options
scholarforge search --project my-research --max-results 50 "microplastics marine invertebrates"

# Export bibliography
scholarforge export --project my-research --format bibtex

# Build knowledge dataset from corpus
scholarforge build --project my-research

# Review project state
scholarforge review-project --project my-research
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

### Project layout (after `scholarforge new`)
```
my-research/
├── project.toml       ← project settings
├── sources/           ← raw API results
├── downloads/         ← downloaded PDFs, EPUBs, HTMLs
├── corpus/            ← documents you imported manually
├── reports/           ← harvest summaries, error logs
└── exports/           ← BibTeX, CSL-JSON, Markdown, knowledge dataset
```

### Knowledge dataset chunk format (`build`)
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
scholarforge [--version] [--no-banner] [--no-color] [--verbose]

Commands:
  new [DIR]                   Create a research project (wizard on TTY)
    --skip-wizard             Skip wizard, use flags instead
    --name NAME               Project name
    --kind thesis|article|book|exploration
    --goal "..."              Research goal in one sentence
    --field humanities|social|life|physical|cs|interdisciplinary
    --recency 5y|10y|any
    --trust-floor peer_reviewed|peer_or_preprint|any
    --languages en,fr,...

  search [--project DIR] "title or question"
    --max-results N           Results per source (default: 25)
    --min-score N             Relevance threshold (default: 10)
    --no-download             Metadata-only, skip downloads
    --dry-run                 Show query plan only
    --multilingual            Include multilingual query variants
    --recent                  Bias toward recent publications

  import [--project DIR] SOURCE_DIR

  build [--project DIR]
    --chunk-size N            Characters per chunk (default: 3500)
    --overlap N               Overlap between chunks (default: 350)
    --source corpus|downloads|all

  export [--project DIR] --format bibtex|csljson|markdown
    --output PATH             Output file path
    --title "..."             Title for Markdown export

  review-project [--project DIR]

Legacy commands (still work):
  harvest, forge, pipeline
```

---

## API Keys (optional)

ScholarForge works without any API keys. Keys improve rate limits and result quality for two sources:

| Source | Key needed | Sign up |
|---|---|---|
| CORE | Free | https://core.ac.uk/services/api |
| Semantic Scholar | Free | https://www.semanticscholar.org/product/api |

### How to add keys

**Option A — global config file (recommended)**

```bash
scholarforge config --init
```

This creates `~/.scholarforge.toml`. Open it in any text editor and fill in your keys:

```toml
[api_keys]
core_api_key = "your-core-key-here"
semantic_scholar_key = "your-s2-key-here"
```

**Option B — environment variables**

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, or Windows environment variables)
export SCHOLARFORGE_CORE_API_KEY="your-key"
export SCHOLARFORGE_SEMANTIC_SCHOLAR_KEY="your-key"
```

**Option C — .env file**

Create a `.env` file in your project folder:

```
SCHOLARFORGE_CORE_API_KEY=your-key
SCHOLARFORGE_SEMANTIC_SCHOLAR_KEY=your-key
```

### Check your current key status

```bash
scholarforge config
```

---

## Requirements

- **Python 3.8+** — zero mandatory third-party packages
- `pip install pypdf` — PDF extraction (highly recommended)
- `pip install python-docx` — DOCX extraction

---

## Changelog

### v3.4.0-beta.1 (2026-04-21)
- Modular package architecture (`scholarforge/` package)
- New CLI: `new`, `search`, `import`, `build`, `export`, `review-project`
- Project workspaces with `project.toml`
- Beginner onboarding wizard (plain-English, no jargon)
- Trust labels + provenance on every record
- BibTeX, CSL-JSON, and annotated Markdown exports
- Title/question → deterministic query expansion (no AI required)
- Domain lexicons: biology, neuroscience, psychiatry, classics, philosophy, music
- 65-test suite

### v3.3.0 (2026-03-30)
- +7 new sources → 20 total: Figshare, HAL, SSRN, Paperity, PMC Full-Text, OA.mg, EThOS/DART-Europe

### v3.2.0
- Removed book/paper mode split — all sources always active
- Added arXiv, Europe PMC, Zenodo, CORE, DOAJ, OpenAIRE (13 total)

### v3.1.0
- Full Unicode support + accent-normalised matching
- Inline `h` help at every prompt; `--explain FIELD` CLI flag
- Pipeline mode

### v3.0.0
- Initial release: combined bibliography harvester + knowledge dataset builder

---

## Author

**Anastasios Papalias** · [github.com/AnastasiosPapalias](https://github.com/AnastasiosPapalias)

## License

MIT — see [LICENSE](LICENSE)
