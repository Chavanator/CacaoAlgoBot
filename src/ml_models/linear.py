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
#Toma

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
    asset = 'USDCHF-OTC'
    print('Activo seleccionado:', asset)
    break

API.change_balance(conta)

# Ajustar un modelo LSTM
scaler = MinMaxScaler(feature_range=(0, 1))

# Función para obtener datos históricos y predecir en cada vela
def analyze_and_trade():
    # Obtener datos históricos reales para el activo deseado (ejemplo: EURUSD)
    historical_data = API.get_candles(asset, 300, 1000, time.time())
    closes = [candle['close'] for candle in historical_data]
    last_close = DataFrame(historical_data)['close'].iloc[-1]

    # Medias móviles
    # Crear un DataFrame de Pandas con los precios de cierre
    df = pd.DataFrame({'Close': closes})

    # Calcular la media móvil de 10 períodos
    df['MA10'] = df['Close'].rolling(window=10).mean()

    # Obtener el valor de la media móvil para el último período
    ma_10_periodos = df['MA10'].iloc[-1]

    print('Media Móvil de 10 períodos:', ma_10_periodos)

    # Calcular el True Range (TR) para cada vela
    highs = [candle['max'] for candle in historical_data]
    lows = [candle['min'] for candle in historical_data]
    tr_list = []
    for i in range(len(historical_data)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        tr_list.append(tr)
    # Calcular el ATR de 14 periodos
    #Cambiar 14 periodos a una variables
    PERIODOS=-14 
    
    atr = np.mean(tr_list[PERIODOS:])
    # Obtener la hora actual
    hora_actual = datetime.now()
    # Formatear la hora actual
    hora_formateada = hora_actual.strftime("%H:%M:%S")
    print("La gráfica de", asset, 'en la temporalidad de ', (300 / 60), "ha sido descargada correctamente'")
    print('A las', hora_formateada, 'horas')
    print('Ultimo cierre:', last_close)

    # Escalar las últimas 100 velas
    scaled_closes = scaler.fit_transform(np.array(closes).reshape(-1, 1))
    scaled_last_100_candles = scaled_closes[-1000:]

    # Preparar los datos para el modelo (asegúrate de haber definido look_back)
    look_back = 5
    X, y = [], []
    for i in range(len(scaled_last_100_candles) - look_back):
        X.append(scaled_last_100_candles[i:i + look_back, 0])
        y.append(scaled_last_100_candles[i + look_back, 0])

    X, y = np.array(X), np.array(y)

    # Definir el modelo de regresión lineal
    lin_model = LinearRegression()

    # Entrenar el modelo de regresión lineal
    lin_model.fit(X, y)

    # Hacer predicciones con el modelo de regresión lineal para las siguientes 10 velas
    lin_forecast = []
    current_sequence = scaled_closes[-look_back:].flatten()

    for _ in range(1):
        lin_prediction = lin_model.predict([current_sequence])
        lin_forecast.append(scaler.inverse_transform(lin_prediction.reshape(-1, 1))[0, 0])
        current_sequence = np.append(current_sequence[1:], lin_prediction)

    # Obtener la última predicción
    predicted_price = lin_forecast[-1]

    # Calcular métricas de evaluación
    rmse = mean_squared_error(y, lin_model.predict(X), squared=False)
    mae = mean_absolute_error(y, lin_model.predict(X))
    r2 = r2_score(y, lin_model.predict(X))

    # Calcular la dirección de la media móvil
    if df['MA10'].iloc[-1] > df['MA10'].iloc[-2]:
        trend_direction = 'alcista'  # Media móvil alcista
    else:
        trend_direction = 'bajista'  # Media móvil bajista
        
    print('\nPredicción de precio:', predicted_price)
    print('Tendencia de EMA:', trend_direction)
    print('RMSE:', rmse)
    print('MAE:', mae)
    print('R^2:', r2)

    # Establecer condiciones mínimas para entrar en la operación
    # Decidir dirección de la operación y otras acciones
# Establecer el umbral mínimo para el coeficiente de determinación (R²)
    umbral_r2 = 0.998

    # Establecer condiciones mínimas para entrar en la operación
    # Decidir dirección de la operación y otras acciones
    if closes[-1] < predicted_price and r2 >= umbral_r2:
        direction = 'call'
    elif closes[-1] > predicted_price and r2 >= umbral_r2:
        direction = 'put'
    else:
        direction = None

    if direction:
        # Abrir la operación
        valor_entrada = 10  # Aquí define el valor de entrada deseado
        compra(asset, valor_entrada, direction, 5, tipo)
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
        print('\n>> Orden abierta\nPar:', ativo, '\nTimeframe:', exp, '\nDirección:', direcao, '\nEntrada de:', valor_entrada, '\nTipo', tipo)
    else:
        print('Error en la apertura de la orden,', id, ativo)


# Realizar 1000 operaciones consecutivas
operaciones_realizadas = 0
while operaciones_realizadas < 1000:
    time.sleep(0.1)

    ### Horario do computador ###
    #minutos = float(datetime.now().strftime('%M.%S')[1:])

    ### horario da iqoption ###
    #segundos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime('%S.%f')[:-3])

    minutos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime('%M.%S')[1:])

    entrar = True if (minutos == 9.58 or minutos == 4.58) else False

    #print('Aguardando Horário de entrada', end='\r')
    if entrar:
        print('\n>> Iniciando análisis')
        analyze_and_trade()
        operaciones_realizadas += 1
        print('\nOperaciones realizadas:', operaciones_realizadas)
        print('Balance actual:', API.get_balance())
        time.sleep(0.1)

# Al finalizar, cerrar la conexión con IQ Option
API.disconnect()
