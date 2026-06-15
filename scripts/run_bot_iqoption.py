import os
import sys
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

from iqoptionapi.stable_api import IQ_Option
from tabulate import tabulate
from colorama import init, Fore, Back

from catalog_pairs import catag

load_dotenv()

init(autoreset=True)
green = Fore.GREEN
yellow = Fore.YELLOW
red = Fore.RED
white = Fore.WHITE

print(green+'''
      
    ██╗     ██╗   ██╗ ██████╗ █████╗ ███████╗     ██████╗ ██████╗ ██████╗ ███████╗
    ██║     ██║   ██║██╔════╝██╔══██╗██╔════╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██║     ██║   ██║██║     ███████║███████╗    ██║     ██║   ██║██║  ██║█████╗  
    ██║     ██║   ██║██║     ██╔══██║╚════██║    ██║     ██║   ██║██║  ██║██╔══╝  
    ███████╗╚██████╔╝╚██████╗██║  ██║███████║    ╚██████╗╚██████╔╝██████╔╝███████╗
    ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝'''+yellow+'''
                                                                                    
                            Cacao_QuantBot - Automated Trading Framework

''')

print(yellow + '***************************************************************************************\n\n')

### LOADING CONFIGURATION ####
email = os.getenv('IQ_EMAIL', '')
senha = os.getenv('IQ_PASSWORD', '')
tipo = os.getenv('TRADE_TYPE', 'automatico')
valor_entrada = float(os.getenv('DEFAULT_TRADE_AMOUNT', '5'))
stop_win = float(os.getenv('DEFAULT_STOP_WIN', '100'))
stop_loss = float(os.getenv('DEFAULT_STOP_LOSS', '100'))
lucro_total = 0
stop = True

USE_MARTINGALE = os.getenv('USE_MARTINGALE', 'S').upper()
if USE_MARTINGALE == 'S':
    martingale = int(os.getenv('MARTINGALE_LEVELS', '2'))
else:
    martingale = 0
fator_mg = float(os.getenv('MARTINGALE_FACTOR', '2.0'))

USE_SOROS = os.getenv('USE_SOROS', 'N').upper()
if USE_SOROS == 'S':
    soros = True
    niveis_soros = int(os.getenv('SOROS_LEVELS', '2'))
    nivel_soros = 0
else:
    soros = False
    niveis_soros = 0
    nivel_soros = 0

valor_soros = 0
lucro_op_atual = 0

analise_medias = os.getenv('ANALISE_MEDIAS', 'N').upper()
velas_medias = int(os.getenv('VELAS_MEDIAS', '10'))

print(yellow+'Connecting to IQ Option')
API = IQ_Option(email, senha)

check, reason = API.connect()
if check:
    print(green + '\nConnected successfully')
else:
    if reason == '{"code":"invalid_credentials","message":"You entered the wrong credentials. Please ensure that your login/password is correct."}':
        print(red+'\nInvalid email or password')
        sys.exit()
    else:
        print(red+ '\nConnection failed')
        print(reason)
        sys.exit()

while True:
    escolha = input(green+'\n>>'+ white +' Select account:\n'+
                            green+'>>'+ white +' 1 - Demo\n'+
                            green+'>>'+ white +' 2 - Real\n'+
                            green+'-->'+ white +' ')
    escolha = int(escolha)
    if escolha == 1:
        conta = 'PRACTICE'
        print('Demo account selected')
        break
    if escolha == 2:
        conta = 'REAL'
        print('Real account selected')
        break
    else:
        print(red+'Invalid choice! Enter 1 or 2')

API.change_balance(conta)

def check_stop():
    global stop, lucro_total
    if lucro_total <= float('-'+str(abs(stop_loss))):
        stop = False
        print(red+'\n#########################')
        print(red+'STOP LOSS REACHED ', str(cifrao), str(lucro_total))
        print(red+'#########################')
        sys.exit()
    if lucro_total >= float(abs(stop_win)):
        stop = False
        print(green+'\n#########################')
        print(green+'STOP WIN REACHED ', str(cifrao), str(lucro_total))
        print(green+'#########################')
        sys.exit()

def payout(par):
    profit = API.get_all_profit()
    all_asset = API.get_all_open_time()
    try:
        if all_asset['binary'][par]['open']:
            if profit[par]['binary'] > 0:
                binary = round(profit[par]['binary'], 2) * 100
        else:
            binary = 0
    except:
        binary = 0
    try:
        if all_asset['turbo'][par]['open']:
            if profit[par]['turbo'] > 0:
                turbo = round(profit[par]['turbo'], 2) * 100
        else:
            turbo = 0
    except:
        turbo = 0
    try:
        if all_asset['digital'][par]['open']:
            digital = API.get_digital_payout(par)
        else:
            digital = 0
    except:
        digital = 0
    return binary, turbo, digital

def compra(ativo, valor_entrada, direcao, exp, tipo):
    global stop, lucro_total, nivel_soros, niveis_soros, valor_soros, lucro_op_atual
    if soros:
        if nivel_soros == 0:
            entrada = valor_entrada
        if nivel_soros >= 1 and valor_soros > 0 and nivel_soros <= niveis_soros:
            entrada = valor_entrada + valor_soros
        if nivel_soros > niveis_soros:
            lucro_op_atual = 0
            valor_soros = 0
            entrada = valor_entrada
            nivel_soros = 0
    else:
        entrada = valor_entrada
    for i in range(martingale + 1):
        if stop == True:
            if tipo == 'digital':
                check, id = API.buy_digital_spot_v2(ativo, entrada, direcao, exp)
            else:
                check, id = API.buy(entrada, ativo, direcao, exp)
            if check:
                if i == 0:
                    print(yellow + '\n>>'+white+' Order opened\n'+yellow+'>>'+white+' Pair:', ativo, '\n'+yellow+'>> '+white+'Timeframe:', exp, '\n'+yellow+'>>'+white+' Amount:', cifrao, entrada)
                if i >= 1:
                    print(yellow + '\n>>'+white+' Martingale order', str(i), '\n'+yellow+'>>'+white+' Pair:', ativo, '\n'+yellow+'>> '+white+'Timeframe:', exp, '\n'+yellow+'>>'+white+' Amount:', cifrao, entrada)
                while True:
                    time.sleep(0.1)
                    status, resultado = API.check_win_digital_v2(id) if tipo == 'digital' else API.check_win_v4(id)
                    if status:
                        lucro_total += round(resultado, 2)
                        valor_soros += round(resultado, 2)
                        lucro_op_atual += round(resultado, 2)
                        if resultado > 0:
                            if i == 0:
                                print(green+ '\n>> Result: WIN \n'+white+'>> Profit:', round(resultado, 2), '\n>> Pair:', ativo, '\n>> Total profit: ', round(lucro_total, 2))
                            if i >= 1:
                                print(green+ '\n>> Result: WIN on martingale', str(i)+white+'\n>> Profit:', round(resultado, 2), '\n>> Pair:', ativo, '\n>> Total profit: ', round(lucro_total, 2))
                        elif resultado == 0:
                            if i == 0:
                                print(yellow +'\n>> Result: DRAW \n'+white+'>> Profit:', round(resultado, 2), '\n>> Pair:', ativo, '\n>> Total profit: ', round(lucro_total, 2))
                            if i >= 1:
                                print(yellow+'\n>> Result: DRAW on martingale', str(i), '\n'+white+'>> Profit:', round(resultado, 2), '\n>> Pair:', ativo, '\n>> Total profit: ', round(lucro_total, 2))
                            if i+1 <= martingale:
                                gale = float(entrada)
                                entrada = round(abs(gale), 2)
                        else:
                            if i == 0:
                                print(red+'\n>> Result: LOSS \n'+white+'>> Profit:', round(resultado, 2), '\n>> Pair:', ativo, '\n>> Total profit: ', round(lucro_total, 2))
                            if i >= 1:
                                print(red+'\n>> Result: LOSS on martingale', str(i), '\n'+white+'>> Profit:', round(resultado, 2), '\n>> Pair:', ativo, '\n>> Total profit: ', round(lucro_total, 2))
                            if i+1 <= martingale:
                                gale = float(entrada) * float(fator_mg)
                                entrada = round(abs(gale), 2)
                        check_stop()
                        break
                if resultado > 0:
                    break
            else:
                print('Error opening order,', id, ativo)
    if soros:
        if lucro_op_atual > 0:
            nivel_soros += 1
            lucro_op_atual = 0
        else:
            valor_soros = 0
            nivel_soros = 0
            lucro_op_atual = 0

def horario():
    x = API.get_server_timestamp()
    now = datetime.fromtimestamp(API.get_server_timestamp())
    return now

def medias(velas):
    soma = 0
    for i in velas:
        soma += i['close']
    media = soma / velas_medias
    if media > velas[-1]['close']:
        tendencia = 'put'
    else:
        tendencia = 'call'
    return tendencia

def estrategia_mhi():
    global tipo
    if tipo == 'automatico':
        binary, turbo, digital = payout(ativo)
        print(binary, turbo, digital)
        if digital > turbo:
            print('Entries will be on digital options')
            tipo = 'digital'
        elif turbo > digital:
            print('Entries will be on binary options')
            tipo = 'binary'
        else:
            print('Pair closed, choose another')
            sys.exit()
    while True:
        time.sleep(0.1)
        minutos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime('%M.%S')[1:])
        entrar = True if (minutos >= 4.59 and minutos <= 5.00) or minutos >= 9.59 else False
        print('Awaiting entry time', minutos, end='\r')
        if entrar:
            print('\n>> Starting MHI strategy analysis')
            direcao = False
            timeframe = 60
            qnt_velas = 3
            if analise_medias == 'S':
                velas = API.get_candles(ativo, timeframe, velas_medias, time.time())
                tendencia = medias(velas)
            else:
                velas = API.get_candles(ativo, timeframe, qnt_velas, time.time())
            velas[-1] = 'Green' if velas[-1]['open'] < velas[-1]['close'] else 'Red' if velas[-1]['open'] > velas[-1]['close'] else 'Doji'
            velas[-2] = 'Green' if velas[-2]['open'] < velas[-2]['close'] else 'Red' if velas[-2]['open'] > velas[-2]['close'] else 'Doji'
            velas[-3] = 'Green' if velas[-3]['open'] < velas[-3]['close'] else 'Red' if velas[-3]['open'] > velas[-3]['close'] else 'Doji'
            cores = velas[-3], velas[-2], velas[-1]
            if cores.count('Green') > cores.count('Red') and cores.count('Doji') == 0:
                direcao = 'put'
            if cores.count('Green') < cores.count('Red') and cores.count('Doji') == 0:
                direcao = 'call'
            if analise_medias == 'S':
                if direcao == tendencia:
                    pass
                else:
                    direcao = 'abort'
            if direcao == 'put' or direcao == 'call':
                print('Candles: ', velas[-3], velas[-2], velas[-1], ' - Entry for ', direcao)
                compra(ativo, valor_entrada, direcao, 1, tipo)
                print('\n')
            else:
                if direcao == 'abort':
                    print('Candles: ', velas[-3], velas[-2], velas[-1])
                    print('Entry aborted - Against trend.')
                else:
                    print('Candles: ', velas[-3], velas[-2], velas[-1])
                    print('Entry aborted - Doji found.')
                time.sleep(2)
            print('\n######################################################################\n')

def estrategia_torresgemeas():
    global tipo
    if tipo == 'automatico':
        binary, turbo, digital = payout(ativo)
        print(binary, turbo, digital)
        if digital > turbo:
            print('Entries will be on digital options')
            tipo = 'digital'
        elif turbo > digital:
            print('Entries will be on binary options')
            tipo = 'binary'
        else:
            print('Pair closed, choose another')
            sys.exit()
    while True:
        time.sleep(0.1)
        minutos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime('%M.%S')[1:])
        entrar = True if (minutos >= 3.59 and minutos <= 4.00) or (minutos >= 8.59 and minutos <= 9.00) else False
        print('Awaiting entry time', minutos, end='\r')
        if entrar:
            print('\n>> Starting Torres Gemeas strategy analysis')
            direcao = False
            timeframe = 60
            qnt_velas = 4
            if analise_medias == 'S':
                velas = API.get_candles(ativo, timeframe, velas_medias, time.time())
                tendencia = medias(velas)
            else:
                velas = API.get_candles(ativo, timeframe, qnt_velas, time.time())
            velas[-4] = 'Green' if velas[-4]['open'] < velas[-4]['close'] else 'Red' if velas[-4]['open'] > velas[-4]['close'] else 'Doji'
            cores = velas[-4]
            if cores.count('Green') > cores.count('Red') and cores.count('Doji') == 0:
                direcao = 'call'
            if cores.count('Green') < cores.count('Red') and cores.count('Doji') == 0:
                direcao = 'put'
            if analise_medias == 'S':
                if direcao == tendencia:
                    pass
                else:
                    direcao = 'abort'
            if direcao == 'put' or direcao == 'call':
                print('Candles: ', velas[-4], ' - Entry for ', direcao)
                compra(ativo, valor_entrada, direcao, 1, tipo)
                print('\n')
            else:
                if direcao == 'abort':
                    print('Candles: ', velas[-4])
                    print('Entry aborted - Against trend.')
                else:
                    print('Candles: ', velas[-4])
                    print('Entry aborted - Doji found.')
                time.sleep(2)
            print('\n######################################################################\n')

def estrategia_mhi_m5():
    global tipo
    if tipo == 'automatico':
        binary, turbo, digital = payout(ativo)
        print(binary, turbo, digital)
        if digital > turbo:
            print('Entries will be on digital options')
            tipo = 'digital'
        elif turbo > digital:
            print('Entries will be on binary options')
            tipo = 'binary'
        else:
            print('Pair closed, choose another')
            sys.exit()
    while True:
        time.sleep(0.1)
        minutos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime('%M.%S'))
        entrar = True if (minutos >= 29.59 and minutos <= 30.00) or minutos == 59.59 else False
        print('Awaiting entry time', minutos, end='\r')
        if entrar:
            print('\n>> Starting MHI M5 strategy analysis')
            direcao = False
            timeframe = 300
            qnt_velas = 3
            if analise_medias == 'S':
                velas = API.get_candles(ativo, timeframe, velas_medias, time.time())
                tendencia = medias(velas)
            else:
                velas = API.get_candles(ativo, timeframe, qnt_velas, time.time())
            velas[-1] = 'Green' if velas[-1]['open'] < velas[-1]['close'] else 'Red' if velas[-1]['open'] > velas[-1]['close'] else 'Doji'
            velas[-2] = 'Green' if velas[-2]['open'] < velas[-2]['close'] else 'Red' if velas[-2]['open'] > velas[-2]['close'] else 'Doji'
            velas[-3] = 'Green' if velas[-3]['open'] < velas[-3]['close'] else 'Red' if velas[-3]['open'] > velas[-3]['close'] else 'Doji'
            cores = velas[-3], velas[-2], velas[-1]
            if cores.count('Green') > cores.count('Red') and cores.count('Doji') == 0:
                direcao = 'put'
            if cores.count('Green') < cores.count('Red') and cores.count('Doji') == 0:
                direcao = 'call'
            if analise_medias == 'S':
                if direcao == tendencia:
                    pass
                else:
                    direcao = 'abort'
            if direcao == 'put' or direcao == 'call':
                print('Candles: ', velas[-3], velas[-2], velas[-1], ' - Entry for ', direcao)
                compra(ativo, valor_entrada, direcao, 5, tipo)
                print('\n')
            else:
                if direcao == 'abort':
                    print('Candles: ', velas[-3], velas[-2], velas[-1])
                    print('Entry aborted - Against trend.')
                else:
                    print('Candles: ', velas[-3], velas[-2], velas[-1])
                    print('Entry aborted - Doji found.')
                time.sleep(2)
            print('\n######################################################################\n')

### USER INPUTS ###
perfil = json.loads(json.dumps(API.get_profile_ansyc()))
cifrao = str(perfil['currency_char'])
nome = str(perfil['name'])
valorconta = float(API.get_balance())

print(yellow+'\n######################################################################')
print('\nHello, ', nome, '\nWelcome to Cacao_QuantBot.')
print('\nYour account balance is', cifrao, valorconta)
print('\nEntry amount:', cifrao, valor_entrada)
print('\nStop win:', cifrao, stop_win)
print('\nStop loss:', cifrao, '-', stop_loss)
print(yellow+'\n######################################################################\n\n')

print('>> Starting pair cataloging')
lista_catalog, linha = catag(API)
print(yellow+ tabulate(lista_catalog, headers=['STRATEGY', 'PAIR', 'WIN', 'GALE1', 'GALE2']))
estrateg = lista_catalog[0][0]
ativo = lista_catalog[0][1]
assertividade = lista_catalog[0][linha]
print('\n>> Best pair: ', ativo, ' | Strategy: ', estrateg, ' | Accuracy: ', assertividade)
print('\n')

while True:
    estrategia = input(green+'\n>>'+ white +' Select strategy:\n'+
                            green+'>>'+ white +' 1 - MHI\n'+
                            green+'>>'+ white +' 2 - Torres Gemeas\n'+
                            green+'>>'+ white +' 3 - MHI M5\n'+
                            green+'-->'+ white +' ')
    estrategia = int(estrategia)
    if estrategia in [1, 2, 3]:
        break
    else:
        print(red+'Invalid choice! Enter 1, 2, or 3')

ativo = input(green+ '\n>>'+white+' Enter the asset to trade: ').upper()
print('\n')

if estrategia == 1:
    estrategia_mhi()
elif estrategia == 2:
    estrategia_torresgemeas()
elif estrategia == 3:
    estrategia_mhi_m5()
