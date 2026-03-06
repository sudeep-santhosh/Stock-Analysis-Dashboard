import yfinance as yf


def load_stock_data(ticker: str, period: str = "3y"):
    df = yf.download(ticker, period=period)

    if df.empty:
        raise ValueError("No data found for ticker")

    # Flatten MultiIndex (yfinance issue)
    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)

    df.dropna(inplace=True)

    return df