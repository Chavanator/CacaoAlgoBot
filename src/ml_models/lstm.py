from iqoptionapi.stable_api import IQ_Option
from configobj import ConfigObj
import time
import warnings
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense

# Ignorar todos los warnings
warnings.filterwarnings("ignore")
# Cargar configuración desde el archivo
config = ConfigObj('config.txt')
email = config['LOGIN']['email']
senha = config['LOGIN']['senha']
tipo = config['AJUSTES']['tipo']
valor_entrada = float(config['AJUSTES']['valor_entrada'])  # Convertir a tipo float

# Establecer conexión con IQ Option
API = IQ_Option(email, senha)
API.connect()

while True:
    escolha = 'demo'  # Aquí podrías cambiar a 'real' si lo deseas
    if escolha == 'demo':
        conta = 'PRACTICE'
        print('Cuenta demo seleccionada')
    activo = input('\n¿Qué activo desea operar? (ej. EURUSD o EURUSD-OTC): ')
    asset = activo
    print('Activo seleccionado:', asset)
    break

API.change_balance(conta)

# Ajustar un modelo LSTM
scaler = MinMaxScaler(feature_range=(0, 1))

# Función para obtener datos históricos y predecir en cada vela
def analyze_and_trade():
    # Obtener datos históricos reales para el activo deseado (ejemplo: EURUSD)
    historical_data = API.get_candles(asset, 600, 500, time.time())
    closes = [candle['close'] for candle in historical_data]

    # Escalar las últimas 100 velas
    scaled_closes = scaler.fit_transform(np.array(closes).reshape(-1, 1))
    scaled_last_100_candles = scaled_closes[-100:]

    # Preparar los datos para el modelo (asegúrate de haber definido look_back)
    look_back = 5
    X, y = [], []
    for i in range(len(scaled_last_100_candles) - look_back):
        X.append(scaled_last_100_candles[i:i+look_back, 0])
        y.append(scaled_last_100_candles[i+look_back, 0])

    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))  # Reshape para LSTM

    # Definir el modelo LSTM
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], 1)))
    model.add(LSTM(units=50))
    model.add(Dense(1))

    # Compilar el modelo
    model.compile(optimizer='adam', loss='mean_squared_error')

    # Ajustar el modelo LSTM
    model.fit(X, y, epochs=1, batch_size=1, verbose=2)

    # Hacer predicciones con el modelo LSTM para las siguientes 10 velas
    lstm_forecast = []
    current_sequence = scaled_closes[-look_back:].flatten()

    for _ in range(1):
        lstm_input = np.reshape(current_sequence, (1, look_back, 1))
        lstm_prediction = model.predict(lstm_input)
        lstm_forecast.append(scaler.inverse_transform(lstm_prediction)[0, 0])
        current_sequence = np.append(current_sequence[1:], lstm_prediction)

    # Obtener la última predicción
    predicted_price = lstm_forecast[-1]

    # Decidir dirección de la operación
    if closes[-1] < predicted_price:
        direction = 'call'
    elif closes[-1] > predicted_price:
        direction = 'put'
    else:
        direction = None

    if direction:
        # Abrir la operación
        compra(asset, valor_entrada, direction, 5, tipo)
        print('\nPrediccion de precio:', predicted_price)
        return True
    else:
        print('No se tomó ninguna decisión de operación.')
        return False

# Función para realizar la operación de compra
def compra(ativo, valor_entrada, direcao, exp, tipo):
    if tipo == 'digital':
        check, id = API.buy_digital_spot_v2(ativo, valor_entrada, direcao, exp)
    else:
        check, id = API.buy(valor_entrada, ativo, direcao, exp)

    if check:
        print('\n>> Orden abierta\nPar:', ativo, '\nTimeframe:', exp, '\nDireccion:', direcao, '\nEntrada de:', valor_entrada)   
    else:
        print('Error en la apertura de la orden,', id, ativo)

# Realizar 1000 operaciones consecutivas
operaciones_realizadas = 0
while operaciones_realizadas < 1000:
    if analyze_and_trade():
        operaciones_realizadas += 1
        print('\nOperaciones realizadas:', operaciones_realizadas)
        print('Balance actual:', API.get_balance())
    time.sleep(600)  # Esperar tiempo en segundos antes de realizar el próximo análisis

# Al finalizar, cerrar la conexión con IQ Option
API.disconnect()
