from iqoptionapi.stable_api import IQ_Option
from configobj import ConfigObj
import warnings
import time
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
import sys

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
retries = 0
while not API.check_connect():
    if retries >= 5:
        raise Exception('No se pudo conectar a IQ Option después de varios intentos.')
    print('Esperando conexión...')
    time.sleep(1)
    retries += 1

print('Conexión exitosa!')
balance_account = API.get_balance()
print('Balance actual:', balance_account)

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
            activo_seleccionado = activos_disponibles[seleccion - 1]
            print('Activo seleccionado:', activo_seleccionado)
            break
        else:
            print("Selección inválida. Por favor, seleccione un número de la lista.")
    except ValueError:
        print("Entrada inválida. Por favor, ingrese un número.")
asset = activo_seleccionado

def get_historical_data(asset, interval, limit):
    """Obtiene datos históricos de velas para el activo especificado."""
    try:
        candles = API.get_candles(asset, interval, limit, time.time())
        if candles:
            return candles
        else:
            raise Exception('No se obtuvieron datos históricos.')
    except Exception as e:
        print(f"Error al obtener datos históricos para el activo {asset} con intervalo {interval}: {e}")
        return []

def prepare_data(closes, look_back):
    """Prepara los datos para el modelo de regresión."""
    closes = closes.reshape(-1, 1)  # Asegura que los datos sean una matriz 2D
    scaled_closes = MinMaxScaler(feature_range=(0, 1)).fit_transform(closes)
    X, y = [], []
    for i in range(len(scaled_closes) - look_back):
        X.append(scaled_closes[i:i + look_back, 0])
        y.append(scaled_closes[i + look_back, 0])
    return np.array(X), np.array(y)

def train_and_predict(closes, look_back, pred_count):
    """Entrena el modelo de regresión y realiza predicciones."""
    X, y = prepare_data(closes, look_back)
    lin_model = LinearRegression()
    lin_model.fit(X, y)
    predictions = []
    last_data = X[-1].copy().reshape(1, -1)
    for _ in range(pred_count):
        prediction = lin_model.predict(last_data)[0]
        predictions.append(prediction)
        last_data = np.append(last_data[:, 1:], prediction).reshape(1, -1)
    return predictions

valor_entrada = balance_account / 100  # Valor de entrada deseado
exp = 300

def compra(asset, valor_entrada, direction, exp, tipo):
    """Realiza la operación de compra."""
    if tipo == 'digital':
        check, id = API.buy_digital_spot(asset, valor_entrada, direction, exp)
    else:
        check, id = API.buy(valor_entrada, asset, direction, exp)
    if check:
        print('\n>> Orden abierta\nPar:', asset, '\nTimeframe:', exp, '\nDirección:', direction, '\nEntrada de:', valor_entrada, '\nTipo:', tipo)
        result = API.check_win_digital_v2(id) if tipo == 'digital' else API.check_win_v3(id)
        print('Resultado de la orden:', result)
        return result
    else:
        print('Error en la apertura de la orden,', id, asset)
        return 0

def analyze_and_trade(asset, valor_entrada):
    historical_data_1m = get_historical_data(asset, 60, 1000)
    historical_data_5m = get_historical_data(asset, 300, 1000)

    if not historical_data_1m or not historical_data_5m:
        return False, valor_entrada

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

    print(f'Predicción de 1 minuto:    {predicted_price_1m}')
    print(f'Precio de cierre 1 minuto: {closes_1m[-1]}')
    print(f'Predicción de 5 minutos:    {predicted_price_5m}')
    print(f'Precio de cierre 5 minutos: {closes_5m[-1]}')

    # Comparar las tendencias
    if predicted_price_1m > closes_1m[-1] and predicted_price_5m > closes_5m[-1]:
        direction = 'call'
    elif predicted_price_1m < closes_1m[-1] and predicted_price_5m < closes_5m[-1]:
        direction = 'put'
    else:
        print('No se tomó ninguna decisión de operación.')
        return False, valor_entrada

    # Realizar la operación de compra
    profit = compra(asset, valor_entrada, direction, exp, tipo)
    return profit != 0, valor_entrada + profit if profit > 0 else valor_entrada

# Realizar 1000 operaciones consecutivas
operaciones_realizadas = 0
max_operaciones_consecutivas = 3
operaciones_consecutivas = 0

while operaciones_realizadas < 1000:
    time.sleep(0.1)
    minutos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime('%M.%S')[1:])
    sys.stdout.write(f'\rTiempo actual (minutos.segundos): {minutos:.2f}')
    sys.stdout.flush()
    entrar = True if (minutos == 9.58 or minutos == 4.58) else False

    if entrar:
        print('\n>> Iniciando análisis')
        resultado, nuevo_valor_entrada = analyze_and_trade(asset, valor_entrada)
        operaciones_realizadas += 1
        print('\nOperaciones realizadas:', operaciones_realizadas)
        print('Balance actual:', API.get_balance())

        if resultado:
            operaciones_consecutivas += 1
            if operaciones_consecutivas <= max_operaciones_consecutivas:
                valor_entrada = nuevo_valor_entrada
            else:
                valor_entrada = balance_account / 100
                operaciones_consecutivas = 0
        else:
            valor_entrada = balance_account / 100
            operaciones_consecutivas = 0

        time.sleep(0.1)

# Al finalizar, cerrar la conexión con IQ Option
API.disconnect()
