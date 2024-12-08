"""
RSI(Relative Strength Index) Trading Strategy

주요 기능:
- RSI 지표 계산 및 매매 신호 생성
- 과매수/과매도 구간 설정 가능
- 기본값: 과매수(70), 과매도(30)
- RSI 기간 조정 가능 (기본 14일)

매매 신호:
- 매수: RSI가 과매도 구간에서 상승할 때
- 매도: RSI가 과매수 구간에서 하락할 때

사용 예시:
    rsi = RSIStrategy(overbought=70, oversold=30, period=14)
    signals, rsi_values = rsi.generate_signals(df)
"""

import pandas as pd

class RSIStrategy:
    def __init__(self, overbought=70, oversold=30, period=14):
        self.overbought = overbought
        self.oversold = oversold
        self.period = period

    def calculate_rsi(self, df):
        """Calculate RSI indicator"""
        df = df.copy()
        df['close'] = df['close']
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.rolling(window=self.period, min_periods=self.period).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=self.period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, df):
        """Generate buy/sell signals based on RSI"""
        rsi = self.calculate_rsi(df)
        signals = pd.Series(index=df.index, data=0)  # 0: no signal, 1: buy, -1: sell
        
        # Buy signal when RSI crosses above oversold
        signals[rsi > self.oversold] = 1
        
        # Sell signal when RSI crosses below overbought
        signals[rsi < self.overbought] = -1
        
        return signals, rsi

    def get_strategy_name(self):
        return "RSI Strategy"
