# 🧪 GenAI QA Requirement Generator

> Scrape any website → AI-generated QA documentation in seconds.
> **100% free. 100% open source. Runs on Streamlit Cloud.**

---

## 🚀 Deploy to Streamlit Cloud in 5 Minutes

### Step 1 — Get a free Groq API key
1. Go to **https://console.groq.com**
2. Sign up (free — no credit card)
3. Click **API Keys → Create API Key**
4. Copy the key (starts with `gsk_`)

### Step 2 — Fork & deploy
1. Fork this repo to your GitHub account
2. Go to **https://share.streamlit.io** → **New App**
3. Select your forked repo, branch `main`, main file `app.py`
4. Click **Advanced settings** → **Secrets** → paste:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Click **Deploy** — done in ~60 seconds ✅

---

## 💻 Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/genai-qa-generator.git
cd genai-qa-generator
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 File Structure

```
.
├── app.py                       ← Streamlit app (entry point)
├── requirements.txt             ← pip dependencies
├── .gitignore
├── README.md
├── .streamlit/
│   └── config.toml              ← Dark theme config
└── utils/
    ├── __init__.py
    ├── scraper.py               ← BeautifulSoup4 scraper
    ├── llm.py                   ← Groq API client
    ├── prompt_builder.py        ← COSTAR prompt engine
    └── exporter.py              ← .md / .json / .txt export
```

---

## 🤖 Models (all free on Groq)

| Model | Params | Context | Use |
|-------|--------|---------|-----|
| LLaMA 3.3 70B | 70B | 128K | Best quality |
| LLaMA 3.1 8B | 8B | 128K | Fastest |
| Mixtral 8x7B | 56B MoE | 32K | Balanced |
| Gemma 2 9B | 9B | 8K | Lightweight |

---

## 📦 requirements.txt

```
streamlit>=1.32.0
groq>=0.9.0
beautifulsoup4>=4.12.0
requests>=2.28.0
```

---

## 📝 License

MIT
