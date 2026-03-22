import streamlit as st 
from data_loader import load_stock_data
from indicators import add_sma,add_rsi
import yfinance as yf

'''
this is done so that streamlit works more effiecntly by chaching the data and not relaoding 
the data constantly 
'''
@st.cache_data(ttl=3600)
def data_prepared(ticker, period):
    df=load_stock_data(ticker,period)
    df=add_sma(df)
    df=add_rsi(df)
    return df 

@st.cache_data(ttl=3600)
def get_stock_info(ticker):
    stock = yf.Ticker(ticker)
    return stock.info


def format_market_cap(value):
    if value >= 1e12:
        return f"{value/1e12:.2f}T"
    elif value >= 1e9:
        return f"{value/1e9:.2f}B"
    elif value >= 1e6:
        return f"{value/1e6:.2f}M"
    else:
        return f"{value:,}"
    

