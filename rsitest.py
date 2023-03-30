import pyupbit
import pandas as pd
import time
from datetime import datetime
from pytz import timezone

f = open("key.txt", 'r')
while True:
    line = f.readline()
    if not line:
        break
    strParse = line.split(":")
    if(strParse[0] == "access"):
        access = strParse[1]
    elif(strParse[0] == "secret"):
        secret = strParse[1]
f.close()

print(access)
print(secret)

upbit = pyupbit.Upbit(access, secret)  # 업비트 객체를 만듭니다.

global rsi_pre_old
global rsi_pre_old2
global trade
global price_unit

rsi_pre_old = 0
rsi_pre_old2 = 0
trade = 'N'
price_unit = 5000


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


def getAmount(type):
    type_ratio = {"BUY": 0.1, "SELL": 0.05}.get(type, 0)
    total = GetTotalRealMoney(upbit.get_balances())
    return round(total*type_ratio)


def Monitor():
    global rsi_pre_old
    global rsi_pre_old2
    global trade
    global price_unit
    df = pyupbit.get_ohlcv("KRW-BTC", interval="minute1")

    rsi_pre_old2 = rsi_pre_old

    #RSI14지표를 구합니다.
    rsi_pre = float(GetRSI(df, 10).iloc[-2])
    rsi_now = float(GetRSI(df, 10).iloc[-1])

    addString = ""
    rsiChangeString = ""
    
    now_price = df["close"].iloc[-1]

    if(rsi_pre_old != rsi_pre and rsi_pre_old > 0): #최초 실행시 (rsi_pre_old == 0) 일때 매매하지 않도록
        rsiChangeString = "change:Y traded:" + trade
        trade = 'N'
        if (rsi_pre > 70 and rsi_pre_old <= 70 and trade == 'N'):
            sell_cnt = round(getAmount("SELL") / now_price, 8)
            print(upbit.sell_limit_order(
                "KRW-BTC", now_price-price_unit, sell_cnt))
            addString = "\tsell - golden cross!!!"
            trade = 'Y'
        elif (rsi_pre <= 70 and rsi_pre_old > 70 and trade == 'N'):
            sell_cnt = round(getAmount("SELL") / now_price, 8)
            print(upbit.sell_limit_order(
                "KRW-BTC", now_price-price_unit, sell_cnt))
            addString = "\tsell - dead cross!!!"
            trade = 'Y'
        elif (rsi_pre >= 30 and rsi_pre_old < 30 and trade == 'N'):
            buy_cnt = round(getAmount("BUY") / now_price, 8)
            print(upbit.buy_limit_order("KRW-BTC", now_price+price_unit, buy_cnt))
            addString = "\tbuy - golden cross!!!"
            trade = 'Y'
        rsi_pre_old = rsi_pre
    elif(rsi_pre_old == 0): #최초 실행시는 rsi_pre_old = rsi_pre 어사인.
        rsi_pre_old = rsi_pre
    else:
        rsiChangeString = "change:N traded:" + trade
 
    print(datetime.now(timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S '),
          rsi_pre_old2, ":", rsi_pre_old, "->", rsi_pre, "->", rsi_now, now_price, rsiChangeString, addString, flush=True)


print("Start Bot at ", datetime.now(
    timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S\t'))

#Monitor()

while 1:
    Monitor()
    time.sleep(5)
# comment:
# end while True:
