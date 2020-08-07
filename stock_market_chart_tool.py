import json
import math
import pandas as pd
from datetime import datetime
from bokeh.plotting import figure, ColumnDataSource, show
from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import BooleanFilter, CDSView, Select, HoverTool, PolyDrawTool
from bokeh.models.formatters import NumeralTickFormatter

P_WIDTH = 1200
P_HEIGHT = 700
TOOLS = 'pan,wheel_zoom,hover,reset'

VBAR_WIDTH = 0.3
RED = (245, 0, 0)
GREEN = (0, 200, 0)
BLACK = (0, 0, 0)
GREY = (235, 235, 235)


# Get the data from a .json file and put the useful data into a pandas dataframe
def get_symbol_df(symb, LoT):
    data = pd.read_json(symbol + '_' + lengthOfTime + '.json')
    pandasData = pd.DataFrame.from_records(data)
    pandasData = pandasData.drop(pandasData.columns[[6, 7, 8, 9, 10, 11, 12, 13, 14]], axis=1)
    pandasData['date'] = pd.to_datetime(pandasData['date'])
    d = {'date': pandasData.date, 'Open': pandasData.open, 'Close': pandasData.close, 'high': pandasData.high,
         'low': pandasData.low, 'volume': pandasData.volume}  # to rename columns
    df = pd.DataFrame(data=d)
    df.reset_index(inplace=True)
    df.set_index('date', inplace=True, drop=True)  # make the date column the index

    # Volume bars height calculation
    df["volHeight"] = (df.volume / df.volume.max()) * (df.high.max() / 6)
    # 20 period Simple Moving Average calculation
    df["sma20"] = df.Close.rolling(20).sum() / 20

    return df

# 50 period moving average
def fifty_mv(df):
    df["sma50"] = df.Close.rolling(50).sum() / 50

    return df

# Standard Deviation column added to calculate the Bollinger Bands
def bollinger_bands(df):
    df['sd'] = df.Close.rolling(min_periods=20, window=20, center=False).std()

    return df

# Plot 50 period moving average
def plot_fifty_mv(df, chart):
    df = fifty_mv(df)
    chart.line(df['index'], df['sma50'], color='orange', alpha=0.7)

    return chart

# Plot Bollinger Bands
def plot_bb(df, chart):
    df = bollinger_bands(df)
    chart.line(df['index'], df['sma20'] + (2 * df['sd']), color=(169, 94, 255), alpha=0.7)
    chart.line(df['index'], df['sma20'] - (2 * df['sd']), color=(77, 178, 255), alpha=0.7)

    return chart


# Drawing the chart
def plot_stock_price(stock, symbol, lengthOfTime):
    p = figure(plot_width=P_WIDTH, plot_height=P_HEIGHT, tools=TOOLS,
               title=symbol + ' (' + lengthOfTime + ')', toolbar_location='above')

    # green or red
    inc = stock.data['Close'] >= stock.data['Open']
    dec = stock.data['Open'] > stock.data['Close']
    view_inc = CDSView(source=stock, filters=[BooleanFilter(inc)])
    view_dec = CDSView(source=stock, filters=[BooleanFilter(dec)])

    # relabel the x-axis to avoid gaps on days of no trading
    p.xaxis.major_label_overrides = {
        i + int(stock.data['index'][0]): date.strftime('%b %d') for i, date in
        enumerate(pd.to_datetime(stock.data["date"]))
    }
    p.xaxis.bounds = (stock.data['index'][0], stock.data['index'][-1])

    # Wicks
    p.segment(x0='index', x1='index', y0='low', y1='high', color=GREY, source=stock, view=view_inc)
    p.segment(x0='index', x1='index', y0='low', y1='high', color=GREY, source=stock, view=view_dec)
    # Candlesticks
    p.vbar(x='index', width=VBAR_WIDTH, top='Open', bottom='Close', fill_color=GREEN, line_color=GREEN,
           source=stock, view=view_inc, name="price")
    p.vbar(x='index', width=VBAR_WIDTH, top='Open', bottom='Close', fill_color=RED, line_color=RED,
           source=stock, view=view_dec, name="price")
    # Simple Moving Average
    p.line(df['index'], df['sma20'], color='yellow', alpha=0.7)
    # Volume bars
    p.vbar(x='index', width=VBAR_WIDTH / 2, top='volHeight', bottom=0, fill_color=GREEN, line_color=GREEN,
           source=stock, view=view_inc, name="price")
    p.vbar(x='index', width=VBAR_WIDTH / 2, top='volHeight', bottom=0, fill_color=RED, line_color=RED,
           source=stock, view=view_dec, name="price")

    # graph formatting
    p.yaxis.formatter = NumeralTickFormatter(format='0,0[.]000')
    p.x_range.range_padding = 0.05
    p.xaxis.ticker.desired_num_ticks = 40
    p.xaxis.major_label_orientation = 3.14 / 4
    p.xgrid.grid_line_alpha = 0.1
    p.ygrid.grid_line_alpha = 0.1

    # hover and draw tool
    price_hover = p.select(dict(type=HoverTool))
    line = p.multi_line([[0, 0]], [[0, 0]], line_width=1, alpha=0.8, color=(255, 255, 255))
    draw_tool_line = PolyDrawTool(renderers=[line])
    p.add_tools(draw_tool_line)

    # Tooltips
    price_hover.names = ["price"]
    price_hover.tooltips = [("Date", "@date{%d-%m-%Y}"),
                            ("Open", "@Open{0,0.00}"),
                            ("Close", "@Close{0,0.00}"),
                            ("Volume", "@volume{0.00 a}")]
    price_hover.formatters = {"@date": 'datetime'}

    return p


# symbol = 'AMZN'
# lengthOfTime = '6m'
# symbol = 'GT'
# lengthOfTime = '3m'
# symbol = 'EBAY'
# lengthOfTime = '1y'

while True:
    symbol = input("Input 'AMZN','GT' or 'EBAY' for different market data: ").upper()
    if symbol == 'AMZN':
        lengthOfTime = '6m'
        break
    elif symbol == 'GT':
        lengthOfTime = '3m'
        break
    elif symbol == 'EBAY':
        lengthOfTime = '1y'
        break
    else:
        print("Oops you typed it in wrong, try again... \n")

df = get_symbol_df(symbol, lengthOfTime)
stock = ColumnDataSource(data=dict(date=[], Open=[], Close=[], high=[], low=[], volume=[], volHeight=[], index=[]))
stock.data = stock.from_df(df)

p_stock = plot_stock_price(stock, symbol, lengthOfTime)

while True:
    fifty = input("An orange 50 period moving average? Y/N: ").upper()
    if fifty == 'Y':
        plot_fifty_mv(df, p_stock)
        break
    elif fifty == 'N':
        break
    else:
        print("Oops you typed it in wrong, try again... \n")

while True:
    bollinger = input("Input 'Y' for Bollinger Bands, 'N' for a yellow 20 period moving average: ").upper()
    if bollinger == 'Y':
        plot_bb(df, p_stock)
        break
    elif bollinger == 'N':
        break
    else:
        print("Oops you typed it in wrong, try again... \n")

# dark theme
curdoc().theme = 'dark_minimal'

show(p_stock)
