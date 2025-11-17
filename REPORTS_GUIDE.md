# Backtest Reports Guide

Order Block Strategy의 백테스트 리포트 생성 및 분석 가이드입니다.

## 📊 리포트 개요

이 전략은 종합적인 백테스트 리포트 시스템을 포함하고 있습니다:

- **HTML 리포트**: 시각적으로 보기 좋은 웹 기반 리포트
- **JSON 데이터**: 프로그래밍 방식으로 접근 가능한 데이터
- **성과 지표**: 30개 이상의 상세한 성능 메트릭
- **거래 기록**: 모든 개별 거래의 상세 내역

## 🚀 빠른 시작

### 1. 데모 리포트 생성

```bash
# 프로젝트 루트에서 실행
cd /home/user/nt_pro

# 단일 시나리오 생성
python strategies/order_block/demo_report.py balanced

# 모든 시나리오 생성 (추천)
python strategies/order_block/demo_report.py all

# 파라미터 비교
python strategies/order_block/demo_report.py compare
```

### 2. 리포트 보기

```bash
# 리포트 뷰어 실행
python view_report.py

# 또는 직접 브라우저로 열기
# reports/demo_report_balanced.html
```

## 📁 리포트 파일 구조

생성된 리포트는 `reports/` 디렉토리에 저장됩니다:

```
reports/
├── demo_report_profitable.html    # 수익성 높은 시나리오
├── demo_report_profitable.json    # 데이터 (JSON)
├── demo_report_balanced.html      # 균형 잡힌 시나리오
├── demo_report_balanced.json
├── demo_report_struggling.html    # 어려운 시나리오
└── demo_report_struggling.json
```

## 📈 포함된 성과 지표

### 기본 통계
- **총 거래 수**: 전체 실행된 거래 횟수
- **승률**: 수익 거래 비율
- **손실률**: 손실 거래 비율
- **무승부 거래**: 손익 0인 거래

### 손익 지표
- **총 손익 ($)**: 절대 수익/손실 금액
- **총 손익 (%)**: 계좌 대비 비율
- **총 수익**: 모든 승리 거래의 합계
- **총 손실**: 모든 손실 거래의 합계
- **Profit Factor**: 총 수익 ÷ 총 손실

### 리스크 지표
- **Sharpe Ratio**: 위험 대비 수익률 (> 1.0이 좋음)
- **최대 낙폭 (DD)**: 최고점에서 최저점까지 최대 하락
- **최대 낙폭 (%)**: 계좌 대비 비율
- **Expectancy**: 거래당 기대 수익

### 거래 분석
- **평균 승리**: 수익 거래의 평균 금액
- **평균 손실**: 손실 거래의 평균 금액
- **최대 승리**: 가장 큰 수익 거래
- **최대 손실**: 가장 큰 손실 거래
- **평균 R:R**: 평균 Risk/Reward 비율

### 거래 기간
- **평균 기간**: 거래당 평균 보유 시간
- **최장 기간**: 가장 긴 거래
- **최단 기간**: 가장 짧은 거래

### 연속 통계
- **최대 연속 승리**: 가장 긴 승리 연속
- **최대 연속 손실**: 가장 긴 손실 연속

### 월별 성과
- **최고 월**: 가장 수익이 높았던 월
- **최악 월**: 가장 손실이 컸던 월
- **평균 월 수익**: 월평균 수익

## 🎯 시나리오 설명

### Profitable (수익성 높음)
- **승률**: 68%
- **특징**: 강력한 리스크 관리, 높은 Sharpe Ratio
- **용도**: 이상적인 시나리오, 목표 설정

### Balanced (균형)
- **승률**: 60%
- **특징**: 중간 수준 수익, 적절한 낙폭
- **용도**: 현실적인 기대치 설정

### Struggling (어려움)
- **승률**: 45%
- **특징**: 최적화 필요, 높은 낙폭
- **용도**: 문제 파악 및 개선 필요 영역 식별

## 💻 프로그래밍 방식 사용

### 리포트 생성 예제

```python
from strategies.order_block import ReportManager, TradeRecord

# 거래 기록 생성 (실제 백테스트 결과 사용)
trades = [
    TradeRecord(
        entry_time="2024-01-15 10:00:00",
        exit_time="2024-01-15 14:30:00",
        direction="LONG",
        entry_price=1.0850,
        exit_price=1.0880,
        quantity=100000.0,
        pnl=300.00,
        pnl_percent=2.0,
        setup_type="TP1",
        risk_reward=2.0,
        duration_minutes=270,
    ),
    # ... 더 많은 거래 추가
]

# 전략 설정
config = {
    'Instrument': 'EUR/USD',
    'Timeframe': '4H / 15M',
    'Stop Loss': '1.0%',
    'Take Profit': '1:2, 1:4',
}

# 리포트 생성
report_manager = ReportManager(output_dir='my_reports')
report_path = report_manager.generate_report(
    trades=trades,
    config=config,
    starting_balance=100000.0,
    report_name='my_backtest_results.html'
)

print(f"Report generated: {report_path}")
```

### 메트릭 계산 예제

```python
from strategies.order_block import PerformanceCalculator

# 성과 지표 계산
metrics = PerformanceCalculator.calculate_metrics(
    trades=trades,
    starting_balance=100000.0
)

# 콘솔에 요약 출력
report_manager.print_summary(metrics)

# 개별 메트릭 접근
print(f"Win Rate: {metrics.win_rate}%")
print(f"Profit Factor: {metrics.profit_factor}")
print(f"Sharpe Ratio: {metrics.sharpe_ratio}")
```

### JSON 데이터 읽기

```python
import json
from pathlib import Path

# JSON 리포트 읽기
json_path = Path("reports/demo_report_balanced.json")
data = json.loads(json_path.read_text())

# 데이터 접근
metrics = data['metrics']
trades = data['trades']
config = data['config']

print(f"Total trades: {metrics['total_trades']}")
print(f"Win rate: {metrics['win_rate']}%")
print(f"Total PnL: ${metrics['total_pnl']:,.2f}")

# 거래 분석
for trade in trades[:5]:  # 첫 5개 거래
    print(f"{trade['direction']} @ {trade['entry_price']}: ${trade['pnl']:.2f}")
```

## 📊 리포트 구성 요소

### 1. 헤더
- 전략 이름
- 생성 일시

### 2. 총 손익 하이라이트
- 대형 시각적 표시
- 색상으로 수익/손실 구분

### 3. 핵심 지표 섹션
- 4개의 핵심 KPI 카드
- 호버 효과로 상호작용

### 4. 승/패 통계
- 6개의 상세 메트릭
- 평균, 최대 값 표시

### 5. 리스크 지표
- 낙폭, R:R, Expectancy
- 경고 색상 표시

### 6. 거래 기간 분석
- 평균, 최장, 최단 기간

### 7. 월별 성과
- 최고/최악/평균 월 수익

### 8. 최근 거래 테이블
- 최대 20개 거래 표시
- 정렬 및 필터 가능
- 색상 코딩

### 9. 전략 설정
- 사용된 모든 파라미터
- 재현성을 위한 기록

### 10. 면책조항
- 리스크 경고
- 중요 공지사항

## 🎨 리포트 스타일

리포트는 다음의 시각적 특징을 가집니다:

- **그라디언트 헤더**: 보라색 그라디언트
- **카드 레이아웃**: 현대적인 카드 디자인
- **색상 코딩**:
  - 녹색: 긍정적 (수익, 승리)
  - 빨간색: 부정적 (손실, 패배)
  - 보라색: 중립적 (정보)
- **호버 효과**: 인터랙티브 요소
- **반응형**: 다양한 화면 크기 지원

## 🔧 커스터마이징

### 리포트 디렉토리 변경

```python
report_manager = ReportManager(output_dir='custom_reports')
```

### 리포트 이름 지정

```python
report_path = report_manager.generate_report(
    trades=trades,
    config=config,
    report_name='eurusd_2024_backtest.html'
)
```

### 시작 잔고 변경

```python
metrics = PerformanceCalculator.calculate_metrics(
    trades=trades,
    starting_balance=50000.0  # $50k 시작
)
```

## 📌 모범 사례

### 1. 정기적인 리포트 생성
- 각 백테스트 실행 후 리포트 생성
- 날짜/버전으로 리포트 명명

### 2. 여러 시나리오 비교
- 다양한 파라미터 세트로 테스트
- 비교 분석을 위해 모두 저장

### 3. JSON 데이터 보관
- 프로그래밍 방식 분석을 위해 JSON 저장
- 장기 성과 추적

### 4. 문서화
- 각 리포트에 상세한 config 포함
- 테스트 조건 및 가정 기록

### 5. 검증
- 데모 리포트로 먼저 테스트
- 실제 데이터 적용 전 확인

## ⚠️ 주의사항

### 과최적화 경계
- 백테스트 결과가 너무 좋으면 의심
- Walk-forward 분석 실시
- Out-of-sample 테스트

### 생존자 편향
- 실패한 전략도 문서화
- 모든 테스트 결과 보관

### 슬리피지 고려
- 백테스트는 이상적 조건
- 실제 거래는 슬리피지 발생
- 보수적 기대치 설정

### 데이터 품질
- 깨끗한 히스토리컬 데이터 사용
- 이상치 및 누락 데이터 확인

## 🔍 리포트 분석 체크리스트

백테스트 리포트를 받았을 때 확인할 사항:

- [ ] **승률**이 현실적인가? (50-70% 범위)
- [ ] **Profit Factor** > 1.5?
- [ ] **Sharpe Ratio** > 1.0?
- [ ] **최대 낙폭**이 수용 가능한가? (< 20%)
- [ ] **평균 R:R**이 양수인가?
- [ ] **Expectancy**가 양수인가?
- [ ] **거래 수**가 통계적으로 유의미한가? (> 30)
- [ ] **연속 손실**을 견딜 수 있는가?
- [ ] **월별 변동성**이 과도하지 않은가?
- [ ] **설정값**이 명확히 문서화되었는가?

## 📚 추가 리소스

### 성과 지표 학습
- **Sharpe Ratio**: [Investopedia](https://www.investopedia.com/terms/s/sharperatio.asp)
- **Profit Factor**: 좋은 전략은 > 2.0
- **Maximum Drawdown**: 심리적 수용 한계 고려

### 백테스팅 모범 사례
- Walk-forward optimization
- Monte Carlo simulation
- Cross-validation

### 리스크 관리
- Position sizing
- Kelly Criterion
- Risk of ruin calculator

## 🆘 문제 해결

### 리포트가 생성되지 않음
```bash
# 디렉토리 권한 확인
mkdir -p reports

# 의존성 확인
python -c "from strategies.order_block import ReportManager"
```

### HTML이 제대로 표시되지 않음
- 최신 브라우저 사용 (Chrome, Firefox, Safari)
- 파일을 로컬에서 열기 (file:// protocol)
- JavaScript 활성화 확인

### 데이터가 이상함
- 거래 데이터 검증
- 시작 잔고 확인
- 날짜/시간 형식 확인

## 📞 도움말

추가 도움이 필요하면:

1. 프로젝트 README 확인
2. 전략 문서 검토
3. 데모 예제 실행
4. 이슈 제출

---

**Happy Backtesting! 📊🚀**

리포트는 과거 성과를 보여주지만, 미래 수익을 보장하지 않습니다. 항상 신중하게 분석하고, 실제 트레이딩 전에 충분히 테스트하세요.
