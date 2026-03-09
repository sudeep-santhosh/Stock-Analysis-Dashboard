import streamlit as st
from data_pipeline import data_prepared
from chart import plot_3mo, plot_6mo, plot_1y

st.set_page_config(layout="wide")

st.title("ITC Candlestick Dashboard")

ticker = "ITC.NS"
#data being cached 
df = data_prepared(ticker, period="3y")


tab1, tab2, tab3 = st.tabs(["3 Month", "6 Month", "1 Year"])

with tab1:
    st.subheader("3 Month View")
    fig_3m = plot_3mo(df, ticker)
    st.plotly_chart(fig_3m, use_container_width=True)

with tab2:
    st.subheader("6 Month View (50 & 200 SMA)")
    fig_6m = plot_6mo(df, ticker)
    st.plotly_chart(fig_6m, use_container_width=True)

with tab3:
    st.subheader("1 Year View (50 & 200 SMA)")
    fig_1y = plot_1y(df, ticker)
    st.plotly_chart(fig_1y, use_container_width=True)