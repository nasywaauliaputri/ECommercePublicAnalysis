import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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

st.title("📊 E-Commerce Advanced Dashboard")

# =====================================================
# 1. TREND ORDER
# =====================================================
st.header("📦 1. Tren Jumlah Pesanan")

trend = data.groupby('month')['order_id'].nunique().reset_index()
trend.columns = ['month', 'total_orders']

fig, ax = plt.subplots()
ax.plot(trend['month'].astype(str), trend['total_orders'], color=ORANGE, linewidth=2)
ax.set_title("Tren Order per Bulan")
plt.xticks(rotation=45)
st.pyplot(fig)

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
    fig1, ax1 = plt.subplots()
    sns.barplot(data=payment, x='payment_type', y='payment_value', ax=ax1, color=YELLOW)
    ax1.set_title("Revenue per Payment Type")
    plt.xticks(rotation=30)
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots()
    sns.barplot(data=payment, x='payment_type', y='order_id', ax=ax2, color=ORANGE)
    ax2.set_title("Transaction Count")
    plt.xticks(rotation=30)
    st.pyplot(fig2)

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

fig3, ax3 = plt.subplots()
ax3.hist(data['delivery_time'].dropna(), bins=30, color=YELLOW)
ax3.set_title("Distribusi Delivery Time")
st.pyplot(fig3)

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

# Mengatasi error qcut pada data duplikat
rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1], duplicates='drop')
rfm['F_Score'] = pd.qcut(rfm['Frequency'], 4, labels=[1, 2, 3, 4], duplicates='drop')
rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4], duplicates='drop')

rfm['Segment'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str)

st.subheader("Contoh Data RFM")
st.dataframe(rfm.head())

fig4, ax4 = plt.subplots()
rfm['Segment'].value_counts().head(10).plot(kind='bar', color=ORANGE, ax=ax4)
ax4.set_title("Top RFM Segments")
st.pyplot(fig4)

# =====================================================
# 5. DELAY SEGMENTATION
# =====================================================
st.header("⏱ 5. Segmentasi Delay")

data['delay_segment'] = pd.cut(
    data['delay'],
    bins=[-999, 0, 5, 10, 50],
    labels=['Early/On Time', 'Slight Delay', 'Moderate Delay', 'Severe Delay']
)

fig5, ax5 = plt.subplots()
data['delay_segment'].value_counts().plot(kind='bar', color=YELLOW, ax=ax5)
ax5.set_title("Segmentasi Keterlambatan Pengiriman")
st.pyplot(fig5)

# =====================================================
# 6. CUSTOMER INSIGHT
# =====================================================
st.header("👥 6. Customer Insight")

top_customers = data.groupby('customer_id')['payment_value'].sum().sort_values(ascending=False).head(10)

fig6, ax6 = plt.subplots()
top_customers.plot(kind='bar', color=ORANGE, ax=ax6)
ax6.set_title("Top 10 Customers by Revenue")
st.pyplot(fig6)
