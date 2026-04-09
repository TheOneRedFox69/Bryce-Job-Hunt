# 🎯 Bryce Hunt — AI Job Search Tool

A personalised job search app built with Streamlit + Anthropic Claude.

## Features

- **AI Web Search** — Claude searches the live web for matching job listings
- **LinkedIn Scraper** — scrapes LinkedIn Jobs public search (no login required)  
- **Indeed Scraper** — scrapes Indeed across UK, EU, and Canada domains
- **Smart Scoring** — every listing scored 0–100 against your profile (role, sector, location, salary, visa)
- **Document Generation** — one-click tailored cover letters and CV summaries per role
- **Save & Track** — save roles, add notes, export a digest

---

## Quick Start

### Option 1: GitHub Codespaces (recommended)
1. Open this repo in GitHub → click **Code → Codespaces → Create codespace**
2. Codespaces will install dependencies automatically
3. Add your Anthropic API key (see Secrets below)
4. Run: `streamlit run app.py`
5. Codespaces will forward port 8501 and open a browser tab

### Option 2: Local
```bash
git clone https://github.com/YOUR_USERNAME/bryce-job-hunt.git
cd bryce-job-hunt
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Add API key (see below)
streamlit run app.py
```

---

## API Key Setup

### Local / Codespaces
Create `.streamlit/secrets.toml` (already gitignored):
```toml
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```
Then load it in your shell (Codespaces auto-loads Streamlit secrets):
```bash
export ANTHROPIC_API_KEY=$(python -c "import tomllib; print(tomllib.load(open('.streamlit/secrets.toml','rb'))['ANTHROPIC_API_KEY'])")
```

### Streamlit Cloud
1. Deploy from GitHub (see below)
2. Go to your app → **Settings → Secrets**
3. Add:
```toml
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

---

## Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → main file: `app.py`
4. Add `ANTHROPIC_API_KEY` in Settings → Secrets
5. Click **Deploy** — live in ~60 seconds

---

## Project Structure

```
bryce-job-hunt/
├── app.py                  # Main Streamlit app
├── requirements.txt
├── src/
│   ├── profile.py          # Your candidate profile (edit this!)
│   ├── search_ai.py        # Claude AI + web search
│   ├── scraper_linkedin.py # LinkedIn public scraper
│   ├── scraper_indeed.py   # Indeed scraper
│   ├── scorer.py           # Scoring engine
│   ├── doc_generator.py    # Cover letter + CV summary AI generation
│   ├── storage.py          # JSON-based saved jobs store
│   └── digest.py           # Email digest builder
├── .streamlit/
│   ├── config.toml         # Theme config
│   └── secrets.toml        # Local secrets (gitignored)
└── .devcontainer/
    └── devcontainer.json   # Codespaces config
```

---

## Customising Your Profile

Edit `src/profile.py` to update:
- Target roles, locations, sectors
- Salary range
- Skills keywords (used for scoring)
- Your CV text and background summary (used for document generation)

---

## LinkedIn Scraper Notes

⚠️ Scraping LinkedIn violates their ToS. The scraper uses their **public** job search 
page (no login required). Expect:
- Frequent blocks / CAPTCHAs — the scraper falls back to a search link gracefully
- Rate limiting after repeated searches — wait a few minutes between runs
- Page structure changes — LinkedIn updates their HTML regularly

For more reliable LinkedIn coverage, consider:
- [linkedin-jobs-scraper](https://github.com/spinlud/py-linkedin-jobs-scraper) — headless Chrome based
- Rotating residential proxies

---

## Cost

- **GitHub** — free
- **Streamlit Cloud** — free tier (1 app, sleeps after inactivity)
- **Anthropic API** — ~$0.01–0.05 per search run (web search + scoring)
- **Document generation** — ~$0.005 per cover letter or CV summary

Typical session (1 search + 3 docs): ~$0.10–0.20
