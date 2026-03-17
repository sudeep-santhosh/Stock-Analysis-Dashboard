import streamlit as st
from data_pipeline import data_prepared,get_stock_info,format_market_cap
from chart import plot_3mo, plot_6mo, plot_1y,plot_3y

st.set_page_config(layout="wide")


st.title("Candlestick Dashboard")
ticker = st.text_input("Enter Stock Ticker", value="ITC.NS").upper()


#data being cached 
df = data_prepared(ticker, period="5y")
info = get_stock_info(ticker)

price = info.get("currentPrice")
high52 = info.get("fiftyTwoWeekHigh")
low52 = info.get("fiftyTwoWeekLow")
marketcap = info.get("marketCap")


col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Price", f"{price:.2f}")
col2.metric("52 Week High", f"{high52:.2f}")
col3.metric("52 Week Low", f"{low52:.2f}")
col4.metric("Market Cap", format_market_cap(marketcap))      

tab1, tab2, tab3 ,tab4= st.tabs(["3 Month", "6 Month", "1 Year", "3 Year"])

with tab1:
    st.subheader("3 Month View")
    fig_3m = plot_3mo(df, ticker)
    st.plotly_chart(fig_3m, use_container_width=True)

with tab2:
    st.subheader("6 Month View ")
    fig_6m = plot_6mo(df, ticker)
    st.plotly_chart(fig_6m, use_container_width=True)

with tab3:
    st.subheader("1 Year View ")
    fig_1y = plot_1y(df, ticker)
    st.plotly_chart(fig_1y, use_container_width=True)

with tab4:
    st.subheader("3 Year View ")
    fig_3y = plot_3y(df, ticker)
    st.plotly_chart(fig_3y, use_container_width=True)

