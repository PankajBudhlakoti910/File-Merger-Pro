import subprocess
import sys

# Force install required packages — fixes Streamlit Cloud environment issues
subprocess.run([sys.executable, "-m", "pip", "install", "openpyxl==3.1.5", "xlrd==2.0.1", "et-xmlfile", "-q"], check=False)

import streamlit as st
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime
import io
import base64
import json
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="📊 File Merger Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
    /* ---- Global ---- */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* ---- Headers ---- */
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.25rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .sub-header {
        text-align: center;
        color: #6B7280;
        margin-bottom: 1.5rem;
        font-size: 1rem;
    }

    /* ---- Step cards ---- */
    .step-card {
        background: linear-gradient(135deg, #EFF6FF 0%, #F0FDF4 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1.25rem;
    }
    .step-card h2 { margin-top: 0; color: #1E40AF; font-size: 1.25rem; }
    .step-card p  { margin-bottom: 0; color: #4B5563; }

    /* ---- Metric cards ---- */
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 6px rgba(0,0,0,0.08);
        border-top: 3px solid #3B82F6;
    }
    .metric-card .value { font-size: 1.75rem; font-weight: 700; color: #1E3A8A; }
    .metric-card .label { font-size: 0.8rem; color: #6B7280; margin-top: 0.2rem; }

    /* ---- Mapping table ---- */
    .mapping-row {
        background: #F9FAFB;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin-bottom: 0.4rem;
        border-left: 3px solid #10B981;
    }
    .mapping-row.unmapped { border-left-color: #F59E0B; }

    /* ---- Download button ---- */
    .dl-btn {
        display: inline-block;
        background: linear-gradient(135deg, #10B981, #059669);
        color: white !important;
        padding: 0.65rem 1.5rem;
        border-radius: 8px;
        font-weight: 700;
        text-decoration: none !important;
        font-size: 0.95rem;
        transition: all .2s;
    }
    .dl-btn:hover { box-shadow: 0 4px 12px rgba(16,185,129,.4); transform: translateY(-1px); }

    /* ---- Step indicator ---- */
    .step-active   { background: linear-gradient(135deg,#3B82F6,#8B5CF6); color:white; }
    .step-done     { background: #10B981; color:white; }
    .step-inactive { background: #E5E7EB; color:#6B7280; }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] { background: #1E3A8A !important; }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] .stButton>button { background: rgba(255,255,255,0.15) !important; border: 1px solid rgba(255,255,255,0.3) !important; }

    /* ---- Feature page cards ---- */
    .feature-card {
        background: white;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        border-top: 4px solid #3B82F6;
        margin-bottom: 1rem;
    }
    .feature-card h4 { margin-top: 0; color: #1E40AF; }
    .feature-card p  { color: #4B5563; margin-bottom: 0; font-size: 0.9rem; }

    /* ---- Filter badges ---- */
    .filter-badge {
        display: inline-block;
        background: #DBEAFE;
        color: #1D4ED8;
        border-radius: 20px;
        padding: 0.2rem 0.7rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────
def init_state():
    defaults = {
        'step': 1,
        'uploaded_files': [],
        'file_dataframes': {},       # {filename: df}
        'all_columns': [],           # union of all columns
        'column_mapping': {},        # {target_col: {source_file: source_col}}
        'merged_data': None,
        'page': 'app',               # 'app' | 'features'
        'mapping_confirmed': False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
CHUNK_SIZE = 50_000  # rows per chunk for large file display


def read_file(uploaded_file):
    """Read an uploaded file into a DataFrame."""
    name = uploaded_file.name
    ext  = os.path.splitext(name)[1].lower()
    try:
        if ext == '.csv':
            return pd.read_csv(uploaded_file)
        elif ext in ('.xlsx', '.xls'):
            return pd.read_excel(uploaded_file)
        elif ext == '.json':
            return pd.read_json(uploaded_file)
        elif ext == '.txt':
            content = uploaded_file.getvalue().decode('utf-8')
            for sep in (',', '\t', '|', ';'):
                try:
                    df = pd.read_csv(io.StringIO(content), sep=sep)
                    if df.shape[1] > 1:
                        return df
                except Exception:
                    pass
            return pd.read_csv(io.StringIO(content), sep=None, engine='python')
        else:
            try:
                return pd.read_csv(uploaded_file)
            except Exception:
                return pd.read_excel(uploaded_file)
    except Exception as e:
        st.warning(f"⚠️ Could not read **{name}**: {e}")
        return None


def to_download_link(df, fmt, filename):
    """Return an HTML <a> download link."""
    if fmt == 'csv':
        data  = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        mime  = 'text/csv'
        ext   = 'csv'
    elif fmt == 'excel':
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            df.to_excel(w, index=False, sheet_name='MergedData')
        data = buf.getvalue()
        mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ext  = 'xlsx'
    else:  # json
        data = df.to_json(orient='records', indent=2, force_ascii=False).encode()
        mime = 'application/json'
        ext  = 'json'

    b64  = base64.b64encode(data).decode()
    full = f"{filename}.{ext}"
    return f'<a class="dl-btn" href="data:{mime};base64,{b64}" download="{full}">📥 Download {full}</a>', full


def chunked_display(df, key_prefix=""):
    """Display large DataFrames in chunks with pagination."""
    total = len(df)
    if total <= CHUNK_SIZE:
        st.dataframe(df, use_container_width=True)
        return

    n_pages = (total - 1) // CHUNK_SIZE + 1
    page    = st.number_input(
        f"Page (1 – {n_pages})", min_value=1, max_value=n_pages,
        value=1, step=1, key=f"{key_prefix}_page"
    )
    start = (page - 1) * CHUNK_SIZE
    end   = min(start + CHUNK_SIZE, total)
    st.caption(f"Showing rows {start+1:,} – {end:,} of {total:,}")
    st.dataframe(df.iloc[start:end], use_container_width=True)


def step_indicator():
    labels = ["📁 Upload", "🔗 Map Columns", "⚙️ Configure", "🔍 Analyse", "💾 Download"]
    cur    = st.session_state.step
    cols   = st.columns(len(labels))
    for i, (col, lbl) in enumerate(zip(cols, labels), 1):
        if i == cur:
            cls = "step-active"
        elif i < cur:
            cls = "step-done"
        else:
            cls = "step-inactive"
        col.markdown(
            f'<div style="padding:8px;border-radius:8px;text-align:center;font-weight:700;" class="{cls}">'
            f'{"✅ " if i < cur else ""}{lbl}</div>',
            unsafe_allow_html=True
        )


def back_button(target_step, label="← Back"):
    if st.button(label, key=f"back_{target_step}_{time.time_ns()}"):
        st.session_state.step = target_step
        st.rerun()


# ─────────────────────────────────────────
# STEP 1 – UPLOAD
# ─────────────────────────────────────────
def read_file_safe(uploaded_file):
    """Read uploaded file — uses same logic as original working code."""
    try:
        filename = uploaded_file.name
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext == '.csv':
            return filename, pd.read_csv(uploaded_file)
        elif file_ext in ['.xlsx', '.xls']:
            return filename, pd.read_excel(uploaded_file)
        elif file_ext == '.json':
            return filename, pd.read_json(uploaded_file)
        elif file_ext == '.txt':
            content = uploaded_file.getvalue().decode('utf-8')
            try:
                return filename, pd.read_csv(io.StringIO(content), sep=',')
            except:
                try:
                    return filename, pd.read_csv(io.StringIO(content), sep='\t')
                except:
                    return filename, pd.read_csv(io.StringIO(content), sep=None, engine='python')
        else:
            try:
                return filename, pd.read_csv(uploaded_file)
            except:
                try:
                    return filename, pd.read_excel(uploaded_file)
                except:
                    content = uploaded_file.getvalue().decode('utf-8')
                    return filename, pd.read_csv(io.StringIO(content), sep=None, engine='python')
    except Exception as e:
        st.warning(f"Could not read {uploaded_file.name}: {str(e)}")
        return uploaded_file.name, None


def render_upload():
    st.markdown("""
    <div class="step-card">
        <h2>📁 STEP 1: Upload Files</h2>
        <p>Upload 1–100 files. Supported formats: CSV, Excel, JSON, TXT</p>
    </div>""", unsafe_allow_html=True)

    files = st.file_uploader(
        "Choose files",
        type=['csv', 'xlsx', 'xls', 'txt', 'json'],
        accept_multiple_files=True,
        key="uploader"
    )

    if files:
        # Only re-read if the file list has changed
        current_names = [f.name for f in files]
        cached_names  = [f.name for f in st.session_state.get('uploaded_files', [])]

        if current_names != cached_names or not st.session_state.file_dataframes:
            dfs    = {}
            errors = []
            total  = len(files)

            progress_text = st.empty()
            progress_bar  = st.progress(0)

            for i, f in enumerate(files):
                progress_text.markdown(f"⏳ Reading **{i+1}/{total}** — `{f.name}`")
                progress_bar.progress((i + 1) / total)
                name, df = read_file_safe(f)
                if df is not None:
                    dfs[name] = df
                else:
                    errors.append(name)

            progress_bar.empty()
            progress_text.empty()

            st.session_state.uploaded_files  = files
            st.session_state.file_dataframes = dfs

            if errors:
                st.warning("⚠️ Could not read: " + ", ".join(errors))
        else:
            dfs = st.session_state.file_dataframes

        if dfs:
            st.success(f"✅ {len(dfs)} file(s) loaded!")

            with st.expander(f"📋 File Summary ({len(dfs)} files)", expanded=True):
                rows = []
                for name, df in dfs.items():
                    rows.append({
                        "File": name,
                        "Rows": f"{len(df):,}",
                        "Columns": len(df.columns),
                        "Column Names": ", ".join(df.columns.tolist()[:8]) + ("…" if len(df.columns) > 8 else "")
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            if st.button("Next: Map Columns →", type="primary", use_container_width=True):
                st.session_state.step = 2
                st.session_state.mapping_confirmed = False
                st.rerun()


# ─────────────────────────────────────────
# STEP 2 – COLUMN MAPPING
# ─────────────────────────────────────────
def normalize_col(col: str) -> str:
    """
    Normalize a column name for matching:
      1. Strip leading/trailing whitespace
      2. Lowercase
      3. Remove all special characters (keep only a-z, 0-9)
      4. Collapse multiple spaces / underscores into a single underscore
    Examples:
      "First Name"  → "first_name"
      "first_name"  → "first_name"
      "First-Name!" → "first_name"
      " FIRST  NAME " → "first_name"
      "Revenue ($)"  → "revenue"
    """
    import re
    s = col.strip().lower()
    # Replace any run of non-alphanumeric characters with a single underscore
    s = re.sub(r'[^a-z0-9]+', '_', s)
    # Strip leading/trailing underscores that result from above
    s = s.strip('_')
    return s


def build_auto_mapping(dfs):
    """
    Build automatic column mapping.
    Columns are matched after:
      - lowercasing
      - removing special characters (spaces, hyphens, brackets, etc.)
    So 'First Name', 'first_name', 'First-Name!' all map to the same target.
    The canonical name shown in the UI is taken from the first file that
    contains that column.
    """
    all_cols = {}
    for fname, df in dfs.items():
        for col in df.columns:
            norm = normalize_col(col)
            if norm not in all_cols:
                # Use the original column name from the first file as the canonical label
                all_cols[norm] = {'canonical': col, 'norm': norm, 'files': {}}
            all_cols[norm]['files'][fname] = col   # store original name per file

    return all_cols  # {norm_name: {canonical, norm, files:{fname:actual_col}}}


def render_column_mapping():
    st.markdown("""
    <div class="step-card">
        <h2>🔗 STEP 2: Column Mapping</h2>
        <p>Review automatic mapping. Manually adjust, skip, or remap columns as needed.</p>
    </div>""", unsafe_allow_html=True)

    dfs    = st.session_state.file_dataframes
    fnames = list(dfs.keys())

    if not dfs:
        st.error("No files loaded.")
        back_button(1)
        return

    auto         = build_auto_mapping(dfs)
    full_cols    = [n for n, v in auto.items() if len(v['files']) == len(fnames)]
    partial_cols = [n for n, v in auto.items() if 0 < len(v['files']) < len(fnames)]

    st.info(
        f"🗂️ **{len(fnames)} files** | "
        f"✅ **{len(full_cols)}** columns in ALL files (auto-mapped) | "
        f"⚠️ **{len(partial_cols)}** columns in SOME files (need decision)"
    )

    # ── TAB 1: Auto-mapped ──────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["✅ Auto-Mapped Columns", "⚠️ Partial / Unmapped Columns"])

    with tab1:
        if not full_cols:
            st.info("No columns are common across all files.")
        else:
            st.success(
                f"**{len(full_cols)} columns** automatically matched "
                f"(lowercase + special chars removed before comparison)."
            )
            st.caption("✎ = original name in that file differs from the canonical name.")
            rows = []
            for n in full_cols:
                v   = auto[n]
                row = {"Target Column": v['canonical'], "Normalised Key": v['norm']}
                for fn in fnames:
                    orig      = v['files'].get(fn, "—")
                    row[fn]   = orig if orig == v['canonical'] else f"{orig} ✎"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── TAB 2: Partial columns ──────────────────────────────────────────────
    with tab2:
        if not partial_cols:
            st.success("All columns are present in every file — no manual mapping needed!")
        else:
            st.warning(
                f"**{len(partial_cols)} columns** are missing from some files. "
                "Choose **Include** (fill blanks) or **Skip** for each."
            )

            # Show ALL partial columns in a compact table first
            summary_rows = []
            for n in partial_cols:
                v = auto[n]
                summary_rows.append({
                    "Column": v['canonical'],
                    "Present in": f"{len(v['files'])}/{len(fnames)} files",
                    "Missing from": ", ".join([fn for fn in fnames if fn not in v['files']])[:80]
                })
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            st.markdown("#### ⚙️ Set action for each partial column:")

            # Use columns layout — 3 per row — for compact display
            for i in range(0, len(partial_cols), 3):
                chunk = partial_cols[i:i+3]
                cols  = st.columns(len(chunk))
                for col_widget, n in zip(cols, chunk):
                    v     = auto[n]
                    canon = v['canonical']
                    with col_widget:
                        st.markdown(f"**`{canon}`**")
                        st.caption(f"In {len(v['files'])}/{len(fnames)} files")
                        st.radio(
                            "Action",
                            ["Include (fill blank)", "Skip"],
                            key=f"action_{n}",
                            horizontal=True,
                            label_visibility="collapsed"
                        )

            # Remap section — only for columns marked Include that have missing files
            st.markdown("#### 🔗 Optional: remap missing columns from another column")
            st.caption("For files missing a column, you can pull data from a differently-named column instead of leaving it blank.")
            for n in partial_cols:
                if st.session_state.get(f"action_{n}", "Include (fill blank)") == "Skip":
                    continue
                v       = auto[n]
                canon   = v['canonical']
                missing = [fn for fn in fnames if fn not in v['files']]
                if not missing:
                    continue
                with st.expander(f"Remap for **{canon}** ({len(missing)} missing files)"):
                    for fn in missing:
                        mapped_cols = {v2['canonical'] for v2 in auto.values() if fn in v2['files']}
                        other_cols  = [c for c in dfs[fn].columns if c not in mapped_cols]
                        if other_cols:
                            st.selectbox(
                                f"`{fn}` → map from:",
                                ["— leave blank —"] + other_cols,
                                key=f"remap_{n}_{fn}"
                            )
                        else:
                            st.caption(f"`{fn}` — no unmapped columns available, will fill blank.")

    # ── Build final mapping_config and save immediately ─────────────────────
    mapping_config = {}

    # All auto-mapped columns always included
    for n in full_cols:
        v = auto[n]
        mapping_config[v['canonical']] = {fn: v['files'][fn] for fn in fnames}

    # Partial columns based on user choices
    for n in partial_cols:
        v      = auto[n]
        canon  = v['canonical']
        action = st.session_state.get(f"action_{n}", "Include (fill blank)")
        if "Skip" in action:
            continue
        mapping_config[canon] = {}
        for fn in fnames:
            if fn in v['files']:
                mapping_config[canon][fn] = v['files'][fn]
            else:
                remap_key = f"remap_{n}_{fn}"
                choice    = st.session_state.get(remap_key, "— leave blank —")
                mapping_config[canon][fn] = choice if choice != "— leave blank —" else None

    # Always persist current mapping to session state (even before button click)
    st.session_state.column_mapping = mapping_config

    st.markdown("---")
    st.info(f"✅ **{len(mapping_config)} columns** will be in the merged output.")

    col1, col2 = st.columns(2)
    with col1:
        back_button(1, "← Back to Upload")
    with col2:
        if st.button("Next: Configure Merge →", type="primary", use_container_width=True):
            st.session_state.step = 3
            st.rerun()


# ─────────────────────────────────────────
# STEP 3 – CONFIGURE & MERGE
# ─────────────────────────────────────────
def apply_mapping_and_merge(dfs, mapping, add_source, handle_dupes):
    """Apply column mapping and concatenate all DataFrames."""
    target_cols = list(mapping.keys())
    frames = []

    for fname, df in dfs.items():
        row_df = pd.DataFrame(index=range(len(df)))
        for tcol in target_cols:
            scol = mapping[tcol].get(fname)
            if scol and scol in df.columns:
                row_df[tcol] = df[scol].values
            else:
                row_df[tcol] = np.nan
        if add_source:
            row_df['_source_file'] = fname
        frames.append(row_df)

    merged = pd.concat(frames, ignore_index=True)

    if handle_dupes == "Remove Exact Duplicates":
        merged = merged.drop_duplicates()
    elif handle_dupes == "Keep First":
        merged = merged.drop_duplicates(keep='first')
    elif handle_dupes == "Keep Last":
        merged = merged.drop_duplicates(keep='last')

    return merged


def render_configure():
    st.markdown("""
    <div class="step-card">
        <h2>⚙️ STEP 3: Configure Merge</h2>
        <p>Choose merge options then click Merge!</p>
    </div>""", unsafe_allow_html=True)

    dfs = st.session_state.file_dataframes
    if not dfs:
        st.error("No files loaded.")
        back_button(1)
        return

    st.info(f"📁 {len(dfs)} files | 🗂️ {len(st.session_state.column_mapping)} target columns mapped")

    col1, col2 = st.columns(2)
    with col1:
        add_source = st.checkbox("Add '_source_file' column", value=True)
    with col2:
        handle_dupes = st.selectbox(
            "Duplicate handling",
            ["Keep All", "Remove Exact Duplicates", "Keep First", "Keep Last"]
        )

    col_left, col_right = st.columns(2)
    with col_left:
        back_button(2, "← Back to Column Mapping")
    with col_right:
        if st.button("🚀 Merge Files!", type="primary", use_container_width=True):
            with st.spinner("Merging…"):
                mapping = st.session_state.column_mapping
                if not mapping:
                    st.error("No column mapping defined. Please go back and configure mapping.")
                    return
                merged = apply_mapping_and_merge(dfs, mapping, add_source, handle_dupes)
                st.session_state.merged_data = merged
                st.session_state.step = 4
                st.rerun()


# ─────────────────────────────────────────
# STEP 4 – ANALYSE
# ─────────────────────────────────────────
def render_analysis():
    st.markdown("""
    <div class="step-card">
        <h2>🔍 STEP 4: Analyse Data</h2>
        <p>Filter, pivot, aggregate, and export your merged dataset.</p>
    </div>""", unsafe_allow_html=True)

    df_orig = st.session_state.merged_data
    if df_orig is None:
        st.error("No merged data found.")
        back_button(3)
        return

    # ── Sidebar-style filter panel ──
    st.subheader("🎛️ Filters")

    cols_all   = df_orig.columns.tolist()
    filter_cols = st.multiselect("Select columns to filter on", cols_all, key="filter_cols")

    filters = {}
    if filter_cols:
        fcols = st.columns(min(len(filter_cols), 3))
        for i, col in enumerate(filter_cols):
            with fcols[i % 3]:
                dtype = df_orig[col].dtype
                if pd.api.types.is_numeric_dtype(dtype):
                    mn, mx = float(df_orig[col].min()), float(df_orig[col].max())
                    if mn == mx:
                        st.info(f"{col}: constant value {mn}")
                        filters[col] = (mn, mx)
                    else:
                        filters[col] = st.slider(col, mn, mx, (mn, mx), key=f"filter_{col}")
                else:
                    unique_vals = df_orig[col].dropna().unique().tolist()
                    if len(unique_vals) <= 100:
                        sel = st.multiselect(col, unique_vals, default=unique_vals, key=f"filter_{col}")
                        filters[col] = sel
                    else:
                        txt = st.text_input(f"{col} (contains)", key=f"filter_{col}")
                        filters[col] = txt

    # Apply filters
    df = df_orig.copy()
    for col, fval in filters.items():
        if pd.api.types.is_numeric_dtype(df[col].dtype):
            df = df[(df[col] >= fval[0]) & (df[col] <= fval[1])]
        elif isinstance(fval, list):
            if fval:
                df = df[df[col].isin(fval)]
        elif isinstance(fval, str) and fval:
            df = df[df[col].astype(str).str.contains(fval, case=False, na=False)]

    # ── Dataset stats ──
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Filtered Rows", f"{len(df):,}")
    c2.metric("Total Rows",    f"{len(df_orig):,}")
    c3.metric("Columns",       len(df.columns))
    c4.metric("% Retained",    f"{100*len(df)/max(len(df_orig),1):.1f}%")

    # ── Data preview ──
    st.markdown("---")
    st.subheader("📄 Data Preview")
    chunked_display(df, "analysis")

    link, fname = to_download_link(df, 'csv', f"filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    st.markdown(link, unsafe_allow_html=True)

    # ── Column statistics ──
    st.markdown("---")
    st.subheader("📊 Column Statistics")

    num_cols = df.select_dtypes(include='number').columns.tolist()
    cat_cols = df.select_dtypes(exclude='number').columns.tolist()

    tab_num, tab_cat = st.tabs(["🔢 Numeric Columns", "🔤 Categorical Columns"])

    with tab_num:
        if num_cols:
            stat_df = df[num_cols].describe().T.reset_index().rename(columns={'index': 'Column'})
            st.dataframe(stat_df, use_container_width=True, hide_index=True)
            link2, _ = to_download_link(stat_df, 'csv', "numeric_stats")
            st.markdown(link2, unsafe_allow_html=True)
        else:
            st.info("No numeric columns.")

    with tab_cat:
        if cat_cols:
            sel_cat = st.selectbox("Select column for value counts", cat_cols, key="cat_col_sel")
            vc = df[sel_cat].value_counts().reset_index()
            vc.columns = [sel_cat, 'Count']
            vc['%'] = (vc['Count'] / vc['Count'].sum() * 100).round(2)
            st.dataframe(vc.head(50), use_container_width=True, hide_index=True)
            link3, _ = to_download_link(vc, 'csv', f"value_counts_{sel_cat}")
            st.markdown(link3, unsafe_allow_html=True)
        else:
            st.info("No categorical columns.")

    # ── Pivot Table ──
    st.markdown("---")
    st.subheader("🔄 Pivot Table")

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        pivot_index = st.selectbox("Row (Index)", ["—"] + cols_all, key="piv_idx")
    with p2:
        pivot_cols  = st.selectbox("Columns", ["—"] + cols_all, key="piv_cols")
    with p3:
        pivot_vals  = st.selectbox("Values",  ["—"] + num_cols,  key="piv_vals")
    with p4:
        pivot_agg   = st.selectbox("Aggregation", ["sum","mean","count","min","max","std"], key="piv_agg")

    if pivot_index != "—" and pivot_vals != "—":
        try:
            pvt_kw = dict(
                index=pivot_index,
                values=pivot_vals,
                aggfunc=pivot_agg,
                margins=True,
                margins_name="Total"
            )
            if pivot_cols != "—":
                pvt_kw['columns'] = pivot_cols

            pvt = pd.pivot_table(df, **pvt_kw)
            st.dataframe(pvt, use_container_width=True)
            link4, _ = to_download_link(pvt.reset_index(), 'csv', "pivot_table")
            st.markdown(link4, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Pivot error: {e}")
    else:
        st.info("Select at least Row and Values to generate a pivot table.")

    # ── Aggregation ──
    st.markdown("---")
    st.subheader("📐 Group-By Aggregation")

    g1, g2, g3 = st.columns(3)
    with g1:
        grp_by = st.multiselect("Group by", cat_cols + num_cols, key="grp_by")
    with g2:
        agg_col = st.multiselect("Aggregate columns", num_cols, key="agg_col")
    with g3:
        agg_fn  = st.multiselect("Functions", ["sum","mean","count","min","max","std"], default=["sum","count"], key="agg_fn")

    if grp_by and agg_col and agg_fn:
        try:
            agg_dict = {c: agg_fn for c in agg_col}
            agg_result = df.groupby(grp_by).agg(agg_dict).reset_index()
            agg_result.columns = [
                f"{c[0]}_{c[1]}" if isinstance(c, tuple) and c[1] else c[0] if isinstance(c, tuple) else c
                for c in agg_result.columns
            ]
            st.dataframe(agg_result, use_container_width=True, hide_index=True)
            link5, _ = to_download_link(agg_result, 'csv', "aggregation")
            st.markdown(link5, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Aggregation error: {e}")
    else:
        st.info("Select Group-by, Aggregate columns and Functions to generate results.")

    # ── Navigation ──
    st.markdown("---")
    col_back, col_next = st.columns(2)
    with col_back:
        back_button(3, "← Back to Configure")
    with col_next:
        if st.button("Next: Download →", type="primary", use_container_width=True):
            st.session_state.step = 5
            st.rerun()


# ─────────────────────────────────────────
# STEP 5 – DOWNLOAD
# ─────────────────────────────────────────
def render_download():
    st.markdown("""
    <div class="step-card">
        <h2>💾 STEP 5: Download Merged File</h2>
        <p>Configure output and download your dataset.</p>
    </div>""", unsafe_allow_html=True)

    df = st.session_state.merged_data
    if df is None:
        st.error("No merged data.")
        back_button(3)
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Rows",    f"{len(df):,}")
    c2.metric("Columns", len(df.columns))
    c3.metric("Files merged", len(st.session_state.file_dataframes))

    col1, col2 = st.columns(2)
    with col1:
        fname_base = st.text_input("Filename (without extension)",
                                   value=f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    with col2:
        fmt = st.selectbox("Format", ['csv', 'excel', 'json'])

    with st.expander("👁️ Preview (first 100 rows)", expanded=True):
        chunked_display(df.head(100), "download_preview")

    st.markdown("---")
    link, full_name = to_download_link(df, fmt, fname_base)
    st.markdown(f"### 📥 {full_name}")
    st.markdown(link, unsafe_allow_html=True)

    st.markdown("---")
    back_button(4, "← Back to Analysis")


# ─────────────────────────────────────────
# FEATURES PAGE
# ─────────────────────────────────────────
def render_features_page():
    st.markdown('<h1 class="main-header">📖 Features Guide</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Everything you can do with File Merger Pro</p>', unsafe_allow_html=True)

    features = [
        ("📁 Multi-Format Upload", "Upload CSV, Excel (.xlsx/.xls), JSON, and TXT files. Mix different formats freely. Up to 100 files in a single session."),
        ("🔗 Automatic Column Mapping", "Columns with the same name (case-insensitive) are mapped automatically across all files. A clear summary shows you which columns match."),
        ("🗂️ Manual Column Mapping", "For columns that appear in only some files, choose to include them (filling missing rows with blanks) or skip them entirely. You can also manually map differently-named columns from specific files."),
        ("⚙️ Flexible Merge Options", "Add a source-file column to track which row came from which file. Control duplicate handling: keep all, remove exact duplicates, keep first, or keep last occurrence."),
        ("🔍 Interactive Filters", "Filter numeric columns using range sliders. Filter categorical columns using multi-select dropdowns. Apply text search filters for high-cardinality columns. All filters are applied in real time."),
        ("📊 Column Statistics", "Instantly see descriptive statistics (min, max, mean, std, quartiles) for all numeric columns. View value counts and percentages for categorical columns."),
        ("🔄 Pivot Tables", "Create pivot tables with any row, column, and value combination. Choose from sum, mean, count, min, max, or std aggregation. Totals are included automatically."),
        ("📐 Group-By Aggregation", "Group data by any column(s) and apply multiple aggregation functions to numeric columns simultaneously."),
        ("📄 Paginated Preview", "Large datasets (50,000+ rows) are displayed page by page to keep the app fast and responsive."),
        ("📥 Flexible Export", "Every table, filter result, pivot, and aggregation has its own download button. Export as CSV, Excel, or JSON. File names include timestamps to avoid confusion."),
        ("🔄 Reset Anytime", "Use the Reset button in the sidebar to start a completely fresh session at any time."),
        ("⬅️ Back Navigation", "Every step has a Back button so you can revise your choices without losing work."),
    ]

    cols = st.columns(2)
    for i, (title, desc) in enumerate(features):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="feature-card">
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🚀 Quick Start")
    st.markdown("""
1. **Upload** your files (Step 1) — mix CSV, Excel, JSON freely.
2. **Review mapping** (Step 2) — confirm auto-mapped columns and decide what to do with partial/unique columns.
3. **Configure** (Step 3) — pick duplicate handling and source-file tracking.
4. **Analyse** (Step 4) — filter, pivot, and aggregate your merged data.
5. **Download** (Step 5) — export the final file in your preferred format.
    """)

    if st.button("← Back to App", type="primary"):
        st.session_state.page = 'app'
        st.rerun()


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## 📊 File Merger Pro")
        st.markdown("---")

        if st.button("🏠 App", use_container_width=True):
            st.session_state.page = 'app'
            st.rerun()
        if st.button("📖 Features Guide", use_container_width=True):
            st.session_state.page = 'features'
            st.rerun()

        st.markdown("---")

        if st.session_state.page == 'app':
            st.markdown(f"**Current Step:** {st.session_state.step} / 5")
            if st.session_state.merged_data is not None:
                df = st.session_state.merged_data
                st.markdown(f"**Merged rows:** {len(df):,}")
                st.markdown(f"**Merged cols:** {len(df.columns)}")

        st.markdown("---")
        st.markdown("**Supported Formats**")
        st.markdown("CSV · Excel · JSON · TXT")

        st.markdown("---")
        if st.button("🔄 Reset Session", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    render_sidebar()

    if st.session_state.page == 'features':
        render_features_page()
        return

    # ── App page ──
    st.markdown('<h1 class="main-header">📊 File Merger Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Merge, map, analyse, and export your data files — effortlessly.</p>', unsafe_allow_html=True)

    step_indicator()
    st.markdown("")

    step = st.session_state.step
    if   step == 1: render_upload()
    elif step == 2: render_column_mapping()
    elif step == 3: render_configure()
    elif step == 4: render_analysis()
    elif step == 5: render_download()

    st.markdown("---")
    st.markdown(
        '<div style="text-align:center;color:#9CA3AF;font-size:.85rem;">'
        'File Merger Pro · Built with Streamlit'
        '</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()