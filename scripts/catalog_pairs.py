import os
from iqoptionapi.stable_api import IQ_Option
import time
import sys
from datetime import datetime
from tabulate import tabulate


def catag(API):
    

    pares_abertos = []

    all_asset = API.get_all_open_time()

    for par in all_asset['digital']:
        if all_asset['digital'][par]['open']:
            pares_abertos.append(par)

    for par in all_asset['turbo']:
        if all_asset['turbo'][par]['open']:
            if par not in pares_abertos:
                pares_abertos.append(par)
            

    timeframe = 60
    qnt_velas  = 120
    qnt_velas_m5= 146

    global resultado
    resultado = []

def obtener_pares_forex():
        try:
            all_assets = API.get_all_assets()  # Obtiene todos los instrumentos disponibles.
            pares_forex = [
                asset['name']
                for asset in all_assets['forex']  # Filtra por la categoría de Forex.
                if not asset['is_otc']           # Excluye los pares OTC.
            ]
            return pares_forex
        except Exception as e:
            print(f"Error al obtener la lista de pares Forex: {e}")
            return []

def mhi():
    global resultado
    pares_forex = obtener_pares_forex()  # Llama al filtro de pares Forex.
    
    if not pares_forex:
        print("No se encontraron pares Forex válidos.")
        return

    for par in pares_forex:
        try:
            velas = API.get_candles(par, timeframe, qnt_velas, time.time())

            if velas is None or len(velas) == 0:
                print(f"Error: No se pudieron obtener velas para el par {par}.")
                continue

            doji = 0
            win = 0
            loss = 0
            gale1 = 0
            gale2 = 0

            for i in range(3, len(velas) - 3):  # Evita índices fuera de rango
                minutos = int(datetime.fromtimestamp(velas[i]['from']).strftime('%M')[1:])

                if minutos == 5 or minutos == 0:
                    try:
                        vela1 = 'Verde' if velas[i - 3]['open'] < velas[i - 3]['close'] else 'Vermelha' if velas[i - 3]['open'] > velas[i - 3]['close'] else 'Doji'
                        vela2 = 'Verde' if velas[i - 2]['open'] < velas[i - 2]['close'] else 'Vermelha' if velas[i - 2]['open'] > velas[i - 2]['close'] else 'Doji'
                        vela3 = 'Verde' if velas[i - 1]['open'] < velas[i - 1]['close'] else 'Vermelha' if velas[i - 1]['open'] > velas[i - 1]['close'] else 'Doji'

                        entrada1 = 'Verde' if velas[i]['open'] < velas[i]['close'] else 'Vermelha' if velas[i]['open'] > velas[i]['close'] else 'Doji'
                        entrada2 = 'Verde' if velas[i + 1]['open'] < velas[i + 1]['close'] else 'Vermelha' if velas[i + 1]['open'] > velas[i + 1]['close'] else 'Doji'
                        entrada3 = 'Verde' if velas[i + 2]['open'] < velas[i + 2]['close'] else 'Vermelha' if velas[i + 2]['open'] > velas[i + 2]['close'] else 'Doji'

                        colores = [vela1, vela2, vela3]

                        if colores.count('Verde') > colores.count('Vermelha') and colores.count('Doji') == 0:
                            direccion = 'Vermelha'
                        elif colores.count('Vermelha') > colores.count('Verde') and colores.count('Doji') == 0:
                            direccion = 'Verde'
                        else:
                            doji += 1
                            continue

                        if entrada1 == direccion:
                            win += 1
                        elif entrada2 == direccion:
                            gale1 += 1
                        elif entrada3 == direccion:
                            gale2 += 1
                        else:
                            loss += 1

                    except IndexError:
                        print(f"Error de índice para el par {par} en la iteración {i}.")
                        continue

            total_entrada = win + gale1 + gale2 + loss

            if total_entrada > 0:
                porc_win = round(win / total_entrada * 100, 2)
                porc_gale1 = round((win + gale1) / total_entrada * 100, 2)
                porc_gale2 = round((win + gale1 + gale2) / total_entrada * 100, 2)

                resultado.append(['MHI', par, porc_win, porc_gale1, porc_gale2])
            else:
                print(f"No se realizaron entradas válidas para el par {par}.")

        except Exception as e:
            print(f"Error procesando el par {par}: {e}")

    def torres():
        global resultado
        for par in pares_abertos:
            velas = API.get_candles(par, timeframe,qnt_velas, time.time())
            doji = 0
            win = 0
            loss = 0
            gale1 = 0
            gale2 = 0

            for i in range(len(velas)):
                minutos = float(datetime.fromtimestamp(velas[i]['from']).strftime('%M')[1:])

                if minutos == 4 or minutos== 9:
                    try:
                        if i <2:
                            pass
                        else:

                            vela1 = 'Verde' if velas[i-4]['open'] < velas[i-4]['close'] else 'Vermelha' if velas[i-4]['open'] > velas[i-4]['close'] else 'Doji'

                            entrada1 = 'Verde' if velas[i]['open'] < velas[i]['close'] else 'Vermelha' if velas[i]['open'] > velas[i]['close'] else 'Doji'
                            entrada2 = 'Verde' if velas[i+1]['open'] < velas[i+1]['close'] else 'Vermelha' if velas[i+1]['open'] > velas[i+1]['close'] else 'Doji'
                            entrada3 ='Verde' if velas[i+2]['open'] < velas[i+2]['close'] else 'Vermelha' if velas[i+2]['open'] > velas[i+2]['close'] else 'Doji'

                            cores = vela1

                            if cores.count('Verde') > cores.count('Vermelha') and cores.count('Doji') == 0 : dir = 'Verde'
                        
                            if cores.count('Vermelha') > cores.count('Verde') and cores.count('Doji') == 0 : dir = 'Vermelha'

                            if cores.count('Doji') >0:
                                doji += 1
                            else:
                                if entrada1 == dir:
                                    win +=1
                                else:
                                    if entrada2 == dir:
                                        gale1 +=1
                                    else:
                                        if entrada3 == dir:
                                            gale2 +=1

                                        else:
                                            loss +=1
                    except:
                        pass

            total_entrada = win + gale1 + gale2 + loss
            qnt_win = win
            qnt_gale1 = win + gale1
            qnt_gale2 = win + gale1 + gale2

            win = round(qnt_win/(total_entrada)*100,2)
            gale1 = round(qnt_gale1/(total_entrada)*100,2)
            gale2 = round(qnt_gale2/(total_entrada)*100,2)

            resultado.append(['TORRES GÊMEAS']+[par]+ [win] +[gale1] + [gale2])

    def mhi_m5():
        global resultado
        for par in pares_abertos:
            velas = API.get_candles(par, 300 ,qnt_velas_m5, time.time())
            doji = 0
            win = 0
            loss = 0
            gale1 = 0
            gale2 = 0

            for i in range(len(velas)):
                minutos = float(datetime.fromtimestamp(velas[i]['from']).strftime('%M'))

                if minutos == 30 or minutos== 00:
                    try:
                        if i <2:
                            pass
                        else:

                            vela1 = 'Verde' if velas[i-3]['open'] < velas[i-3]['close'] else 'Vermelha' if velas[i-3]['open'] > velas[i-3]['close'] else 'Doji'
                            vela2 = 'Verde' if velas[i-2]['open'] < velas[i-2]['close'] else 'Vermelha' if velas[i-2]['open'] > velas[i-2]['close'] else 'Doji'
                            vela3 = 'Verde' if velas[i-1]['open'] < velas[i-1]['close'] else 'Vermelha' if velas[i-1]['open'] > velas[i-1]['close'] else 'Doji'

                            entrada1 = 'Verde' if velas[i]['open'] < velas[i]['close'] else 'Vermelha' if velas[i]['open'] > velas[i]['close'] else 'Doji'
                            entrada2 = 'Verde' if velas[i+1]['open'] < velas[i+1]['close'] else 'Vermelha' if velas[i+1]['open'] > velas[i+1]['close'] else 'Doji'
                            entrada3 ='Verde' if velas[i+2]['open'] < velas[i+2]['close'] else 'Vermelha' if velas[i+2]['open'] > velas[i+2]['close'] else 'Doji'

                            cores = vela1,vela2,vela3

                            if cores.count('Verde') > cores.count('Vermelha') and cores.count('Doji') == 0 : dir = 'Vermelha'
                        
                            if cores.count('Vermelha') > cores.count('Verde') and cores.count('Doji') == 0 : dir = 'Verde'

                            if cores.count('Doji') >0:
                                doji += 1
                            else:
                                if entrada1 == dir:
                                    win +=1
                                else:
                                    if entrada2 == dir:
                                        gale1 +=1
                                    else:
                                        if entrada3 == dir:
                                            gale2 +=1

                                        else:
                                            loss +=1
                    except:
                        pass

            total_entrada = win + gale1 + gale2 + loss
            qnt_win = win
            qnt_gale1 = win + gale1
            qnt_gale2 = win + gale1 + gale2

            win = round(qnt_win/(total_entrada)*100,2)
            gale1 = round(qnt_gale1/(total_entrada)*100,2)
            gale2 = round(qnt_gale2/(total_entrada)*100,2)

            resultado.append(['MHI M5'] + [par]+ [win] +[gale1] + [gale2])


    mhi()
    torres()
    mhi_m5()

    USE_MARTINGALE = os.getenv('USE_MARTINGALE', 'S').upper()
    MARTINGALE_LEVELS = int(os.getenv('MARTINGALE_LEVELS', '2'))
    if USE_MARTINGALE == 'S':
        if MARTINGALE_LEVELS == 0:
            linha = 2
        if MARTINGALE_LEVELS == 1:
            linha = 3
        if MARTINGALE_LEVELS >= 2:
            linha = 4
    else:
        linha = 2

    lista_catalog = sorted(resultado, key = lambda x: x[linha], reverse = True)

    return lista_catalog, linha