"""
MACD(Moving Average Convergence Divergence) Trading Strategy

주요 기능:
- MACD 라인: 단기EMA - 장기EMA
- 시그널 라인: MACD의 이동평균
- 히스토그램: MACD - 시그널 라인
- 기본 파라미터: 
    * 단기EMA: 12일
    * 장기EMA: 26일
    * 시그널: 9일

매매 신호:
- 매수: MACD가 시그널 라인을 상향 돌파할 때
- 매도: MACD가 시그널 라인을 하향 돌파할 때

특징:
- 추세 추종형 지표
- 모멘텀과 추세를 동시에 분석
- 다양한 시장 상황에서 활용 가능

사용 예시:
    macd = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
    signals, (macd, signal, hist) = macd.generate_signals(df)
"""

import pandas as pd

class MACDStrategy:
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate_macd(self, df):
        """Calculate MACD indicator"""
        df = df.copy()
        # Calculate the short and long EMAs
        exp1 = df['close'].ewm(span=self.fast_period, adjust=False).mean()
        exp2 = df['close'].ewm(span=self.slow_period, adjust=False).mean()
        
        # Calculate MACD line
        macd = exp1 - exp2
        
        # Calculate the signal line
        signal = macd.ewm(span=self.signal_period, adjust=False).mean()
        
        # Calculate the histogram
        hist = macd - signal
        
        return macd, signal, hist

    def generate_signals(self, df):
        """Generate buy/sell signals based on MACD"""
        macd, signal, hist = self.calculate_macd(df)
        signals = pd.Series(index=df.index, data=0)
        
        # Buy signal when MACD crosses above signal line
        signals[macd > signal] = 1
        
        # Sell signal when MACD crosses below signal line
        signals[macd < signal] = -1
        
        return signals, (macd, signal, hist)

    def get_strategy_name(self):
        return "MACD Strategy"
