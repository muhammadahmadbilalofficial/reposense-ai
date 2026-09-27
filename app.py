

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Make sure analyzer.py (sitting next to app.py) is importable
sys.path.insert(0, str(Path(__file__).parent))
import analyzer  # noqa: E402


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RepoSense AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Layout ── */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* ── KPI cards ── */
    .kpi-card {
        background: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        text-align: center;
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: .06em;
        color: #8b92a5;
        text-transform: uppercase;
        margin-bottom: .35rem;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #e2e8f0;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #636b82;
        margin-top: .25rem;
    }

    /* ── Section headers ── */
    .section-header {
        font-size: 1rem;
        font-weight: 700;
        color: #a5b4fc;
        letter-spacing: .04em;
        border-left: 3px solid #6366f1;
        padding-left: .6rem;
        margin: 1.4rem 0 .8rem 0;
    }

    /* ── Severity badges ── */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: .04em;
    }
    .badge-high   { background:#3d1515; color:#f87171; border:1px solid #7f1d1d; }
    .badge-medium { background:#3d2a00; color:#fbbf24; border:1px solid #78350f; }
    .badge-low    { background:#1a2e1a; color:#4ade80; border:1px solid #14532d; }
    .badge-info   { background:#1e2a3d; color:#60a5fa; border:1px solid #1e3a5f; }

    /* ── Onboarding checklist ── */
    .check-item {
        display: flex;
        align-items: center;
        gap: .5rem;
        padding: .45rem .6rem;
        border-radius: 8px;
        margin-bottom: .3rem;
        font-size: .87rem;
    }
    .check-ok  { background:#162016; color:#86efac; }
    .check-bad { background:#261616; color:#f87171; }

    /* ── Dataframe styling override ── */
    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _kpi(label: str, value: str, sub: str = "") -> None:
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section(title: str) -> None:
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def _badge(severity: str) -> str:
    return (
        f'<span class="badge badge-{severity}">{severity.upper()}</span>'
    )


def _fmt_number(n: int) -> str:
    return f"{n:,}"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 RepoSense AI")
    st.markdown(
        "<p style='color:#636b82;font-size:.82rem;margin-top:-.5rem;'>"
        "Instant repository intelligence</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    repo_path = st.text_input(
        "Repository path",
        placeholder="/path/to/your/project",
        help="Absolute or relative path to the repository root.",
    )

    scan_clicked = st.button("🚀  Scan Repository", use_container_width=True, type="primary")

    st.divider()
    st.markdown(
        "<p style='color:#4b5563;font-size:.75rem;text-align:center;'>"
        "RepoSense AI · v1.0</p>",
        unsafe_allow_html=True,
    )


# ── Session-state cache ───────────────────────────────────────────────────────
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None

if scan_clicked and repo_path:
    root = Path(repo_path.strip())
    with st.spinner("Scanning repository…"):
        try:
            files   = analyzer.scan_directory(root)
            lang_r  = analyzer.language_breakdown(files)
            onboard = analyzer.check_onboarding_files(root)
            audit   = analyzer.security_quality_scan(files)
            st.session_state.scan_result = {
                "root":    root,
                "files":   files,
                "lang":    lang_r,
                "onboard": onboard,
                "audit":   audit,
            }
        except NotADirectoryError:
            st.error(f"❌  Path not found or is not a directory: `{repo_path}`")
            st.session_state.scan_result = None
        except Exception as exc:  # pragma: no cover
            st.error(f"❌  Unexpected error: {exc}")
            st.session_state.scan_result = None

elif scan_clicked and not repo_path:
    st.warning("⚠️  Please enter a repository path first.")


# ── Landing state ─────────────────────────────────────────────────────────────
if st.session_state.scan_result is None:
    st.markdown(
        """
        <div style="text-align:center;padding:5rem 0 3rem;">
            <div style="font-size:3.5rem;">🔍</div>
            <h1 style="color:#e2e8f0;font-size:2rem;margin:.6rem 0 .4rem;">RepoSense AI</h1>
            <p style="color:#636b82;font-size:1rem;max-width:460px;margin:0 auto;">
                Enter a local repository path in the sidebar and click
                <strong style="color:#a5b4fc;">Scan Repository</strong>
                to get instant architecture, quality, and onboarding insights.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# ── Unpack results ────────────────────────────────────────────────────────────
result  = st.session_state.scan_result
root    = result["root"]
lang_r  = result["lang"]
onboard = result["onboard"]
audit   = result["audit"]

totals     = lang_r["totals"]
lang_df: pd.DataFrame = lang_r["summary"]
per_lang   = lang_r["per_language"]

findings_df: pd.DataFrame = audit["findings"]
audit_stats = audit["stats"]
audit_sum: pd.DataFrame   = audit["summary"]

primary_lang = (
    lang_df.iloc[0]["language"]
    if not lang_df.empty
    else "—"
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"<h2 style='color:#e2e8f0;margin-bottom:.1rem;'>📁 {root.name}</h2>"
    f"<p style='color:#636b82;font-size:.82rem;margin-top:0;'>{root}</p>",
    unsafe_allow_html=True,
)

# ── KPI cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    _kpi("Total Files", _fmt_number(totals["total_files"]))
with k2:
    _kpi("Lines of Code", _fmt_number(totals["total_lines"]))
with k3:
    _kpi("Primary Language", primary_lang)
with k4:
    score = onboard["score"]
    _kpi(
        "Onboarding Score",
        f"{score['pct']}%",
        f"{score['found']} / {score['total']} files present",
    )
with k5:
    high = audit_stats["high"]
    _kpi(
        "Security Issues",
        str(high),
        "high-severity findings",
    )

st.markdown("<br>", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_arch, tab_audit, tab_onboard = st.tabs(
    ["🗂️  Architecture & Languages",
     "🛡️  Code Quality & Security Audit",
     "🚀  Developer Onboarding Guide"]
)


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Architecture & Languages
# ════════════════════════════════════════════════════════════════════════════
with tab_arch:
    if lang_df.empty:
        st.info("No files found in the repository.")
    else:
        col_pie, col_bar = st.columns([1, 1], gap="large")

        # ── Pie chart: files by language ─────────────────────────────────────
        with col_pie:
            _section("File distribution by language")
            fig_pie = px.pie(
                lang_df,
                names="language",
                values="file_count",
                hole=0.42,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Files: %{value}<br>Share: %{percent}<extra></extra>",
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c9d1d9",
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=320,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # ── Bar chart: lines of code by language ─────────────────────────────
        with col_bar:
            _section("Lines of code by language")
            top_n = lang_df[lang_df["language"] != "Other"].head(10)
            fig_bar = px.bar(
                top_n.sort_values("total_lines"),
                x="total_lines",
                y="language",
                orientation="h",
                color="total_lines",
                color_continuous_scale="Blues",
                labels={"total_lines": "Lines", "language": ""},
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c9d1d9",
                coloraxis_showscale=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=320,
                xaxis=dict(gridcolor="#2d3250"),
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # ── Full breakdown table ──────────────────────────────────────────────
        _section("Detailed language table")
        display_df = lang_df.rename(columns={
            "language":    "Language",
            "file_count":  "Files",
            "total_lines": "Lines",
            "pct_files":   "% Files",
            "pct_lines":   "% Lines",
        })
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "% Files":  st.column_config.ProgressColumn("% Files",  min_value=0, max_value=100, format="%.1f%%"),
                "% Lines":  st.column_config.ProgressColumn("% Lines",  min_value=0, max_value=100, format="%.1f%%"),
                "Files":    st.column_config.NumberColumn("Files",  format="%d"),
                "Lines":    st.column_config.NumberColumn("Lines",  format="%d"),
            },
        )


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Code Quality & Security Audit
# ════════════════════════════════════════════════════════════════════════════
with tab_audit:
    # ── Stats strip ──────────────────────────────────────────────────────────
    a1, a2, a3, a4, a5 = st.columns(5)
    sev_map = {
        "Files Scanned":   (str(audit_stats["files_scanned"]),  "#60a5fa"),
        "Total Findings":  (str(audit_stats["total_findings"]), "#e2e8f0"),
        "High":            (str(audit_stats["high"]),            "#f87171"),
        "Medium":          (str(audit_stats["medium"]),          "#fbbf24"),
        "Low / Info":      (
            str(audit_stats["low"] + audit_stats["info"]),      "#4ade80"
        ),
    }
    for col, (lbl, (val, colour)) in zip([a1, a2, a3, a4, a5], sev_map.items()):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{lbl}</div>
                    <div class="kpi-value" style="color:{colour};font-size:1.7rem;">{val}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    if findings_df.empty:
        st.success("✅  No issues detected in scanned Python files.")
    else:
        col_sum, col_chart = st.columns([1, 1], gap="large")

        # ── Summary table ─────────────────────────────────────────────────────
        with col_sum:
            _section("Issues by check type")
            st.dataframe(
                audit_sum.rename(columns={
                    "label":    "Check",
                    "category": "Category",
                    "severity": "Severity",
                    "count":    "Count",
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Count": st.column_config.ProgressColumn(
                        "Count",
                        min_value=0,
                        max_value=int(audit_sum["count"].max()) if not audit_sum.empty else 1,
                        format="%d",
                    ),
                },
            )

        # ── Donut: findings by severity ───────────────────────────────────────
        with col_chart:
            _section("Finding severity breakdown")
            sev_data = pd.DataFrame(
                [
                    {"Severity": "High",   "Count": audit_stats["high"]},
                    {"Severity": "Medium", "Count": audit_stats["medium"]},
                    {"Severity": "Low",    "Count": audit_stats["low"]},
                    {"Severity": "Info",   "Count": audit_stats["info"]},
                ]
            ).query("Count > 0")

            if not sev_data.empty:
                fig_sev = px.pie(
                    sev_data,
                    names="Severity",
                    values="Count",
                    hole=0.5,
                    color="Severity",
                    color_discrete_map={
                        "High":   "#f87171",
                        "Medium": "#fbbf24",
                        "Low":    "#4ade80",
                        "Info":   "#60a5fa",
                    },
                )
                fig_sev.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>",
                )
                fig_sev.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#c9d1d9",
                    showlegend=False,
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=290,
                )
                st.plotly_chart(fig_sev, use_container_width=True)

        # ── Findings drill-down ───────────────────────────────────────────────
        _section("All findings")

        sev_filter = st.multiselect(
            "Filter by severity",
            options=["high", "medium", "low", "info"],
            default=["high", "medium"],
            key="sev_filter",
        )
        cat_filter = st.multiselect(
            "Filter by category",
            options=findings_df["category"].unique().tolist(),
            default=findings_df["category"].unique().tolist(),
            key="cat_filter",
        )

        filtered = findings_df[
            findings_df["severity"].isin(sev_filter)
            & findings_df["category"].isin(cat_filter)
        ].copy()

        if filtered.empty:
            st.info("No findings match the selected filters.")
        else:
            # Trim file path to last 3 parts for readability
            filtered["file"] = filtered["file"].apply(
                lambda p: "/".join(Path(p).parts[-3:])
            )
            filtered["severity"] = filtered["severity"].apply(
                lambda s: s.upper()
            )
            st.dataframe(
                filtered.rename(columns={
                    "file":     "File",
                    "line":     "Line",
                    "category": "Category",
                    "label":    "Issue",
                    "severity": "Severity",
                    "snippet":  "Code Snippet",
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Line": st.column_config.NumberColumn("Line", format="%d", width="small"),
                    "Severity": st.column_config.TextColumn("Severity", width="small"),
                },
            )
            st.caption(f"Showing {len(filtered):,} of {len(findings_df):,} findings")


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — Developer Onboarding Guide
# ════════════════════════════════════════════════════════════════════════════
with tab_onboard:
    col_check, col_tasks = st.columns([1, 1], gap="large")

    # ── Onboarding checklist ─────────────────────────────────────────────────
    with col_check:
        _section("Project health checklist")
        score = onboard["score"]

        # Score gauge
        gauge_fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=score["pct"],
                number={"suffix": "%", "font": {"color": "#e2e8f0", "size": 36}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#4b5563"},
                    "bar":  {"color": "#6366f1"},
                    "bgcolor": "#1e2130",
                    "bordercolor": "#2d3250",
                    "steps": [
                        {"range": [0,  40],  "color": "#2d1515"},
                        {"range": [40, 70],  "color": "#2d2a15"},
                        {"range": [70, 100], "color": "#162016"},
                    ],
                    "threshold": {
                        "line":  {"color": "#a5b4fc", "width": 3},
                        "thickness": 0.8,
                        "value": score["pct"],
                    },
                },
            )
        )
        gauge_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9",
            height=220,
            margin=dict(t=20, b=0, l=30, r=30),
        )
        st.plotly_chart(gauge_fig, use_container_width=True)
        st.caption(
            f"**{score['found']} of {score['total']}** onboarding files detected"
        )

        # File-by-file checklist
        for label, info in onboard["details"].items():
            if info["found"]:
                path_hint = f" — <code style='font-size:.75rem;'>{info['path']}</code>"
                st.markdown(
                    f'<div class="check-item check-ok">✅ <b>{label}</b>{path_hint}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="check-item check-bad">❌ <b>{label}</b>'
                    f' <span style="color:#6b7280;font-size:.78rem;">not found</span></div>',
                    unsafe_allow_html=True,
                )

    # ── Generated starter tasks ──────────────────────────────────────────────
    with col_tasks:
        _section("Generated starter tasks")

        tasks: list[tuple[str, str, str]] = []  # (priority, emoji, description)

        # Missing onboarding files → high-priority tasks
        for missing_lbl in onboard["missing"]:
            tasks.append((
                "High",
                "📄",
                f"Create a **{missing_lbl}** file to improve project discoverability.",
            ))

        # Security findings → critical tasks
        if audit_stats["high"] > 0:
            tasks.append((
                "Critical",
                "🔐",
                f"Resolve **{audit_stats['high']} high-severity security finding(s)** "
                "(hardcoded secrets, eval/exec, shell injection).",
            ))
        if audit_stats["medium"] > 0:
            tasks.append((
                "High",
                "⚠️",
                f"Address **{audit_stats['medium']} medium-severity issue(s)** "
                "(bare excepts, insecure hashes, mutable defaults).",
            ))

        # Quality hints from TODO/FIXME
        todo_count = len(findings_df[findings_df["label"].str.contains("TODO|FIXME", na=False)])
        if todo_count:
            tasks.append((
                "Medium",
                "📝",
                f"Resolve **{todo_count} TODO / FIXME** comment(s) left in the codebase.",
            ))

        # print() statements
        print_count = len(findings_df[findings_df["label"].str.contains("print", case=False, na=False)])
        if print_count:
            tasks.append((
                "Low",
                "🖨️",
                f"Remove or replace **{print_count} print() statement(s)** with proper logging.",
            ))

        # Large codebase hint
        if totals["total_lines"] > 10_000:
            tasks.append((
                "Medium",
                "📐",
                "Large codebase detected — consider adding **architecture documentation** (e.g. ARCHITECTURE.md).",
            ))

        # Generic good-practice tasks always shown
        tasks += [
            ("Low",  "🧪", "Set up a **test suite** (pytest) if one does not already exist."),
            ("Low",  "🔄", "Add a **CI/CD pipeline** to automate linting, testing, and deployment."),
            ("Low",  "🐳", "Containerise the application with **Docker** for consistent environments."),
        ]

        priority_colour = {
            "Critical": "#f87171",
            "High":     "#fbbf24",
            "Medium":   "#60a5fa",
            "Low":      "#4ade80",
        }
        priority_bg = {
            "Critical": "#2d1515",
            "High":     "#2d2010",
            "Medium":   "#101e2d",
            "Low":      "#0d1f0d",
        }

        for priority, emoji, desc in tasks:
            colour = priority_colour.get(priority, "#9ca3af")
            bg     = priority_bg.get(priority, "#1e2130")
            st.markdown(
                f"""
                <div style="
                    background:{bg};
                    border:1px solid {colour}33;
                    border-left:4px solid {colour};
                    border-radius:8px;
                    padding:.65rem .9rem;
                    margin-bottom:.45rem;
                    font-size:.86rem;
                    color:#e2e8f0;
                    display:flex;
                    gap:.55rem;
                    align-items:flex-start;
                ">
                    <span style="font-size:1rem;">{emoji}</span>
                    <div>
                        <span style="
                            font-size:.68rem;font-weight:700;letter-spacing:.06em;
                            color:{colour};text-transform:uppercase;
                        ">{priority}</span><br>
                        {desc}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


