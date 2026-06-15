from iqoptionapi.stable_api import IQ_Option
import pandas as pd
import os
import time
from dotenv import load_dotenv

load_dotenv()

email = os.getenv('IQ_EMAIL', '')
senha = os.getenv('IQ_PASSWORD', '')
if not email or not senha:
    print("Error: IQ_EMAIL and IQ_PASSWORD must be set in .env file")
    exit(1)

OUTPUT_DIR = os.getenv('HISTORICAL_DATA_DIR', 'data/historical')

API = IQ_Option(email, senha)
API.connect()

if API.check_connect():
    print("Connection established successfully")
else:
    print("Error connecting to IQ Option")
    exit(1)

# Pares de divisas y temporalidades
symbols = ['GBPJPY',
    'GBPJPY-OTC',
    'EURJPY',
    'EURJPY-OTC',
    'USDJPY',
    'USDJPY-OTC',
    'CADCHF'
]

timeframes = {
    '1m': 60,
    '5m': 300,
    '15m': 900,
    '1h': 3600
}

def obtener_datos_historicos(API, symbol, timeframe, timeframe_name):
    # Crear un DataFrame de Pandas vacío
    df_total = pd.DataFrame()

    # Establecer el número de velas y fechas deseadas
    num_candles = 1000
    num_dates = 100
    
    for i in range(num_dates):
        try:
            end_time = API.get_server_timestamp() - (i * timeframe * num_candles)
            candles = API.get_candles(symbol, timeframe, num_candles, end_time)

            # Crear un DataFrame con los datos de las velas
            df = pd.DataFrame(candles)
            df['at'] = pd.to_datetime(df['from'], unit='s')  # Convertir timestamp a datetime
            df.set_index('at', inplace=True)  # Establecer 'at' como el índice

            # Crear los directorios si no existen
            file_dir = f'{OUTPUT_DIR}/{symbol}/{timeframe_name}/'
            os.makedirs(file_dir, exist_ok=True)

            # Guardar los datos en un archivo CSV
            date_str = df.index[-1].strftime('%Y%m%d%H%M%S')  # Convertir la fecha a string
            file_path = os.path.join(file_dir, f'{symbol}_{timeframe_name}_{date_str}.csv')
            df.to_csv(file_path, columns=['open', 'close', 'min', 'max'])

            # Confirmar la descarga de la gráfica
            print(f"La gráfica para {symbol} en temporalidad {timeframe_name} ha sido descargada correctamente como '{file_path}'")

            # Dormir un poco para evitar limitaciones de la API
            time.sleep(1)
        except Exception as e:
            print(f"Error al obtener datos para {symbol} en la iteración {i}: {e}")

# Descargar datos para todos los símbolos y temporalidades
for symbol in symbols:
    for timeframe_name, timeframe in timeframes.items():
        obtener_datos_historicos(API, symbol, timeframe, timeframe_name)

API.close()
print("Connection closed")
