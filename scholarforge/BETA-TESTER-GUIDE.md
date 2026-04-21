# ScholarForge — Beta Tester Guide

Thank you for testing ScholarForge. This guide walks you through installation and first use on **Windows 11**. It assumes no prior experience with Python or the terminal.

---

## Step 1 — Install Python

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Click **Download Python 3.x.x** (the big yellow button)
3. Run the installer
4. **Important:** on the first screen, tick the box that says **"Add Python to PATH"** before clicking Install

To verify: open the Start menu, search for **Command Prompt**, open it, and type:

```
python --version
```

You should see something like `Python 3.12.3`. If you do, Python is ready.

---

## Step 2 — Install Git

1. Go to [https://git-scm.com/downloads](https://git-scm.com/downloads)
2. Click **Windows**, download the installer, run it
3. Click Next through all the steps — the defaults are fine

To verify (in Command Prompt):

```
git --version
```

You should see something like `git version 2.44.0`.

---

## Step 3 — Install ScholarForge

Open **Command Prompt** (search for it in the Start menu) and run these commands one by one. Copy and paste each line, then press Enter and wait for it to finish before typing the next.

```
git clone https://github.com/AnastasiosPapalias/Python.git
```

```
cd Python\scholarforge
```

```
pip install -e .
```

```
pip install pypdf python-docx
```

This downloads ScholarForge and installs it. It only needs to be done once.

To verify:

```
scholarforge --version
```

You should see `ScholarForge 3.4.0-beta.1` (or similar).

---

## Step 4 — Create your first research project

Choose a folder where you want to store your research. For example, your Desktop.

In Command Prompt:

```
cd %USERPROFILE%\Desktop
```

```
mkdir my-research
```

```
scholarforge new my-research
```

ScholarForge will start a wizard and ask you a few plain-English questions:
- Your project name
- What you are researching (one sentence)
- Your research field
- What you are writing (thesis, article, book, or just exploring)
- How recent the sources should be
- How strict the trust filter should be
- What language(s) sources should be in

Press **Enter** to accept the default shown in brackets, or type your answer.

---

## Step 5 — Search for papers

After creating the project, run a search. Paste your research topic or a full paper title — no need to use keywords.

```
scholarforge search --project %USERPROFILE%\Desktop\my-research "your research topic or question here"
```

Example:

```
scholarforge search --project %USERPROFILE%\Desktop\my-research "effects of microplastics on marine invertebrate reproduction"
```

ScholarForge will search 20 academic databases simultaneously. This takes 1–3 minutes depending on your internet connection. Downloaded PDFs will appear in the `downloads/` folder inside your project.

---

## Step 6 — Export your bibliography

After searching, you can export a bibliography:

```
scholarforge export --project %USERPROFILE%\Desktop\my-research --format bibtex
```

Or as a readable Markdown file:

```
scholarforge export --project %USERPROFILE%\Desktop\my-research --format markdown
```

The file will appear in the `exports/` folder inside your project.

---

## Step 7 — Review your project

At any time, you can see a summary of what your project contains:

```
scholarforge review-project --project %USERPROFILE%\Desktop\my-research
```

---

## Where your files end up

```
Desktop\my-research\
├── project.toml       ← your project settings
├── downloads\         ← PDFs downloaded automatically
├── corpus\            ← papers you add manually
├── exports\           ← bibliography files
└── reports\           ← harvest logs and summaries
```

---

## Reporting problems

If anything goes wrong or looks unexpected, please note:

1. The exact command you ran
2. The error message shown (a screenshot works fine)
3. What you expected to happen

Send these to Anastasios. Every bug report helps — even "this was confusing" is useful feedback.

---

## Tips

- You can run `scholarforge` in any folder — it works from anywhere once installed
- The search accepts full sentences, not just keywords — try pasting a paper title directly
- Press Ctrl+C at any time to cancel a running command

---

*ScholarForge v3.4.0-beta.1 — Thank you for your time.*
