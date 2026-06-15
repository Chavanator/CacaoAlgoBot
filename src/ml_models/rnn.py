from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, SimpleRNN
from sklearn.preprocessing import MinMaxScaler
import numpy as np

from iqoptionapi.stable_api import IQ_Option
from configobj import ConfigObj
import warnings
import time
import sys
import pandas as pd
from datetime import datetime

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
        
# Function to get historical data and prepare for RNN
def get_historical_data_for_rnn(asset, interval, limit):
    historical_data = API.get_candles(asset, interval * 60, limit, time.time())
    closes = np.array([candle['close'] for candle in historical_data])
    return closes

# Function to prepare data for RNN (X, y)
def prepare_rnn_data(closes, look_back=60):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_closes = scaler.fit_transform(closes.reshape(-1, 1))

    X, y = [], []
    for i in range(len(scaled_closes) - look_back):
        X.append(scaled_closes[i:i + look_back, 0])
        y.append(1 if scaled_closes[i + look_back, 0] > scaled_closes[i + look_back - 1, 0] else 0)  # 1 for up, 0 for down

    X = np.array(X)
    y = np.array(y)
    return X, y, scaler

# Function to build and compile RNN model
def build_rnn_model(input_shape):
    model = Sequential()
    model.add(SimpleRNN(units=50, input_shape=(input_shape[1], 1), return_sequences=False))
    model.add(Dense(1, activation='sigmoid'))  # Output probability of going up
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

# Function to train the RNN model
def train_rnn_model(asset, interval, epochs=10, batch_size=32):
    closes = get_historical_data_for_rnn(asset, interval, 1000)
    X, y, scaler = prepare_rnn_data(closes)

    # Reshape X to [samples, time steps, features] for RNN
    X = X.reshape(X.shape[0], X.shape[1], 1)

    # Build the model
    rnn_model = build_rnn_model(X.shape)

    # Train the model
    rnn_model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=1)
    
    return rnn_model, scaler

# Function to make predictions using the trained RNN model
def predict_next_candle_direction(rnn_model, scaler, closes, look_back=60):
    scaled_closes = scaler.transform(closes.reshape(-1, 1))
    last_sequence = scaled_closes[-look_back:].reshape(1, look_back, 1)
    
    # Predict the probability of the next candle going up
    prediction = rnn_model.predict(last_sequence)
    
    return prediction[0][0]  # Probability of going up

# Train the RNN model for a specific asset and timeframe
rnn_model, scaler = train_rnn_model(asset, temporalidad_seleccionada)

# Realizar 1000 operaciones consecutivas
operaciones_realizadas = 0
ciclo_ganado = 0
valor_entrada_inicial = API.get_balance() / 100
valor_entrada = valor_entrada_inicial

# Use the model to predict the direction of the next candle
while operaciones_realizadas < 1000:
    time.sleep(0.1)
    minutos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime('%M.%S')[1:])
    sys.stdout.write(f'\rTiempo actual (minutos.segundos): {minutos:.2f}')
    sys.stdout.flush()
    entrar = minutos in {4.55, 9.55}  # Ajustar los tiempos para que coincidan con la temporalidad seleccionada

    if entrar:
        print('\n>> Iniciando análisis con RNN')
        closes = get_historical_data_for_rnn(asset, temporalidad_seleccionada, 1000)
        prediction = predict_next_candle_direction(rnn_model, scaler, closes)

        print(f'Probabilidad de que la próxima vela suba: {prediction:.2f}')
        
        # Decidir dirección de la operación en base a la predicción
        if prediction > 0.8:
            direction = 'call'
        elif prediction < 0.2:
            direction = 'put'
        
        # Realizar operación (se simula la operación aquí, sin un resultado numérico)
        resultado = prediction > 0.5
        if resultado:
            ciclo_ganado += 1
            if ciclo_ganado == 3:
                valor_entrada = valor_entrada_inicial
                ciclo_ganado = 0
        else:
            valor_entrada = valor_entrada_inicial
            ciclo_ganado = 0
        
        operaciones_realizadas += 1
        print('\nOperaciones realizadas:', operaciones_realizadas)
        print('Balance actual:', API.get_balance())
        time.sleep(60)
