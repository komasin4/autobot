import pyupbit
import pandas as pd
import time
from datetime import datetime
from pytz import timezone
import requests
import json

global rsi_pre_old
global rsi_pre_old2
global trade
global price_unit

rsi_pre_old = 0
rsi_pre_old2 = 0
trade = 'N'
price_unit = 5000

#key값을 읽어옴
f = open("./key/key.txt", 'r')
while True:
    line = f.readline()
    if not line:
        break
    strParse = line.split("|")
    if(strParse[0] == "access"):
        access = strParse[1]
    elif(strParse[0] == "secret"):
        secret = strParse[1]
    elif(strParse[0] == "token"):
        token = strParse[1]
    elif(strParse[0] == "chatid"):
        chatid = strParse[1]
f.close()

upbit = pyupbit.Upbit(access, secret)  # 업비트 객체를 만듭니다.

#텔레그램 메시지 전송
def telegram_send(token, chatid, msg):
    API_HOST = "https://api.telegram.org/bot"
    url = API_HOST + token + '/sendmessage'
    headers = {'Content-Type': 'application/json',
               'charset': 'UTF-8', 'Accept': '*/*'}
    body = {
        "chat_id": chatid,
        "text": msg
    }

    try:
        response = requests.post(url, body)
        print("response status %r" % response.status_code)
        print("response text %r" % response.text)
    except Exception as ex:
        print(ex)

def GetRSI(ohlcv, period):
    ohlcv["close"] = ohlcv["close"]
    delta = ohlcv["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    return pd.Series(100 - (100 / (1 + RS)), name="RSI")

def GetKRW(balances):
    krw = 0
    for value in balances:
        try:
            ticker = value['currency']
            if ticker == "KRW":  # 원화일 때는 평균 매입 단가가 0이므로 구분해서 총 평가금액을 구한다.
                krw = value['balance']
                break
        except Exception as e:
            print("GetKRW error:", e)
    return krw
    

def GetTotalRealMoney(balances):
    total = 0.0
    for value in balances:

        try:
            ticker = value['currency']
            if ticker == "KRW":  # 원화일 때는 평균 매입 단가가 0이므로 구분해서 총 평가금액을 구한다.
                total += (float(value['balance']) + float(value['locked']))
            else:

                avg_buy_price = float(value['avg_buy_price'])
                # 드랍받은 코인(평균매입단가가 0이다) 제외 하고 현재가격으로 평가금액을 구한다,.
                if avg_buy_price != 0 and (float(value['balance']) != 0 or float(value['locked']) != 0):
                    realTicker = value['unit_currency'] + \
                        "-" + value['currency']

                    time.sleep(0.1)
                    nowPrice = pyupbit.get_current_price(realTicker)
                    total += (float(nowPrice) *
                              (float(value['balance']) + float(value['locked'])))
        except Exception as e:
            print("GetTotalRealMoney error:", e)

    return total

#총 원금을 구한다!
def GetTotalMoney(balances):
    total = 0.0
    for value in balances:
        try:
            ticker = value['currency']
            if ticker == "KRW": #원화일 때는 평균 매입 단가가 0이므로 구분해서 총 평가금액을 구한다.
                total += (float(value['balance']) + float(value['locked']))
            else:
                avg_buy_price = float(value['avg_buy_price'])

                #매수평균가(avg_buy_price)가 있으면서 잔고가 0이 아닌 코인들의 총 매수가격을 더해줍니다.
                if avg_buy_price != 0 and (float(value['balance']) != 0 or float(value['locked']) != 0):
                    #balance(잔고 수량) + locked(지정가 매도로 걸어둔 수량) 이렇게 해야 제대로 된 값이 구해집니다.
                    #지정가 매도 주문이 없다면 balance에 코인 수량이 100% 있지만 지정가 매도 주문을 걸면 그 수량만큼이 locked로 옮겨지기 때문입니다.
                    total += (avg_buy_price * (float(value['balance']) + float(value['locked'])))
        except Exception as e:
            print("GetTotalMoney error:", e)
    return total


def GetAmount(type, TotalRealMoney):
    type_ratio = {"BUY": 0.05, "SELL": 0.05}.get(type, 0)
    return round(TotalRealMoney*type_ratio)

def GetRevenue(TotalMoeny, TotalRealMoney):
    return (TotalRealMoney - TotalMoeny) * 100.0 / TotalMoeny

def Monitor():
    global rsi_pre_old
    global rsi_pre_old2
    global trade
    global price_unit
    global token
    global chatid
    
    #strSend = "%s,%f,%f"%("메시지", 1.2, 1.3)
    #telegram_send(token, chatid, strSend)
    
    #df = pyupbit.get_ohlcv("KRW-BTC", interval="minute3")
    df = pyupbit.get_ohlcv("KRW-BTC", interval="minute1")

    rsi_pre_old2 = rsi_pre_old

    #RSI14지표를 구합니다.
    rsi_pre = float(GetRSI(df, 14).iloc[-2])
    rsi_now = float(GetRSI(df, 14).iloc[-1])

    addString = ""
    rsiChangeString = ""
    rsiChange = False
    
    now_price = df["close"].iloc[-1]

    balances = upbit.get_balances()
    TotalMoeny = GetTotalMoney(balances) #총 원금
    TotalRealMoney = GetTotalRealMoney(balances) #총 평가금액
    TotalRevenue = GetRevenue(TotalMoeny, TotalRealMoney)
    Krw = GetKRW(balances)

    if(rsi_pre_old != rsi_pre and rsi_pre_old > 0): #최초 실행시 (rsi_pre_old == 0) 일때 매매하지 않도록
        rsiChangeString = "change:Y traded:" + trade
        trade = 'N'
        sendMsg = ""
        cnt = 0
        order = 0
        
        if (rsi_pre > 70 and rsi_pre_old <= 70 and trade == 'N'):
            cnt = round(GetAmount("SELL", TotalRealMoney) / now_price, 8)
            order = now_price-price_unit
            print(upbit.sell_limit_order("KRW-BTC", order, cnt))
            addString = "sell - golden cross!!!"
            trade = 'Y'
        elif (rsi_pre <= 70 and rsi_pre_old > 70 and trade == 'N'):
            cnt = round(GetAmount("SELL", TotalRealMoney) / now_price, 8)
            order = now_price-price_unit
            print(upbit.sell_limit_order("KRW-BTC",order, cnt))
            addString = "sell - dead cross!!!"
            trade = 'Y'
        elif (rsi_pre >= 30 and rsi_pre_old < 30 and trade == 'N' and TotalRevenue > 1): #수익율이 1% 이상일때만 매도
            cnt = round(GetAmount("BUY", TotalRealMoney) / now_price, 8)
            order = now_price+price_unit
            print(upbit.buy_limit_order("KRW-BTC", order, cnt))
            addString = "buy - golden cross!!!"
            trade = 'Y'
        if(trade == 'Y'):
            print(sendMsg)
            sendMsg = addString + str(order) + ":" + str(cnt) + ":" + str(order*cnt)
            telegram_send(token, chatid, sendMsg)
        rsi_pre_old = rsi_pre
        rsiChange = True
    elif(rsi_pre_old == 0): #최초 실행시는 rsi_pre_old = rsi_pre 어사인.
        rsi_pre_old = rsi_pre
        rsiChangeString = "change:N traded:" + trade
        rsiChange = False
    else:
        rsiChangeString = "change:N traded:" + trade
        rsiChange = False
 
    if(rsiChange == True):
        print(datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S'),
              f"{rsi_pre_old2:.10f}", f"{rsi_pre:.10f}", f"{rsi_now: .10f}", now_price, 
              '%d' % (TotalMoeny), '%d' % (TotalRealMoney), f"{TotalRevenue: .2f} ", '%d' % (int(float(Krw))), addString, flush=True)
            #rsi_pre_old2, ":", rsi_pre_old, "->", rsi_pre, "->", rsi_now, now_price, rsiChangeString, addString, flush=True)

print("Start Bot at ", datetime.now(
    timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S\t'), flush=True)

#Monitor()

while 1:
    Monitor()
    time.sleep(3)
# comment:
# end while True:
