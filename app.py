"""
Dasbor "Lensa Kesenjangan: Pola Kesenjangan, Pengeluaran, dan Pendidikan di Indonesia"
TAHAP 2 - Desain & Animasi (mengikuti referensi p3re.jp).

Jalankan:
    pip install dash plotly pandas openpyxl      (gunakan Dash versi terbaru)
    python app.py
Lalu buka http://127.0.0.1:8050

Struktur folder:
    app.py
    assets/styles.css                    <- tema, hero, loader/sapuan gelombang, tombol pill, modal
    assets/app.js                        <- loader, nav, scroll reveal, count-up, sapuan gelombang
    Pengeluaran_Hierarki_2025_Cleaned.(csv|xlsx)
    Kemiskinan_KabKota_2025_Cleaned.(csv|xlsx)
    Dataset_Multivariat_BPS_2023_2025.(csv|xlsx)
    indonesia_kabkota.geojson            <- ditambahkan nanti oleh pengguna
"""

import json
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from plotly.subplots import make_subplots

# ----------------------------------------------------------------------------
# 0. KONFIGURASI
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

# --- GeoJSON batas Kab/Kota (disediakan pengguna nanti) ---
GEOJSON_PATH = BASE_DIR / "indonesia_kabkota.geojson"
# Nama field di properties GeoJSON yang berisi nama kab/kota (contoh: "NAME_2", "NAMOBJ", "WADMKK").
GEO_NAME_PROPERTY = "WADMKK"
# Alias manual bila ada nama yang tidak cocok setelah normalisasi:
#   {"nama versi geojson (ternormalisasi)": "nama versi data (ternormalisasi)"}
NAME_ALIASES = {
    'banyuasin': 'banyu asin',
    'batanghari': 'batang hari',
    'fak fak': 'fakfak',
    'gunungkidul': 'gunung kidul',
    'kota banjarbaru': 'kota banjar baru',
    'kotabaru': 'kota baru',
    'kota bau bau': 'kota baubau',
    'kota lubuk linggau': 'kota lubuklinggau',
    'kota padang sidempuan': 'kota padangsidimpuan',
    'kota palangkaraya': 'kota palangka raya',
    'kota pare pare': 'kota parepare',
    'kota pematangsiantar': 'kota pematang siantar',
    'kota sawahlunto': 'kota sawah lunto',
    'labuhanbatu': 'labuhan batu',
    'labuhanbatu selatan': 'labuhan batu selatan',
    'labuhanbatu utara': 'labuhan batu utara',
    'kepulauan tanimbar': 'maluku tenggara barat',
    'pasangkayu': 'mamuju utara',
    'muko muko': 'mukomuko',
    'pangkajene kepulauan': 'pangkajene dan kepulauan',
    'kepulauan siau tagulandang biaro': 'siau tagulandang biaro',
    'toba': 'toba samosir',
    'tulang bawang': 'tulangbawang'
}

YEARS = [2023, 2024, 2025]
DEFAULT_YEAR = 2025
MAX_PROFILE = 8  # batas provinsi pada grafik detail di modal

# --- Palet & tipografi tema (selaras dengan assets/styles.css) ---
NAVY = "#1D384A"
SEA = "#029EEB"
PALE = "#C0D5E8"
PALE_BG = "#E5EEF6"
TRANSPARENT = "rgba(0,0,0,0)"
# --- Tema grafik selaras menu Persona 3 Reload (font & warna sama dengan assets/p3/style.css) ---
INK = "#020914"        # latar panel
CYAN = "#16cffb"       # aksen utama
ICE = "#7de6fd"
ORANGE = "#E69F00"     # Okabe-Ito: pasangan aman buta warna untuk cyan
GRID = "rgba(22,207,251,.12)"
AXIS = "rgba(22,207,251,.55)"
FONT_BODY = '"Poppins", "Noto Sans", Arial, sans-serif'
FONT_HEAD = '"Rodin Pro Bold", "NewRodin Pro UB", "Poppins", sans-serif'  # judul/legenda: huruf miring tebal ala menu
CL_COLORS = ["#E69F00", "#56B4E9", "#CC79A7"]   # klaster IPM rendah/sedang/tinggi (Okabe-Ito, terang di latar gelap)
CHORO_CLASSES = ["#123a8c", "#0a63d6", "#1593e6", "#16cffb", "#a8f0ff", "#ffffff"]  # berurutan, kecerahan naik
BLUE_SCALE = [[0, "#3A78A6"], [0.35, "#1F7DB5"], [0.65, SEA], [0.85, "#7CC8F5"], [1, PALE_BG]]
PROFILE_COLORS = ["#029EEB", "#E5EEF6", "#7CC8F5", "#2DD4BF", "#F6C177", "#A78BFA", "#FB7185", "#94A3B8"]

GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,600&display=swap"
)


# ----------------------------------------------------------------------------
# 1. PEMUATAN DATA (read-only: tidak ada dropna / perubahan struktur)
# ----------------------------------------------------------------------------
def load_table(stem: str) -> pd.DataFrame:
    """Muat dataset apa adanya. Mendukung .csv (sesuai blueprint) maupun .xlsx."""
    csv_path = BASE_DIR / f"{stem}.csv"
    xlsx_path = BASE_DIR / f"{stem}.xlsx"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    if xlsx_path.exists():
        return pd.read_excel(xlsx_path)
    raise FileNotFoundError(f"Tidak menemukan {stem}.csv ataupun {stem}.xlsx di {BASE_DIR}")


df_exp = load_table("Pengeluaran_Hierarki_2025_Cleaned")        # 20 baris, 4 kolom
df_exp24 = load_table("Pengeluaran_Hierarki_2024_Cleaned")        # pembanding untuk pertumbuhan 2024 -> 2025
df_kab = load_table("Kemiskinan_KabKota_2025_Cleaned")          # 509 kab/kota
df_multi = load_table("Dataset_Multivariat_LENGKAP_8_Variabel")      # 38 provinsi, NaN 2023 utk DOB Papua

if len(df_kab) != 509:
    print(f"[PERINGATAN] Data kemiskinan berisi {len(df_kab)} baris, diharapkan 509.")
if len(df_multi) != 38:
    print(f"[PERINGATAN] Data multivariat berisi {len(df_multi)} baris, diharapkan 38.")


# ----------------------------------------------------------------------------
# 2. UTILITAS PENCOCOKAN NAMA WILAYAH (untuk Peta)
# ----------------------------------------------------------------------------
def normalize_region(name: str) -> str:
    """
    Normalisasi nama kab/kota agar data & GeoJSON bisa digabung.
    Hasil: huruf kecil, tanpa awalan kabupaten, awalan "kota" dipertahankan.
    """
    s = str(name).lower().strip()
    s = re.sub(r"[.,'’`\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^(kabupaten|kab)\s+", "", s)
    s = re.sub(r"^kota\s+(administrasi|adm)\s+", "kota ", s)
    s = re.sub(r"^(administrasi|adm)\s+", "", s)
    return NAME_ALIASES.get(s, s)


# Salinan untuk keperluan peta (df_kab asli tidak disentuh)
df_kab_map = df_kab.assign(_key=df_kab["Wilayah"].map(normalize_region))


def _ring_area(ring):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(ring, ring[1:] + ring[:1])) / 2


def _rewind_geometry(geom):
    """
    Plotly (d3-geo) mengharuskan ring LUAR searah jarum jam dan lubang (hole) berlawanan arah.
    GeoJSON standar RFC 7946 justru kebalikannya (luar = berlawanan jarum jam). Bila tidak dibalik,
    polygon dianggap "seluruh bola bumi kecuali wilayah ini" sehingga peta tampil sebagai
    persegi panjang berwarna tunggal.
    """
    def fix(ring, clockwise):
        is_cw = _ring_area(ring) < 0
        return ring if is_cw == clockwise else ring[::-1]

    def fix_poly(poly):
        return [fix(poly[0], True)] + [fix(h, False) for h in poly[1:]]

    if geom["type"] == "Polygon":
        geom["coordinates"] = fix_poly(geom["coordinates"])
    elif geom["type"] == "MultiPolygon":
        geom["coordinates"] = [fix_poly(p) for p in geom["coordinates"]]


def load_geojson():
    """Muat GeoJSON jika ada, lalu sisipkan kunci gabung `_key`. Return (geojson | None, status_teks)."""
    if not GEOJSON_PATH.exists():
        return None, f"GeoJSON belum tersedia ({GEOJSON_PATH.name}). Peta akan aktif setelah file ditambahkan."

    with open(GEOJSON_PATH, encoding="utf-8") as f:
        gj = json.load(f)

    # Buang fitur tanpa geometri (geometry: null) -- satu saja sudah cukup membuat Plotly gagal
    # menggambar seluruh peta ("Cannot read properties of null (reading 'type')").
    gj["features"] = [ft for ft in gj["features"] if ft.get("geometry") and ft["properties"].get(GEO_NAME_PROPERTY)]

    for feat in gj["features"]:
        _rewind_geometry(feat["geometry"])
        props = feat.setdefault("properties", {})
        if GEO_NAME_PROPERTY not in props:
            raise KeyError(
                f"Properti '{GEO_NAME_PROPERTY}' tidak ada di GeoJSON. "
                f"Properti tersedia: {list(props.keys())}. Ubah GEO_NAME_PROPERTY."
            )
        props["_key"] = normalize_region(props[GEO_NAME_PROPERTY])

    geo_keys = {ft["properties"]["_key"] for ft in gj["features"]}
    data_keys = set(df_kab_map["_key"])
    matched = data_keys & geo_keys
    only_data = sorted(data_keys - geo_keys)
    only_geo = sorted(geo_keys - data_keys)

    print(f"[GeoJSON] Cocok: {len(matched)}/{len(data_keys)} wilayah data.")
    if only_data:
        print(f"[GeoJSON] Ada di DATA tapi tidak di GeoJSON ({len(only_data)}): {only_data}")
    if only_geo:
        print(f"[GeoJSON] Ada di GeoJSON tapi tidak di DATA ({len(only_geo)}): {only_geo}")

    return gj, f"GeoJSON dimuat. {len(matched)}/{len(data_keys)} wilayah data berhasil dicocokkan."


GEOJSON, GEO_STATUS = load_geojson()


# ----------------------------------------------------------------------------
# 3. TEMA PLOTLY & FUNGSI PEMBUAT GRAFIK
# ----------------------------------------------------------------------------
def apply_theme(fig: go.Figure, **layout) -> go.Figure:
    """Tema gelap ala menu P3R: latar transparan, font Poppins/Rodin, garis bantu cyan tipis, tooltip berbingkai cyan."""
    font = {**dict(family=FONT_BODY, color="#ffffff", size=13), **layout.pop("font", {})}   # gabungkan, bukan dobel
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=TRANSPARENT,
        plot_bgcolor=TRANSPARENT,
        font=font,
        hoverlabel=dict(bgcolor=INK, bordercolor=CYAN, align="left", font=dict(family=FONT_BODY, color="#ffffff", size=13)),
        legend={**dict(font=dict(family=FONT_BODY, size=12, color="#ffffff"), bgcolor="rgba(2,9,20,.55)", bordercolor=AXIS, borderwidth=1),
                **layout.pop("legend", {})},
        **layout,
    )
    for upd in (fig.update_xaxes, fig.update_yaxes):
        upd(gridcolor=GRID, zerolinecolor=AXIS, linecolor=AXIS, tickfont=dict(family=FONT_BODY, color=PALE),
            title_font=dict(family=FONT_HEAD, color=ICE, size=13))
    return fig


def cbar(title: str, **kw) -> dict:
    """Legenda warna seragam: judul Rodin cyan, tanpa bingkai."""
    return dict(title=dict(text=title.upper(), font=dict(family=FONT_HEAD, size=12, color=CYAN)), outlinewidth=0, thickness=14,
                tickfont=dict(family=FONT_BODY, size=11, color="#ffffff"), **kw)


def empty_figure(message: str, height: int = 420) -> go.Figure:
    """Figure kosong bertema berisi pesan (placeholder peta / modal tanpa pilihan)."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
        font=dict(family=FONT_HEAD, size=15, color=PALE),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return apply_theme(fig, height=height, margin=dict(t=20, l=20, r=20, b=20))


def build_treemap() -> go.Figure:
    """Visualisasi 1: Hierarki pengeluaran Level 1 -> Level 2 -> Level 3."""
    fig = px.treemap(
        df_exp,
        path=["Level 1", "Level 2", "Level 3"],
        values="Nilai Rupiah",
        color="Level 2",
        color_discrete_map={"(?)": NAVY, "Makanan": SEA, "Bukan Makanan": "#2F6F9F"},
        template="plotly_dark",
    )
    fig.update_traces(
        textinfo="label+percent parent",
        textfont=dict(family=FONT_BODY, color="#FFFFFF"),
        marker=dict(line=dict(color=NAVY, width=2)),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Nilai: Rp %{value:,.0f}<br>"
            "Porsi dari induk: %{percentParent:.1%}<br>"
            "Porsi dari total: %{percentRoot:.1%}"
            "<extra></extra>"
        ),
        hoverlabel=dict(bgcolor=NAVY, bordercolor=SEA, font=dict(family=FONT_BODY, color=PALE_BG)),
    )
    return apply_theme(fig, height=560, margin=dict(t=20, l=10, r=10, b=10))


def build_choropleth() -> go.Figure:
    """Visualisasi 2: Choropleth kemiskinan kab/kota. Placeholder bila GeoJSON belum ada."""
    if GEOJSON is None:
        return empty_figure(
            "Peta belum dapat dirender:<br>file GeoJSON batas Kab/Kota belum ditambahkan.", height=450
        )

    v = df_kab_map["Kemiskinan_2025"]
    edges = np.unique(np.round(np.quantile(v, [0, .2, .4, .6, .8, .95, 1]), 2))   # kelas kuantil; kelas teratas = 5% tertinggi
    lo, hi = float(v.min()), float(v.max())
    frac = [(e - lo) / (hi - lo) for e in edges]
    scale = []
    for i in range(len(edges) - 1):   # skala bertangga: tiap kelas satu warna (kuantil menjaga peta tetap terbaca meski data miring ke kanan)
        scale += [[frac[i], CHORO_CLASSES[i]], [frac[i + 1], CHORO_CLASSES[i]]]
    fig = px.choropleth(
        df_kab_map,
        geojson=GEOJSON,
        locations="_key",
        featureidkey="properties._key",
        color="Kemiskinan_2025",
        color_continuous_scale=scale,
        range_color=(lo, hi),
        hover_name="Wilayah",
        hover_data={"_key": False, "Kemiskinan_2025": ":.2f"},
        labels={"Kemiskinan_2025": "Kemiskinan 2025 (%)"},
        template="plotly_dark",
    )
    fig.update_traces(marker_line=dict(color="rgba(2,9,20,.85)", width=0.35))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor=TRANSPARENT)
    return apply_theme(
        fig,
        height=520,
        margin=dict(t=20, l=0, r=0, b=0),
        geo=dict(bgcolor=TRANSPARENT),
        coloraxis_colorbar=cbar("Kemiskinan (%)", tickvals=[float(e) for e in edges], ticktext=[f"{e:.1f}" for e in edges],
                                ticks="outside", ticklen=4, tickcolor=CYAN, len=0.85),
    )


# (kunci, label sumbu, templat nama kolom di dataset multivariat)
SPLOM_VARS = [
    ("RLS", "Lama Sekolah (RLS)", "RLS_{y}"),
    ("TPT", "TPT (%)", "TPT_Agustus_{y}"),
    ("IPM", "IPM", "IPM_{y}"),
]


def build_splom(year: int) -> tuple[go.Figure, str]:
    """
    Visualisasi 3: SPLOM RLS - TPT - IPM untuk tahun terpilih.
    Satu trace Splom => brushing & linking antar-panel bawaan Plotly.
    Baris NaN TIDAK di-drop; Plotly melewatkan titik NaN saat render.
    """
    col = {key: tmpl.format(y=year) for key, _, tmpl in SPLOM_VARS}
    d = df_multi[["Provinsi", col["RLS"], col["TPT"], col["IPM"]]]  # subset, df_multi tidak berubah

    fig = go.Figure(
        go.Splom(
            dimensions=[dict(label=label, values=d[col[key]]) for key, label, _ in SPLOM_VARS],
            customdata=d.values.tolist(),   # [Provinsi, RLS, TPT, IPM]
            marker=dict(
                color=d[col["IPM"]],
                colorscale=BLUE_SCALE,
                showscale=True,
                colorbar=dict(title="IPM", outlinewidth=0),
                size=9,
                line=dict(width=0.6, color=PALE_BG),
            ),
            diagonal_visible=False,
            showupperhalf=False,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Lama Sekolah: %{customdata[1]:.2f} tahun<br>"
                "TPT: %{customdata[2]:.2f}%<br>"
                "IPM: %{customdata[3]:.2f}"
                "<extra></extra>"
            ),
            selected=dict(marker=dict(opacity=1)),
            unselected=dict(marker=dict(opacity=0.15)),
        )
    )
    apply_theme(
        fig,
        title=dict(
            text=f"Pendidikan - Serapan Kerja - IPM ({year})",
            font=dict(family=FONT_HEAD, size=18, color=PALE_BG),
        ),
        dragmode="select",
        height=650,
        margin=dict(t=60, l=60, r=20, b=40),
    )

    missing = d.loc[d[[col["RLS"], col["TPT"], col["IPM"]]].isna().any(axis=1), "Provinsi"].tolist()
    note = (
        f"Provinsi tanpa data {year} (tidak ditampilkan di grafik): {', '.join(missing)}."
        if missing else f"Seluruh {len(d)} provinsi memiliki data lengkap pada {year}."
    )
    return fig, note


PROFILE_INDICATORS = [
    ("IPM", "IPM_{y}", "indeks"),
    ("Rata-rata Lama Sekolah", "RLS_{y}", "tahun"),
    ("Pengangguran (TPT)", "TPT_Agustus_{y}", "%"),
    ("Kemiskinan", "Kemiskinan_Maret_{y}", "%"),
]


def build_profile(names: list[str]) -> go.Figure:
    """Grafik detail modal: tren 2023-2025 empat indikator untuk provinsi terpilih (NaN = celah, tidak diputus)."""
    if not names:
        return empty_figure("Sorot atau klik provinsi pada SPLOM untuk melihat profilnya.")

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[f"{title} ({unit})" for title, _, unit in PROFILE_INDICATORS],
        horizontal_spacing=0.1, vertical_spacing=0.2,
    )
    for i, name in enumerate(names):
        row = df_multi.loc[df_multi["Provinsi"] == name].iloc[0]
        color = PROFILE_COLORS[i % len(PROFILE_COLORS)]
        for k, (_, template, unit) in enumerate(PROFILE_INDICATORS):
            values = [row[template.format(y=y)] for y in YEARS]
            fig.add_trace(
                go.Scatter(
                    x=YEARS, y=values, mode="lines+markers",
                    name=name, legendgroup=name, showlegend=(k == 0),
                    line=dict(color=color, width=2.5), marker=dict(size=8),
                    connectgaps=False,
                    hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:.2f}} {unit}<extra></extra>",
                ),
                row=k // 2 + 1, col=k % 2 + 1,
            )
    fig.update_xaxes(tickmode="array", tickvals=YEARS)
    fig.update_annotations(font=dict(family=FONT_HEAD, size=14, color=PALE_BG))
    return apply_theme(
        fig,
        height=580,
        margin=dict(t=50, l=50, r=20, b=70),
        legend=dict(orientation="h", y=-0.1),
    )



# ----------------------------------------------------------------------------
# 3b. TAMBAHAN UAS: hierarki 2 representasi, peta 2 jenis, multivariat 8 variabel (PCA, paralel, heatmap, SPLOM)
# ----------------------------------------------------------------------------
import numpy as np  # noqa: E402
from functools import lru_cache  # noqa: E402
from dash import Patch  # noqa: E402
from scipy.cluster.hierarchy import leaves_list, linkage  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

# Palet ramah buta warna (Okabe-Ito) untuk kategori; Viridis/Cividis untuk skala berurutan
OKABE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00"]
SRC = {
    "hier": "Sumber: BPS, Pengeluaran per Kapita menurut kelompok komoditas, 2024-2025 (ukuran: 2025; warna: pertumbuhan nominal)",
    "map": "Sumber: BPS, Persentase Penduduk Miskin menurut Kabupaten/Kota, 2025",
    "mv": "Sumber: BPS, IPM, Kemiskinan, TPT, RLS, HLS, UHH, Pengeluaran per Kapita, Gini menurut Provinsi, 2023-2025",
}


def add_source(fig: go.Figure, key: str, y: float = -0.02, shift: int | None = None) -> go.Figure:
    """Teks 'Sumber: BPS'. shift = jarak piksel di bawah area plot (lebih stabil daripada y relatif)."""
    kw = dict(y=0, yshift=-shift) if shift is not None else dict(y=y)
    fig.add_annotation(text=SRC[key], xref="paper", yref="paper", x=0, xanchor="left", yanchor="top",
                       showarrow=False, font=dict(family=FONT_BODY, size=9, color=ICE), **kw)
    return fig


# --- Hierarki: ukuran = Nilai Rupiah 2025, warna = pertumbuhan nominal 2024 -> 2025 (%) ---
def _node_values(df: pd.DataFrame) -> dict:
    """id simpul ("A/B/C", sama dengan id Plotly) -> total nilai; induk = jumlah anak."""
    root = df["Level 1"].iloc[0]
    out = {root: float(df["Nilai Rupiah"].sum())}
    for l2, g in df.groupby("Level 2", sort=False):
        out[f"{root}/{l2}"] = float(g["Nilai Rupiah"].sum())
    for _, r in df.iterrows():
        out[f"{r['Level 1']}/{r['Level 2']}/{r['Level 3']}"] = float(r["Nilai Rupiah"])
    return out


def build_hier(kind: str) -> go.Figure:
    fn = px.sunburst if kind == "sunburst" else px.treemap
    fig = fn(df_exp, path=["Level 1", "Level 2", "Level 3"], values="Nilai Rupiah", template="plotly_dark")
    t = fig.data[0]
    v25, v24 = _node_values(df_exp), _node_values(df_exp24)
    ids = list(t.ids)
    growth = np.array([100 * (v25[i] / v24[i] - 1) if v24.get(i) else 0.0 for i in ids])
    prev = np.array([v24.get(i, np.nan) for i in ids])
    lim = float(np.ceil(np.abs(growth).max()))
    fig.update_traces(
        marker=dict(colors=growth, colorscale=[[0, CYAN], [0.5, "#f4f8fc"], [1, ORANGE]], cmid=0, cmin=-lim, cmax=lim,
                    showscale=True, colorbar=cbar("Pertumbuhan 2024-2025", ticksuffix=" %", len=0.92),
                    line=dict(color=INK, width=3)),
        customdata=np.column_stack([growth, prev]),
        textinfo="label+percent parent", textfont=dict(family=FONT_BODY, size=13, color=INK),
        hovertemplate=("<b>%{label}</b><br>2025: Rp %{value:,.0f}<br>2024: Rp %{customdata[1]:,.0f}<br>"
                       "Pertumbuhan nominal: <b>%{customdata[0]:+.1f}%</b><br>Porsi dari total: %{percentRoot:.1%}<extra></extra>"),
    )
    if kind == "sunburst":
        fig.update_traces(insidetextorientation="radial", leaf=dict(opacity=1))
    else:   # treemap: pita judul per kelompok + penunjuk posisi bersudut (chevron)
        fig.update_traces(marker_pad=dict(t=26, l=4, r=4, b=4), root_color="rgba(2,9,20,.9)",
                          pathbar=dict(visible=True, side="top", thickness=26, edgeshape=">",
                                       textfont=dict(family=FONT_HEAD, size=12, color=INK)))
    fig.update_layout(uniformtext=dict(minsize=10, mode="hide"))   # sembunyikan label yang terlalu kecil
    apply_theme(fig, margin=dict(t=10, l=6, r=6, b=34))
    return add_source(fig, "hier")


# --- Peta: choropleth (rasio %) dan simbol proporsional ---
def _centroid(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    best, ba = None, -1.0
    for poly in polys:
        ring = poly[0]
        a = cx = cy = 0.0
        for p0, p1 in zip(ring, ring[1:] + ring[:1]):
            x0, y0, x1, y1 = p0[0], p0[1], p1[0], p1[1]
            c = x0 * y1 - x1 * y0
            a += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
        if abs(a) > ba and a != 0:
            ba, best = abs(a), (cx / (3 * a), cy / (3 * a))
    return best


GEO_CENT = {ft["properties"]["_key"]: _centroid(ft["geometry"]) for ft in GEOJSON["features"]} if GEOJSON else {}


def build_bubble() -> go.Figure:
    d = df_kab_map.assign(c=df_kab_map["_key"].map(GEO_CENT)).dropna(subset=["c"])
    fig = go.Figure()
    fig.add_trace(go.Choropleth(geojson=GEOJSON, featureidkey="properties._key", locations=d["_key"], z=[0] * len(d),
                                colorscale=[[0, "#0b1d44"], [1, "#0b1d44"]], showscale=False, hoverinfo="skip",
                                marker=dict(line=dict(color="rgba(22,207,251,.45)", width=0.4)), name="Batas wilayah"))
    v = d["Kemiskinan_2025"]
    fig.add_trace(go.Scattergeo(lon=[c[0] for c in d["c"]], lat=[c[1] for c in d["c"]], mode="markers", name="Kemiskinan (%)",
                                customdata=np.column_stack([d["Wilayah"], v]),
                                marker=dict(size=v, sizemode="area", sizeref=2 * v.max() / (26 ** 2), sizemin=1.5,
                                            color=ORANGE, opacity=0.78, line=dict(color="#ffffff", width=0.6)),
                                hovertemplate="<b>%{customdata[0]}</b><br>Kemiskinan: %{customdata[1]:.2f}%<extra></extra>"))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor=TRANSPARENT)
    fig.add_annotation(text="Luas lingkaran proporsional dengan persentase kemiskinan", xref="paper", yref="paper",
                       x=1, y=1, xanchor="right", showarrow=False, font=dict(family=FONT_BODY, size=11, color=ICE))
    apply_theme(fig, margin=dict(t=10, l=0, r=0, b=34), geo=dict(bgcolor=TRANSPARENT),
                legend=dict(orientation="h", y=0.02, x=0.02))
    return add_source(fig, "map")


def build_map(kind: str = "choropleth") -> go.Figure:
    if GEOJSON is None:
        return build_choropleth()
    return build_bubble() if kind == "bubble" else add_source(build_choropleth(), "map")


# --- Multivariat 8 variabel ---
MV = [("IPM", "IPM", "IPM_{y}"), ("Kemiskinan", "Kemiskinan (%)", "Kemiskinan_Maret_{y}"),
      ("TPT", "TPT (%)", "TPT_Agustus_{y}"), ("RLS", "RLS (th)", "RLS_{y}"), ("HLS", "HLS (th)", "HLS_{y}"),
      ("UHH", "UHH (th)", "UHH_{y}"), ("Pengeluaran", "Pengeluaran (Rp)", "Pengeluaran_{y}"), ("Gini", "Gini", "Gini_{y}")]
MV_KEYS = [k for k, _, _ in MV]


def mv_frame(year: int) -> pd.DataFrame:
    d = df_multi[["Provinsi"] + [t.format(y=year) for _, _, t in MV]].copy()   # salinan subset; df_multi tidak berubah
    d.columns = ["Provinsi"] + MV_KEYS
    return d


@lru_cache(maxsize=8)
def mv_model(year: int) -> dict:
    d = mv_frame(year)
    ok = d.dropna().reset_index(drop=True)
    X = StandardScaler().fit_transform(ok[MV_KEYS])
    pca = PCA(n_components=2).fit(X)
    Z = pca.transform(X)
    km = KMeans(n_clusters=3, n_init=10, random_state=42).fit(X)
    order = ok.assign(c=km.labels_).groupby("c")["IPM"].mean().sort_values().index.tolist()   # klaster urut IPM naik
    rank = {c: r for r, c in enumerate(order)}
    lab = np.array([rank[c] for c in km.labels_])
    dist = np.sqrt((Z ** 2).sum(1))
    out = ok["Provinsi"][dist > dist.mean() + 1.5 * dist.std()].tolist()
    return dict(d=d, ok=ok, X=X, Z=Z, lab=lab, evr=pca.explained_variance_ratio_, load=pca.components_.T, out=out,
                missing=d.loc[d[MV_KEYS].isna().any(axis=1), "Provinsi"].tolist())


CL_NAME = ["IPM rendah", "IPM sedang", "IPM tinggi"]


def mv_note(year: int) -> str:
    m = mv_model(year)
    l1 = sorted(zip(m["load"][:, 0], MV_KEYS), key=lambda t: -abs(t[0]))[:3]
    txt = (f"PCA {year}: PC1 {m['evr'][0]*100:.1f}% + PC2 {m['evr'][1]*100:.1f}% = {sum(m['evr'])*100:.1f}% variansi. "
           f"PC1 didominasi {', '.join(f'{k} ({v:+.2f})' for v, k in l1)}. ")
    txt += "Klaster: " + ", ".join(f"{CL_NAME[i]} {int((m['lab']==i).sum())}" for i in range(3)) + ". "
    txt += f"Pencilan: {', '.join(m['out']) or 'tidak ada'}. "
    if m["missing"]:
        txt += f"Tanpa data {year} (tidak diikutkan): {', '.join(m['missing'])}."
    return txt


SPLOM_DEFAULT = ["IPM", "Kemiskinan", "TPT", "RLS", "Pengeluaran"]   # 5 variabel agar tiap sel terbaca; bisa diubah di UI


def _title(txt: str) -> dict:
    """Judul huruf miring tebal cyan (bagian sebelum ':'), keterangan putih kecil sebagai subjudul."""
    head, _, sub = txt.partition(":")
    out = dict(text=head.strip().upper(), x=0.01, xanchor="left", font=dict(family=FONT_HEAD, size=16, color=CYAN))
    if sub.strip():
        out["subtitle"] = dict(text=sub.strip(), font=dict(family=FONT_BODY, size=11, color=PALE))
    return out


def build_pca(year: int) -> go.Figure:
    m = mv_model(year); ok = m["ok"]; Z = m["Z"]
    xr = max(abs(Z[:, 0]).max(), 1) * 1.25
    yr = max(abs(Z[:, 1]).max(), 1) * 1.35
    fig = go.Figure()
    for i in range(3):   # satu trace per klaster -> legenda; selectedpoints diatur per trace lewat callback
        idx = np.where(m["lab"] == i)[0]
        nm = ok["Provinsi"].iloc[idx]
        pos = ["middle left" if Z[j, 0] > 0.55 * xr else "middle right" if Z[j, 0] < -0.55 * xr else "top center" for j in idx]
        fig.add_trace(go.Scatter(x=Z[idx, 0], y=Z[idx, 1], mode="markers+text", name=CL_NAME[i], customdata=nm,
                                 text=[n if n in m["out"] else "" for n in nm], textposition=pos, cliponaxis=False,
                                 textfont=dict(family=FONT_HEAD, size=12, color="#ffffff"),
                                 marker=dict(size=13, color=CL_COLORS[i], line=dict(width=1.5, color="#ffffff")),
                                 selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=0.2)),
                                 hovertemplate="<b>%{customdata}</b><br>PC1 %{x:.2f} | PC2 %{y:.2f}<extra>" + CL_NAME[i] + "</extra>"))
    sc = 0.5 * xr / np.sqrt((m["load"] ** 2).sum(1)).max()   # panjang panah variabel
    for k, nm in enumerate(MV_KEYS):
        lx, ly = m["load"][k, 0] * sc, m["load"][k, 1] * sc
        # Pada anotasi berpanah Plotly, teks menempel di EKOR panah (ax, ay), bukan di kepala. Jadi panah dan label
        # dipisah: panah tanpa teks dari titik nol ke ujung, label sebagai anotasi sendiri di ujung panah.
        fig.add_annotation(x=lx, y=ly, ax=0, ay=0, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2,
                           arrowcolor="rgba(125,230,253,.8)", arrowwidth=1.6, text="")
        fig.add_annotation(x=lx, y=ly, xref="x", yref="y", showarrow=False, text=nm, font=dict(family=FONT_BODY, size=10, color="#ffffff"),
                           bgcolor="rgba(2,9,20,.82)", bordercolor=CYAN, borderwidth=1, borderpad=2,   # label bergaya tag menu
                           xanchor="left" if lx >= 0 else "right", yanchor="bottom" if ly >= 0 else "top",
                           xshift=5 if lx >= 0 else -5)
    fig.update_xaxes(title=f"PC1 ({m['evr'][0]*100:.1f}% variansi)", range=[-xr, xr], zeroline=True)
    fig.update_yaxes(title=f"PC2 ({m['evr'][1]*100:.1f}% variansi)", range=[-yr, yr], zeroline=True)
    apply_theme(fig, title=_title(f"Biplot PCA {year}: provinsi (titik) dan arah variabel (panah)"), dragmode="select",
                margin=dict(t=58, l=56, r=20, b=70),
                legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom", font=dict(size=11)))
    return add_source(fig, "mv", shift=56)


def build_splom8(year: int, keys: list[str] | None = None) -> go.Figure:
    m = mv_model(year); d = m["d"]
    sel = [(k, lbl) for k, lbl, _ in MV if k in (keys or SPLOM_DEFAULT)] or [(k, lbl) for k, lbl, _ in MV[:3]]
    cmap = dict(zip(m["ok"]["Provinsi"], m["lab"]))
    colors = [CL_COLORS[cmap[p]] if p in cmap else "#8a97a3" for p in d["Provinsi"]]
    fig = go.Figure(go.Splom(
        dimensions=[dict(label=lbl, values=d[k]) for k, lbl in sel], customdata=d["Provinsi"], text=d["Provinsi"],
        marker=dict(color=colors, size=8, opacity=0.92, line=dict(width=0.8, color="#ffffff")), diagonal_visible=False, showupperhalf=False,
        hovertemplate="<b>%{customdata}</b><extra></extra>",
        selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=0.15))))
    fig.update_xaxes(tickfont=dict(size=9), title_font=dict(size=10))
    fig.update_yaxes(tickfont=dict(size=9), title_font=dict(size=10))
    apply_theme(fig, title=_title(f"Scatterplot Matrix {year} (warna = klaster IPM; abu-abu = tanpa data)"), dragmode="select",
                margin=dict(t=48, l=64, r=14, b=70))
    return add_source(fig, "mv", shift=56)


def build_parcoords(year: int, sel: list[str] | None) -> go.Figure:
    m = mv_model(year); ok = m["ok"]
    s = set(sel or [])
    z = [1 if p in s else 0 for p in ok["Provinsi"]] if s else [0.5] * len(ok)
    fig = go.Figure(go.Parcoords(
        line=dict(color=z, cmin=0, cmax=1, colorscale=[[0, "rgba(125,160,200,.28)"], [0.5, CYAN], [1, ORANGE]]),
        dimensions=[dict(label=lbl, values=ok[k]) for k, lbl, _ in MV], labelangle=-20,
        labelfont=dict(family=FONT_HEAD, color="#ffffff", size=12), tickfont=dict(family=FONT_BODY, color=ICE, size=9), rangefont=dict(family=FONT_BODY, color=ICE, size=9)))
    apply_theme(fig, title=_title("Koordinat Paralel: tiap garis = satu provinsi (jingga = tersorot)"), margin=dict(t=100, l=40, r=40, b=70))
    return add_source(fig, "mv", shift=56)


def build_heat(year: int) -> go.Figure:
    m = mv_model(year); ok = m["ok"]; X = m["X"]
    order = leaves_list(linkage(X, "ward"))
    fig = go.Figure(go.Heatmap(z=X[order], x=[lbl for _, lbl, _ in MV], y=ok["Provinsi"].iloc[order].tolist(), zmin=-2.5, zmax=2.5,
                               xgap=2, ygap=2, colorscale=[[0, CYAN], [0.5, "#0b1630"], [1, ORANGE]],
                               colorbar=cbar("z-skor", len=0.85),
                               hovertemplate="<b>%{y}</b><br>%{x}: z=%{z:.2f}<extra></extra>"))
    fig.update_yaxes(type="category", autorange="reversed", dtick=1, tickfont=dict(size=9), automargin=True)
    fig.update_xaxes(tickfont=dict(size=10), side="bottom")
    apply_theme(fig, title=_title("Heatmap terklaster: cyan = di bawah rata-rata, jingga = di atas (z-skor)"),
                margin=dict(t=48, l=10, r=10, b=84))
    return add_source(fig, "mv", shift=66)


# ----------------------------------------------------------------------------
# 3c. CERITA DATA (webstory) + DAFTAR SUMBER
# ----------------------------------------------------------------------------
# Halaman SUMBER (zz-extra.js) membaca daftar ini BERDASARKAN URUTAN (indeks 0..3), jadi tetap berupa list, bukan dict.
# Kosong ("") = tampil merah "BELUM DIISI". "-" = tidak berlaku.
# Soal UAS poin 2b: judul tabel, tahun, URL, tanggal akses wajib dicantumkan untuk tiap data BPS.
SOURCES = [
    dict(phrase="Ke mana uang rumah tangga pergi?",
         judul="Rata-rata Pengeluaran per Kapita Sebulan Menurut Kelompok Komoditas (Rupiah)",
         tahun="2024 dan 2025",
         url="https://www.bps.go.id/id/statistics-table/3/VTJaSFFtWklXVnBYZVdSREwyczJlbm93UWpVM1FUMDkjMw==/rata-rata-pengeluaran-per-kapita-sebulan-menurut-kelompok-komoditas-dan-klasifikasi-desa--rupiah---2023.html?year=2025",
         akses="4 Oktober 2026", satuan="Rupiah (Rp)",
         dipakai="Treemap/Sunburst hierarki (ukuran: pengeluaran 2025; warna: pertumbuhan nominal 2024-2025)",
         file="Pengeluaran_Hierarki_2024_Cleaned.xlsx; Pengeluaran_Hierarki_2025_Cleaned.xlsx",
         catatan="Pertumbuhan bersifat nominal (belum dikoreksi inflasi)."),
    dict(phrase="Di mana kemiskinan menumpuk?",
         judul="Persentase Penduduk Miskin (P0) Menurut Kabupaten/Kota",
         tahun="2025",
         url="https://www.bps.go.id/id/statistics-table/2/NjIxIzI=/persentase-penduduk-miskin-menurut-kabupaten-kota.html",
         akses="4 Oktober 2026", satuan="Persen (%)",
         dipakai="Choropleth (%) dan peta simbol proporsional, 509 kabupaten/kota", file="Kemiskinan_KabKota_2025_Cleaned.xlsx",
         catatan="Batas wilayah (non-BPS): indonesia_kabkota.geojson, bersumber dari https://github.com/ardian28/GeoJson-Indonesia-38-Provinsi/tree/main/Kabupaten (diakses 4 Oktober 2026)."),
    dict(phrase="Sekolah, kerja, dan umur panjang",
         judul="Indikator Makro Sosial Ekonomi (8 Variabel Multivariat)",
         tahun="2023–2025",
         url=("Berasal dari 8 tabel BPS berbeda:\n"
              "1. TPT: https://www.bps.go.id/id/statistics-table/2/NTQzIzI=/tingkat-pengangguran-terbuka-menurut-provinsi.html\n"
              "2. IPM: https://www.bps.go.id/id/statistics-table/3/V25GaFNHaExaMnhITm1sWmRrUlJZelJzYUc1SGR6MDkjMw==/indeks-pembangunan-manusia-menurut-provinsi--2022.html?year=2025\n"
              "3. Penduduk Miskin: https://www.bps.go.id/id/statistics-table/3/UkVkWGJVZFNWakl6VWxKVFQwWjVWeTlSZDNabVFUMDkjMw==/jumlah-dan-persentase-penduduk-miskin-menurut-provinsi--2023.html?year=2025\n"
              "4. RLS: https://www.bps.go.id/id/statistics-table/2/NDE1IzI=/-metode-baru--rata-rata-lama-sekolah.html\n"
              "5. HLS: https://www.bps.go.id/id/statistics-table/2/NDE3IzI=/-metode-baru--harapan-lama-sekolah--tahun-.html\n"
              "6. UHH: https://www.bps.go.id/id/statistics-table/2/MjIwNiMy/-metode-baru--umur-harapan-hidup-saat-lahir--uhh--hasil-long-form-sp2020.html\n"
              "7. Pengeluaran: https://www.bps.go.id/id/statistics-table/2/NDE2IzI=/-metode-baru--pengeluaran-per-kapita-disesuaikan.html\n"
              "8. Gini Ratio: https://www.bps.go.id/id/statistics-table/2/OTgjMg==/gini-ratio-menurut-provinsi-dan-daerah.html"),
         akses="4 Oktober 2026", satuan="Beragam (Indeks, Persen, Tahun, Rupiah)",
         dipakai="PCA, k-means, SPLOM, koordinat paralel, heatmap terklaster; 8 variabel x 38 provinsi",
         file="Dataset_Multivariat_LENGKAP_8_Variabel.xlsx",
         catatan="IPM, Kemiskinan, TPT, RLS, HLS, UHH, Pengeluaran, Gini. Empat provinsi Papua baru tanpa data 2023."),
]


def _fmt(v: float, d: int = 1) -> str:
    return f"{v:.{d}f}".replace(".", ",")


def _sg(v: float) -> str:
    return f"{v:+.1f}".replace(".", ",")


def _li(*items: str) -> str:
    return "<ol>" + "".join(f"<li>{i}</li>" for i in items) + "</ol>"


def story_belanja() -> str:
    v25, v24 = _node_values(df_exp), _node_values(df_exp24)
    root = df_exp["Level 1"].iloc[0]
    g = lambda k: 100 * (v25[k] / v24[k] - 1)  # noqa: E731
    leaves = sorted([k for k in v25 if k.count("/") == 2], key=g)
    nm = lambda k: k.split("/")[-1]  # noqa: E731
    share = 100 * v25[f"{root}/Makanan"] / v25[root]
    return "<h4>CERITA: KE MANA UANG PERGI?</h4>" + _li(
        f"Makanan menyerap <b>{_fmt(share)}%</b> pengeluaran 2025; bukan makanan {_fmt(100 - share)}%.",
        f"Total tumbuh <b>{_sg(g(root))}%</b> (nominal): bukan makanan {_sg(g(f'{root}/Bukan Makanan'))}% vs makanan {_sg(g(f'{root}/Makanan'))}%.",
        f"Naik tertinggi: <b>{nm(leaves[-1])}</b> ({_sg(g(leaves[-1]))}%); turun: <b>{nm(leaves[0])}</b> ({_sg(g(leaves[0]))}%).")


def story_peta() -> str:
    d = df_kab.sort_values("Kemiskinan_2025", ascending=False)
    v = d["Kemiskinan_2025"]; t = d.head(3)
    ge = int((v >= 15).sum())
    return _li(
        f"Median kemiskinan {len(d)} kab/kota: <b>{_fmt(v.median())}%</b> (rentang {_fmt(v.min())}% sampai {_fmt(v.max())}%).",
        f"Tertinggi: <b>{t.iloc[0]['Wilayah']}</b> ({_fmt(t.iloc[0]['Kemiskinan_2025'])}%), {t.iloc[1]['Wilayah']} ({_fmt(t.iloc[1]['Kemiskinan_2025'])}%), "
        f"{t.iloc[2]['Wilayah']} ({_fmt(t.iloc[2]['Kemiskinan_2025'])}%).",
        f"<b>{ge}</b> kab/kota ({_fmt(100 * ge / len(d), 0)}%) di atas 15%. Coba peta simbol untuk membandingkan besarannya.")


def mv_story(view: str, year: int) -> str:
    m = mv_model(year); ok = m["ok"]; load = m["load"]; ev = m["evr"] * 100
    corr = ok[MV_KEYS].corr()
    if view == "pca":
        l1 = sorted(zip(load[:, 0], MV_KEYS), key=lambda t: -abs(t[0]))[:3]
        l2 = sorted(zip(load[:, 1], MV_KEYS), key=lambda t: -abs(t[0]))[:2]
        ipm = load[MV_KEYS.index("IPM"), 0]
        txt = (f"Cara baca: titik = provinsi, panah = arah variabel. PC1 ({_fmt(ev[0])}%) didominasi {', '.join(f'{k} ({v:+.2f})' for v, k in l1)}"
               + (f": makin ke {'kanan' if ipm > 0 else 'kiri'}, makin tinggi pembangunan manusia. " if "IPM" in [k for _, k in l1] else ". ")
               + f"PC2 ({_fmt(ev[1])}%) didominasi {', '.join(f'{k} ({v:+.2f})' for v, k in l2)}"
               + (" (ketimpangan, berdiri sendiri dari PC1). " if l2[0][1] == "Gini" else ". "))
        txt += "Klaster: " + ", ".join(f"{CL_NAME[i]} {int((m['lab'] == i).sum())}" for i in range(3)) + f". Pencilan: {', '.join(m['out']) or 'tidak ada'}."
    elif view == "splom":
        pairs = sorted(((corr.iloc[i, j], MV_KEYS[i], MV_KEYS[j]) for i in range(8) for j in range(i)), key=lambda t: -abs(t[0]))[:3]
        gmax = corr["Gini"].drop("Gini").abs().max()
        txt = (f"Cara baca: tiap sel membandingkan dua variabel; warna = klaster. Terkuat: {'; '.join(f'{a}-{b} (r={r:+.2f})' for r, a, b in pairs)}. "
               f"TPT-RLS r={corr.loc['TPT', 'RLS']:+.2f}: daerah lebih terdidik tidak otomatis lebih rendah penganggurannya. "
               f"Gini nyaris terpisah dari yang lain (|r| maks {gmax:.2f}).")
    elif view == "parcoords":
        s = ok.sort_values("IPM"); lo = s.head(2); hi = s.iloc[-1]
        cap = ["IPM", "RLS", "HLS", "UHH", "Pengeluaran"]; med = ok[cap].median()
        cnt = [int((r[cap] < med).sum()) for _, r in lo.iterrows()]
        txt = (f"Cara baca: tiap garis = satu provinsi; sorot di PCA/SPLOM untuk melihat garis jingga. IPM terendah: {lo.iloc[0]['Provinsi']} ({_fmt(lo.iloc[0]['IPM'])}) dan "
               f"{lo.iloc[1]['Provinsi']} ({_fmt(lo.iloc[1]['IPM'])}), di bawah median pada {cnt[0]}/5 dan {cnt[1]}/5 indikator capaian. Tertinggi: {hi['Provinsi']} ({_fmt(hi['IPM'])}).")
    else:
        order = leaves_list(linkage(m["X"], "ward")); names = ok["Provinsi"].iloc[order].tolist()
        gmax = corr["Gini"].drop("Gini").abs().max()
        txt = (f"Cara baca: tiap baris provinsi, jingga = di atas rata-rata, cyan = di bawah. Baris diurut klaster hierarkis (Ward): ujung atas {', '.join(names[:3])}; "
               f"ujung bawah {', '.join(names[-3:])}. Kolom Gini {'tidak ' if gmax < 0.35 else ''}membentuk blok warna yang sama dengan indikator lain (|r| maks {gmax:.2f}).")
    return re.sub(r"(?<=\d)\.(?=\d)", ",", txt)   # desimal ala Indonesia


# ----------------------------------------------------------------------------
# 4. LAYOUT: cangkang HTML/CSS/JS dari zip (p3_shell.html + assets/p3), grafik Dash ditempatkan oleh JS
# ----------------------------------------------------------------------------
import json  # noqa: E402

_ASSETS = BASE_DIR / "public" / "assets"
if not _ASSETS.exists():
    _ASSETS = BASE_DIR / "assets"

app = Dash(
    __name__,
    assets_folder=str(_ASSETS),
)
app.title = "Lensa Kesenjangan"
server = app.server  # untuk deployment (gunicorn app:server)


def build_p3data() -> dict:
    """Rata-rata nasional per tahun untuk batang statistik halaman KORELASI (NaN diabaikan, df tak diubah)."""
    spec = [("Indeks Pembangunan Manusia", "IPM_{y}", 100, "IPM", 1), ("Rata-rata Lama Sekolah", "RLS_{y}", 15, "THN", 2),
            ("Harapan Lama Sekolah", "HLS_{y}", 20, "THN", 2), ("Umur Harapan Hidup", "UHH_{y}", 85, "THN", 1),
            ("Pengangguran Terbuka (TPT)", "TPT_Agustus_{y}", 10, "%", 2), ("Tingkat Kemiskinan", "Kemiskinan_Maret_{y}", 20, "%", 2),
            ("Pengeluaran/Kapita (ribu Rp)", "Pengeluaran_{y}", 20000, "RIBU", 0), ("Rasio Gini", "Gini_{y}", 0.5, "GINI", 3)]
    years = {}
    for y in YEARS:
        rows = []
        for name, tmpl, mx, unit, dec in spec:
            m = float(df_multi[tmpl.format(y=y)].mean())
            rows.append({"name": name, "level": int(round(min(m / mx * 100, 100))),
                         "label": f"{m:.{dec}f}".replace(".", ","), "unit": unit})
        years[str(y)] = rows
    return {"years": years, "stories": {"belanja": story_belanja(), "peta": story_peta()}}


def fit(fig: go.Figure) -> go.Figure:
    """Biarkan grafik mengikuti ukuran slot (tinggi diatur CSS)."""
    fig.update_layout(height=None, autosize=True)
    return fig


SHELL = (BASE_DIR / "p3_shell.html").read_text(encoding="utf-8")
# <style> kecil di <head>: nilai sumber yang berisi banyak baris/URL panjang (halaman SUMBER) harus turun baris dan tidak meluber.
SRC_CSS = "<style>.p3-src-row>span:last-child{white-space:pre-line;overflow-wrap:anywhere;min-width:0}</style>"
app.index_string = (
    '<!DOCTYPE html><html lang="id"><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}' + SRC_CSS + '</head><body>'
    + SHELL.replace("__APP_ENTRY__", "{%app_entry%}")
    + "<script>window.P3DATA=" + json.dumps(build_p3data()).replace("</", "<\\/") + ";window.P3SOURCES=" + json.dumps(SOURCES).replace("</", "<\\/") + ";</script>"
    + "<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>"
)

GRAPH_CONFIG = {"displaylogo": False, "responsive": True}
FILL = {"flex": "1", "minHeight": 0, "height": "100%"}


def radio(rid, options, value):
    return dcc.RadioItems(id=rid, options=options, value=value, inline=True, className="p3-radio")


app.layout = html.Div(
    [
        dcc.Store(id="year-store", data=DEFAULT_YEAR),   # diubah oleh tab tahun di halaman KORELASI
        dcc.Store(id="sel-prov", data=[]),               # provinsi tersorot (brushing & linking antar tampilan)
        # --- BELANJA: hierarki, 2 representasi + penunjuk posisi ---
        html.Div(id="wrap-treemap", className="p3-wrap", children=[
            radio("hier-kind", [{"label": "Treemap", "value": "treemap"}, {"label": "Sunburst", "value": "sunburst"}], "treemap"),
            html.Div("Posisi: klik sebuah kotak/irisan untuk menelusuri", id="hier-crumb", className="p3-note"),
            dcc.Graph(id="treemap", figure=fit(build_hier("treemap")), config=GRAPH_CONFIG, style=FILL),
        ]),
        # --- PETA: choropleth & simbol proporsional ---
        html.Div(id="wrap-map", className="p3-wrap", children=[
            radio("map-kind", [{"label": "Choropleth (%)", "value": "choropleth"}, {"label": "Simbol proporsional", "value": "bubble"}], "choropleth"),
            html.Div(GEO_STATUS, id="geo-status", className="p3-note"),
            dcc.Loading(type="circle", color="#16cffb", parent_style={"flex": "1", "minHeight": 0},
                        children=dcc.Graph(id="choropleth", figure=fit(build_map("choropleth")), config=GRAPH_CONFIG, style=FILL)),
        ]),
        # --- KORELASI: 4 tampilan multivariat, satu per satu (besar), seleksi tetap terhubung ---
        html.Div(id="wrap-splom", className="p3-wrap", children=[
            radio("mv-view", [{"label": "PCA", "value": "pca"}, {"label": "SPLOM", "value": "splom"},
                              {"label": "Paralel", "value": "parcoords"}, {"label": "Heatmap", "value": "heat"}], "pca"),
            html.Div(id="splom-vars-box", style={"display": "none"}, children=[
                html.Span("Variabel SPLOM:", className="p3-lbl"),
                dcc.Checklist(id="splom-vars", options=[{"label": k, "value": k} for k in MV_KEYS], value=SPLOM_DEFAULT,
                              inline=True, className="p3-radio")]),
            html.Div(id="splom-note", className="p3-note"),
            html.Div(className="p3-stack", children=[
                html.Div(id=f"v-{k}", className="p3-view" + (" active" if k == "pca" else ""),
                         children=dcc.Graph(id=k, config=GRAPH_CONFIG, style=FILL))
                for k in ["splom", "pca", "parcoords", "heat"]]),
            html.Div(className="p3-foot", children=[
                html.Div(id="selected-provinces", className="p3-note"),
                html.Button("Hapus sorotan", id="clear-sel", className="p3-clear", n_clicks=0)]),
        ]),
    ]
)


# ----------------------------------------------------------------------------
# 5. CALLBACK
# ----------------------------------------------------------------------------
@app.callback(Output("treemap", "figure"), Input("hier-kind", "value"))
def update_hier(kind):
    return fit(build_hier(kind))


@app.callback(Output("hier-crumb", "children"), Input("treemap", "clickData"), prevent_initial_call=True)
def update_crumb(click):
    pid = ((click or {}).get("points") or [{}])[0].get("id")
    return "Posisi: " + " › ".join(str(pid).split("/")) if pid else no_update


@app.callback(Output("choropleth", "figure"), Input("map-kind", "value"))
def update_map(kind):
    return fit(build_map(kind))


@app.callback(Output("pca", "figure"), Output("heat", "figure"), Output("sel-prov", "data"), Input("year-store", "data"))
def update_views(year):
    y = int(year or DEFAULT_YEAR)
    return fit(build_pca(y)), fit(build_heat(y)), []


@app.callback(Output("splom-note", "children"), Input("mv-view", "value"), Input("year-store", "data"))
def update_story(view, year):
    return mv_story(view, int(year or DEFAULT_YEAR))


@app.callback(Output("splom", "figure"), Input("year-store", "data"), Input("splom-vars", "value"))
def update_splom(year, keys):
    return fit(build_splom8(int(year or DEFAULT_YEAR), keys))


@app.callback(
    Output("v-splom", "className"), Output("v-pca", "className"), Output("v-parcoords", "className"), Output("v-heat", "className"),
    Output("splom-vars-box", "style"), Input("mv-view", "value"),
)
def switch_view(view):
    cls = lambda k: "p3-view active" if k == view else "p3-view"  # noqa: E731
    return cls("splom"), cls("pca"), cls("parcoords"), cls("heat"), ({} if view == "splom" else {"display": "none"})


@app.callback(
    Output("sel-prov", "data", allow_duplicate=True),
    Input("splom", "selectedData"), Input("pca", "selectedData"), Input("clear-sel", "n_clicks"),
    State("year-store", "data"), prevent_initial_call=True,
)
def link_selection(sp, pc, _clear, year):
    """Sumber seleksi (SPLOM atau PCA) -> daftar nama provinsi bersama; tombol hapus mengosongkannya."""
    y = int(year or DEFAULT_YEAR)
    if ctx.triggered_id == "clear-sel":
        return []
    if ctx.triggered_id == "pca":
        names = [p["customdata"] for p in (pc or {}).get("points", []) if "customdata" in p]
    else:
        idx = sorted({p["pointNumber"] for p in (sp or {}).get("points", []) if "pointNumber" in p})
        names = mv_model(y)["d"]["Provinsi"].iloc[idx].tolist()
    return sorted(set(names))


@app.callback(Output("parcoords", "figure"), Input("sel-prov", "data"), Input("year-store", "data"))
def update_parcoords(sel, year):
    return fit(build_parcoords(int(year or DEFAULT_YEAR), sel))


@app.callback(
    Output("splom", "figure", allow_duplicate=True), Output("pca", "figure", allow_duplicate=True),
    Input("sel-prov", "data"), State("year-store", "data"), prevent_initial_call=True,
)
def highlight_views(sel, year):
    """Brushing & linking: sorot provinsi yang sama di SPLOM dan PCA (selectedpoints)."""
    y = int(year or DEFAULT_YEAR); m = mv_model(y); s = set(sel or [])
    sp, pc = Patch(), Patch()
    sp["data"][0]["selectedpoints"] = [i for i, n in enumerate(m["d"]["Provinsi"]) if n in s] if s else None
    for c in range(3):
        names = m["ok"]["Provinsi"][m["lab"] == c].tolist()
        pc["data"][c]["selectedpoints"] = [i for i, n in enumerate(names) if n in s] if s else None
    return sp, pc


@app.callback(Output("selected-provinces", "children"), Input("sel-prov", "data"))
def show_selected(sel):
    if not sel:
        return "Tarik kotak seleksi pada SPLOM atau PCA: provinsi yang sama tersorot di keempat tampilan."
    return f"Provinsi tersorot ({len(sel)}): {', '.join(sel)}"


if __name__ == "__main__":
    app.run(debug=False)