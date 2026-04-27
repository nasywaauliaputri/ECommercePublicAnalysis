import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")

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
    
    df = orders.merge(payments, on='order_id')
    return df

df = load_data()

st.title("📊 E-Commerce Dashboard")

# ===============================
# SIDEBAR FILTER
# ===============================
st.sidebar.header("Filter Data")

min_date = df['order_purchase_timestamp'].min()
max_date = df['order_purchase_timestamp'].max()

start_date = st.sidebar.date_input("Start Date", min_date)
end_date = st.sidebar.date_input("End Date", max_date)

df = df[
    (df['order_purchase_timestamp'] >= pd.to_datetime(start_date)) &
    (df['order_purchase_timestamp'] <= pd.to_datetime(end_date))
]

# ===============================
# METRIC
# ===============================
st.subheader("📌 Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric("Total Orders", df['order_id'].nunique())
col2.metric("Total Revenue", round(df['payment_value'].sum(), 2))
col3.metric("Avg Transaction", round(df['payment_value'].mean(), 2))

# ===============================
# 1. TREN ORDER
# ===============================
st.subheader("📈 Tren Jumlah Order")

df['month'] = df['order_purchase_timestamp'].dt.to_period('M')
orders_trend = df.groupby('month')['order_id'].nunique()

fig, ax = plt.subplots()
orders_trend.plot(ax=ax)
st.pyplot(fig)

# ===============================
# 2. PAYMENT ANALYSIS
# ===============================
st.subheader("💳 Metode Pembayaran")

payment_count = df['payment_type'].value_counts()
payment_revenue = df.groupby('payment_type')['payment_value'].sum()

col1, col2 = st.columns(2)

with col1:
    st.write("Jumlah Penggunaan")
    fig, ax = plt.subplots()
    payment_count.plot(kind='bar', ax=ax)
    st.pyplot(fig)

with col2:
    st.write("Total Revenue")
    fig, ax = plt.subplots()
    payment_revenue.plot(kind='bar', ax=ax)
    st.pyplot(fig)

# ===============================
# 3. DELIVERY ANALYSIS
# ===============================
st.subheader("🚚 Kinerja Pengiriman")

df_delivered = df[df['order_status'] == 'delivered'].copy()

df_delivered['delivery_time'] = (
    df_delivered['order_delivered_customer_date'] - 
    df_delivered['order_purchase_timestamp']
).dt.days

df_delivered['delay'] = (
    df_delivered['order_delivered_customer_date'] - 
    df_delivered['order_estimated_delivery_date']
).dt.days

avg_delivery = df_delivered['delivery_time'].mean()
avg_delay = df_delivered['delay'].mean()

col1, col2 = st.columns(2)
col1.metric("Avg Delivery Time (days)", round(avg_delivery, 2))
col2.metric("Avg Delay (days)", round(avg_delay, 2))

# kategori delay
def delay_cat(x):
    if x <= 0:
        return 'On Time/Early'
    elif x <= 3:
        return 'Slight Delay'
    else:
        return 'Late'

df_delivered['delay_category'] = df_delivered['delay'].apply(delay_cat)

delay_dist = df_delivered['delay_category'].value_counts()

fig, ax = plt.subplots()
delay_dist.plot(kind='bar', ax=ax)
st.pyplot(fig)

# ===============================
# 4. RFM ANALYSIS
# ===============================
st.subheader("👥 RFM Analysis")

latest_date = df['order_purchase_timestamp'].max()

rfm = df.groupby('customer_id').agg({
    'order_purchase_timestamp': lambda x: (latest_date - x.max()).days,
    'order_id': 'count',
    'payment_value': 'sum'
})

rfm.columns = ['Recency', 'Frequency', 'Monetary']

# ranking (biar tidak error)
rfm['R_score'] = pd.qcut(rfm['Recency'].rank(method='first'), 4, labels=[4,3,2,1])
rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1,2,3,4])
rfm['M_score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 4, labels=[1,2,3,4])

rfm['RFM_score'] = rfm[['R_score','F_score','M_score']].astype(int).sum(axis=1)

def segment(score):
    if score >= 10:
        return 'High Value'
    elif score >= 6:
        return 'Medium Value'
    else:
        return 'Low Value'

rfm['segment'] = rfm['RFM_score'].apply(segment)

segment_dist = rfm['segment'].value_counts()

fig, ax = plt.subplots()
segment_dist.plot(kind='bar', ax=ax)
st.pyplot(fig)
