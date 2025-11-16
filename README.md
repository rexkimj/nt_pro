# Nautilus Trader - Order Block Strategy

Professional algorithmic trading strategy implementation using Nautilus Trader framework.

## 🎯 Project Overview

This repository contains a complete implementation of an **Order Block Trading Strategy** based on Smart Money Concepts (SMC). The strategy identifies institutional order flow and market structure to generate high-probability trading signals.

## 📦 What's Included

### Order Block Strategy (`strategies/order_block/`)

A sophisticated multi-timeframe strategy that combines:

- ✅ **Order Block Detection** - Identifies institutional supply/demand zones
- ✅ **Fair Value Gap (FVG)** - Detects price imbalances
- ✅ **Liquidity Sweep** - Identifies stop hunts and liquidity grabs
- ✅ **Change of Character (CHoCH)** - Confirms market structure shifts
- ✅ **Fibonacci Retracement** - Optimal entry zone filtering
- ✅ **Advanced Risk Management** - Multi-target, trailing stops, daily limits

### Documentation

- 📚 **Strategy README** - Complete strategy documentation
- 📊 **Backtest Examples** - Ready-to-use backtesting scripts
- 🏗️ **Architecture Guide** - Nautilus Trader system overview
- 📖 **Quick Reference** - Common patterns and code snippets

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd nt_pro

# Install Nautilus Trader
pip install nautilus_trader

# Install dependencies
pip install -r requirements.txt  # If available
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
)

# Create strategy
strategy = OrderBlockStrategy(config)
```

### 3. Run Backtest

```bash
# Navigate to strategy directory
cd strategies/order_block

# Run backtest
python backtest_example.py backtest

# Optimize parameters
python backtest_example.py optimize

# View live trading setup
python backtest_example.py live
```

## 📁 Project Structure

```
nt_pro/
├── strategies/
│   └── order_block/
│       ├── __init__.py              # Package exports
│       ├── indicators.py            # Technical indicators
│       ├── strategy.py              # Main strategy class
│       ├── backtest_example.py      # Backtesting scripts
│       └── README.md               # Strategy documentation
│
├── ARCHITECTURE_OVERVIEW.md        # System architecture
├── NAUTILUS_TRADER_CODEBASE_GUIDE.md  # Codebase reference
├── QUICK_REFERENCE.md              # Code patterns
├── README_EXPLORATION.md           # Exploration guide
├── STRATEGY_TEMPLATE.py            # Strategy template
└── README.md                       # This file
```

## 🎓 Strategy Overview

### Entry Logic

The strategy enters trades when **ALL** conditions align:

1. **Order Block (H4/D1)** - Price returns to institutional zone
2. **Fair Value Gap** - Imbalance present in same direction
3. **Liquidity Sweep** - Stop hunt occurred recently
4. **CHoCH (15m)** - Market structure break confirmed
5. **Fibonacci Zone** - Price in 0.5-0.618 retracement (optional)

### Risk Management

| Feature | Configuration |
|---------|---------------|
| Stop Loss | Order Block boundary ± 1% |
| Take Profit 1 | 1:2 Risk/Reward (50% close) |
| Take Profit 2 | 1:4 Risk/Reward (trailing) |
| Trailing Stop | Activates at 1:2 RR, 20 pips distance |
| Daily Max Loss | 2% of account balance |
| Max Positions | 1 concurrent trade |

### Example Trade

**Long Entry**:
- Entry: 1.0865 (price in OB + Fib golden zone)
- Stop Loss: 1.0850 (15 pips risk)
- TP1: 1.0895 (30 pips, 1:2 RR)
- TP2: 1.0925 (60 pips, 1:4 RR)

At TP1: Close 50%, activate trailing stop for remaining position.

## 📊 Performance Features

### Multi-Timeframe Analysis
- **Higher Timeframe (H4/D1)**: Order Block, FVG, Liquidity Sweep detection
- **Lower Timeframe (15m)**: Entry confirmation via CHoCH

### Signal Quality
- Multiple confluence factors required
- Fibonacci filtering for optimal entries
- Recent structure break confirmation

### Position Management
- Partial profit taking at TP1
- Trailing stop for remaining position
- Breakeven move after TP1
- Daily loss circuit breaker

## ⚙️ Configuration

### Key Parameters

```python
# Order Block Detection
ob_swing_lookback = 5          # Swing point detection period
ob_min_strength_pips = 20.0    # Minimum move strength
ob_max_blocks = 10             # Maximum tracked blocks

# Risk Management
stop_loss_percent = 1.0        # SL distance from OB (%)
tp1_risk_reward = 2.0          # First target (1:2)
tp2_risk_reward = 4.0          # Second target (1:4)
tp1_close_percent = 50.0       # % to close at TP1

# Daily Risk
daily_max_loss_percent = 2.0   # Maximum daily loss
max_positions = 1              # Concurrent trades limit
```

See `strategies/order_block/README.md` for complete parameter reference.

## 🧪 Testing

### Backtesting

```bash
# Basic backtest with default parameters
python strategies/order_block/backtest_example.py backtest

# Parameter optimization
python strategies/order_block/backtest_example.py optimize
```

### Recommended Testing Process

1. **Backtest** - 2+ years historical data
2. **Walk-forward analysis** - Avoid overfitting
3. **Paper trading** - 1-3 months simulation
4. **Live (minimum size)** - Start with smallest position
5. **Scale gradually** - Increase size as confidence builds

## 📚 Documentation

### Strategy Documentation
- **[Order Block Strategy README](strategies/order_block/README.md)** - Complete strategy guide
- **[Backtest Examples](strategies/order_block/backtest_example.py)** - Usage examples

### Nautilus Trader Resources
- **[Architecture Overview](ARCHITECTURE_OVERVIEW.md)** - System design
- **[Codebase Guide](NAUTILUS_TRADER_CODEBASE_GUIDE.md)** - Implementation reference
- **[Quick Reference](QUICK_REFERENCE.md)** - Code patterns
- **[Official Docs](https://nautilustrader.io/docs/)** - Nautilus Trader documentation

### Learning Path

**Beginners** (1.5-2 hours):
1. Read README_EXPLORATION.md
2. Review ARCHITECTURE_OVERVIEW.md
3. Study NAUTILUS_TRADER_CODEBASE_GUIDE.md sections 1-3
4. Experiment with STRATEGY_TEMPLATE.py

**Intermediate** (1-1.5 hours):
1. Review Guide sections 3-6
2. Study Architecture diagrams
3. Analyze Order Block strategy code

**Advanced** (30-45 minutes):
1. Review strategy implementation
2. Customize parameters
3. Implement modifications

## ⚠️ Important Warnings

### Before Live Trading

- [ ] Thoroughly backtest on multiple instruments
- [ ] Paper trade for minimum 1 month
- [ ] Understand all entry/exit conditions
- [ ] Verify risk management works correctly
- [ ] Start with minimum position size
- [ ] NEVER risk more than you can afford to lose

### Risk Disclosure

```
⚠️ TRADING CARRIES SIGNIFICANT RISK OF LOSS ⚠️

- Past performance does NOT guarantee future results
- This strategy is for EDUCATIONAL purposes only
- Always use proper risk management
- Never risk money you cannot afford to lose
- Thoroughly test before live trading
```

## 🛠️ Development

### Adding Custom Indicators

```python
from strategies.order_block.indicators import OrderBlockDetector

class MyCustomIndicator(OrderBlockDetector):
    def __init__(self, custom_param=10):
        super().__init__()
        self.custom_param = custom_param

    def update(self, bar):
        # Custom logic here
        return super().update(bar)
```

### Extending the Strategy

```python
from strategies.order_block import OrderBlockStrategy

class MyCustomStrategy(OrderBlockStrategy):
    def _check_long_entry_conditions(self, bar):
        # Add custom filters
        base_conditions = super()._check_long_entry_conditions(bar)
        custom_filter = self._my_custom_check(bar)
        return base_conditions and custom_filter
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙋 Support

For questions or issues:

1. Review documentation in this README
2. Check `strategies/order_block/README.md`
3. Consult Nautilus Trader [official docs](https://nautilustrader.io/docs/)
4. Open an issue on GitHub

## 🔄 Version History

### v1.0.0 (Current)
- ✅ Order Block detection (H4/D1)
- ✅ Fair Value Gap detection
- ✅ Liquidity Sweep identification
- ✅ CHoCH confirmation (15m)
- ✅ Fibonacci filtering
- ✅ Multi-target risk management
- ✅ Trailing stop implementation
- ✅ Daily loss limits
- ✅ Complete documentation
- ✅ Backtest examples

## 🎯 Roadmap

### Planned Features
- [ ] Additional SMC concepts (Break of Structure, etc.)
- [ ] Volume analysis integration
- [ ] Optimized parameter sets for different instruments
- [ ] Machine learning signal filtering
- [ ] Multi-instrument support
- [ ] Advanced portfolio management
- [ ] Real-time alerting system
- [ ] Performance analytics dashboard

## 📞 Contact

For strategy questions, customization requests, or collaboration:
- Open an issue on GitHub
- Join Nautilus Trader community

---

**Built with [Nautilus Trader](https://nautilustrader.io)** - Professional algorithmic trading platform

**Remember**: Success in trading requires discipline, proper risk management, and continuous learning!

---

*Disclaimer: This software is provided for educational purposes only. Trading involves substantial risk of loss. Past performance is not indicative of future results. Always conduct thorough testing and use proper risk management.*
