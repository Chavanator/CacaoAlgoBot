from iqoptionapi.stable_api import IQ_Option
from configobj import ConfigObj
import time
import warnings
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from pandas import DataFrame

# Ignorar todos los warnings
warnings.filterwarnings("ignore")

# Cargar configuración desde el archivo
config = ConfigObj('config.txt')
email = config['LOGIN']['email']
senha = config['LOGIN']['senha']
tipo = config['AJUSTES']['tipo']
analise_medias = config['AJUSTES']['analise_medias']  # Convertir a tipo float
velas_medias = int(config['AJUSTES']['velas_medias'])

# Establecer conexión con IQ Option
API = IQ_Option(email, senha)
API.connect()

while True:
    escolha = 'demo'  # Aquí podrías cambiar a 'real' si lo deseas
    if escolha == 'demo':
        conta = 'PRACTICE'
        print('Cuenta demo seleccionada')
    #activo = input('\n¿Qué activo desea operar? (ej. EURUSD o EURUSD-OTC): ')
    asset = 'EURUSD-OTC'
    print('Activo seleccionado:', asset)
    break

API.change_balance(conta)

# Ajustar un modelo LSTM
scaler = MinMaxScaler(feature_range=(0, 1))

# Función para obtener datos históricos
def get_historical_data(asset, interval, limit):
    return API.get_candles(asset, interval, limit, time.time())

# Función para calcular el ATR
# Función para realizar el análisis y trading
def analyze_and_trade(asset):
    historical_data_1m = get_historical_data(asset, 60, 300)
    historical_data_5m = get_historical_data(asset, 300, 1000)
    historical_data_10m = get_historical_data(asset, 600, 1000)

    closes_1m = np.array([candle['close'] for candle in historical_data_1m])
    closes_5m = np.array([candle['close'] for candle in historical_data_5m])
    closes_10m = np.array([candle['close'] for candle in historical_data_10m])

    # Preparar datos para el modelo
    scaler_1m = MinMaxScaler(feature_range=(0, 1))
    scaler_5m = MinMaxScaler(feature_range=(0, 1))
    scaler_10m = MinMaxScaler(feature_range=(0, 1))
    scaled_closes_1m = scaler_1m.fit_transform(closes_1m.reshape(-1, 1))
    scaled_closes_5m = scaler_5m.fit_transform(closes_5m.reshape(-1, 1))
    scaled_closes_10m = scaler_10m.fit_transform(closes_10m.reshape(-1, 1))

    look_back = 200
    X_1m, y_1m = [], []
    X_5m, y_5m = [], []
    X_10m, y_10m = [], []
    for i in range(len(scaled_closes_1m) - look_back):
        X_1m.append(scaled_closes_1m[i:i + look_back, 0])
        y_1m.append(scaled_closes_1m[i + look_back, 0])

    for i in range(len(scaled_closes_5m) - look_back):
        X_5m.append(scaled_closes_5m[i:i + look_back, 0])
        y_5m.append(scaled_closes_5m[i + look_back, 0])

    for i in range(len(scaled_closes_10m) - look_back):
        X_10m.append(scaled_closes_10m[i:i + look_back, 0])
        y_10m.append(scaled_closes_10m[i + look_back, 0])

    X_1m, y_1m = np.array(X_1m), np.array(y_1m)
    X_5m, y_5m = np.array(X_5m), np.array(y_5m)
    X_10m, y_10m = np.array(X_10m), np.array(y_10m)

    # Entrenar el modelo de regresión lineal para las tres temporalidades
    lin_model_1m = LinearRegression()
    lin_model_5m = LinearRegression()
    lin_model_10m = LinearRegression()
    lin_model_1m.fit(X_1m, y_1m)
    lin_model_5m.fit(X_5m, y_5m)
    lin_model_10m.fit(X_10m, y_10m)

    # Hacer predicciones con los modelos
    lin_forecast_1m = lin_model_1m.predict([scaled_closes_1m[-look_back:].flatten()])
    lin_forecast_5m = lin_model_5m.predict([scaled_closes_5m[-look_back:].flatten()])
    lin_forecast_10m = lin_model_10m.predict([scaled_closes_10m[-look_back:].flatten()])
    predicted_price_1m = scaler_1m.inverse_transform(lin_forecast_1m.reshape(-1, 1))[0, 0]
    predicted_price_5m = scaler_5m.inverse_transform(lin_forecast_5m.reshape(-1, 1))[0, 0]
    predicted_price_10m = scaler_10m.inverse_transform(lin_forecast_10m.reshape(-1, 1))[0, 0]

    # Comparar las tendencias
    if (predicted_price_1m > closes_1m[-1] and predicted_price_5m > closes_5m[-1] and predicted_price_10m > closes_10m[-1]):
        direction = 'call'
    elif (predicted_price_1m < closes_1m[-1] and predicted_price_5m < closes_5m[-1] and predicted_price_10m < closes_10m[-1]):
        direction = 'put'
    else:
        print('No se tomó ninguna decisión de operación.')
        return False

    # Realizar operación de compra
    valor_cuenta= API.get_balance()
    valor_entrada = valor_cuenta/100  # Valor de entrada deseado
    compra(asset, valor_entrada, direction, 20, tipo)
    return True

# Función para realizar la operación de compra
def compra(asset, valor_entrada, direction, exp, tipo):
    if tipo == 'digital':
        check, id = API.buy_digital_spot(asset, valor_entrada, direction, exp)
    else:
        check, id = API.buy(valor_entrada, asset, direction, exp)
        
    if check:
        print('\n>> Orden abierta\nPar:', asset, '\nTimeframe:', exp, '\nDirección:', direction, '\nEntrada de:', valor_entrada, '\nTipo', tipo)
    else:
        print('Error en la apertura de la orden,', id, asset)

# Realizar 1000 operaciones consecutivas
operaciones_realizadas = 0
while operaciones_realizadas < 1000:
    time.sleep(0.1)
    minutos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime('%M.%S')[1:])
    entrar = True if (minutos == 19.58 or minutos == 39.58 or minutos == 59.58) else False

    if entrar:
        print('\n>> Iniciando análisis')
        analyze_and_trade(asset)
        operaciones_realizadas += 1
        print('\nOperaciones realizadas:', operaciones_realizadas)
        print('Balance actual:', API.get_balance())
        time.sleep(0.1)

# Al finalizar, cerrar la conexión con IQ Option
API.disconnect()
