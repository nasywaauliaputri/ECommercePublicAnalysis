import streamlit as st
import pandas as pd
import plotly.express as px

# =====================
# CONFIG
# =====================
ORANGE = "#FFA500"
YELLOW = "#FFD700"

st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")

# =====================
# LOAD & CLEAN DATA
# =====================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("Dashboard/cleaned_merged_data.csv")
    except FileNotFoundError:
        st.error("File cleaned_merged_data.csv tidak ditemukan!")
        st.stop()

    # =====================
    # VALIDASI KOLOM
    # =====================
    required_cols = [
        'order_id','customer_id','order_purchase_timestamp',
        'order_delivered_customer_date','order_estimated_delivery_date',
        'payment_type','payment_value'
    ]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"Kolom tidak ditemukan: {missing}")
        st.stop()

    # =====================
    # DATETIME SAFE PARSE
    # =====================
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')
    df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'], errors='coerce')
    df['order_estimated_delivery_date'] = pd.to_datetime(df['order_estimated_delivery_date'], errors='coerce')

    # =====================
    # DROP DATA KRUSIAL NULL
    # =====================
    df = df.dropna(subset=['order_purchase_timestamp'])

    # =====================
    # FIX DUPLIKASI ORDER (MULTI PAYMENT)
    # =====================
    df = df.groupby(['order_id', 'customer_id'], as_index=False).agg({
        'order_purchase_timestamp': 'first',
        'order_delivered_customer_date': 'first',
        'order_estimated_delivery_date': 'first',
        'payment_value': 'sum',
        'payment_type': 'first'
    })

    # =====================
    # FEATURE ENGINEERING
    # =====================
    df['year'] = df['order_purchase_timestamp'].dt.year
    df['month'] = df['order_purchase_timestamp'].dt.to_period('M')

    return df

df = load_data()

# =====================
# SIDEBAR
# =====================
st.sidebar.title("Filter Data")

year_filter = st.sidebar.multiselect(
    "Pilih Tahun",
    options=sorted(df['year'].dropna().unique()),
    default=sorted(df['year'].dropna().unique())
)

st.sidebar.markdown("### ℹ️ Info")
st.sidebar.info("Dashboard by Nasywa Aulia Putri 🚀")

data = df[df['year'].isin(year_filter)].copy()

if data.empty:
    st.warning("Tidak ada data untuk filter yang dipilih")
    st.stop()

# =====================
# TITLE
# =====================
st.title("📊 E-Commerce Advanced Dashboard")

# =====================================================
# 1. TREND ORDER
# =====================================================
st.header("📦 1. Tren Jumlah Pesanan")

trend = data.groupby('month')['order_id'].nunique().reset_index()
trend.columns = ['month', 'total_orders']
trend['month'] = trend['month'].astype(str)

fig1 = px.line(trend, x='month', y='total_orders', markers=True)
fig1.update_traces(line=dict(color=ORANGE, width=3))

st.plotly_chart(fig1, use_container_width=True)

# =====================================================
# 2. PAYMENT ANALYSIS
# =====================================================
st.header("💳 2. Metode Pembayaran")

payment = data.groupby('payment_type').agg({
    'order_id': 'count',
    'payment_value': 'sum'
}).reset_index()

col1, col2 = st.columns(2)

with col1:
    fig2 = px.bar(payment, x='payment_type', y='payment_value', color='payment_type')
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    fig3 = px.bar(payment, x='payment_type', y='order_id', color='payment_type')
    st.plotly_chart(fig3, use_container_width=True)

# =====================================================
# 3. DELIVERY PERFORMANCE
# =====================================================
st.header("🚚 3. Kinerja Pengiriman")

data['delivery_time'] = (
    data['order_delivered_customer_date'] -
    data['order_purchase_timestamp']
).dt.days

data['delay'] = (
    data['order_delivered_customer_date'] -
    data['order_estimated_delivery_date']
).dt.days

data['is_late'] = data['delay'] > 0

def safe_mean(series):
    return round(series.mean(), 2) if not series.dropna().empty else 0

col3, col4, col5 = st.columns(3)

col3.metric("Rata-rata Delivery Time", safe_mean(data['delivery_time']))
col4.metric("Rata-rata Delay", safe_mean(data['delay']))
col5.metric("Tingkat Keterlambatan (%)", safe_mean(data['is_late']) * 100)

# histogram aman
data_hist = data.dropna(subset=['delivery_time'])

fig4 = px.histogram(data_hist, x='delivery_time', nbins=30, color_discrete_sequence=[YELLOW])
st.plotly_chart(fig4, use_container_width=True)

# =====================================================
# 4. RFM ANALYSIS
# =====================================================
st.header("📊 4. RFM Analysis")

snapshot_date = data['order_purchase_timestamp'].max()

rfm = data.groupby('customer_id').agg({
    'order_purchase_timestamp': lambda x: (snapshot_date - x.max()).days,
    'order_id': 'count',
    'payment_value': 'sum'
})

rfm.columns = ['Recency', 'Frequency', 'Monetary']

if rfm.shape[0] < 4:
    st.warning("Data terlalu sedikit untuk RFM analysis")
else:
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4,3,2,1], duplicates='drop')
    rfm['F_Score'] = pd.qcut(rfm['Frequency'], 4, labels=[1,2,3,4], duplicates='drop')
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1,2,3,4], duplicates='drop')

    rfm['Segment'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str)

    st.dataframe(rfm.head())

    fig5 = px.bar(rfm['Segment'].value_counts().head(10))
    fig5.update_traces(marker_color=ORANGE)

    st.plotly_chart(fig5, use_container_width=True)

# =====================================================
# 5. DELAY SEGMENTATION
# =====================================================
st.header("⏱ 5. Segmentasi Delay")

data['delay_segment'] = pd.cut(
    data['delay'],
    bins=[-999, 0, 5, 10, 50],
    labels=['Early/On Time', 'Slight Delay', 'Moderate Delay', 'Severe Delay']
)

fig6 = px.bar(data['delay_segment'].value_counts())
fig6.update_traces(marker_color=YELLOW)

st.plotly_chart(fig6, use_container_width=True)

# =====================================================
# 6. CUSTOMER INSIGHT
# =====================================================
st.header("👥 6. Customer Insight")

top_customers = data.groupby('customer_id')['payment_value'].sum().sort_values(ascending=False).head(10)

fig7 = px.bar(top_customers)
fig7.update_traces(marker_color=ORANGE)

st.plotly_chart(fig7, use_container_width=True)
