from iqoptionapi.stable_api import IQ_Option
from configobj import ConfigObj
import pandas as pd
import os
import time

# Load configuration from the file
config = ConfigObj('config.txt')
email = config['LOGIN']['email']
senha = config['LOGIN']['senha']

# Establish connection with IQ Option
API = IQ_Option(email, senha)
API.connect()

# Verificar si la conexión fue exitosa
if API.check_connect():
    print("Conexión establecida con éxito")
else:
    print("Error al conectar")
    exit()

# Definir el símbolo y la temporalidad
symbol = 'EURUSD'
timeframe = 300  # 5 minutos en segundos
timeframe_name = '5m'

def obtener_datos_historicos(API, symbol, timeframe, timeframe_name, start_date, end_date):
    # Crear un DataFrame de Pandas vacío
    df_total = pd.DataFrame()

    try:
        # Obtener las velas históricas por lotes de tiempo
        num_candles = 1000
        start_time = end_date.timestamp()
        while start_time > start_date.timestamp():
            candles = API.get_candles(symbol, timeframe, num_candles, start_time)
            df = pd.DataFrame(candles)
            df['at'] = pd.to_datetime(df['from'], unit='s')  # Convertir timestamp a datetime
            df.set_index('at', inplace=True)  # Establecer 'at' como el índice
            df_total = pd.concat([df_total, df])
            start_time = df['from'].iloc[0] - 1  # Siguiente lote de velas

        # Crear el directorio si no existe
        file_dir = f'D:/iqrobot/df_test/{symbol}/{timeframe_name}/'
        os.makedirs(file_dir, exist_ok=True)

        # Guardar los datos en un archivo CSV
        file_path = os.path.join(file_dir, f'{symbol}_{timeframe_name}_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv')
        df_total.to_csv(file_path, columns=['open', 'close', 'min', 'max', 'volume'])

        # Confirmar la descarga de la gráfica
        print(f"La gráfica para {symbol} en temporalidad {timeframe_name} ha sido descargada correctamente como '{file_path}'")

        # Dormir un poco para evitar limitaciones de la API
        time.sleep(1)
    except Exception as e:
        print(f"Error al obtener datos para {symbol}: {e}")

# Definir la fecha de inicio y la fecha de fin
start_date = pd.Timestamp('2021-01-01', tz='UTC')
end_date = pd.Timestamp('2024-07-01', tz='UTC')

# Descargar datos para el par EUR/USD en temporalidad de 5 minutos
obtener_datos_historicos(API, symbol, timeframe, timeframe_name, start_date, end_date)

# Desconectar de la API
API.close_connection()
print("Conexión cerrada")
