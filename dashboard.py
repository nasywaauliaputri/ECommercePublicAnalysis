import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="E-Commerce Dashboard",
    layout="wide",
    page_icon="📊"
)

# ===============================
# HEADER
# ===============================
st.title("📊 E-Commerce Performance Dashboard")
st.markdown("Analisis tren order, metode pembayaran, dan kinerja pengiriman")

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data():
    orders = pd.read_csv("orders_dataset.csv", parse_dates=[
        'order_purchase_timestamp',
        'order_approved_at',
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ])
    payments = pd.read_csv("order_payments_dataset.csv")
    return orders.merge(payments, on='order_id')

df = load_data()

# ===============================
# SIDEBAR
# ===============================
st.sidebar.header("📌 Filter")

date_range = st.sidebar.date_input(
    "Pilih Rentang Waktu",
    [df['order_purchase_timestamp'].min(), df['order_purchase_timestamp'].max()]
)

df = df[
    (df['order_purchase_timestamp'] >= pd.to_datetime(date_range[0])) &
    (df['order_purchase_timestamp'] <= pd.to_datetime(date_range[1]))
]

# ===============================
# METRICS
# ===============================
st.subheader("📌 Key Metrics")

col1, col2, col3 = st.columns(3)
col1.metric("Total Orders", f"{df['order_id'].nunique():,}")
col2.metric("Total Revenue", f"${df['payment_value'].sum():,.0f}")
col3.metric("Avg Transaction", f"${df['payment_value'].mean():,.2f}")

st.markdown("---")

# ===============================
# TREN ORDER
# ===============================
st.subheader("📈 Tren Order Bulanan")

df['month'] = df['order_purchase_timestamp'].dt.to_period('M')
trend = df.groupby('month')['order_id'].nunique()

fig, ax = plt.subplots()
trend.plot(ax=ax)
ax.set_title("Monthly Orders")
st.pyplot(fig)

# ===============================
# PAYMENT
# ===============================
st.subheader("💳 Analisis Pembayaran")

col1, col2 = st.columns(2)

payment_count = df['payment_type'].value_counts()
payment_revenue = df.groupby('payment_type')['payment_value'].sum()

with col1:
    st.markdown("**Frekuensi Penggunaan**")
    fig, ax = plt.subplots()
    payment_count.plot(kind='bar', ax=ax)
    st.pyplot(fig)

with col2:
    st.markdown("**Revenue per Metode**")
    fig, ax = plt.subplots()
    payment_revenue.plot(kind='bar', ax=ax)
    st.pyplot(fig)

st.markdown("---")

# ===============================
# DELIVERY
# ===============================
st.subheader("🚚 Kinerja Pengiriman")

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
col1.metric("Avg Delivery (days)", round(df_del['delivery_time'].mean(), 2))
col2.metric("Avg Delay (days)", round(df_del['delay'].mean(), 2))

# ===============================
# RFM
# ===============================
st.subheader("👥 Customer Segmentation (RFM)")

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

seg = rfm['segment'].value_counts()

fig, ax = plt.subplots()
seg.plot(kind='bar', ax=ax)
st.pyplot(fig)

st.markdown("---")
st.caption("Dashboard by Streamlit 🚀")
