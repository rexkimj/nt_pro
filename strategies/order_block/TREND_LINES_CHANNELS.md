# Trend Lines and Channels - 사용 가이드

## 개요

Order Block 전략에 추세선(Trend Lines)과 채널(Channels) 자동 감지 기능이 추가되었습니다.

### 주요 기능

1. **TrendLineDetector**: 스윙 포인트를 기반으로 지지선과 저항선을 자동으로 감지
2. **ChannelDetector**: 평행한 추세선 쌍을 찾아 가격 채널을 식별
3. **TrendLineVisualizer**: 감지된 추세선과 채널을 시각화

## 작동 원리

### 추세선 감지 (TrendLineDetector)

추세선 감지기는 다음 단계로 작동합니다:

1. **스윙 포인트 수집**: 가격의 고점(swing high)과 저점(swing low) 식별
2. **조합 분석**: 모든 스윙 포인트 쌍을 연결하여 잠재적 추세선 생성
3. **터치 포인트 계산**: 각 선에 얼마나 많은 다른 스윙 포인트가 접촉하는지 계산
4. **검증**: 최소 터치 수(기본 2개)를 만족하는 추세선만 유지
5. **강도 평가**: 터치 수와 정확도를 기반으로 추세선 강도 점수 계산

#### 주요 파라미터

```python
TrendLineDetector(
    min_touches=2,                    # 추세선 검증 최소 터치 수
    max_lines=10,                     # 추적할 최대 추세선 수
    touch_tolerance_pips=5.0,         # 터치 판단 허용 오차 (pips)
    min_bars_between_touches=3        # 터치 포인트 간 최소 봉 수
)
```

### 채널 감지 (ChannelDetector)

채널 감지기는 다음과 같이 작동합니다:

1. **평행선 찾기**: 감지된 지지선과 저항선 중 평행한 쌍 찾기
2. **채널 폭 계산**: 두 선 사이의 평균 거리 계산
3. **검증**: 채널 폭이 최소/최대 범위 내에 있고 충분한 터치가 있는지 확인
4. **방향 분류**: 상승(ascending), 하락(descending), 수평(horizontal) 채널로 분류
5. **강도 평가**: 선의 강도, 터치 수, 평행도를 기반으로 채널 강도 계산

#### 주요 파라미터

```python
ChannelDetector(
    min_channel_touches=4,            # 채널 검증 최소 터치 수 (양쪽 합계)
    max_channels=5,                   # 추적할 최대 채널 수
    parallel_tolerance=0.15,          # 평행 판단 허용 오차 (15%)
    min_channel_width_pips=20.0,      # 최소 채널 폭 (pips)
    max_channel_width_pips=500.0      # 최대 채널 폭 (pips)
)
```

## 전략 통합

### 설정 파라미터

전략 설정에 다음 파라미터가 추가되었습니다:

```python
from strategies.order_block import OrderBlockStrategyConfig

config = OrderBlockStrategyConfig(
    # ... 기존 파라미터 ...

    # 추세선 감지 파라미터
    tl_min_touches=2,
    tl_max_lines=10,
    tl_touch_tolerance_pips=5.0,
    tl_min_bars_between_touches=3,

    # 채널 감지 파라미터
    ch_min_touches=4,
    ch_max_channels=5,
    ch_parallel_tolerance=0.15,
    ch_min_width_pips=20.0,
    ch_max_width_pips=500.0,

    # 진입 필터
    use_trend_line_filter=True,       # 추세선 필터 활성화
    use_channel_filter=True,          # 채널 필터 활성화
)
```

### 진입 조건 필터링

추세선과 채널은 진입 조건의 추가 필터로 사용됩니다:

#### 롱 포지션

- **추세선 필터**: 가격이 지지 추세선 근처에 있을 때만 진입
- **채널 필터**: 가격이 채널 하단(지지선) 근처에 있을 때만 진입

#### 숏 포지션

- **추세선 필터**: 가격이 저항 추세선 근처에 있을 때만 진입
- **채널 필터**: 가격이 채널 상단(저항선) 근처에 있을 때만 진입

## 시각화

### 기본 사용법

```python
from strategies.order_block.visualization import TrendLineVisualizer

# 시각화 도구 생성
viz = TrendLineVisualizer(figsize=(16, 10))

# 추세선과 채널 시각화
viz.plot_trend_lines_and_channels(
    bars=list(strategy.htf_trendline_detector.bars),
    trend_line_detector=strategy.htf_trendline_detector,
    channel_detector=strategy.htf_channel_detector,
    title='EUR/USD H4 - Trend Lines and Channels',
    show_support=True,
    show_resistance=True,
    show_channels=True,
    save_path='trend_analysis.png'  # 파일로 저장 (옵션)
)
```

### 스윙 포인트 시각화

```python
# 스윙 포인트만 시각화
viz.plot_swing_points(
    bars=list(strategy.htf_ob_detector.bars),
    swing_highs=strategy.htf_ob_detector.swing_highs,
    swing_lows=strategy.htf_ob_detector.swing_lows,
    title='Price Chart with Swing Points',
    save_path='swing_points.png'
)
```

## 실전 예제

### 백테스팅에서 사용

```python
from nautilus_trader.backtest.node import BacktestNode
from strategies.order_block import OrderBlockStrategyConfig, OrderBlockStrategy

# 설정 생성 (추세선/채널 필터 활성화)
config = OrderBlockStrategyConfig(
    instrument_id=InstrumentId.from_str("EUR/USD.SIM"),
    htf_bar_type=BarType.from_str("EUR/USD.SIM-4-HOUR-MID-INTERNAL"),
    ltf_bar_type=BarType.from_str("EUR/USD.SIM-15-MINUTE-MID-INTERNAL"),
    base_trade_size=Decimal("100000"),

    # 추세선/채널 기능 활성화
    use_trend_line_filter=True,
    use_channel_filter=True,

    # 로깅 활성화하여 감지 결과 확인
    log_signals=True,
)

# 백테스트 실행
node = BacktestNode(configs=[config])
results = node.run()

# 전략 인스턴스 가져오기
strategy = node.trader.strategies()[0]

# 결과 시각화
from strategies.order_block.visualization import TrendLineVisualizer

viz = TrendLineVisualizer()
viz.plot_trend_lines_and_channels(
    bars=list(strategy.htf_trendline_detector.bars),
    trend_line_detector=strategy.htf_trendline_detector,
    channel_detector=strategy.htf_channel_detector,
    title=f'Backtest Results - {config.instrument_id}',
    save_path='backtest_trend_analysis.png'
)
```

### 감지된 추세선 정보 조회

```python
# 활성 지지선 조회
support_lines = strategy.htf_trendline_detector.get_active_trend_lines('support')
for i, line in enumerate(support_lines):
    print(f"Support {i+1}:")
    print(f"  Direction: {line.direction}")
    print(f"  Touches: {line.touch_count}")
    print(f"  Strength: {line.strength:.2f}")
    print(f"  Slope: {line.slope:.6f}")
    print()

# 활성 저항선 조회
resistance_lines = strategy.htf_trendline_detector.get_active_trend_lines('resistance')
for i, line in enumerate(resistance_lines):
    print(f"Resistance {i+1}:")
    print(f"  Direction: {line.direction}")
    print(f"  Touches: {line.touch_count}")
    print(f"  Strength: {line.strength:.2f}")
    print()

# 활성 채널 조회
channels = strategy.htf_channel_detector.get_active_channels()
for i, channel in enumerate(channels):
    print(f"Channel {i+1}:")
    print(f"  Direction: {channel.direction}")
    print(f"  Width: {channel.width * 10000:.1f} pips")
    print(f"  Strength: {channel.strength:.2f}")
    print()
```

## 성능 최적화

### 추세선 감지 성능

추세선 감지는 조합 분석을 사용하므로 스윙 포인트가 많을수록 계산량이 증가합니다:

- 최근 20개의 스윙 포인트만 분석 (효율성 향상)
- 가장 강한 5개의 추세선만 유지
- `min_bars_between_touches` 파라미터로 불필요한 계산 감소

### 메모리 관리

- 추세선: 최대 `max_lines` 개까지만 유지 (기본값: 10)
- 채널: 최대 `max_channels` 개까지만 유지 (기본값: 5)
- 스윙 포인트: 최대 50개까지만 유지

## 알고리즘 상세

### 추세선 강도 계산

```
strength = touch_count - (avg_distance_from_line / tolerance) * 0.5
```

- `touch_count`: 추세선에 접촉한 스윙 포인트 수
- `avg_distance_from_line`: 포인트들의 평균 거리
- `tolerance`: 터치 판단 허용 오차

### 채널 강도 계산

```
strength = avg_line_strength + touch_bonus + parallelism_score
```

- `avg_line_strength`: 상단/하단 추세선의 평균 강도
- `touch_bonus`: 총 터치 수 * 0.5
- `parallelism_score`: 평행도 점수 (0~1)

## 주의사항

1. **필터 조합**: 추세선과 채널 필터를 모두 활성화하면 진입 기회가 크게 감소할 수 있습니다. 백테스팅을 통해 최적의 조합을 찾으세요.

2. **파라미터 조정**: 거래하는 상품과 타임프레임에 따라 파라미터를 조정해야 합니다:
   - 변동성이 큰 상품: `touch_tolerance_pips` 증가
   - 긴 타임프레임: `min_bars_between_touches` 증가

3. **시각화 성능**: 많은 봉 데이터를 시각화하면 느릴 수 있습니다. 필요한 구간만 선택하여 시각화하세요.

4. **채널 방향**: 채널 방향은 평균 기울기로 결정됩니다:
   - `ascending`: 상승 채널 (양의 기울기)
   - `descending`: 하락 채널 (음의 기울기)
   - `horizontal`: 수평 채널 (기울기 거의 0)

## 문제 해결

### 추세선이 감지되지 않는 경우

- `min_touches` 파라미터를 낮춰보세요 (예: 2 → 1)
- `touch_tolerance_pips`를 늘려보세요
- 충분한 스윙 포인트가 감지되는지 확인하세요

### 채널이 감지되지 않는 경우

- `parallel_tolerance`를 늘려보세요 (예: 0.15 → 0.25)
- `min_channel_width_pips`와 `max_channel_width_pips` 범위를 조정하세요
- 먼저 추세선이 제대로 감지되는지 확인하세요

### 너무 많은 추세선/채널이 감지되는 경우

- `min_touches`를 늘려보세요
- `touch_tolerance_pips`를 줄여보세요
- `max_lines`와 `max_channels`를 줄여보세요

## 추가 개선 아이디어

1. **동적 파라미터**: 시장 변동성에 따라 `touch_tolerance_pips` 자동 조정
2. **추세선 돌파**: 추세선 돌파를 별도 시그널로 활용
3. **채널 이탈**: 채널 이탈을 추세 전환 시그널로 활용
4. **가중치 시스템**: 강도가 높은 추세선/채널에 더 높은 가중치 부여

## 참고 자료

- `indicators.py`: TrendLineDetector, ChannelDetector 구현
- `strategy.py`: 전략 통합 예제
- `visualization.py`: 시각화 유틸리티
- `backtest_example.py`: 백테스팅 예제
