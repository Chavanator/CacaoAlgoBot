from iqoptionapi.stable_api import IQ_Option
from configobj import ConfigObj
import warnings
import time
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression

# Ignorar todos los warnings
warnings.filterwarnings("ignore")

# Cargar configuración desde el archivo
config = ConfigObj('config.txt')
email = config['LOGIN']['email']
senha = config['LOGIN']['senha']
tipo = config['AJUSTES']['tipo']

# Establecer conexión con IQ Option
API = IQ_Option(email, senha)
API.connect()

# Esperar hasta que la conexión sea exitosa
while not API.check_connect():
    print('Esperando conexión...')
    time.sleep(1)

print('Conexión exitosa!')

def obtener_activos_disponibles():
    activos = API.get_all_open_time()
    return [activo for activo in activos['binary'] if activos['binary'][activo]['open']]

def mostrar_menu_activos(activos):
    print("\nActivos disponibles:")
    for idx, activo in enumerate(activos, 1):
        print(f"{idx}. {activo}")

activos_disponibles = obtener_activos_disponibles()
mostrar_menu_activos(activos_disponibles)

while True:
    try:
        seleccion = int(input("\nSeleccione el número del activo que desea operar: "))
        if 1 <= seleccion <= len(activos_disponibles):
            activo_seleccionado = activos_disponibles[seleccion-1]
            print('Activo seleccionado:', activo_seleccionado)
            break
        else:
            print("Selección inválida. Por favor, seleccione un número de la lista.")
    except ValueError:
        print("Entrada inválida. Por favor, ingrese un número.")
asset = activo_seleccionado

# Función para obtener datos históricos
def get_historical_data(asset, interval, limit):
    return API.get_candles(asset, interval, limit, time.time())

# Función para calcular el ATR
def calculate_atr(highs, lows, closes, period):
    tr_list = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        tr_list.append(tr)
    atr = np.mean(tr_list[-period:])
    return atr

# Función para realizar el análisis y trading
def analyze_and_trade(asset, valor_entrada):
    historical_data_1m = get_historical_data(asset, 60, 1000)
    historical_data_5m = get_historical_data(asset, 300, 1000)

    closes_1m = np.array([candle['close'] for candle in historical_data_1m])
    closes_5m = np.array([candle['close'] for candle in historical_data_5m])

    # Preparar datos para el modelo
    scaler_1m = MinMaxScaler(feature_range=(0, 1))
    scaler_5m = MinMaxScaler(feature_range=(0, 1))
    scaled_closes_1m = scaler_1m.fit_transform(closes_1m.reshape(-1, 1))
    scaled_closes_5m = scaler_5m.fit_transform(closes_5m.reshape(-1, 1))

    look_back = 200
    X_1m, y_1m = [], []
    X_5m, y_5m = [], []
    for i in range(len(scaled_closes_1m) - look_back):
        X_1m.append(scaled_closes_1m[i:i + look_back, 0])
        y_1m.append(scaled_closes_1m[i + look_back, 0])

    for i in range(len(scaled_closes_5m) - look_back):
        X_5m.append(scaled_closes_5m[i:i + look_back, 0])
        y_5m.append(scaled_closes_5m[i + look_back, 0])

    X_1m, y_1m = np.array(X_1m), np.array(y_1m)
    X_5m, y_5m = np.array(X_5m), np.array(y_5m)

    # Entrenar el modelo de regresión lineal para ambas temporalidades
    lin_model_1m = LinearRegression()
    lin_model_5m = LinearRegression()
    lin_model_1m.fit(X_1m, y_1m)
    lin_model_5m.fit(X_5m, y_5m)

    # Hacer predicciones con los modelos
    lin_forecast_1m = lin_model_1m.predict([scaled_closes_1m[-look_back:].flatten()])
    lin_forecast_5m = lin_model_5m.predict([scaled_closes_5m[-look_back:].flatten()])
    predicted_price_1m = scaler_1m.inverse_transform(lin_forecast_1m.reshape(-1, 1))[0, 0]
    predicted_price_5m = scaler_5m.inverse_transform(lin_forecast_5m.reshape(-1, 1))[0, 0]

    # Comparar las tendencias
    if predicted_price_1m > closes_1m[-1] and predicted_price_5m > closes_5m[-1]:
        direction = 'call'
    elif predicted_price_1m < closes_1m[-1] and predicted_price_5m < closes_5m[-1]:
        direction = 'put'
    else:
        print('No se tomó ninguna decisión de operación.')
        return False, valor_entrada

    # Realizar operación de compra
    exp=300
    resultado_operacion, nuevo_valor_entrada = compra(asset, valor_entrada, exp, direction, tipo)
    return resultado_operacion, nuevo_valor_entrada

# Función para realizar la operación de compra
def compra(asset, valor_entrada, exp, direction, tipo):
    
    if tipo == 'digital':
        check, id = API.buy_digital_spot(asset, valor_entrada, direction, exp)
    else:
        check, id = API.buy(valor_entrada, asset, direction, exp)

    if check:
        print('\n>> Orden abierta\nPar:', asset, '\nTimeframe:', exp, '\nDirección:', direction, '\nEntrada de:', valor_entrada, '\nTipo', tipo)
        # Esperar a que la operación termine
        while True:
            check, win = API.check_win_digital_v2(id) if tipo == 'digital' else API.check_win_v3(id)
            if check:
                print(f'Resultado de la operación: {"Ganada" if win > 0 else "Perdida"}, Monto: {win}')
                if win > 0:
                    nuevo_valor_entrada = valor_entrada + win  # Reinvertir la ganancia más la cantidad inicial
                    return True, nuevo_valor_entrada
                else:
                    return False, valor_entrada
    else:
        print('Error en la apertura de la orden,', id, asset)
        return False, valor_entrada

# Realizar 1000 operaciones consecutivas
operaciones_realizadas = 0
ciclo_ganado = 0
valor_entrada_inicial = API.get_balance() / 100
valor_entrada = valor_entrada_inicial

while operaciones_realizadas < 1000:
    time.sleep(0.1)
    minutos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime('%M.%S')[1:])
    entrar = minutos in {9.58, 4.58}

    if entrar:
        print('\n>> Iniciando análisis')
        resultado, nuevo_valor_entrada = analyze_and_trade(asset, valor_entrada)
        if resultado:
            ciclo_ganado += 1
            if ciclo_ganado == 3:
                valor_entrada = valor_entrada_inicial
                ciclo_ganado = 0
            else:
                valor_entrada = nuevo_valor_entrada
        else:
            valor_entrada = valor_entrada_inicial
            ciclo_ganado = 0
        operaciones_realizadas += 1
        print('\nOperaciones realizadas:', operaciones_realizadas)
        print('Balance actual:', API.get_balance())
        time.sleep(60)  # Ajustar el tiempo de espera para evitar operaciones continuas muy rápidas

# Al finalizar, cerrar la conexión con IQ Option
API.disconnect()
