import plotly.graph_objects as go
from plotly.subplots import make_subplots   
from indicators import support_restantce_bands

def _build_chart(df, ticker: str, months: int, include_sma: bool):

    df_display = df.last(f"{months}M")

    fig = make_subplots(
        rows=2,cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df_display.index,
        open=df_display["Open"],
        high=df_display["High"],
        low=df_display["Low"],
        close=df_display["Close"],
        name="Price"
    ),row=1, col=1)

    if include_sma:
        fig.add_trace(go.Scatter(
            x=df_display.index,
            y=df_display["SMA50"],
            mode="lines",
            name="50 SMA"
        ),row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df_display.index,
            y=df_display["SMA200"],
            mode="lines",
            name="200 SMA"
        ),row=1, col=1)
    #RSI plot
    fig.add_trace(
        go.Scatter(
            x=df_display.index,
            y=df_display["RSI"],
            mode="lines",
            name="RSI"
    ,),row=2, col=1 )

    fig.add_hline(y=70, line_dash="dash", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", row=2, col=1)

    #this is only for 3y support bands and resistance bands 
    if months == 36 and not df_display.empty:

        support, resistance = support_restantce_bands(df_display)
        fig.add_hline(
        y=support,
        line_dash="dash",
        line_color="green",
        annotation_text="Support",
        annotation_position="bottom right",
        row=1, col=1
        )

        fig.add_hline(
        y=resistance,
        line_dash="dash",
        line_color="red",
        annotation_text="Resistance",
        annotation_position="top right",
        row=1, col=1
        )
    
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

def plot_3y(df, ticker):
    return _build_chart(df, ticker, 36, include_sma=True)

