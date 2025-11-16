# Order Block Trading Strategy

Professional Smart Money Concepts (SMC) trading strategy for Nautilus Trader.

## 📋 Overview

This strategy implements institutional trading concepts based on Order Blocks, Fair Value Gaps, Liquidity Sweeps, and Market Structure analysis. It combines multiple timeframe analysis with strict risk management to identify high-probability trading opportunities.

## 🎯 Strategy Logic

### Entry Conditions (ALL must be met)

1. **Order Block Detection (H4/D1)**
   - Identifies institutional order blocks on higher timeframes
   - Tracks bullish/bearish OBs and their tested status
   - Uses swing point analysis to find setup candles

2. **Fair Value Gap (FVG)**
   - Detects price imbalances (gaps) in the market
   - Confirms institutional interest in the zone
   - Filters for unfilled gaps aligned with OB direction

3. **Liquidity Sweep**
   - Identifies stop hunts above/below recent highs/lows
   - Confirms smart money accumulation/distribution
   - Must occur within 5 bars of entry signal

4. **Change of Character (CHoCH) - 15m**
   - Confirms trend reversal on lower timeframe
   - Break of market structure signaling new direction
   - Must occur within configurable bars of entry

5. **Fibonacci Golden Zone (Optional)**
   - Price must be in 0.5-0.618 retracement level
   - Optimal risk/reward entry zone
   - Calculated from recent swing high/low

### Risk Management

| Parameter | Default | Description |
|-----------|---------|-------------|
| **Stop Loss** | OB bottom/top ± 1% | Placed below/above order block |
| **TP1** | 1:2 Risk/Reward | Close 50% of position |
| **TP2** | 1:4 Risk/Reward | Trailing stop for remaining |
| **Trailing Stop** | Activates at 1:2 RR | 20 pips distance |
| **Daily Max Loss** | 2% of account | Circuit breaker protection |
| **Max Positions** | 1 | Avoid overexposure |

## 📁 Project Structure

```
strategies/order_block/
├── __init__.py              # Package initialization
├── indicators.py            # Technical indicators
│   ├── OrderBlockDetector
│   ├── FVGDetector
│   ├── LiquiditySweepDetector
│   ├── CHoCHDetector
│   └── FibonacciCalculator
├── strategy.py              # Main strategy class
├── backtest_example.py      # Backtesting examples
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Installation

Ensure Nautilus Trader is installed:

```bash
pip install nautilus_trader
```

### 2. Basic Usage

```python
from decimal import Decimal
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId

from strategies.order_block import OrderBlockStrategy, OrderBlockStrategyConfig

# Configure strategy
config = OrderBlockStrategyConfig(
    instrument_id=InstrumentId.from_str("EUR/USD.SIM"),
    htf_bar_type=BarType.from_str("EUR/USD.SIM-4-HOUR-MID-EXTERNAL"),
    ltf_bar_type=BarType.from_str("EUR/USD.SIM-15-MINUTE-MID-EXTERNAL"),
    base_trade_size=Decimal("100000"),

    # Risk management
    stop_loss_percent=1.0,
    tp1_risk_reward=2.0,
    tp2_risk_reward=4.0,
    daily_max_loss_percent=2.0,

    # Entry filters
    use_fibonacci_filter=True,
    max_bars_since_choch=10,
)

# Create strategy instance
strategy = OrderBlockStrategy(config)
```

### 3. Run Backtest

```bash
# Basic backtest
python strategies/order_block/backtest_example.py backtest

# Parameter optimization
python strategies/order_block/backtest_example.py optimize

# Live trading setup guide
python strategies/order_block/backtest_example.py live
```

## ⚙️ Configuration Parameters

### Core Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `instrument_id` | InstrumentId | Required | Trading instrument |
| `htf_bar_type` | BarType | Required | Higher timeframe (H4/D1) |
| `ltf_bar_type` | BarType | Required | Lower timeframe (15m) |
| `base_trade_size` | Decimal | Required | Position size |

### Order Block Detection

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ob_swing_lookback` | int | 5 | Bars to detect swing points |
| `ob_min_strength_pips` | float | 20.0 | Minimum move strength |
| `ob_max_blocks` | int | 10 | Maximum tracked blocks |

### FVG Detection

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fvg_max_gaps` | int | 20 | Maximum tracked gaps |

### Liquidity Sweep

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ls_lookback` | int | 20 | Bars for high/low detection |
| `ls_reversal_pips` | float | 10.0 | Minimum reversal size |

### CHoCH Detection

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `choch_swing_lookback` | int | 5 | Swing detection period |

### Entry Filters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_fibonacci_filter` | bool | True | Require golden zone entry |
| `max_bars_since_choch` | int | 10 | Max age of CHoCH signal |

### Risk Management

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stop_loss_percent` | float | 1.0 | SL distance from OB (%) |
| `tp1_risk_reward` | float | 2.0 | First take profit ratio |
| `tp2_risk_reward` | float | 4.0 | Second take profit ratio |
| `tp1_close_percent` | float | 50.0 | % to close at TP1 |
| `use_trailing_stop` | bool | True | Enable trailing stop |
| `trailing_stop_activation_rr` | float | 2.0 | RR to activate trailing |
| `trailing_stop_distance_pips` | float | 20.0 | Trailing distance |
| `daily_max_loss_percent` | float | 2.0 | Daily loss circuit breaker |
| `max_positions` | int | 1 | Maximum concurrent trades |

## 📊 Example Workflow

### Long Trade Example

1. **H4 Analysis**
   - Identify bullish Order Block at 1.0850-1.0870
   - Detect bullish FVG at 1.0860
   - Price sweeps low at 1.0845 and reverses

2. **15m Confirmation**
   - CHoCH detected: price breaks above recent lower high
   - Current price: 1.0865 (in Fib golden zone 0.5-0.618)

3. **Entry Execution**
   - Enter LONG at 1.0865
   - SL: 1.0850 (OB low - 1%) = 15 pips risk
   - TP1: 1.0895 (1:2 = 30 pips)
   - TP2: 1.0925 (1:4 = 60 pips)

4. **Trade Management**
   - At TP1: Close 50% of position, move SL to breakeven
   - Activate trailing stop for remaining 50%
   - Trail stop 20 pips below price as it moves up

## 🔍 Indicators Explained

### OrderBlockDetector

Identifies the last opposing candle before a strong price move:

- **Bullish OB**: Last bearish candle before bullish impulse
- **Bearish OB**: Last bullish candle before bearish impulse
- Tracks whether OB has been tested by price

### FVGDetector

Detects 3-candle imbalance patterns:

- **Bullish FVG**: Candle1 high < Candle3 low
- **Bearish FVG**: Candle1 low > Candle3 high
- Tracks whether gap has been filled

### LiquiditySweepDetector

Identifies stop hunts:

- Price briefly breaks recent high/low
- Reverses back inside range
- Indicates liquidity grab before real move

### CHoCHDetector

Detects trend reversals:

- **Bullish**: Break above recent lower high
- **Bearish**: Break below recent higher low
- Confirms change in market structure

### FibonacciCalculator

Calculates retracement levels:

- Identifies golden zone (0.5-0.618)
- Optimal entry area for risk/reward
- Based on recent swing high/low

## 📈 Performance Optimization

### Parameter Tuning

1. **Swing Lookback Period**
   - Smaller (3-5): More sensitive, more signals
   - Larger (7-10): More selective, stronger signals

2. **Stop Loss Distance**
   - Tighter (0.5%): Better RR, more stopped out
   - Wider (1.5%): Lower RR, fewer stop outs

3. **Take Profit Ratios**
   - Conservative: TP1=1.5:1, TP2=3:1
   - Aggressive: TP1=2.5:1, TP2=5:1

4. **Fibonacci Filter**
   - Enabled: Fewer but higher quality entries
   - Disabled: More entries, potentially lower win rate

### Recommended Optimization Process

1. **Backtest** on 2+ years of data
2. **Walk-forward analysis** to avoid overfitting
3. **Paper trade** for 1-3 months
4. **Start live** with minimum size
5. **Scale up** gradually as confidence builds

## ⚠️ Important Warnings

### Before Live Trading

- [ ] Thoroughly backtest on multiple instruments
- [ ] Paper trade for minimum 1 month
- [ ] Understand all entry/exit conditions
- [ ] Verify risk management works correctly
- [ ] Start with minimum position size
- [ ] Never risk more than you can afford to lose

### Known Limitations

1. **Requires clean data**: Strategy needs accurate OHLC bars
2. **Computational overhead**: Multiple timeframe analysis
3. **Not suitable for**: Highly volatile, low liquidity instruments
4. **Best for**: Major forex pairs, liquid crypto pairs
5. **Market conditions**: Works best in trending markets

### Risk Disclosure

```
TRADING CARRIES SIGNIFICANT RISK OF LOSS.
Past performance does not guarantee future results.
This strategy is for educational purposes only.
Always use proper risk management.
Never risk money you cannot afford to lose.
```

## 🛠️ Development

### Running Tests

```python
# Unit tests for indicators
pytest tests/test_indicators.py

# Integration tests for strategy
pytest tests/test_strategy.py

# Full backtest validation
pytest tests/test_backtest.py
```

### Adding Custom Indicators

```python
from strategies.order_block.indicators import OrderBlockDetector

# Extend the base detector
class CustomOBDetector(OrderBlockDetector):
    def __init__(self, *args, custom_param=10, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_param = custom_param

    def _identify_order_block(self, swing):
        # Your custom logic here
        return super()._identify_order_block(swing)
```

## 📚 Resources

### Smart Money Concepts

- **Order Blocks**: Institutional supply/demand zones
- **Fair Value Gaps**: Price inefficiencies to be filled
- **Liquidity Sweeps**: Stop hunts for better fills
- **Market Structure**: Break of structure signals

### Recommended Reading

1. "Trading in the Zone" by Mark Douglas
2. "Market Wizards" by Jack Schwager
3. "The New Trading for a Living" by Dr. Alexander Elder
4. Smart Money Concepts courses by various educators

### Nautilus Trader Documentation

- [Official Docs](https://nautilustrader.io/docs/)
- [Strategy Development Guide](https://nautilustrader.io/docs/guides/strategy_development)
- [Backtesting Guide](https://nautilustrader.io/docs/guides/backtesting)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙋 Support

For questions or issues:

1. Check the documentation above
2. Review Nautilus Trader docs
3. Open an issue on GitHub
4. Join Nautilus Trader community

## 🔄 Version History

### v1.0.0 (Current)
- Initial release
- Full Order Block strategy implementation
- Multi-timeframe analysis
- Comprehensive risk management
- Backtesting examples

---

**Disclaimer**: This strategy is provided as-is for educational purposes. Use at your own risk. The authors are not responsible for any trading losses.

**Remember**: The best strategy is one you understand completely and can execute with discipline!
