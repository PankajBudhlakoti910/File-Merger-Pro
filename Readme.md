# 📊 File Merger Pro

> **Merge, map, analyse, and export your data files — effortlessly.**

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 Live Demo

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

> Deploy your own: see [Deployment](#-deployment) section below.

---

## ✨ Features at a Glance

| Feature | Details |
|---|---|
| 📁 **Multi-Format Upload** | CSV, Excel (.xlsx / .xls), JSON, TXT — mix freely |
| 🔗 **Auto Column Mapping** | Case-insensitive exact match across all files |
| 🗂️ **Manual Column Mapping** | Map differently-named columns; skip or fill missing |
| ⚙️ **Merge Options** | Source-file column, duplicate control |
| 🔍 **Smart Filters** | Sliders for numeric, multi-select for categorical, text search for large sets |
| 📊 **Column Statistics** | Describe + value counts with export |
| 🔄 **Pivot Tables** | Any row/column/value + 6 aggregation functions |
| 📐 **Group-By Aggregation** | Multi-column grouping × multi-function |
| 📄 **Paginated Preview** | Handles 1M+ row datasets without crashing |
| 📥 **Flexible Export** | CSV · Excel · JSON with one click at every table |
| ⬅️ **Back Navigation** | Step back at any point without losing data |

---

## 📸 Screenshots

### Step 1 – Upload
Upload any combination of CSV, Excel, JSON, or TXT files. A summary table shows row counts and column names at a glance.

### Step 2 – Column Mapping
Automatic mapping for columns shared across all files. Partial columns show which files are missing them, with per-file remapping controls and Include / Skip options.

### Step 3 – Configure & Merge
Choose duplicate handling and whether to add a source-file tracking column, then merge with one click.

### Step 4 – Analyse
Live filters, descriptive stats, pivot tables, and group-by aggregations — all with individual download buttons.

### Step 5 – Download
Export the complete merged dataset as CSV, Excel, or JSON.

---

## 🏁 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip

### Install & Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/file-merger-pro.git
cd file-merger-pro

# 2. (Optional but recommended) create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

Open your browser at **http://localhost:8501**.

---

## 🌐 Deployment

### Streamlit Community Cloud (Free, Recommended)

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select your repo → set **Main file path** to `app.py`.
4. Click **Deploy** — you'll get a public URL instantly.

### Other Platforms

| Platform | Command |
|---|---|
| **Railway** | Connect repo → auto-detects Streamlit |
| **Render** | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0` |
| **Heroku** | Add `Procfile`: `web: streamlit run app.py --server.port $PORT` |
| **Docker** | See `Dockerfile` below |

#### Dockerfile (optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

---

## 📂 Project Structure

```
file-merger-pro/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── LICENSE             # MIT License
```

---

## 🛠️ How It Works

### Column Mapping Logic

```
For each unique column name (normalised to lowercase):
  ├── Present in ALL files  → Auto-mapped ✅
  └── Present in SOME files → Manual decision required:
        ├── Include: fill missing rows with blank (NaN)
        ├── Include + Remap: pull from a differently-named column in missing files
        └── Skip: column is excluded from the merged output
```

### Large Dataset Handling

- Files are read lazily (one at a time) to minimise peak memory.
- Preview tables are paginated at **50,000 rows per page**.
- Filters are applied in-memory on the merged DataFrame (works well up to ~5M rows on a standard machine).

---

## 🤝 Contributing

Pull requests are welcome!

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

MIT © 2024 — see [LICENSE](LICENSE) for details.
