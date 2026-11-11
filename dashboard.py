from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
MAIN_DATA = BASE_DIR / "main_data.csv"
RAW_DATA = BASE_DIR.parent / "data" / "day.csv"

WEATHER_ORDER = ["Cerah", "Berkabut", "Hujan/Salju Ringan"]
SEASON_ORDER = ["Spring", "Summer", "Fall", "Winter"]
DEMAND_ORDER = ["Rendah", "Sedang", "Tinggi"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

# warna sama seperti di notebook: biru = fokus, merah = terendah, abu-abu = lainnya
BLUE, GREY, RED = "#1f77b4", "#b0b0b0", "#d62728"


# ---------------------------------------------------------------- data
def prepare_data(raw_path: Path) -> pd.DataFrame:
    """Cleaning yang sama dengan notebook: label kategori, tipe datetime, perbaikan hum = 0."""
    df = pd.read_csv(raw_path)

    df["dteday"] = pd.to_datetime(df["dteday"])
    df["season"] = df["season"].map({1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"})
    df["yr"] = df["yr"].map({0: 2011, 1: 2012})
    df["weathersit"] = df["weathersit"].map(
        {1: "Cerah", 2: "Berkabut", 3: "Hujan/Salju Ringan"}
    )
    df["weekday"] = df["weekday"].map(
        {0: "Minggu", 1: "Senin", 2: "Selasa", 3: "Rabu", 4: "Kamis", 5: "Jumat", 6: "Sabtu"}
    )

    # hum = 0 tidak valid -> ganti dengan median hum pada kondisi cuaca yang sama
    for idx in df[df["hum"] == 0].index:
        cuaca = df.loc[idx, "weathersit"]
        df.loc[idx, "hum"] = df.loc[(df["weathersit"] == cuaca) & (df["hum"] > 0), "hum"].median()

    return df


@st.cache_data
def load_data() -> pd.DataFrame:
    if not MAIN_DATA.exists():
        if not RAW_DATA.exists():
            st.error("File data tidak ditemukan. Pastikan dashboard/main_data.csv atau data/day.csv ada.")
            st.stop()
        prepare_data(RAW_DATA).to_csv(MAIN_DATA, index=False)

    return pd.read_csv(MAIN_DATA, parse_dates=["dteday"])


# ---------------------------------------------------------------- helpers
def fmt(x: float) -> str:
    """Format angka gaya Indonesia: 4.877"""
    return f"{x:,.0f}".replace(",", ".")


def show(fig: go.Figure) -> None:
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:  # versi streamlit lama
        st.plotly_chart(fig, use_container_width=True)


def finish(fig: go.Figure, xtitle: str, ytitle: str) -> go.Figure:
    fig.update_layout(
        xaxis_title=xtitle,
        yaxis_title=ytitle,
        showlegend=False,
        height=420,
        margin=dict(t=30, b=40, l=10, r=10),
    )
    return fig


def stacked_bar(ct: pd.DataFrame, colors: dict) -> go.Figure:
    fig = go.Figure()
    for k in ct.columns:
        fig.add_trace(
            go.Bar(
                name=k,
                x=list(ct.index),
                y=ct[k],
                marker_color=colors[k],
                text=[f"{v:.0f}%" if v >= 6 else "" for v in ct[k]],
                textposition="inside",
                hovertemplate=f"{k}: " + "%{y:.1f}%<extra></extra>",
            )
        )
    finish(fig, "Tingkat Permintaan Harian", "Persentase Hari (%)")
    fig.update_layout(barmode="stack", showlegend=True, legend=dict(orientation="h", y=1.15, title_text=""))
    fig.update_yaxes(range=[0, 100])
    return fig


# ---------------------------------------------------------------- page
st.set_page_config(page_title="Bike Sharing Dashboard", page_icon="🚲", layout="wide")

df = load_data()

st.title("🚲 Bike Sharing Dashboard")
st.caption("Capital Bikeshare, Washington D.C. · data penyewaan sepeda harian 2011-2012")

# ---- sidebar filter
with st.sidebar:
    st.header("Filter Data")

    tgl_min, tgl_max = df["dteday"].min().date(), df["dteday"].max().date()
    rentang = st.date_input(
        "Rentang tanggal", value=(tgl_min, tgl_max), min_value=tgl_min, max_value=tgl_max
    )
    musim_pilih = st.multiselect("Musim", SEASON_ORDER, default=SEASON_ORDER)
    cuaca_pilih = st.multiselect("Kondisi cuaca", WEATHER_ORDER, default=WEATHER_ORDER)

# date_input mengembalikan 1 tanggal saat user baru memilih tanggal awal
if isinstance(rentang, (tuple, list)) and len(rentang) == 2:
    awal, akhir = rentang
else:
    awal, akhir = tgl_min, tgl_max

df_f = df[
    (df["dteday"].dt.date >= awal)
    & (df["dteday"].dt.date <= akhir)
    & (df["season"].isin(musim_pilih))
    & (df["weathersit"].isin(cuaca_pilih))
]

if df_f.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Ubah filter di sidebar.")
    st.stop()

# ---- ringkasan
m1, m2, m3 = st.columns(3)
m1.metric("Jumlah hari", fmt(len(df_f)))
m2.metric("Rata-rata penyewaan per hari", fmt(df_f["cnt"].mean()))
m3.metric("Total penyewaan", fmt(df_f["cnt"].sum()))

tab1, tab2, tab3, tab4 = st.tabs(
    ["Pertanyaan 1: Cuaca", "Pertanyaan 2: Musim", "Tren Bulanan", "Analisis Lanjutan"]
)

# ---- Pertanyaan 1
with tab1:
    st.subheader("Seberapa besar penurunan penyewaan saat cuaca buruk?")
    st.write(
        "Rata-rata penyewaan harian pada cuaca berkabut dan hujan/salju ringan "
        "dibandingkan dengan cuaca cerah."
    )

    cuaca = (
        df_f.groupby("weathersit")["cnt"]
        .agg(jumlah_hari="count", rata_rata="mean")
        .reindex(WEATHER_ORDER)
        .dropna()
    )
    has_baseline = "Cerah" in cuaca.index

    if has_baseline:
        base = cuaca.loc["Cerah", "rata_rata"]
        cuaca["selisih"] = (cuaca["rata_rata"] / base - 1) * 100

        for col, (k, row) in zip(st.columns(len(cuaca)), cuaca.iterrows()):
            if k == "Cerah":
                col.metric("Cerah (pembanding)", fmt(row["rata_rata"]))
            else:
                col.metric(k, fmt(row["rata_rata"]), f"{row['selisih']:.0f}% dari cuaca cerah")
    else:
        st.info("Sertakan cuaca Cerah dan minimal satu kondisi lain agar perbandingan bisa dihitung.")

    labels = [
        fmt(v) if (not has_baseline or k == "Cerah") else f"{fmt(v)}<br>({cuaca.loc[k, 'selisih']:.0f}%)"
        for k, v in cuaca["rata_rata"].items()
    ]
    fig = go.Figure(
        go.Bar(
            x=cuaca.index,
            y=cuaca["rata_rata"],
            marker_color=[BLUE if k == "Cerah" else GREY for k in cuaca.index],
            text=labels,
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{x}<br>Rata-rata: %{y:,.0f} per hari<extra></extra>",
        )
    )
    finish(fig, "Kondisi Cuaca", "Rata-rata Penyewaan per Hari")
    fig.update_yaxes(range=[0, cuaca["rata_rata"].max() * 1.25])
    show(fig)

    kecil = cuaca[cuaca["jumlah_hari"] < 30]
    if not kecil.empty:
        st.caption(
            "Jumlah hari sedikit pada "
            + ", ".join(f"{k} ({int(v)} hari)" for k, v in kecil["jumlah_hari"].items())
            + ", sehingga angkanya perlu dibaca dengan hati-hati."
        )

# ---- Pertanyaan 2
with tab2:
    st.subheader("Musim apa yang paling ramai dan paling sepi?")
    st.write("Rata-rata penyewaan harian pada tiap musim beserta selisih antara yang tertinggi dan terendah.")

    musim = (
        df_f.groupby("season")["cnt"]
        .agg(jumlah_hari="count", rata_rata="mean")
        .reindex(SEASON_ORDER)
        .dropna()
    )

    if len(musim) >= 2:
        tertinggi, terendah = musim["rata_rata"].idxmax(), musim["rata_rata"].idxmin()
        hi, lo = musim.loc[tertinggi, "rata_rata"], musim.loc[terendah, "rata_rata"]
        warna = [BLUE if k == tertinggi else RED if k == terendah else GREY for k in musim.index]

        c1, c2, c3 = st.columns(3)
        c1.metric(f"Tertinggi: {tertinggi}", fmt(hi))
        c2.metric(f"Terendah: {terendah}", fmt(lo))
        c3.metric("Selisih", fmt(hi - lo), f"{tertinggi} ±{hi / lo:.1f}× {terendah}", delta_color="off")
    else:
        warna = [BLUE] * len(musim)
        st.info("Pilih minimal dua musim agar perbandingan bisa dihitung.")

    fig = go.Figure(
        go.Bar(
            x=musim.index,
            y=musim["rata_rata"],
            marker_color=warna,
            text=[fmt(v) for v in musim["rata_rata"]],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{x}<br>Rata-rata: %{y:,.0f} per hari<extra></extra>",
        )
    )
    finish(fig, "Musim", "Rata-rata Penyewaan per Hari")
    fig.update_yaxes(range=[0, musim["rata_rata"].max() * 1.2])
    show(fig)

# ---- Tren bulanan
with tab3:
    st.subheader("Tren rata-rata penyewaan harian per bulan")
    st.write("Perbandingan 2011 dan 2012 untuk melihat pola musiman dan pertumbuhan.")

    tren = df_f.groupby(["yr", "mnth"])["cnt"].mean().reset_index()

    fig = go.Figure()
    for tahun, warna_t in zip(sorted(tren["yr"].unique()), [GREY, BLUE]):
        d = tren[tren["yr"] == tahun]
        fig.add_trace(
            go.Scatter(
                x=[MONTHS[m - 1] for m in d["mnth"]],
                y=d["cnt"],
                mode="lines+markers",
                name=str(tahun),
                line=dict(color=warna_t, width=3),
                hovertemplate="%{x} " + str(tahun) + "<br>%{y:,.0f} per hari<extra></extra>",
            )
        )
    finish(fig, "Bulan", "Rata-rata Penyewaan per Hari")
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.15, title_text=""))
    fig.update_xaxes(categoryorder="array", categoryarray=MONTHS)
    show(fig)

# ---- Analisis lanjutan: clustering manual (binning)
with tab4:
    st.subheader("Clustering Manual (Binning) Tingkat Permintaan Harian")
    st.write(
        "Hari dikelompokkan menjadi Rendah, Sedang, dan Tinggi berdasarkan kuartil jumlah penyewaan (cnt), "
        "tanpa algoritma machine learning. Lalu dilihat cuaca dan musim yang dominan pada tiap kelompok."
    )

    # batas kuartil dihitung dari seluruh data (sama seperti notebook), jadi arti kelompok tetap
    q1, q3 = df["cnt"].quantile([0.25, 0.75])
    d = df_f.assign(
        kelompok=pd.cut(df_f["cnt"], bins=[0, q1, q3, df["cnt"].max()], labels=DEMAND_ORDER, include_lowest=True)
    )
    jumlah = d["kelompok"].value_counts().reindex(DEMAND_ORDER).fillna(0).astype(int)

    c1, c2, c3 = st.columns(3)
    c1.metric("Rendah", f"{fmt(jumlah['Rendah'])} hari", f"cnt ≤ {fmt(q1)}", delta_color="off")
    c2.metric("Sedang", f"{fmt(jumlah['Sedang'])} hari", f"cnt {fmt(q1)} - {fmt(q3)}", delta_color="off")
    c3.metric("Tinggi", f"{fmt(jumlah['Tinggi'])} hari", f"cnt > {fmt(q3)}", delta_color="off")

    def komposisi(kolom: str, urutan: list) -> pd.DataFrame:
        ct = pd.crosstab(d["kelompok"], d[kolom], normalize="index").mul(100)
        return ct.reindex(index=DEMAND_ORDER, columns=urutan).fillna(0)

    ct_cuaca = komposisi("weathersit", WEATHER_ORDER)
    ct_musim = komposisi("season", SEASON_ORDER)

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Komposisi cuaca pada tiap tingkat permintaan**")
        show(stacked_bar(ct_cuaca, {"Cerah": BLUE, "Berkabut": GREY, "Hujan/Salju Ringan": RED}))
    with g2:
        st.markdown("**Komposisi musim pada tiap tingkat permintaan**")
        show(stacked_bar(
            ct_musim,
            {"Spring": "#2ca02c", "Summer": "#ffbb33", "Fall": "#ff7f0e", "Winter": "#6baed6"},
        ))

    if jumlah["Rendah"] > 0:
        musim_r = ct_musim.loc["Rendah"].idxmax()
        buruk = ct_cuaca.loc["Rendah", ["Berkabut", "Hujan/Salju Ringan"]].sum()
        st.info(
            f"**Permintaan rendah:** didominasi musim {musim_r} ({ct_musim.loc['Rendah', musim_r]:.0f}%), "
            f"dan {buruk:.0f}% harinya berkabut atau hujan/salju ringan."
        )
    if jumlah["Tinggi"] > 0:
        musim_t = ct_musim.loc["Tinggi"].idxmax()
        st.info(
            f"**Permintaan tinggi:** didominasi musim {musim_t} ({ct_musim.loc['Tinggi', musim_t]:.0f}%), "
            f"dan {ct_cuaca.loc['Tinggi', 'Cerah']:.0f}% harinya bercuaca cerah."
        )
    st.caption("Batas kelompok dihitung dari seluruh data 2011-2012; grafik mengikuti filter di sidebar.")

st.caption("Sumber data: Bike Sharing Dataset (day.csv)")
