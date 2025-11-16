# Nautilus Trader Quick Reference

## Strategy Implementation Checklist

### 1. Create Strategy Configuration
```python
from dataclasses import dataclass
from nautilus_trader.trading.strategy import StrategyConfig

@dataclass
class YourStrategyConfig(StrategyConfig):
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    # Add your custom parameters here
```

### 2. Create Strategy Class
```python
class YourStrategy(Strategy):
    def __init__(self, config: YourStrategyConfig) -> None:
        super().__init__(config)
        # Store config parameters
        # Initialize indicators
    
    def on_start(self) -> None:
        # Subscribe to data
        # Register indicators
    
    def on_bar(self, bar: Bar) -> None:
        # Main trading logic
    
    def on_stop(self) -> None:
        # Cleanup
```

### 3. Key Methods to Implement
| Method | Purpose | Called When |
|--------|---------|------------|
| `on_start()` | Initialize strategy | Strategy starts |
| `on_bar(bar)` | Process OHLC bar | New bar closes |
| `on_quote_tick(tick)` | Process bid/ask | Quote arrives |
| `on_trade_tick(tick)` | Process trade | Trade executes |
| `on_stop()` | Cleanup | Strategy stops |

---

## Common Code Patterns

### Subscribe to Data
```python
def on_start(self) -> None:
    self.subscribe_bars(self.bar_type)
    self.subscribe_quote_ticks(self.instrument_id)
    self.subscribe_trade_ticks(self.instrument_id)
```

### Register Indicators
```python
def on_start(self) -> None:
    self.register_indicator_for_bars(self.bar_type, self.my_ema)
    self.register_indicator_for_quote_ticks(self.instrument_id, self.my_rsi)
```

### Access Current Position
```python
position = self.cache.position(self.instrument_id)
if position and position.is_long:
    # You have a long position
    entry_price = position.entry_price
    quantity = position.quantity
```

### Submit Orders
```python
# Market buy
self.buy(quantity=Decimal("100"))

# Market sell
self.sell(quantity=Decimal("100"))

# Close position
self.close_position(position.id)

# Cancel order
self.cancel_order(order.id)
```

### Check Position State
```python
if position:
    position.is_long      # True if long
    position.is_short     # True if short
    position.is_flat      # True if no position
    position.quantity     # Current size
    position.entry_price  # Average entry
```

### Access Historical Data
```python
bars = self.cache.bars(self.bar_type)
quotes = self.cache.quote_ticks(self.instrument_id)
trades = self.cache.trade_ticks(self.instrument_id)
orders = self.cache.orders(self.instrument_id)
```

---

## Indicator Patterns

### Use Built-in Indicator
```python
from nautilus_trader.indicators import ExponentialMovingAverage

class MyStrategy(Strategy):
    def __init__(self, config: MyStrategyConfig) -> None:
        super().__init__(config)
        self.ema = ExponentialMovingAverage(period=20)
    
    def on_start(self) -> None:
        self.register_indicator_for_bars(self.bar_type, self.ema)
    
    def on_bar(self, bar: Bar) -> None:
        current_ema = self.ema.value  # Auto-updated
```

### Create Custom Indicator
```python
from nautilus_trader.indicators import Indicator

class MyIndicator(Indicator):
    def __init__(self, period: int) -> None:
        super().__init__(period=period)
    
    def handle_bar(self, bar: Bar) -> None:
        # Update indicator logic
        self._value = calculate_indicator(bar)
    
    @property
    def value(self) -> float:
        return self._value
```

---

## Order Execution Flow

### Simple Entry/Exit
```python
def on_bar(self, bar: Bar) -> None:
    position = self.cache.position(self.instrument_id)
    
    # Entry logic
    if bar.close > self.sma_50.value and (position is None or position.is_flat):
        self.buy(quantity=self.trade_size)
    
    # Exit logic
    elif bar.close < self.sma_50.value and position and position.is_long:
        self.close_position(position.id)
```

### Entry with Stop-Loss and Take-Profit
```python
def on_bar(self, bar: Bar) -> None:
    position = self.cache.position(self.instrument_id)
    
    if position and position.is_long:
        # Stop-loss
        if bar.close <= position.entry_price - self.stop_loss:
            self.close_position(position.id)
        
        # Take-profit
        elif bar.close >= position.entry_price + self.take_profit:
            self.close_position(position.id)
```

---

## Data Access Patterns

### Cache API Methods
```python
# Positions
cache.position(instrument_id)           # Current position
cache.positions(instrument_id)          # All positions for instrument

# Orders
cache.order(order_id)                   # Single order
cache.orders(instrument_id)             # All orders for instrument
cache.order_exists(order_id)            # Check if order exists

# Market Data
cache.bars(bar_type)                    # Historical bars
cache.quote_ticks(instrument_id)        # Historical quotes
cache.trade_ticks(instrument_id)        # Historical trades

# Account
cache.account()                         # Account info
cache.balance(venue)                    # Balance for venue
cache.portfolio()                       # Portfolio state
```

---

## Testing Your Strategy

### Minimal Backtest
```python
from nautilus_trader.backtest.node import BacktestNode

config = YourStrategyConfig(
    instrument_id=InstrumentId.from_str("EURUSD.SIM"),
    bar_type=BarType.from_str("EURUSD.SIM,1-HOUR"),
    trade_size=Decimal("100000"),
)

node = BacktestNode()
results = node.run([config])
print(results.summary())
```

### Key Results Metrics
```python
results.summary()          # Print full summary
results.total_return      # Total return %
results.win_rate          # Win rate %
results.profit_factor     # Profit factor
results.sharpe_ratio      # Sharpe ratio
results.drawdown_max      # Maximum drawdown
```

---

## Debugging Tips

### Log Strategy Actions
```python
def on_bar(self, bar: Bar) -> None:
    self.log.info(f"Bar: {bar.close}, Time: {bar.ts_event}")
    position = self.cache.position(self.instrument_id)
    self.log.info(f"Position: {position}")
```

### Check Indicator Values
```python
def on_bar(self, bar: Bar) -> None:
    if self.ema.ready:  # Check if indicator has enough data
        self.log.info(f"EMA: {self.ema.value}")
    else:
        self.log.info("Indicator not ready yet")
```

### Verify Data Subscription
```python
def on_bar(self, bar: Bar) -> None:
    bars = self.cache.bars(self.bar_type)
    self.log.info(f"Bars in cache: {len(bars)}")
```

---

## Common Mistakes to Avoid

1. **Forgetting to register indicators** - Indicators won't update without registration
2. **Using uninitialized position** - Always check if position exists before accessing
3. **Not subscribing to data** - Won't receive data without subscription in `on_start()`
4. **Indicator not ready** - Check `indicator.ready` property before using value
5. **Double-entry trades** - Always check if position is flat before entering
6. **Forgetting on_start()** - Setup must happen in on_start(), not __init__
7. **Using stale cache data** - Always re-fetch from cache, not stored references

---

## File Structure for Your Strategy

```
your-strategy-project/
├── strategies/
│   ├── __init__.py
│   ├── order_block_strategy.py      # Main strategy
│   └── config.py                     # Configuration classes
├── indicators/
│   ├── __init__.py
│   └── order_block.py               # Custom indicators
├── backtests/
│   ├── order_block_eurusd.py        # Backtest scripts
│   └── order_block_gbpusd.py
├── tests/
│   ├── test_strategy.py
│   └── test_indicators.py
├── data/
│   └── (historical data files)
└── README.md
```

---

## Next Steps After Basic Implementation

1. Add multiple timeframe analysis
2. Implement dynamic position sizing
3. Add portfolio-level risk management
4. Optimize parameters with walk-forward analysis
5. Add order book analysis for entries
6. Implement trailing stops
7. Add custom alert/logging
8. Deploy to paper trading first

