"""
Moving Average Trading Strategy

주요 기능:
- 단순이동평균(SMA)과 지수이동평균(EMA) 지원
- 3개의 이동평균선 사용 (단기, 중기, 장기)
- 골든크로스/데드크로스 감지
- 추세 강도 분석

매매 신호:
- 매우 강한 매수 (2): 단기-중기, 중기-장기 모두 골든크로스
- 강한 매수 (1): 어느 한 쪽의 골든크로스
- 매우 강한 매도 (-2): 단기-중기, 중기-장기 모두 데드크로스
- 강한 매도 (-1): 어느 한 쪽의 데드크로스

추세 분석:
- Strong Uptrend: 단기 > 중기 > 장기
- Strong Downtrend: 단기 < 중기 < 장기
- Potential Reversal (Bullish): 단기 > 중기, 중기 < 장기
- Potential Reversal (Bearish): 단기 < 중기, 중기 > 장기
- Sideways/Neutral: 그 외의 경우

사용 예시:
    ma = MovingAverageStrategy(short_period=5, medium_period=20, long_period=60, ma_type='SMA')
    signals, indicators = ma.generate_signals(df)
    current_trend = ma.get_current_trend(indicators)
"""

import pandas as pd
import numpy as np

class MovingAverageStrategy:
    def __init__(self, short_period=5, medium_period=20, long_period=60, ma_type='SMA'):
        """
        Initialize Moving Average Strategy
        ma_type: 'SMA' for Simple Moving Average or 'EMA' for Exponential Moving Average
        """
        self.short_period = short_period
        self.medium_period = medium_period
        self.long_period = long_period
        self.ma_type = ma_type.upper()

    def calculate_ma(self, series, period):
        """Calculate moving average based on type"""
        if self.ma_type == 'SMA':
            return series.rolling(window=period).mean()
        elif self.ma_type == 'EMA':
            return series.ewm(span=period, adjust=False).mean()
        else:
            raise ValueError("MA type must be either 'SMA' or 'EMA'")

    def calculate_all_mas(self, df):
        """Calculate all moving averages"""
        df = df.copy()
        
        # Calculate different period MAs
        short_ma = self.calculate_ma(df['close'], self.short_period)
        medium_ma = self.calculate_ma(df['close'], self.medium_period)
        long_ma = self.calculate_ma(df['close'], self.long_period)
        
        return short_ma, medium_ma, long_ma

    def detect_crossover(self, fast_ma, slow_ma):
        """Detect golden cross (1) and death cross (-1)"""
        crossover = pd.Series(0, index=fast_ma.index)
        
        # Golden Cross: Fast MA crosses above Slow MA
        golden_cross = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        crossover[golden_cross] = 1
        
        # Death Cross: Fast MA crosses below Slow MA
        death_cross = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))
        crossover[death_cross] = -1
        
        return crossover

    def generate_signals(self, df):
        """Generate buy/sell signals based on MA crossovers"""
        short_ma, medium_ma, long_ma = self.calculate_all_mas(df)
        
        # Detect different crossovers
        short_medium_cross = self.detect_crossover(short_ma, medium_ma)
        medium_long_cross = self.detect_crossover(medium_ma, long_ma)
        short_long_cross = self.detect_crossover(short_ma, long_ma)
        
        # Combine signals (you can adjust the weights here)
        signals = pd.Series(0, index=df.index)
        
        # Strong buy signals
        signals[(short_medium_cross == 1) & (medium_long_cross == 1)] = 2  # Very strong buy
        signals[(short_medium_cross == 1) | (medium_long_cross == 1)] = 1  # Strong buy
        
        # Strong sell signals
        signals[(short_medium_cross == -1) & (medium_long_cross == -1)] = -2  # Very strong sell
        signals[(short_medium_cross == -1) | (medium_long_cross == -1)] = -1  # Strong sell
        
        # Additional trend confirmation
        trend = pd.Series(0, index=df.index)
        trend[short_ma > medium_ma] = 1
        trend[short_ma < medium_ma] = -1
        
        return signals, {
            'short_ma': short_ma,
            'medium_ma': medium_ma,
            'long_ma': long_ma,
            'trend': trend,
            'short_medium_cross': short_medium_cross,
            'medium_long_cross': medium_long_cross,
            'short_long_cross': short_long_cross
        }

    def get_strategy_name(self):
        return f"{self.ma_type} Moving Average Strategy"

    def get_current_trend(self, indicators):
        """Get current market trend based on MA positions"""
        last_idx = indicators['short_ma'].index[-1]
        
        short = indicators['short_ma'][last_idx]
        medium = indicators['medium_ma'][last_idx]
        long = indicators['long_ma'][last_idx]
        
        if short > medium > long:
            return "Strong Uptrend"
        elif short < medium < long:
            return "Strong Downtrend"
        elif short > medium and medium < long:
            return "Potential Reversal (Bullish)"
        elif short < medium and medium > long:
            return "Potential Reversal (Bearish)"
        else:
            return "Sideways/Neutral"
