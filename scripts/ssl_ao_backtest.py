import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html

# Definir la función calculate_sma
def calculate_sma(df, period):
    return df['Close'].rolling(window=period).mean()

# Cargar los datos y ejecutar la estrategia de trading
data = pd.read_csv('D:/iqrobot/df_test/EURUSD/5m/EURUSD_5m_20240101_20240624.csv', parse_dates=['at'])
data.rename(columns={'at': 'Date', 'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close'}, inplace=True)
data.set_index('Date', inplace=True)

# Calcular SMA con el mejor periodo encontrado
best_sma_period = 50
data['SMA'] = calculate_sma(data, best_sma_period)

# Ejecutar la estrategia y recolectar las señales
results_df = pd.DataFrame(columns=['operación', 'resultado', 'direccion', 'Date', 'Close Date'])
open_trade = False
trade_type = None
entry_index = 0
entry_price = 0

for i in range(best_sma_period, len(data)):
    if open_trade and (i - entry_index == 3):
        result = 85 if (trade_type == 'compra' and data['Close'].iloc[i] > entry_price) or \
                       (trade_type == 'venta' and data['Close'].iloc[i] < entry_price) else 100
        results_df.loc[len(results_df)] = [len(results_df) + 1, result, trade_type, data.index[entry_index], data.index[i]]
        open_trade = False
        trade_type = None
        entry_price = 0

    data['lower_closes'] = (data['Close'] < data['Close'].shift(1)) & \
                           (data['Close'].shift(1) < data['Close'].shift(2)) & \
                           (data['Close'].shift(2) < data['Close'].shift(3))

    data['enter_long'] = (data['Close'] > data['SMA']) & data['lower_closes']

    data['higher_closes'] = (data['Close'] > data['Close'].shift(1)) & \
                            (data['Close'].shift(1) > data['Close'].shift(2)) & \
                            (data['Close'].shift(2) > data['Close'].shift(3))

    data['enter_short'] = (data['Close'] < data['SMA']) & data['higher_closes']

    if data['enter_long'].iloc[i]:
        open_trade = True
        trade_type = 'compra'
        entry_index = i
        entry_price = data['Close'].iloc[i]

    elif data['enter_short'].iloc[i]:
        open_trade = True
        trade_type = 'venta'
        entry_index = i
        entry_price = data['Close'].iloc[i]

# Guardar el historial de operaciones en un archivo CSV
results_df.to_csv('D:/iqrobot/df_test/operation_history.csv', index=False)

# Preparar las señales de compra y venta para el gráfico
buy_signals_open = results_df[results_df['direccion'] == 'compra']['Date']
buy_signals_close = results_df[results_df['direccion'] == 'compra']['Close Date']
sell_signals_open = results_df[results_df['direccion'] == 'venta']['Date']
sell_signals_close = results_df[results_df['direccion'] == 'venta']['Close Date']

# Crear el gráfico de velas interactivo con las señales
fig = go.Figure(data=[go.Candlestick(x=data.index,
                                     open=data['Open'],
                                     high=data['High'],
                                     low=data['Low'],
                                     close=data['Close'],
                                     name='OHLC')])

# Agregar la SMA
fig.add_trace(go.Scatter(x=data.index, y=data['SMA'], mode='lines', name=f'SMA {best_sma_period}', line=dict(color='blue')))

# Agregar las señales de compra y venta
fig.add_trace(go.Scatter(x=buy_signals_open, y=data.loc[buy_signals_open, 'Close'], mode='markers', name='Buy Open', marker=dict(symbol='triangle-up', size=10, color='green')))
fig.add_trace(go.Scatter(x=buy_signals_close, y=data.loc[buy_signals_close, 'Close'], mode='markers', name='Buy Close', marker=dict(symbol='circle', size=10, color='lightgreen')))
fig.add_trace(go.Scatter(x=sell_signals_open, y=data.loc[sell_signals_open, 'Close'], mode='markers', name='Sell Open', marker=dict(symbol='triangle-down', size=10, color='red')))
fig.add_trace(go.Scatter(x=sell_signals_close, y=data.loc[sell_signals_close, 'Close'], mode='markers', name='Sell Close', marker=dict(symbol='circle', size=10, color='pink')))

# Ajustar el diseño del gráfico
fig.update_layout(title='Gráfico de Velas OHLC con SMA y Señales de Trading',
                  yaxis_title='Precio',
                  xaxis_title='Fecha')

# Calcular estadísticas de operaciones
ganadas = len(results_df[results_df['resultado'] == 85])
perdidas = len(results_df[results_df['resultado'] == 100])

# Crear la aplicación Dash
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Gráfico de Velas OHLC Interactivo"),
    dcc.Graph(figure=fig),
    html.Div(f"Operaciones ganadas: {ganadas}"),
    html.Div(f"Operaciones perdidas: {perdidas}"),
    html.Div("El historial de operaciones se ha guardado en 'operation_history.csv'")
])

if __name__ == '__main__':
    app.run_server(debug=True)
