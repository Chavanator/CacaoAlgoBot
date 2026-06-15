from iqoptionapi.stable_api import IQ_Option
from configobj import ConfigObj
import warnings
import time
import sys
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
balance_account = API.get_balance()
print('Balance actual:', balance_account)

def obtener_activos_disponibles():
    activos = API.get_all_open_time()
    return [activo for activo in activos['binary'] if activos['binary'][activo]['open']]

def mostrar_menu_activos(activos):
    print("\nActivos disponibles:")
    for idx, activo in enumerate(activos, 1):
        print(f"{idx}. {activo}")

def mostrar_menu_temporalidades():
    temporalidades = {1: "1 minuto", 5: "5 minutos", 15: "15 minutos", 60: "1 hora"}
    print("\nTemporalidades disponibles:")
    for key, value in temporalidades.items():
        print(f"{key}. {value}")
    return temporalidades

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
valor_entrada = balance_account / 100  # Valor de entrada deseado

temporalidades = mostrar_menu_temporalidades()

while True:
    try:
        seleccion_temporalidad = int(input("\nSeleccione la temporalidad para operar: "))
        if seleccion_temporalidad in temporalidades:
            temporalidad_seleccionada = seleccion_temporalidad
            print('Temporalidad seleccionada:', temporalidades[temporalidad_seleccionada])
            break
        else:
            print("Selección inválida. Por favor, seleccione un número de la lista.")
    except ValueError:
        print("Entrada inválida. Por favor, ingrese un número.")

# Función para obtener datos históricos
def get_historical_data(asset, interval, limit):
    return API.get_candles(asset, interval * 60, limit, time.time())

# Función para realizar el análisis y trading
def analyze_and_trade(asset, valor_entrada, interval):
    historical_data = get_historical_data(asset, interval, 1000)
    closes = np.array([candle['close'] for candle in historical_data])

    # Imprimir el último cierre de la temporalidad seleccionada
    print(f'Último cierre de {interval} minutos: {closes[-1]}')

    # Preparar datos para el modelo
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_closes = scaler.fit_transform(closes.reshape(-1, 1))

    look_back = 200
    X, y = [], []
    for i in range(len(scaled_closes) - look_back):
        X.append(scaled_closes[i:i + look_back, 0])
        y.append(scaled_closes[i + look_back, 0])

    X, y = np.array(X), np.array(y)

    # Entrenar el modelo de regresión lineal para la temporalidad seleccionada
    lin_model = LinearRegression()
    lin_model.fit(X, y)

    # Hacer predicciones con el modelo
    lin_forecast = lin_model.predict([scaled_closes[-look_back:].flatten()])
    predicted_price = scaler.inverse_transform(lin_forecast.reshape(-1, 1))[0, 0]

    # Imprimir las predicciones
    print(f'Predicción de {interval} minutos: {predicted_price}')

    # Comparar la tendencia
    if predicted_price > closes[-1]:
        direction = 'call'
    elif predicted_price < closes[-1]:
        direction = 'put'
    else:
        print('No se tomó ninguna decisión de operación.')
        return False, valor_entrada

    # Realizar operación de compra
    resultado_operacion, nuevo_valor_entrada = compra(asset, valor_entrada, interval, direction, tipo)
    return resultado_operacion, nuevo_valor_entrada

# Función para realizar la operación de compra
def compra(asset, valor_entrada, exp, direction, tipo):
    if tipo == 'digital':
        check, id = API.buy_digital_spot(asset, valor_entrada, direction, exp * 60)
    else:
        check, id = API.buy(valor_entrada, asset, direction, exp * 60)

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
    sys.stdout.write(f'\rTiempo actual (minutos.segundos): {minutos:.2f}')
    sys.stdout.flush()
    entrar = minutos in {4.58, 9.58}  # Ajustar los tiempos para que coincidan con la temporalidad seleccionada

    if entrar:
        print('\n>> Iniciando análisis')
        resultado, nuevo_valor_entrada = analyze_and_trade(asset, valor_entrada, temporalidad_seleccionada)
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
