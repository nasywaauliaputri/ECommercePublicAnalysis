import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="E-Commerce Dashboard", layout="wide", page_icon="📊")

# ===============================
# STYLE (biar lebih clean)
# ===============================
st.markdown("""
<style>
.metric-card {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data():
    orders = pd.read_csv("orders_dataset.csv", parse_dates=[
        'order_purchase_timestamp',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ])
    payments = pd.read_csv("order_payments_dataset.csv")
    return orders.merge(payments, on='order_id')

df = load_data()

# ===============================
# HEADER
# ===============================
st.title("📊 E-Commerce Dashboard")
st.caption("Insight bisnis berbasis data")

# ===============================
# FILTER
# ===============================
date_range = st.date_input(
    "Filter Tanggal",
    [df['order_purchase_timestamp'].min(), df['order_purchase_timestamp'].max()]
)

df = df[
    (df['order_purchase_timestamp'] >= pd.to_datetime(date_range[0])) &
    (df['order_purchase_timestamp'] <= pd.to_datetime(date_range[1]))
]

# ===============================
# KPI CARDS
# ===============================
total_orders = df['order_id'].nunique()
total_revenue = df['payment_value'].sum()
avg_order = df['payment_value'].mean()

col1, col2, col3 = st.columns(3)
col1.metric("🛒 Total Orders", f"{total_orders:,}")
col2.metric("💰 Revenue", f"${total_revenue:,.0f}")
col3.metric("📦 Avg Order", f"${avg_order:,.2f}")

# ===============================
# TABS
# ===============================
tab1, tab2, tab3 = st.tabs(["📈 Tren Order", "💳 Payment", "🚚 Delivery"])

# ===============================
# TAB 1: TREN ORDER
# ===============================
with tab1:
    df['month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    trend = df.groupby('month')['order_id'].nunique().reset_index()

    fig = px.line(trend, x='month', y='order_id', title="Tren Order per Bulan")
    st.plotly_chart(fig, use_container_width=True)

    # Insight otomatis
    growth = trend['order_id'].pct_change().mean() * 100
    st.info(f"📌 Rata-rata pertumbuhan order: {growth:.2f}%")

# ===============================
# TAB 2: PAYMENT
# ===============================
with tab2:
    payment_count = df['payment_type'].value_counts().reset_index()
    payment_count.columns = ['payment_type', 'count']

    payment_rev = df.groupby('payment_type')['payment_value'].sum().reset_index()

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(payment_count, x='payment_type', y='count', title="Frekuensi Payment")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(payment_rev, x='payment_type', y='payment_value', title="Revenue per Payment")
        st.plotly_chart(fig, use_container_width=True)

    top_method = payment_rev.sort_values(by='payment_value', ascending=False).iloc[0]['payment_type']
    st.info(f"📌 Metode paling menguntungkan: {top_method}")

# ===============================
# TAB 3: DELIVERY
# ===============================
with tab3:
    df_del = df[df['order_status'] == 'delivered'].copy()

    df_del['delivery_time'] = (
        df_del['order_delivered_customer_date'] - 
        df_del['order_purchase_timestamp']
    ).dt.days

    df_del['delay'] = (
        df_del['order_delivered_customer_date'] - 
        df_del['order_estimated_delivery_date']
    ).dt.days

    col1, col2 = st.columns(2)
    col1.metric("⏱ Avg Delivery", round(df_del['delivery_time'].mean(), 2))
    col2.metric("⚠ Avg Delay", round(df_del['delay'].mean(), 2))

    # kategori delay
    df_del['category'] = df_del['delay'].apply(
        lambda x: 'On Time' if x <= 0 else 'Late'
    )

    delay_dist = df_del['category'].value_counts().reset_index()
    delay_dist.columns = ['category', 'count']

    fig = px.pie(delay_dist, names='category', values='count', title="Distribusi Pengiriman")
    st.plotly_chart(fig, use_container_width=True)

    late_pct = (df_del['delay'] > 0).mean() * 100
    st.info(f"📌 Persentase keterlambatan: {late_pct:.2f}%")

# ===============================
# RFM (bonus section)
# ===============================
st.markdown("## 👥 Customer Segmentation (RFM)")

latest = df['order_purchase_timestamp'].max()

rfm = df.groupby('customer_id').agg({
    'order_purchase_timestamp': lambda x: (latest - x.max()).days,
    'order_id': 'count',
    'payment_value': 'sum'
})

rfm.columns = ['Recency', 'Frequency', 'Monetary']

rfm['R_score'] = pd.qcut(rfm['Recency'].rank(method='first'), 4, labels=[4,3,2,1])
rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1,2,3,4])
rfm['M_score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 4, labels=[1,2,3,4])

rfm['score'] = rfm[['R_score','F_score','M_score']].astype(int).sum(axis=1)

rfm['segment'] = rfm['score'].apply(
    lambda x: 'High Value' if x >= 10 else 'Medium Value' if x >= 6 else 'Low Value'
)

seg = rfm['segment'].value_counts().reset_index()
seg.columns = ['segment', 'count']

fig = px.bar(seg, x='segment', y='count', title="Distribusi Customer Segment")
st.plotly_chart(fig, use_container_width=True)

top_segment = seg.sort_values(by='count', ascending=False).iloc[0]['segment']
st.success(f"🎯 Mayoritas customer berada di segmen: {top_segment}")
