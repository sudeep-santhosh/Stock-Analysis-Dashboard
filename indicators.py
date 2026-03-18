def add_sma(df):
    df["SMA50"] = df["Close"].rolling(window=50).mean()
    df["SMA200"] = df["Close"].rolling(window=200).mean()
    return df

def add_rsi(df,period=14):
    delta=df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def support_restantce_bands(df):
    df_display = df.last("3Y")
    support = df_display["Low"].min()
    resistance = df_display["High"].max()
    return support, resistance
