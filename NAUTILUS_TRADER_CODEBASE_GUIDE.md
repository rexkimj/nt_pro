# Nautilus Trader Codebase Exploration Guide

## 1. OVERALL PROJECT STRUCTURE

### Technology Stack
- **Hybrid Codebase**: Python, Cython, and Rust
- **Core**: Performance-critical components written in Rust or Cython
- **Python Bindings**: Statically linked Rust libraries via Cython (CPython API extension)
- **Architecture**: Modular, event-driven design with adapter pattern for venue connectivity

### Main Directory Layout

```
nautilus_trader/
├── core/                    # Low-level components, constants, and functions
├── common/                  # Common utilities for assembling framework components
├── network/                 # Low-level networking client components
├── serialization/           # Serialization implementations
├── trading/                 # Trading engine components and strategies
├── indicators/              # Technical indicators (RSI, MACD, EMA, etc.)
├── backtest/                # Backtesting engine and utilities
├── system/                  # NautilusKernel and system implementations
├── live/                    # Live trading system implementation
├── adapters/                # Exchange and data provider adapters
├── examples/                # Example strategies and backtests
└── tests/                   # Test suite
```

### Key Subpackages
- **nautilus_trader.core** - Base components used throughout the framework
- **nautilus_trader.common** - Common assembly utilities
- **nautilus_trader.network** - Networking base
- **nautilus_trader.serialization** - Serialization base
- **nautilus_trader.system** - NautilusKernel and system infrastructure
- **nautilus_trader.trading** - Trading strategies and execution
- **nautilus_trader.indicators** - Technical indicators library
- **nautilus_trader.backtest** - Backtesting framework

---

## 2. STRATEGY IMPLEMENTATION PATTERNS

### Strategy Structure Overview

There are TWO main components to implement:

1. **Strategy Implementation** - Inherits from `Strategy` class
2. **Strategy Configuration** (optional) - Inherits from `StrategyConfig` class

#### Key Principle
```
The SAME source code can be used for both backtesting AND live trading
```

### Strategy Base Class Hierarchy

```
Actor (base class)
  └── Strategy (your strategies inherit from this)
```

### Strategy Base Class - Key Methods & Handlers

#### Data Handlers (Methods you override)
These handlers are called automatically when subscribed data arrives:

```python
def on_order_book_deltas(self, deltas: OrderBookDeltas) -> None:
    """Called when order book deltas received"""
    
def on_order_book(self, order_book: OrderBook) -> None:
    """Called when full order book snapshot received"""
    
def on_quote_tick(self, tick: QuoteTick) -> None:
    """Called when quote tick (bid/ask) data received"""
    
def on_trade_tick(self, tick: TradeTick) -> None:
    """Called when trade tick data received (note: 'tick', not 'trade')"""
    
def on_bar(self, bar: Bar) -> None:
    """Called when OHLC bar data received"""
    
def on_instrument(self, instrument: Instrument) -> None:
    """Called when instrument information received"""
    
def on_instrument_status(self, data: InstrumentStatus) -> None:
    """Called when instrument status changes"""
    
def on_data(self, data: Data) -> None:
    """Called for custom data types"""
```

#### Order Execution Methods
```python
def submit_order(self, order: Order, position_id: PositionId = None) -> None:
    """Submit an order to the system"""
    
def modify_order(self, order: Order) -> None:
    """Modify an existing order"""
    
def cancel_order(self, order_id: OrderId) -> None:
    """Cancel an existing order"""
```

#### Indicator Registration Methods
```python
def register_indicator_for_bars(self, bar_type: BarType, indicator: Indicator) -> None:
    """Register indicator to receive bar updates"""
    
def register_indicator_for_quote_ticks(self, instrument_id: InstrumentId, indicator: Indicator) -> None:
    """Register indicator to receive quote tick updates"""
    
def register_indicator_for_trade_ticks(self, instrument_id: InstrumentId, indicator: Indicator) -> None:
    """Register indicator to receive trade tick updates"""
```

### Basic Strategy Template

```python
from nautilus_trader.trading.strategy import Strategy, StrategyConfig
from nautilus_trader.core.data import Bar
from nautilus_trader.indicators import ExponentialMovingAverage

class MyStrategy(Strategy):
    def __init__(self, config: MyStrategyConfig) -> None:
        super().__init__(config)
        
        # Initialize configuration
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.trade_size = config.trade_size
        
        # Initialize indicators
        self.fast_ema = ExponentialMovingAverage(period=config.fast_ema_period)
        self.slow_ema = ExponentialMovingAverage(period=config.slow_ema_period)
    
    def on_start(self) -> None:
        """Called when strategy starts"""
        # Subscribe to data
        self.subscribe_bars(self.bar_type)
        
        # Register indicators
        self.register_indicator_for_bars(self.bar_type, self.fast_ema)
        self.register_indicator_for_bars(self.bar_type, self.slow_ema)
    
    def on_bar(self, bar: Bar) -> None:
        """Called on each new bar"""
        # Update indicators manually or automatically
        # (automatic if using register_indicator_for_bars)
        
        # Access the cache for data
        position = self.cache.position(self.instrument_id)
        
        # Trading logic
        if self.fast_ema.value > self.slow_ema.value:
            # Entry logic
            if position is None or position.is_flat:
                self.buy(self.trade_size)
        else:
            # Exit logic
            if position and position.is_long:
                self.close_position(position.id)
    
    def on_stop(self) -> None:
        """Called when strategy stops"""
        # Cleanup logic
        pass


class MyStrategyConfig(StrategyConfig):
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    fast_ema_period: int = 10
    slow_ema_period: int = 20
```

---

## 3. EXISTING STRATEGY EXAMPLES

### EMA Cross Strategy (Minimal Example)
Located at: `nautilus_trader/examples/strategies/ema_cross.py`

**Key Features:**
- Simple moving average cross strategy
- Fast EMA period: 10 (default)
- Slow EMA period: 20 (default)
- Enters position when fast EMA crosses slow EMA
- Uses StrategyConfig for parameterization

**Configuration Parameters:**
```python
class EMACrossConfig(StrategyConfig):
    instrument_id: InstrumentId          # Trading instrument
    bar_type: BarType                    # OHLC bar resolution
    trade_size: Decimal                  # Position size
    fast_ema_period: int = 10           # Fast moving average period
    slow_ema_period: int = 20           # Slow moving average period
    subscribe_trade_ticks: bool = False # Optional trade tick subscription
    subscribe_quote_ticks: bool = False # Optional quote tick subscription
    close_positions_on_stop: bool = True # Auto-close on shutdown
```

### Backtest Examples
**FX Examples:**
- `/examples/backtest/fx_ema_cross_audusd_ticks.py` - AUD/USD with ticks
- `/examples/backtest/fx_ema_cross_bracket_gbpusd_bars_external.py` - GBP/USD with bracket orders

**Crypto Examples:**
- `/examples/backtest/crypto_ema_cross_ethusdt_trade_ticks.py` - ETH/USDT with trade ticks
- `/examples/backtest/crypto_ema_cross_ethusdt_trailing_stop.py` - With trailing stops

**Equity Examples:**
- `/examples/backtest/databento_ema_cross_long_only_tsla_trades.py` - TSLA long-only variant

---

## 4. INDICATORS AND CUSTOM LOGIC IMPLEMENTATION

### Available Built-in Indicators

Located in: `nautilus_trader.indicators`

**Moving Averages:**
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- DEMA (Double EMA)
- TEMA (Triple EMA)
- HMA (Hull Moving Average)
- WMA (Weighted Moving Average)
- VWAP (Volume Weighted Average Price)
- Adaptive Moving Averages
- Linear Regression

**Momentum Indicators:**
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Aroon
- Bollinger Bands
- CCI (Commodity Channel Index)
- Stochastics
- Rate of Change (ROC)

### Indicator Features
- **High Performance**: Bounded memory usage with efficient circular buffers
- **Unified Interface**: Supports bars, quotes, trades, and order book data
- **Real-time Processing**: Optimized for latency-sensitive applications
- **Recommendation**: Use Cython for performance-critical indicators

### Indicator Implementation Pattern

```python
from nautilus_trader.indicators import Indicator

class MyCustomIndicator(Indicator):
    def __init__(self, period: int, name: str = None) -> None:
        super().__init__(period=period, name=name)
    
    def handle_bar(self, bar: Bar) -> None:
        """Process new bar"""
        # Update indicator value
        pass
    
    def handle_quote_tick(self, tick: QuoteTick) -> None:
        """Process quote tick (if applicable)"""
        pass
    
    def handle_trade_tick(self, tick: TradeTick) -> None:
        """Process trade tick (if applicable)"""
        pass
    
    @property
    def value(self) -> float:
        """Return current indicator value"""
        return self._value
```

### Using Indicators in Strategy

```python
# Manual indicator updates
def on_bar(self, bar: Bar) -> None:
    self.my_indicator.handle_bar(bar)  # Manual update
    current_value = self.my_indicator.value

# Or automatic registration (recommended)
def on_start(self) -> None:
    self.register_indicator_for_bars(self.bar_type, self.my_indicator)
    # Now on_bar automatically updates it
```

---

## 5. DATA HANDLING PATTERNS

### Cache-Based Access Pattern

The **Cache** is a central in-memory database storing all trading-related data:

```python
# Access via strategy's cache object
def on_bar(self, bar: Bar) -> None:
    # Get position data
    position = self.cache.position(self.instrument_id)
    
    # Get order data
    order = self.cache.order(self.order_id)
    orders = self.cache.orders(self.instrument_id)
    
    # Get historical market data
    quote_ticks = self.cache.quote_ticks(self.instrument_id)
    trade_ticks = self.cache.trade_ticks(self.instrument_id)
    bars = self.cache.bars(self.bar_type)
    
    # Get account and portfolio data
    account = self.cache.account()
    balance = self.cache.balance(self.instrument_id.venue)
```

### Cache Contents
- Complete order history and execution state
- All positions and account information
- Historical market data (quote ticks, trade ticks, bars)
- Custom data snapshots

### Data Subscription Pattern

```python
def on_start(self) -> None:
    # Subscribe to data types
    self.subscribe_bars(self.bar_type)
    self.subscribe_quote_ticks(self.instrument_id)
    self.subscribe_trade_ticks(self.instrument_id)
    self.subscribe_order_book_deltas(self.instrument_id)
```

### Data Types

```python
# Bar Data (OHLC)
from nautilus_trader.core.data import Bar
bar.open, bar.high, bar.low, bar.close, bar.volume

# Quote Tick (Bid/Ask)
from nautilus_trader.core.data import QuoteTick
quote.bid, quote.ask, quote.bid_size, quote.ask_size, quote.ts_event

# Trade Tick (Executed trades)
from nautilus_trader.core.data import TradeTick
trade.price, trade.size, trade.ts_event

# Order Book Deltas
from nautilus_trader.core.data import OrderBookDeltas
deltas.updates  # List of order book updates
```

### Message Bus Pattern

The system uses a **Message Bus** for all communication:

```
Strategy -> OrderEmulator -> ExecAlgorithm -> RiskEngine -> ExecutionEngine -> ExecutionClient
```

- Routes market data to subscribers
- Manages order commands and execution events
- Handles multiple data types (quotes, trades, bars, order books, custom data)
- Ensures proper ordering of events

---

## 6. ORDER EXECUTION PATTERNS

### Order Submission Flow

```python
def on_bar(self, bar: Bar) -> None:
    # Create order
    order = self.order_factory.market(
        instrument_id=self.instrument_id,
        order_side=OrderSide.BUY,
        quantity=self.trade_size,
    )
    
    # Submit order (simplified)
    # or use convenience methods:
    self.buy(quantity=self.trade_size)
    self.sell(quantity=self.trade_size)
```

### Order Execution Path
1. **Strategy** submits `SubmitOrder` command
2. **OrderEmulator** (if emulated orders enabled)
3. **ExecAlgorithm** (if execution algorithm specified)
4. **RiskEngine** (validates against risk limits)
5. **ExecutionEngine** (prepares for transmission)
6. **ExecutionClient** (sends to venue)

### Position Management Modes

**NETTING Mode (default):**
- One position per instrument
- All fills aggregated into single position
- Position flips from LONG to SHORT as net quantity changes

**HEDGING Mode:**
- Multiple simultaneous positions allowed
- Each position has unique position ID
- Separate tracking of LONG and SHORT positions

```python
# Access position
position = self.cache.position(self.instrument_id)

# Check position state
if position:
    position.is_long  # Currently long?
    position.is_short # Currently short?
    position.is_flat  # No position?
    position.quantity # Current size
    position.entry_price # Average entry price
```

### Position Closing

```python
# Close entire position
if position and position.is_long:
    self.close_position(position.id)

# Or sell specific quantity
self.sell(quantity=desired_size)
```

### Order Types and Modifiers

```python
# Market Orders
self.buy(quantity)   # Market buy
self.sell(quantity)  # Market sell

# Limit Orders (via order factory)
limit_order = self.order_factory.limit(
    instrument_id=self.instrument_id,
    order_side=OrderSide.BUY,
    quantity=self.trade_size,
    price=target_price,
)
self.submit_order(limit_order)

# Bracket Orders (stop-loss + take-profit)
# Typically handled by execution algorithms
```

### Order Reconciliation
For **live trading**, the system reconciles external order state with internal state through the **LiveExecutionEngine**, ensuring consistency across syncing failures.

---

## 7. RECOMMENDED APPROACH FOR ORDER BLOCK TRADING STRATEGY

### Step 1: Understand Order Block Concepts
Order blocks are price zones where institutions accumulated or distributed positions, typically at swing highs/lows or structural breaks.

**Key Components:**
- Identify order blocks at structural levels
- Monitor price action around these blocks
- Trade rejections/reversals at block boundaries
- Track order block "breaks" as continuation signals

### Step 2: Create Custom Order Block Indicator

```python
# File: indicators/order_block.py
from nautilus_trader.indicators import Indicator
from nautilus_trader.core.data import Bar
from typing import List

class OrderBlockIndicator(Indicator):
    """
    Identifies order blocks based on:
    - Swing highs and lows
    - Breakout structure
    - Volume profile
    """
    
    def __init__(
        self,
        lookback_period: int = 20,
        min_range: float = 50,  # Minimum points for valid block
        name: str = None
    ) -> None:
        super().__init__(name=name)
        self.lookback_period = lookback_period
        self.min_range = min_range
        
        self.order_blocks: List[dict] = []  # [{high, low, type, timestamp}, ...]
        self.bars_buffer = []
    
    def handle_bar(self, bar: Bar) -> None:
        """Identify order blocks from bar data"""
        self.bars_buffer.append(bar)
        
        if len(self.bars_buffer) > self.lookback_period:
            self.bars_buffer.pop(0)
        
        # Detect swing highs/lows
        if len(self.bars_buffer) >= 3:
            mid_idx = len(self.bars_buffer) // 2
            mid_bar = self.bars_buffer[mid_idx]
            
            # Check if swing high
            is_swing_high = all(
                mid_bar.high > self.bars_buffer[i].high
                for i in range(len(self.bars_buffer))
                if i != mid_idx
            )
            
            # Check if swing low
            is_swing_low = all(
                mid_bar.low < self.bars_buffer[i].low
                for i in range(len(self.bars_buffer))
                if i != mid_idx
            )
            
            if is_swing_high or is_swing_low:
                block_type = 'supply' if is_swing_high else 'demand'
                block_range = abs(mid_bar.high - mid_bar.low)
                
                if block_range >= self.min_range:
                    self.order_blocks.append({
                        'high': mid_bar.high,
                        'low': mid_bar.low,
                        'type': block_type,
                        'timestamp': bar.ts_event,
                    })
    
    @property
    def value(self) -> float:
        """Return number of active order blocks"""
        return len(self.order_blocks)
    
    def get_order_blocks(self) -> List[dict]:
        """Get list of identified order blocks"""
        return self.order_blocks.copy()
    
    def is_at_block(self, price: float, tolerance: float = 0.01) -> str:
        """Check if price is at order block boundary"""
        for block in self.order_blocks:
            if abs(price - block['high']) < tolerance or \
               abs(price - block['low']) < tolerance:
                return block['type']
        return None
```

### Step 3: Create Order Block Strategy

```python
# File: strategies/order_block_strategy.py
from nautilus_trader.trading.strategy import Strategy, StrategyConfig
from nautilus_trader.core.data import Bar
from indicators.order_block import OrderBlockIndicator

class OrderBlockStrategyConfig(StrategyConfig):
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    order_block_lookback: int = 20
    risk_points: int = 50
    reward_multiplier: float = 2.0

class OrderBlockStrategy(Strategy):
    def __init__(self, config: OrderBlockStrategyConfig) -> None:
        super().__init__(config)
        
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.trade_size = config.trade_size
        self.risk_points = config.risk_points
        self.reward_multiplier = config.reward_multiplier
        
        # Initialize order block indicator
        self.order_block = OrderBlockIndicator(
            lookback_period=config.order_block_lookback
        )
    
    def on_start(self) -> None:
        """Initialize strategy"""
        self.subscribe_bars(self.bar_type)
        self.register_indicator_for_bars(self.bar_type, self.order_block)
    
    def on_bar(self, bar: Bar) -> None:
        """Handle bar events"""
        
        # Get current position
        position = self.cache.position(self.instrument_id)
        
        # Check if price is at order block
        block_type = self.order_block.is_at_block(bar.close)
        
        if block_type == 'supply':
            # Potential short at supply block with rejection
            if position is None or position.is_flat:
                self._enter_short(bar)
        
        elif block_type == 'demand':
            # Potential long at demand block with rejection
            if position is None or position.is_flat:
                self._enter_long(bar)
        
        # Position management
        if position:
            self._manage_position(bar, position)
    
    def _enter_long(self, bar: Bar) -> None:
        """Enter long position"""
        self.buy(quantity=self.trade_size)
    
    def _enter_short(self, bar: Bar) -> None:
        """Enter short position"""
        self.sell(quantity=self.trade_size)
    
    def _manage_position(self, bar: Bar, position) -> None:
        """Manage open position"""
        # Implement stop-loss and take-profit logic
        if position.is_long:
            stop_loss = position.entry_price - self.risk_points
            take_profit = position.entry_price + (self.risk_points * self.reward_multiplier)
            
            if bar.close <= stop_loss:
                self.close_position(position.id)
            elif bar.close >= take_profit:
                self.close_position(position.id)
        
        elif position.is_short:
            stop_loss = position.entry_price + self.risk_points
            take_profit = position.entry_price - (self.risk_points * self.reward_multiplier)
            
            if bar.close >= stop_loss:
                self.close_position(position.id)
            elif bar.close <= take_profit:
                self.close_position(position.id)
```

### Step 4: Create Backtest Script

```python
# File: examples/backtest/order_block_strategy_backtest.py
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.backtest.results import BacktestResults
from strategies.order_block_strategy import OrderBlockStrategyConfig

# Configuration
config = OrderBlockStrategyConfig(
    instrument_id="EURUSD.SIM",
    bar_type=BarType.from_str("EURUSD.SIM,15-MINUTE"),
    trade_size=Decimal("100000"),
    order_block_lookback=20,
    risk_points=50,
    reward_multiplier=2.0,
)

# Run backtest
node = BacktestNode()
results = node.run([config])

# Analyze results
print(results.summary())
```

### Step 5: Key Considerations

**Data Requirements:**
- OHLC bars at desired timeframe (15-min, 1-hour, 4-hour, daily)
- Sufficient history to identify order blocks

**Optimization Points:**
- Lookback period for swing detection
- Minimum block range threshold
- Risk/reward ratio
- Position size management
- Multiple timeframe confirmation

**Testing Strategy:**
1. Start with longer timeframes (4H, Daily)
2. Test on multiple instruments
3. Walk-forward analysis for robustness
4. Live paper trading validation

---

## KEY FILES TO REFERENCE

1. **EMA Cross Strategy**: `nautilus_trader/examples/strategies/ema_cross.py`
2. **Backtest Examples**: `nautilus_trader/examples/backtest/`
3. **Indicators Module**: `nautilus_trader/indicators/`
4. **Strategy Base Class**: `nautilus_trader/trading/strategy.py`
5. **Order Types**: `nautilus_trader/trading/orders/`
6. **Cache API**: `nautilus_trader/core/cache.py`
7. **Data Types**: `nautilus_trader/core/data.py`

---

## COMMON PATTERNS SUMMARY

| Pattern | Use Case | Key Classes |
|---------|----------|------------|
| **Bar-Based Strategy** | OHLC data analysis | on_bar(), BarType |
| **Tick-Based Strategy** | Real-time quote/trade | on_quote_tick(), on_trade_tick() |
| **Indicator Registration** | Automatic updates | register_indicator_for_bars() |
| **Position Management** | Entry/exit logic | self.cache.position() |
| **Order Submission** | Send orders | submit_order(), buy(), sell() |
| **Multi-Timeframe** | Confluence signals | Multiple BarTypes |
| **Risk Management** | Stop-loss/TP | close_position(), modify_order() |
| **Custom Indicators** | Domain logic | Custom Indicator subclass |

---

## NEXT STEPS

1. Review the EMA Cross strategy example
2. Examine a complete backtest example
3. Implement your order block indicator
4. Test with historical data
5. Paper trade before going live
6. Monitor and optimize based on results

