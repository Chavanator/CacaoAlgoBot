from iqoptionapi.stable_api import IQ_Option
from configobj import ConfigObj
import time
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression

# Cargar configuración desde el archivo
config = ConfigObj('config.txt')
email = config['LOGIN']['email']
senha = config['LOGIN']['senha']
tipo = config['AJUSTES']['tipo']
valor_entrada = float(config['AJUSTES']['valor_entrada'])  # Convertir a tipo float

# Establecer conexión con IQ Option
API = IQ_Option(email, senha)
API.connect()

escolha = 'demo'
# Seleccionar cuenta demo o real
while True:
    if escolha == 'demo':
        conta = 'PRACTICE'
        print('Cuenta demo seleccionada')
        break
    elif escolha == 'real':
        conta = 'REAL'
        print('Cuenta real seleccionada')
        break
    else:
        print('¡Elección incorrecta! Escriba demo o real')

API.change_balance(conta)


# Ajustar un modelo de Regresión Lineal
scaler = MinMaxScaler(feature_range=(0, 1))
linear_regressor = LinearRegression()

# Función para obtener datos históricos y predecir en cada vela
def analyze_and_trade():
    # Obtener datos históricos reales para el activo deseado (ejemplo: EURUSD)
    historical_data = API.get_candles('EURUSD-OTC', 600, 500, time.time())
    closes = [candle['close'] for candle in historical_data]

    # Escalar las últimas 100 velas
    scaled_last_100_candles = scaler.fit_transform(np.array(closes[-100:]).reshape(-1, 1))

    # Preparar los datos para el modelo (asegúrate de haber definido look_back)
    look_back = 10 # Definir el valor adecuado para tu estrategia
    X_pred = []
    for i in range(len(scaled_last_100_candles) - look_back):
        X_pred.append(scaled_last_100_candles[i:i + look_back, 0])

    X_pred = np.array(X_pred)

    # Usar un Regresor Lineal
    linear_regressor.fit(X_pred, scaled_last_100_candles[look_back:, 0])

    # Hacer predicciones con el Regresor Lineal para las siguientes 10 velas
    linear_forecast = []
    current_sequence = scaled_last_100_candles[-look_back:].flatten()

    for _ in range(10):
        linear_prediction = linear_regressor.predict(np.reshape(current_sequence, (1, -1)))
        linear_forecast.append(scaler.inverse_transform(linear_prediction.reshape(-1, 1))[0, 0])
        current_sequence = np.append(current_sequence[1:], linear_prediction)

    # Obtener la última predicción
    predicted_price = linear_forecast[-1]
    
    # Decidir dirección de la operación
    if closes[-1] < predicted_price:
        direction = 'call'
    elif closes[-1] > predicted_price:
        direction = 'put'
    else:
        direction = None

    if direction:
        # Abrir la operación
        time.time()
        compra('EURUSD-OTC', valor_entrada, direction, 10, tipo)
        print('\n Prediccion de precio', predicted_price)
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
        print('\n >> Orden abierta \n Par:', ativo, '\n Timeframe:',exp, '\n Direccion:', direcao, '\n Entrada de:', valor_entrada)   
    else:
        print('Error en la apertura de la orden,', id, ativo)


# Realizar 1000 operaciones consecutivas
operaciones_realizadas = 0
while operaciones_realizadas < 1000:
    if analyze_and_trade():
        operaciones_realizadas += 1
        print('\n Operaciones realizadas:', operaciones_realizadas)
        print('\n Balance actual:', API.get_balance())
    time.sleep(600)  # Esperar tiempo en segundos antes de realizar el próximo análisis

# Al finalizar, cerrar la conexión con IQ Option
API.disconnect()