import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go

# =====================
# THEME (KUNING-ORANGE)
# =====================
sns.set_theme(style="whitegrid")
ORANGE = "#FFA500"
YELLOW = "#FFD700"

st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .main {
        background-color: #fffaf0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================
# LOAD DATA
# =====================
@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_merged_data.csv")

    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date'])
    df['order_estimated_delivery_date'] = pd.to_datetime(df['order_estimated_delivery_date'])

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
    options=sorted(df['year'].unique()),
    default=sorted(df['year'].unique())
)

data = df[df['year'].isin(year_filter)]

st.title("📊 E-Commerce Advanced Dashboard (Interactive)")

# =====================================================
# 1. TREND ORDER (PLOTLY)
# =====================================================
st.header("📦 1. Tren Jumlah Pesanan (Interactive Plotly)")

trend = data.groupby('month')['order_id'].nunique().reset_index()
trend['month'] = trend['month'].astype(str)

fig = px.line(
    trend,
    x="month",
    y="total_orders",
    title="Tren Order per Bulan",
    markers=True
)
fig.update_traces(line=dict(color=ORANGE, width=3))
fig.update_layout(xaxis_title="Month", yaxis_title="Total Orders")

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# 2. PAYMENT ANALYSIS (PLOTLY)
# =====================================================
st.header("💳 2. Metode Pembayaran (Interactive Plotly)")

payment = data.groupby('payment_type').agg({
    'order_id': 'count',
    'payment_value': 'sum'
}).reset_index()

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(
        payment,
        x='payment_type',
        y='payment_value',
        title="Revenue per Payment Type",
        color='payment_type'
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(
        payment,
        x='payment_type',
        y='order_id',
        title="Transaction Count",
        color='payment_type'
    )
    st.plotly_chart(fig2, use_container_width=True)

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

col3, col4, col5 = st.columns(3)

col3.metric("Rata-rata Delivery Time", round(data['delivery_time'].mean(), 2))
col4.metric("Rata-rata Delay", round(data['delay'].mean(), 2))
col5.metric("Tingkat Keterlambatan (%)", round(data['is_late'].mean() * 100, 2))

fig3 = px.histogram(
    data,
    x="delivery_time",
    nbins=30,
    title="Distribusi Delivery Time",
    color_discrete_sequence=[YELLOW]
)
st.plotly_chart(fig3, use_container_width=True)

# =====================================================
# 4. RFM ANALYSIS (STATIC)
# =====================================================
st.header("📊 4. RFM Analysis")

snapshot_date = data['order_purchase_timestamp'].max()

rfm = data.groupby('customer_id').agg({
    'order_purchase_timestamp': lambda x: (snapshot_date - x.max()).days,
    'order_id': 'count',
    'payment_value': 'sum'
})

rfm.columns = ['Recency', 'Frequency', 'Monetary']

# Mengatasi error qcut
rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1], duplicates='drop')
rfm['F_Score'] = pd.qcut(rfm['Frequency'], 4, labels=[1, 2, 3, 4], duplicates='drop')
rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4], duplicates='drop')

rfm['Segment'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str)

st.dataframe(rfm.head())

fig4 = px.bar(
    rfm['Segment'].value_counts().head(10),
    title="Top RFM Segments",
    labels={'value': 'Count', 'index': 'Segment'}
)
fig4.update_traces(marker_color=ORANGE)
st.plotly_chart(fig4, use_container_width=True)

# =====================================================
# 5. DELAY SEGMENTATION (PLOTLY)
# =====================================================
st.header("⏱ 5. Segmentasi Delay")

data['delay_segment'] = pd.cut(
    data['delay'],
    bins=[-999, 0, 5, 10, 50],
    labels=['Early/On Time', 'Slight Delay', 'Moderate Delay', 'Severe Delay']
)

fig5 = px.bar(
    data['delay_segment'].value_counts(),
    title="Segmentasi Keterlambatan Pengiriman",
    labels={'index': 'Segment', 'value': 'Count'}
)
fig5.update_traces(marker_color=YELLOW)
st.plotly_chart(fig5, use_container_width=True)

# =====================================================
# 6. CUSTOMER INSIGHT (PLOTLY)
# =====================================================
st.header("👥 6. Customer Insight")

top_customers = data.groupby('customer_id')['payment_value'].sum().sort_values(ascending=False).head(10)

fig6 = px.bar(
    top_customers,
    title="Top 10 Customers by Revenue",
    labels={'index': 'Customer ID', 'value': 'Revenue'}
)
fig6.update_traces(marker_color=ORANGE)
st.plotly_chart(fig6, use_container_width=True)
