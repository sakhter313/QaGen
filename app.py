"""
app.py — GenAI QA Requirement Generator
========================================
Streamlit Cloud application using Groq's free API + open-source LLMs.

── Deploy to Streamlit Cloud (free) ────────────────────────────────────────
  1. Push this repo to GitHub (all files including utils/ and .streamlit/)
  2. Go to https://share.streamlit.io → New App
  3. Repository: your repo  |  Branch: main  |  Main file: app.py
  4. Click "Advanced settings" → Secrets → paste:
         GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxx"
  5. Click Deploy

── Run locally ─────────────────────────────────────────────────────────────
  pip install -r requirements.txt
  streamlit run app.py
"""

import time
import streamlit as st

from utils.scraper        import scrape_single_page, scrape_website
from utils.llm            import generate_qa_requirements, AVAILABLE_MODELS
from utils.prompt_builder import build_prompt
from utils.exporter       import export_markdown, export_json

# ── Must be the very first Streamlit call ────────────────────────────────────
st.set_page_config(
    page_title="GenAI QA Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (injected once at startup) ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;700;800&display=swap');

:root {
  --bg:     #0b0f1a;
  --surf:   #111827;
  --border: #1e2d42;
  --green:  #00e5a0;
  --blue:   #38bdf8;
  --amber:  #fbbf24;
  --text:   #e2e8f0;
  --muted:  #6b7280;
  --mono:   'JetBrains Mono', monospace;
  --sans:   'Syne', sans-serif;
  --r:      10px;
}

html, body, [class*="css"] { font-family: var(--sans); background: var(--bg); color: var(--text); }
[data-testid="stSidebar"]  { background: var(--surf) !important; border-right: 1px solid var(--border); }
h1,h2,h3,h4                { font-family: var(--sans); font-weight: 800; }

/* Buttons */
[data-testid="stButton"] > button {
  background: linear-gradient(135deg, var(--green), var(--blue)) !important;
  color: #050a12 !important; font-family: var(--sans) !important; font-weight: 700 !important;
  border: none !important; border-radius: var(--r) !important;
  padding: .55rem 1.4rem !important; letter-spacing: .02em !important;
  transition: transform .15s, box-shadow .15s !important;
}
[data-testid="stButton"] > button:hover {
  transform: translateY(-2px) !important; box-shadow: 0 6px 20px rgba(0,229,160,.25) !important;
}

/* Code */
code, pre { font-family: var(--mono) !important; font-size: 12.5px !important;
  background: #080d14 !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }

/* Card with left accent bar */
.card {
  background: var(--surf); border: 1px solid var(--border); border-radius: var(--r);
  padding: 1.1rem 1.3rem; margin-bottom: .8rem; position: relative;
}
.card::before {
  content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
  background: linear-gradient(180deg, var(--green), var(--blue)); border-radius: 4px 0 0 4px;
}

/* Badges */
.badge { display:inline-block; padding:2px 9px; border-radius:20px; font-size:10.5px;
  font-weight:700; font-family:var(--mono); letter-spacing:.05em; text-transform:uppercase; }
.bg { background:rgba(0,229,160,.12);  color:var(--green); border:1px solid rgba(0,229,160,.3); }
.bb { background:rgba(56,189,248,.12); color:var(--blue);  border:1px solid rgba(56,189,248,.3); }
.ba { background:rgba(251,191,36,.12); color:var(--amber); border:1px solid rgba(251,191,36,.3); }

/* Metric cards */
.mrow { display:flex; gap:.8rem; flex-wrap:wrap; margin-bottom:1.3rem; }
.mc   { background:var(--surf); border:1px solid var(--border); border-radius:var(--r);
  padding:.85rem 1rem; flex:1; min-width:100px; text-align:center; }
.mv   { font-size:1.85rem; font-weight:800;
  background:linear-gradient(135deg,var(--green),var(--blue));
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; line-height:1.1; }
.ml   { font-size:9.5px; color:var(--muted); text-transform:uppercase;
  letter-spacing:.08em; font-family:var(--mono); margin-top:3px; }

/* Divider */
.hr { border:none; border-top:1px solid var(--border); margin:1.3rem 0; }

/* Logo */
.logo { font-size:1.4rem; font-weight:800;
  background:linear-gradient(135deg,var(--green),var(--blue));
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.logo-sub { font-size:9.5px; color:var(--muted); font-family:var(--mono); letter-spacing:.07em; }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# show_output() — defined first so all tabs can call it
# ============================================================================
def show_output(content: str, urls: list, model: str, key: str) -> None:
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown("### 📄 Generated QA Documentation")

    if model:
        lbl = AVAILABLE_MODELS.get(model, {}).get("label", model)
        st.markdown(
            f'<span class="badge bg">✓ Generated</span> '
            f'<span class="badge bb">🤖 {lbl}</span> '
            f'<span class="badge ba">📄 {len(urls)} page(s)</span>',
            unsafe_allow_html=True,
        )
        st.write("")

    with st.expander("📋 Rendered View", expanded=True):
        st.markdown(content)

    with st.expander("🔤 Raw Markdown"):
        st.code(content, language="markdown")

    st.markdown("#### 💾 Download")
    c1, c2, c3, _ = st.columns([1, 1, 1, 2])
    with c1:
        st.download_button("⬇ .md",   export_markdown(content).encode(), "qa_requirements.md",   "text/markdown",    key=f"{key}_md")
    with c2:
        st.download_button("⬇ .json", export_json(content, urls).encode(), "qa_requirements.json","application/json", key=f"{key}_json")
    with c3:
        st.download_button("⬇ .txt",  content.encode(),                    "qa_requirements.txt",  "text/plain",      key=f"{key}_txt")


# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:.3rem;">'
        '<span style="font-size:2rem">🧪</span>'
        '<div><div class="logo">QA GenAI</div>'
        '<div class="logo-sub">REQUIREMENT GENERATOR</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # ── API key (reads from st.secrets on Streamlit Cloud, editable locally)
    st.markdown("### 🔑 Groq API Key")
    _default = ""
    try:
        # st.secrets works on Streamlit Cloud; raises FileNotFoundError locally
        _default = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass

    api_key = st.text_input(
        "key",
        value=_default,
        type="password",
        placeholder="gsk_...",
        label_visibility="collapsed",
        help="Free at console.groq.com — no credit card needed.",
    )

    if not api_key:
        st.markdown(
            '<div class="card" style="font-size:12px;color:#6b7280;'
            'font-family:\'JetBrains Mono\',monospace;line-height:2;">'
            '🆓 <strong style="color:#00e5a0;">Get free key</strong><br>'
            '→ console.groq.com<br>→ Sign up (instant)<br>'
            '→ API Keys → Create<br>→ Paste above ↑</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # ── Model picker
    st.markdown("### 🤖 Model")
    model_key = st.selectbox(
        "model",
        list(AVAILABLE_MODELS.keys()),
        format_func=lambda k: AVAILABLE_MODELS[k]["label"],
        label_visibility="collapsed",
    )
    m = AVAILABLE_MODELS[model_key]
    st.markdown(
        f'<div class="card" style="font-size:11px;color:#6b7280;'
        f'font-family:\'JetBrains Mono\',monospace;line-height:1.9;">'
        f'<span class="badge bg">{m["size"]}</span> '
        f'<span class="badge bb">{m["type"]}</span><br><br>'
        f'⚡ {m["speed"]} &nbsp;·&nbsp; 🧠 {m["context"]}<br>'
        f'📝 {m["best_for"]}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

    # ── Output options
    st.markdown("### 🧩 Sections")
    sections = st.multiselect(
        "s", label_visibility="collapsed",
        options=["Functional Requirements","User Stories",
                 "Acceptance Criteria","Edge Cases","Test Cases"],
        default=["Functional Requirements","User Stories",
                 "Acceptance Criteria","Edge Cases"],
    )
    n_scenarios = st.slider("Scenarios per page", 2, 8, 4)
    strict      = st.toggle("Strict COSTAR mode", value=True)

    st.markdown("<div class='hr'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:11px;color:#6b7280;'
        'font-family:\'JetBrains Mono\',monospace;line-height:2;">'
        '🐍 Python · 🎈 Streamlit<br>'
        '🤖 Groq SDK · 🧠 LLaMA 3<br>'
        '🌐 BeautifulSoup4<br>'
        '📦 100% Open Source</div>',
        unsafe_allow_html=True,
    )


# ============================================================================
# PAGE HEADER
# ============================================================================
st.markdown(
    '<h1 style="font-size:2.2rem;font-weight:800;margin-bottom:.1rem;">'
    'GenAI QA Requirement Generator</h1>'
    '<p style="color:#6b7280;font-family:\'JetBrains Mono\',monospace;font-size:12px;margin-top:0;">'
    'Scrape any website → structured QA docs in seconds &nbsp;|&nbsp;'
    '<span class="badge bg">FREE</span> '
    '<span class="badge bb">OPEN SOURCE</span> '
    '<span class="badge ba">NO COST</span></p>',
    unsafe_allow_html=True,
)
st.markdown("<div class='hr'></div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🌐  URL Scraper", "📝  Paste Content", "📖  How It Works"])


# ============================================================================
# TAB 1 — URL SCRAPER
# ============================================================================
with tab1:

    col_url, col_btns = st.columns([3, 1])

    with col_url:
        urls_val = st.session_state.get("demo_urls", "")
        urls_input = st.text_area(
            "🔗 URLs — one per line",
            value=urls_val,
            placeholder=(
                "https://your-app.com/\n"
                "https://your-app.com/login\n"
                "https://your-app.com/register\n"
                "https://your-app.com/cart"
            ),
            height=130,
        )

    with col_btns:
        st.markdown("**Demo:**")
        if st.button("📋 Load demo", key="load_demo"):
            st.session_state["demo_urls"] = (
                "https://sauce-demo.myshopify.com/\n"
                "https://sauce-demo.myshopify.com/account/login\n"
                "https://sauce-demo.myshopify.com/account/register\n"
                "https://sauce-demo.myshopify.com/cart"
            )
            st.rerun()
        if st.button("🧹 Clear", key="clear_all"):
            for k in ["demo_urls","sc_out","sc_urls","sc_model"]:
                st.session_state.pop(k, None)
            st.rerun()

    # Inline warnings
    if not api_key:
        st.warning("⚠️ Add your Groq API key in the sidebar  (free at console.groq.com).")
    if not sections:
        st.warning("⚠️ Select at least one output section in the sidebar.")

    can_run = bool(api_key and urls_input.strip() and sections)

    b1, b2, _ = st.columns([1, 1, 4])
    with b1:
        do_scrape = st.button("🔍 Scrape & Preview", disabled=not urls_input.strip(), key="btn_scrape")
    with b2:
        do_gen    = st.button("⚡ Generate QA Docs", disabled=not can_run, key="btn_gen", type="primary")

    # ── Scrape preview ────────────────────────────────────────────────────────
    if do_scrape and urls_input.strip():
        url_list = [u.strip() for u in urls_input.strip().splitlines() if u.strip()]
        pages, bar = [], st.progress(0, text="Starting…")
        for i, u in enumerate(url_list):
            pages.append(scrape_single_page(u))
            bar.progress((i + 1) / len(url_list), text=f"Scraped: {u[:60]}")
            time.sleep(0.1)
        bar.empty()

        ok  = [p for p in pages if not p.get("error")]
        err = [p for p in pages if p.get("error")]
        for p in err:
            st.error(f"⚠️ {p['url']}: {p['error']}")
        if ok:
            st.success(f"✅ {len(ok)} page(s) scraped.")
            nh = sum(len(p.get("headings",[])) for p in ok)
            nb = sum(len(p.get("buttons", [])) for p in ok)
            ni = sum(len(p.get("inputs",  [])) for p in ok)
            st.markdown(
                f'<div class="mrow">'
                f'<div class="mc"><div class="mv">{len(ok)}</div><div class="ml">Pages</div></div>'
                f'<div class="mc"><div class="mv">{nh}</div><div class="ml">Headings</div></div>'
                f'<div class="mc"><div class="mv">{nb}</div><div class="ml">Buttons</div></div>'
                f'<div class="mc"><div class="mv">{ni}</div><div class="ml">Inputs</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            for p in pages:
                icon = "⚠️" if p.get("error") else "📄"
                with st.expander(f"{icon} {p['url']}", expanded=False):
                    if p.get("error"):
                        st.error(p["error"])
                    else:
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.markdown("**Headings**")
                            st.write(p.get("headings") or ["—"])
                        with c2:
                            st.markdown("**Buttons / CTAs**")
                            st.write(p.get("buttons",[])[:15] or ["—"])
                        with c3:
                            st.markdown("**Form Inputs**")
                            st.write(p.get("inputs") or ["—"])

    # ── Generate ──────────────────────────────────────────────────────────────
    if do_gen and can_run:
        url_list = [u.strip() for u in urls_input.strip().splitlines() if u.strip()]

        with st.spinner("🌐 Scraping pages…"):
            pages = [scrape_single_page(u) for u in url_list]

        content_txt = scrape_website(pages)
        prompt      = build_prompt(content_txt, sections, n_scenarios, strict)

        with st.spinner(f"🤖 Generating with {AVAILABLE_MODELS[model_key]['label']}…"):
            result = generate_qa_requirements(prompt, api_key, model_key)

        if result["success"]:
            st.session_state.update({
                "sc_out":   result["content"],
                "sc_urls":  url_list,
                "sc_model": model_key,
            })
            st.success(f"✅ Done — {result['tokens']:,} tokens used.")
            show_output(result["content"], url_list, model_key, key="sc")
        else:
            st.error(f"❌ {result['error']}")
            st.info("💡 Check your API key · wait 60 s if rate-limited · try LLaMA 3.1 8B.")

    elif "sc_out" in st.session_state and not do_gen:
        show_output(
            st.session_state["sc_out"],
            st.session_state.get("sc_urls", []),
            st.session_state.get("sc_model", ""),
            key="sc_c",
        )


# ============================================================================
# TAB 2 — PASTE CONTENT
# ============================================================================
with tab2:
    st.markdown(
        "Paste Figma specs, design notes, HTML snippets, or plain text — "
        "generate QA docs **without scraping**."
    )

    pasted = st.text_area(
        "📋 Paste UI content",
        height=220,
        placeholder=(
            "Page: Login\n"
            "Elements: Email input, Password input, Login button, Forgot password link\n\n"
            "Page: Dashboard\n"
            "Elements: Welcome banner, Logout button, Search bar, Activity table"
        ),
        key="paste_area",
    )

    if not api_key:
        st.warning("⚠️ Add your Groq API key in the sidebar.")

    paste_ok = bool(api_key and pasted.strip() and sections)

    if st.button("⚡ Generate QA Docs", disabled=not paste_ok, key="btn_paste", type="primary"):
        prompt = build_prompt(pasted, sections, n_scenarios, strict)
        with st.spinner(f"🤖 Generating with {AVAILABLE_MODELS[model_key]['label']}…"):
            result = generate_qa_requirements(prompt, api_key, model_key)
        if result["success"]:
            st.session_state["pt_out"] = result["content"]
            st.success(f"✅ Done — {result['tokens']:,} tokens used.")
            show_output(result["content"], ["Pasted Content"], model_key, key="pt")
        else:
            st.error(f"❌ {result['error']}")

    elif "pt_out" in st.session_state:
        show_output(st.session_state["pt_out"], ["Pasted Content"], "", key="pt_c")


# ============================================================================
# TAB 3 — HOW IT WORKS
# ============================================================================
with tab3:
    l, r = st.columns(2)

    with l:
        st.markdown("""
### 🏗️ Architecture
```
URLs or pasted text
       │
       ▼
 scraper.py        BeautifulSoup4
 headings / buttons / inputs
       │
       ▼
 prompt_builder.py  COSTAR framework
 FR · US · AC · EC · TC
       │
       ▼
 llm.py             Groq API (free)
 LLaMA 3 / Mixtral / Gemma 2
       │
       ▼
 exporter.py
 .md  /  .json  /  .txt
       │
       ▼
 Streamlit Cloud UI
```

### ⚙️ Pipeline
1. **Scrape** — extract UI elements from each URL
2. **Prompt** — COSTAR wraps content with QA rules
3. **Generate** — Groq routes to open-source model
4. **Render** — structured markdown in the app
5. **Export** — download `.md`, `.json`, or `.txt`
""")

    with r:
        st.markdown("""
### 🤖 Free Models on Groq

| Model | Params | Context |
|-------|--------|---------|
| LLaMA 3.3 70B | 70B | 128K |
| LLaMA 3.1 8B | 8B | 128K |
| Mixtral 8x7B | 56B MoE | 32K |
| Gemma 2 9B | 9B | 8K |

All are **free** — no credit card.

### 🎯 COSTAR Framework
| | Applied As |
|-|-----------|
| **C**ontext | Senior QA Engineer role |
| **O**bjective | QA docs only |
| **S**tyle | Given / When / Then |
| **T**one | Technical, precise |
| **A**udience | QA teams & devs |
| **R**esponse | Strict markdown |

### 🚀 Deploy to Streamlit Cloud

```
1. Push repo to GitHub
2. share.streamlit.io → New App
3. Main file: app.py
4. Advanced settings → Secrets:
   GROQ_API_KEY = "gsk_..."
5. Deploy ✅
```

### 📦 requirements.txt
```
streamlit>=1.32.0
groq>=0.9.0
beautifulsoup4>=4.12.0
requests>=2.28.0
```
""")
