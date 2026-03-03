import plotly.graph_objects as go


def _build_chart(df, ticker: str, months: int, include_sma: bool):

    df_display = df.last(f"{months}M")

    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df_display.index,
        open=df_display["Open"],
        high=df_display["High"],
        low=df_display["Low"],
        close=df_display["Close"],
        name="Price"
    ))

    if include_sma:
        fig.add_trace(go.Scatter(
            x=df_display.index,
            y=df_display["SMA50"],
            mode="lines",
            name="50 SMA"
        ))

        fig.add_trace(go.Scatter(
            x=df_display.index,
            y=df_display["SMA200"],
            mode="lines",
            name="200 SMA"
        ))

    fig.update_layout(
        title=f"{ticker} - {months} Month Chart",
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )

    return fig


def plot_3mo(df, ticker):
    return _build_chart(df, ticker, 3, include_sma=False)


def plot_6mo(df, ticker):
    return _build_chart(df, ticker, 6, include_sma=True)


def plot_1y(df, ticker):
    return _build_chart(df, ticker, 12, include_sma=True)