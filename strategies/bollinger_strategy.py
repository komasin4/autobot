"""
Bollinger Bands Trading Strategy

주요 기능:
- 볼린저 밴드 계산 (상단, 중간, 하단 밴드)
- 이동평균 기간 설정 가능 (기본 20일)
- 표준편차 배수 조정 가능 (기본 2)

매매 신호:
- 매수: 가격이 하단 밴드에 닿거나 하향 돌파할 때
- 매도: 가격이 상단 밴드에 닿거나 상향 돌파할 때

특징:
- 변동성 기반 매매에 효과적
- 추세와 함께 사용시 효과가 증대
- RSI나 MACD와 조합하여 사용 가능

사용 예시:
    bb = BollingerStrategy(period=20, std_dev=2)
    signals, bands = bb.generate_signals(df)
"""

import pandas as pd

class BollingerStrategy:
    def __init__(self, period=20, std_dev=2):
        self.period = period
        self.std_dev = std_dev

    def calculate_bollinger_bands(self, df):
        """Calculate Bollinger Bands"""
        df = df.copy()
        typical_price = df['close']
        
        middle_band = typical_price.rolling(window=self.period).mean()
        std = typical_price.rolling(window=self.period).std()
        
        upper_band = middle_band + (std * self.std_dev)
        lower_band = middle_band - (std * self.std_dev)
        
        return upper_band, middle_band, lower_band

    def generate_signals(self, df):
        """Generate buy/sell signals based on Bollinger Bands"""
        upper, middle, lower = self.calculate_bollinger_bands(df)
        signals = pd.Series(index=df.index, data=0)
        
        # Buy signal when price touches lower band
        signals[df['close'] <= lower] = 1
        
        # Sell signal when price touches upper band
        signals[df['close'] >= upper] = -1
        
        return signals, (upper, middle, lower)

    def get_strategy_name(self):
        return "Bollinger Bands Strategy"
