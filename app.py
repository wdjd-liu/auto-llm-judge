"""Auto LLM Judge — Streamlit web app."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Auto LLM Judge",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── base ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #F7F8FC;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
[data-testid="stSidebar"] { display: none; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }

/* ── hide default streamlit header padding ── */
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1100px;
}

/* ── hero banner ── */
.hero {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
    border-radius: 16px;
    padding: 40px 48px;
    color: white;
    margin-bottom: 32px;
}
.hero h1 { font-size: 2.4rem; font-weight: 700; margin: 0 0 8px 0; color: white; }
.hero p  { font-size: 1.05rem; margin: 0; opacity: 0.88; }

/* ── section card ── */
.card {
    background: #ffffff;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.card h3 { margin-top: 0; font-size: 1.05rem; font-weight: 600; color: #111827; }

/* ── pipeline step cards ── */
.pipe-step {
    background: #F0F4FF;
    border: 1px solid #C7D2FE;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    height: 100%;
}
.pipe-step.active {
    background: #EEF2FF;
    border: 2px solid #4F46E5;
}
.pipe-num {
    display: inline-block;
    background: #4F46E5;
    color: white;
    border-radius: 50%;
    width: 28px; height: 28px;
    line-height: 28px;
    font-size: 0.8rem;
    font-weight: 700;
    margin-bottom: 8px;
}
.pipe-step.active .pipe-num { background: #4F46E5; }
.pipe-title { font-weight: 600; font-size: 0.9rem; color: #1E1B4B; margin: 4px 0; }
.pipe-desc  { font-size: 0.8rem; color: #4B5563; line-height: 1.4; }

/* ── dimension cards ── */
.dim-card {
    background: #ffffff;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
    border-left: 4px solid #4F46E5;
}
.dim-card.sub { border-left-color: #9CA3AF; }
.dim-name  { font-weight: 700; font-size: 0.95rem; color: #111827; margin: 0 0 4px 0; }
.dim-tag   { font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
             letter-spacing: 0.05em; color: #6366F1; margin-bottom: 8px; display: block; }
.dim-tag.sub { color: #9CA3AF; }
.dim-desc  { font-size: 0.85rem; color: #4B5563; margin: 0; line-height: 1.55; }

/* ── formula box ── */
.formula {
    background: #F8F7FF;
    border: 1px solid #C7D2FE;
    border-radius: 10px;
    padding: 20px 24px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.88rem;
    color: #1E1B4B;
    line-height: 2;
}

/* ── model chips ── */
.model-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #EEF2FF;
    border: 1px solid #C7D2FE;
    border-radius: 999px;
    padding: 8px 18px;
    font-size: 0.88rem;
    font-weight: 600;
    color: #3730A3;
    margin-right: 10px;
    margin-bottom: 8px;
}

/* ── section heading ── */
.section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #111827;
    margin: 28px 0 14px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #E5E7EB;
    margin-left: 8px;
}

/* ── verdict & score badges ── */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    margin-right: 5px;
}
.badge-pass { background: #D1FAE5; color: #065F46; }
.badge-fail { background: #FEE2E2; color: #991B1B; }
.badge-err  { background: #FEF3C7; color: #92400E; }
.badge-1    { background: #DBEAFE; color: #1E40AF; }
.badge-0    { background: #F3F4F6; color: #374151; }

/* ── reasoning blocks ── */
.axis-block { margin-bottom: 18px; }
.axis-label {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #6366F1;
    margin-bottom: 4px;
}
.axis-label.sub { color: #9CA3AF; }
.axis-text  { font-size: 0.85rem; color: #374151; line-height: 1.6; }

/* ── step indicator (evaluate tab) ── */
.step-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6366F1;
    margin-bottom: 6px;
}

/* ── info note ── */
.note {
    background: #F0F4FF;
    border-left: 3px solid #6366F1;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: #374151;
    margin: 14px 0;
}

/* ── Streamlit overrides ── */
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 16px 20px;
}
div[data-testid="stMetricValue"] { color: #111827 !important; font-weight: 700; }
div[data-testid="stMetricLabel"] { color: #6B7280 !important; font-size: 0.8rem; }
div[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 2px solid #E5E7EB;
}
div[data-testid="stTabs"] [data-baseweb="tab"] {
    font-weight: 600;
    color: #6B7280;
    padding: 10px 20px;
    border-radius: 8px 8px 0 0;
}
div[data-testid="stTabs"] [aria-selected="true"] {
    color: #4F46E5 !important;
    border-bottom: 2px solid #4F46E5;
}
div[data-testid="stFileUploader"] {
    border: 2px dashed #C7D2FE;
    border-radius: 10px;
    padding: 12px;
    background: #F5F7FF;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4F46E5, #7C3AED);
    border: none;
    border-radius: 8px;
    padding: 10px 28px;
    font-weight: 600;
    font-size: 1rem;
    color: white;
    transition: opacity 0.2s;
}
.stButton > button[kind="primary"]:hover { opacity: 0.9; }
.stButton > button[kind="primary"]:disabled { opacity: 0.4; }
.stDownloadButton > button {
    background: white;
    border: 1.5px solid #4F46E5;
    color: #4F46E5;
    border-radius: 8px;
    font-weight: 600;
}
.stExpander { border: 1px solid #E5E7EB !important; border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────

def verdict_badge(v: str) -> str:
    cls = "badge-pass" if v == "PASS" else ("badge-fail" if v == "FAIL" else "badge-err")
    return f'<span class="badge {cls}">{v}</span>'


def score_badge(val: int) -> str:
    cls = "badge-1" if val == 1 else ("badge-0" if val == 0 else "badge-err")
    label = "✓ Pass" if val == 1 else ("✗ Fail" if val == 0 else "ERR")
    return f'<span class="badge {cls}">{label}</span>'


def results_to_csv_bytes(df: pd.DataFrame, outputs) -> bytes:
    from aiTSR_judge.schemas import JudgeOutput
    out = df.copy()
    for col in JudgeOutput.OUTPUT_COLUMNS:
        out[col] = [getattr(o, col, None) for o in outputs]
    if all(o.error is None for o in outputs):
        out.drop(columns=["error"], inplace=True, errors="ignore")
    return out.to_csv(index=False).encode()


def section(icon: str, title: str):
    st.markdown(f'<div class="section-title">{icon}&nbsp;{title}</div>', unsafe_allow_html=True)


# ── tabs ──────────────────────────────────────────────────────────────────────
tab_about, tab_eval, tab_results = st.tabs(["  ⚖️  About  ", "  ▶  Evaluate  ", "  📊  Results  "])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — About
# ═══════════════════════════════════════════════════════════════════════════════
with tab_about:

    st.markdown("""
    <div class="hero">
        <h1>⚖️ Auto LLM Judge</h1>
        <p>An automated rubric-based framework for evaluating AI assistant responses —
        powered by Claude Opus 4 with extended thinking.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── what it does ──────────────────────────────────────────────────────────
    section("📌", "What it does")
    st.markdown("""
    <div class="card">
        <p style="color:#374151; font-size:0.95rem; line-height:1.7; margin:0">
        <b>Auto LLM Judge</b> takes three inputs — a user query, an AI response, and a ground truth
        reference answer — and uses a large language model as a judge to score the response on
        <b>4 binary quality dimensions</b>, then returns a <b>PASS / FAIL verdict</b>.<br><br>
        It is designed for teams that need scalable, consistent evaluation of AI-generated responses
        without manual annotation.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_i1, col_i2, col_i3 = st.columns(3)
    col_i1.markdown("""<div class="card" style="text-align:center">
        <div style="font-size:1.6rem">💬</div>
        <div style="font-weight:700;color:#111827;margin:6px 0 4px">utterance</div>
        <div style="font-size:0.83rem;color:#6B7280">The user's query or question</div>
    </div>""", unsafe_allow_html=True)
    col_i2.markdown("""<div class="card" style="text-align:center">
        <div style="font-size:1.6rem">🤖</div>
        <div style="font-weight:700;color:#111827;margin:6px 0 4px">response</div>
        <div style="font-size:0.83rem;color:#6B7280">The AI response being evaluated</div>
    </div>""", unsafe_allow_html=True)
    col_i3.markdown("""<div class="card" style="text-align:center">
        <div style="font-size:1.6rem">✅</div>
        <div style="font-weight:700;color:#111827;margin:6px 0 4px">ground_truth</div>
        <div style="font-size:0.83rem;color:#6B7280">The ideal reference answer</div>
    </div>""", unsafe_allow_html=True)

    # ── pipeline ──────────────────────────────────────────────────────────────
    section("🔄", "Evaluation pipeline")
    pc1, pc2, pc3, pc4 = st.columns(4)
    stages = [
        ("1", "Ground Truth Generation", "Frontier models independently produce reference answers", False),
        ("2", "Fact-Checking", "Same models verify factual accuracy of the production response", False),
        ("3", "Consensus Clustering", "Responses are grouped into a single ground truth signal", False),
        ("4", "Rubric Scoring", "The judge model scores on 4 axes and returns a verdict", True),
    ]
    for col, (num, title, desc, active) in zip([pc1, pc2, pc3, pc4], stages):
        cls = "pipe-step active" if active else "pipe-step"
        active_tag = "<div style=\"font-size:0.7rem;font-weight:700;color:#4F46E5;margin:2px 0\">← This tool</div>" if active else ""
        html = (
            "<div class=\"" + cls + "\">"
            "<div class=\"pipe-num\">" + num + "</div>"
            "<div class=\"pipe-title\">" + title + "</div>"
            + active_tag +
            "<div class=\"pipe-desc\">" + desc + "</div>"
            "</div>"
        )
        col.markdown(html, unsafe_allow_html=True)

    # ── 4 axes ────────────────────────────────────────────────────────────────
    section("📐", "The 4 scoring dimensions")
    st.markdown("<p style='color:#6B7280;font-size:0.88rem;margin-bottom:16px'>Each dimension is scored <b>0</b> (fail) or <b>1</b> (pass) by the judge model.</p>", unsafe_allow_html=True)

    da1, da2 = st.columns(2)
    dims_info = [
        ("Relevant", "Counts toward verdict", False,
         "Does the response address the user's actual question? A response that talks about an unrelated topic scores 0, even if it is technically accurate."),
        ("Correct & Complete", "Counts toward verdict", False,
         "Is the response factually correct and does it cover all necessary information? Partial answers or incorrect facts score 0."),
        ("Clear", "Counts toward verdict", False,
         "Is the response easy to understand and well-structured? Rambling, confusing, or overly verbose responses score 0."),
        ("Factual", "Sub-metric only — does NOT affect verdict", True,
         "Are all factual claims grounded and accurate? Reported for diagnostic analysis but excluded from the PASS / FAIL calculation."),
    ]
    for i, (name, tag, is_sub, desc) in enumerate(dims_info):
        col = da1 if i % 2 == 0 else da2
        sub_cls = "dim-card sub" if is_sub else "dim-card"
        tag_cls = "dim-tag sub" if is_sub else "dim-tag"
        col.markdown(f"""
        <div class="{sub_cls}">
            <p class="dim-name">{name}</p>
            <span class="{tag_cls}">{tag}</span>
            <p class="dim-desc">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

    # ── verdict logic ─────────────────────────────────────────────────────────
    section("🏁", "Verdict logic")
    vl1, vl2 = st.columns([1, 1])
    with vl1:
        st.markdown("""
        <div class="formula">
            rubric_total = relevant<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; + correct_and_complete<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; + clear<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<em>(max = 3)</em><br><br>
            verdict = <b>"PASS"</b> if rubric_total == 3<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>"FAIL"</b> otherwise
        </div>
        """, unsafe_allow_html=True)
    with vl2:
        st.markdown("""
        <div class="note">
            <b>Why all-or-nothing?</b><br>
            A response must be relevant, complete, <em>and</em> clear to be genuinely useful.
            A single failure on any dimension degrades the user experience enough to count as a FAIL.
        </div>
        <div class="note" style="margin-top:10px">
            <b>Why is Factual excluded from the verdict?</b><br>
            Factual accuracy is already captured inside Correct & Complete.
            The separate Factual axis surfaces grounding failures for diagnostic analysis only.
        </div>
        """, unsafe_allow_html=True)

    # ── judge model ───────────────────────────────────────────────────────────
    section("🧠", "Judge model")
    st.markdown("""
    <div class="card">
        <span class="model-chip">🤖 Claude Opus 4</span>
        <span class="model-chip">💭 Extended Thinking</span>
        <span class="model-chip">🎯 10 000 token budget</span>
        <p style="margin:16px 0 0; font-size:0.88rem; color:#4B5563; line-height:1.65">
        Claude Opus 4 with <b>extended thinking</b> performs internal chain-of-thought reasoning
        before producing its final JSON score output. This reduces scoring inconsistency on
        ambiguous cases and improves calibration — especially on the Correct & Complete dimension,
        which requires careful comparison against the ground truth reference.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── CSV format ────────────────────────────────────────────────────────────
    section("📄", "CSV input format")
    st.markdown("""
    <div class="card">
        <p style="font-size:0.88rem;color:#4B5563;margin-top:0">
        Upload a CSV with at least these three columns. Additional columns are passed through to the output unchanged.
        </p>
    """, unsafe_allow_html=True)
    csv_df = pd.DataFrame({
        "Column": ["`utterance`", "`response`", "`ground_truth`", "`prior_context`", "`grounding_context`", "`request_time`"],
        "Required": ["✅", "✅", "✅", "optional", "optional", "optional"],
        "Example": [
            "What's the weather like today?",
            "It's 72°F and sunny.",
            "The current temperature is 72°F with clear skies.",
            "User asked about rain yesterday.",
            "Weather API: temp=72, condition=sunny",
            "2024-06-15T10:30:00Z",
        ]
    })
    st.dataframe(csv_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Evaluate
# ═══════════════════════════════════════════════════════════════════════════════
with tab_eval:
    st.markdown("""
    <div class="hero" style="padding:28px 40px">
        <h1 style="font-size:1.8rem">▶ Run Evaluation</h1>
        <p>Upload your CSV and click Evaluate to score each response with the LLM judge.</p>
    </div>
    """, unsafe_allow_html=True)

    e1, e2 = st.columns([1, 1], gap="large")

    with e1:
        # ── API key ───────────────────────────────────────────────────────────
        st.markdown('<div class="step-label">Step 1 — Anthropic API key</div>', unsafe_allow_html=True)
        env_key = os.environ.get("ANTHROPIC_API_KEY", "")
        api_key = st.text_input(
            "API key",
            value=env_key,
            type="password",
            placeholder="sk-ant-api03-...",
            label_visibility="collapsed",
            help="Get yours at console.anthropic.com",
        )
        if api_key:
            st.markdown('<p style="color:#059669;font-size:0.83rem;margin-top:4px">✓ API key detected</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#D97706;font-size:0.83rem;margin-top:4px">⚠ Enter your Anthropic API key to proceed</p>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── model info ────────────────────────────────────────────────────────
        st.markdown('<div class="step-label">Step 3 — Judge model</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="card" style="padding:14px 18px;margin-bottom:0">
            <span class="model-chip" style="font-size:0.8rem">🤖 Claude Opus 4</span>
            <span class="model-chip" style="font-size:0.8rem">💭 Extended Thinking</span>
        </div>
        """, unsafe_allow_html=True)

    with e2:
        # ── CSV upload ────────────────────────────────────────────────────────
        st.markdown('<div class="step-label">Step 2 — Upload evaluation CSV</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "CSV with columns: utterance, response, ground_truth",
            type=["csv"],
            label_visibility="collapsed",
            help="Optional columns: prior_context, grounding_context, request_time",
        )

    df: pd.DataFrame | None = None
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded)
            required_cols = {"utterance", "response", "ground_truth"}
            missing = required_cols - set(df.columns)
            if missing:
                st.error(f"CSV is missing required columns: {', '.join(sorted(missing))}")
                df = None
            else:
                optional_found = [c for c in ["prior_context", "grounding_context", "request_time"] if c in df.columns]
                st.markdown(f"""
                <div style="background:#D1FAE5;border:1px solid #6EE7B7;border-radius:8px;
                            padding:10px 16px;font-size:0.85rem;color:#065F46;margin:12px 0">
                    ✓ Loaded <b>{len(df)} rows</b>
                    {"&nbsp; · &nbsp; Optional columns: " + ", ".join(f"<code>{c}</code>" for c in optional_found) if optional_found else ""}
                </div>
                """, unsafe_allow_html=True)
                st.markdown("**Preview — first 5 rows**")
                st.dataframe(df.head(5), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Could not parse CSV: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── evaluate button ───────────────────────────────────────────────────────
    st.markdown('<div class="step-label">Step 4 — Run</div>', unsafe_allow_html=True)
    ready = bool(api_key) and df is not None
    if not ready:
        st.markdown('<p style="font-size:0.83rem;color:#9CA3AF">Complete steps 1 and 2 to enable evaluation.</p>', unsafe_allow_html=True)

    if st.button("⚖️  Evaluate", disabled=not ready, type="primary"):
        from aiTSR_judge import AiTSRJudge, JudgeInput

        judge = AiTSRJudge(api_key=api_key, model="claude-opus-4-5", extended_thinking=True, thinking_budget=10_000)

        inputs = []
        parse_err = False
        for _, row in df.iterrows():
            try:
                inputs.append(JudgeInput.from_csv_row(row.to_dict()))
            except ValueError as e:
                st.error(str(e))
                parse_err = True
                break

        if not parse_err:
            results = []
            n = len(inputs)
            progress_bar = st.progress(0)
            status = st.empty()
            for i, inp in enumerate(inputs):
                status.markdown(f'<p style="color:#6366F1;font-size:0.88rem">Scoring row {i + 1} of {n}…</p>', unsafe_allow_html=True)
                results.append(judge.score(inp))
                progress_bar.progress((i + 1) / n)

            status.markdown('<p style="color:#059669;font-size:0.88rem;font-weight:600">✓ Evaluation complete</p>', unsafe_allow_html=True)
            st.session_state["results"] = results
            st.session_state["df"] = df.copy()

            verdicts = [o.verdict for o in results]
            n_pass = verdicts.count("PASS")
            n_fail = verdicts.count("FAIL")
            n_err  = verdicts.count("ERROR")
            total  = len(results)

            st.markdown("<br>", unsafe_allow_html=True)
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Total rows", total)
            mc2.metric("PASS", n_pass)
            mc3.metric("FAIL", n_fail)
            mc4.metric("PASS rate", f"{100 * n_pass / total:.1f}%" if total else "—")

            if n_err:
                st.warning(f"{n_err} row(s) encountered errors during scoring.")

            st.markdown("<br>", unsafe_allow_html=True)
            csv_bytes = results_to_csv_bytes(df, results)
            st.download_button(
                label="⬇  Download results CSV",
                data=csv_bytes,
                file_name="llm_judge_results.csv",
                mime="text/csv",
            )
            st.markdown("""
            <div class="note" style="margin-top:14px">
                Switch to the <b>📊 Results</b> tab for per-example breakdowns and reasoning.
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Results
# ═══════════════════════════════════════════════════════════════════════════════
with tab_results:
    results  = st.session_state.get("results")
    source_df = st.session_state.get("df")

    if not results:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#9CA3AF">
            <div style="font-size:3rem">📊</div>
            <div style="font-size:1.1rem;font-weight:600;margin:12px 0 6px;color:#6B7280">No results yet</div>
            <div style="font-size:0.88rem">Run an evaluation in the <b>Evaluate</b> tab first.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        outputs = results
        total   = len(outputs)
        verdicts = [o.verdict for o in outputs]
        n_pass  = verdicts.count("PASS")

        def avg(col: str) -> str:
            vals = [getattr(o, col) for o in outputs if getattr(o, col, -1) >= 0]
            return f"{sum(vals) / len(vals):.2f}" if vals else "—"

        st.markdown("""
        <div class="hero" style="padding:24px 36px">
            <h1 style="font-size:1.6rem">📊 Results</h1>
            <p>Per-example scores, reasoning, and verdict breakdown.</p>
        </div>
        """, unsafe_allow_html=True)

        # ── summary metrics ───────────────────────────────────────────────────
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        s1.metric("Total", total)
        s2.metric("PASS rate", f"{100 * n_pass / total:.1f}%")
        s3.metric("Relevant", avg("relevant"))
        s4.metric("C&C", avg("correct_and_complete"))
        s5.metric("Factual", avg("factual"))
        s6.metric("Clear", avg("clear"))

        st.markdown("<br>", unsafe_allow_html=True)

        # ── summary table ─────────────────────────────────────────────────────
        section("📋", "All rows")

        def truncate(s: str, n: int = 65) -> str:
            s = str(s)
            return s[:n] + "…" if len(s) > n else s

        table_rows = []
        for i, o in enumerate(outputs):
            utt = truncate(source_df.iloc[i]["utterance"]) if source_df is not None else f"Row {i+1}"
            table_rows.append({
                "#": i + 1,
                "Utterance": utt,
                "Verdict": o.verdict,
                "Relevant": o.relevant,
                "C&C": o.correct_and_complete,
                "Factual": o.factual,
                "Clear": o.clear,
                "Total /3": o.rubric_total,
            })

        table_df = pd.DataFrame(table_rows)

        def color_verdict(val):
            if val == "PASS": return "background-color:#D1FAE5;color:#065F46;font-weight:700"
            if val == "FAIL": return "background-color:#FEE2E2;color:#991B1B;font-weight:700"
            return ""

        def color_score(val):
            if val == 1: return "background-color:#DBEAFE;color:#1E40AF"
            if val == 0: return "background-color:#F3F4F6;color:#374151"
            return ""

        styled = (
            table_df.style
            .map(color_verdict, subset=["Verdict"])
            .map(color_score, subset=["Relevant", "C&C", "Factual", "Clear", "Total /3"])
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # ── expandable rows ───────────────────────────────────────────────────
        section("🔍", "Per-example detail")

        for i, o in enumerate(outputs):
            row_data = source_df.iloc[i] if source_df is not None else {}
            icon = "✅" if o.verdict == "PASS" else ("❌" if o.verdict == "FAIL" else "⚠️")
            label = f"{icon}  Row {i + 1} — {o.verdict}  ·  Score {o.rubric_total}/3"

            with st.expander(label):
                # ── input text ────────────────────────────────────────────────
                ec1, ec2 = st.columns([1, 1])
                with ec1:
                    st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px">User Query</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:12px;font-size:0.88rem;color:#111827;line-height:1.6;min-height:60px">{str(row_data.get("utterance", ""))}</div>', unsafe_allow_html=True)

                    st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.06em;margin:14px 0 4px">AI Response</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:12px;font-size:0.88rem;color:#111827;line-height:1.6;min-height:80px">{str(row_data.get("response", ""))}</div>', unsafe_allow_html=True)

                with ec2:
                    st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px">Ground Truth</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:12px;font-size:0.88rem;color:#111827;line-height:1.6;min-height:160px">{str(row_data.get("ground_truth", ""))}</div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── verdict row ───────────────────────────────────────────────
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">'
                    f'<span style="font-weight:700;color:#111827">Verdict</span>'
                    f'{verdict_badge(o.verdict)}'
                    f'<span style="color:#6B7280;font-size:0.85rem">Rubric score: <b>{o.rubric_total} / 3</b></span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # ── dimension scores ──────────────────────────────────────────
                dc1, dc2 = st.columns(2)
                dims = [
                    ("Relevant", o.relevant, o.relevant_reasoning, False),
                    ("Correct & Complete", o.correct_and_complete, o.correct_and_complete_reasoning, False),
                    ("Clear", o.clear, o.clear_reasoning, False),
                    ("Factual", o.factual, o.factual_reasoning, True),
                ]
                for j, (name, score, reasoning, is_sub) in enumerate(dims):
                    col = dc1 if j % 2 == 0 else dc2
                    tag = "Sub-metric — not in verdict" if is_sub else "Counts toward verdict"
                    label_cls = "axis-label sub" if is_sub else "axis-label"
                    col.markdown(
                        f'<div class="axis-block">'
                        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">'
                        f'<span style="font-weight:700;font-size:0.88rem;color:#111827">{name}</span>'
                        f'{score_badge(score)}'
                        f'</div>'
                        f'<div class="{label_cls}">{tag}</div>'
                        f'<div class="axis-text">{reasoning}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                # ── justification ─────────────────────────────────────────────
                if o.justification:
                    st.markdown('<div style="font-size:0.75rem;font-weight:700;color:#6366F1;text-transform:uppercase;letter-spacing:0.06em;margin:8px 0 6px">Overall Justification</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="note">{o.justification}</div>', unsafe_allow_html=True)
                if o.error:
                    st.error(f"Scoring error: {o.error}")
