"""
Trading Strategy Manager

주요 기능:
- 여러 거래 전략을 통합 관리
- 각 전략의 신호를 결합하여 최종 매매 신호 생성
- 커스텀 가중치 설정 가능
- 실시간 시장 분석 및 모니터링

포함된 전략:
1. RSI (Relative Strength Index)
   - 과매수/과매도 구간 기반 매매
2. Bollinger Bands
   - 변동성 기반 매매
3. MACD (Moving Average Convergence Divergence)
   - 추세 추종형 매매
4. Moving Average (SMA/EMA)
   - 이동평균 크로스오버 기반 매매

사용 예시:
    manager = StrategyManager()
    results = manager.analyze_all(ticker="KRW-BTC", interval="minute3")
    
    # 커스텀 가중치로 통합 신호 얻기
    weights = {
        'rsi': 0.3,
        'bollinger': 0.2,
        'macd': 0.2,
        'ma_sma': 0.15,
        'ma_ema': 0.15
    }
    signal = manager.get_combined_signal(results, weights)
"""

import pyupbit
from strategies.rsi_strategy import RSIStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.moving_average_strategy import MovingAverageStrategy

class StrategyManager:
    def __init__(self):
        self.strategies = {
            'rsi': RSIStrategy(),
            'bollinger': BollingerStrategy(),
            'macd': MACDStrategy(),
            'ma_sma': MovingAverageStrategy(ma_type='SMA'),
            'ma_ema': MovingAverageStrategy(ma_type='EMA')
        }

    def analyze_all(self, ticker="KRW-BTC", interval="minute3"):
        """Analyze using all strategies"""
        df = pyupbit.get_ohlcv(ticker, interval=interval)
        results = {}
        
        for name, strategy in self.strategies.items():
            signals, indicators = strategy.generate_signals(df)
            results[name] = {
                'signals': signals,
                'indicators': indicators
            }
        
        return results

    def get_combined_signal(self, results, weights=None):
        """
        Combine signals from all strategies
        weights: dictionary of strategy weights (e.g., {'rsi': 0.4, 'bollinger': 0.3, 'macd': 0.3})
        """
        if weights is None:
            weights = {name: 1/len(self.strategies) for name in self.strategies.keys()}
            
        final_signal = 0
        for name, weight in weights.items():
            if name in results:
                final_signal += results[name]['signals'].iloc[-1] * weight
                
        # Threshold for final decision
        if final_signal > 0.5:
            return 1  # Strong buy signal
        elif final_signal < -0.5:
            return -1  # Strong sell signal
        return 0  # No clear signal

def main():
    manager = StrategyManager()
    results = manager.analyze_all()
    
    # Example of getting combined signal with custom weights
    weights = {
        'rsi': 0.4,
        'bollinger': 0.3,
        'macd': 0.3
    }
    
    signal = manager.get_combined_signal(results, weights)
    print(f"Combined Signal: {signal}")

if __name__ == "__main__":
    main()
