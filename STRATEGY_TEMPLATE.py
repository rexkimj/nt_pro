"""
Nautilus Trader Strategy Template
==================================

This is a basic template to get you started with Nautilus Trader strategy development.
Copy this file and modify for your specific strategy.

Key Components:
1. StrategyConfig - Configuration class with parameters
2. Strategy - Main strategy logic class
3. Handler methods - Methods called on events (on_bar, on_quote_tick, etc.)
"""

from decimal import Decimal
from typing import Optional

from nautilus_trader.core.data import Bar, BarType, InstrumentId
from nautilus_trader.indicators import ExponentialMovingAverage
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


# ============================================================================
# STEP 1: Define Configuration Class
# ============================================================================

class TemplateStrategyConfig(StrategyConfig):
    """
    Configuration class for the Template Strategy.
    
    All parameters here can be passed when creating the strategy, allowing for
    easy backtesting with different parameter sets.
    """
    
    # REQUIRED parameters (these must be provided)
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal
    
    # OPTIONAL parameters (with defaults)
    ema_period: int = 20
    close_positions_on_stop: bool = True
    log_trades: bool = True


# ============================================================================
# STEP 2: Define Strategy Class
# ============================================================================

class TemplateStrategy(Strategy):
    """
    A template trading strategy demonstrating:
    - Configuration management
    - Indicator usage
    - Position management
    - Order execution
    - Data access via cache
    """
    
    def __init__(self, config: TemplateStrategyConfig) -> None:
        """
        Initialize the strategy.
        
        Args:
            config: Strategy configuration object containing all parameters
        """
        super().__init__(config)
        
        # Store configuration parameters as instance variables
        self.instrument_id = config.instrument_id
        self.bar_type = config.bar_type
        self.trade_size = config.trade_size
        self.ema_period = config.ema_period
        self.close_positions_on_stop = config.close_positions_on_stop
        self.log_trades = config.log_trades
        
        # Initialize indicators
        self.ema = ExponentialMovingAverage(period=self.ema_period, name="EMA")
        
        # Track trades if enabled
        self.trades_count = 0
    
    def on_start(self) -> None:
        """
        Called once when the strategy starts.
        
        Use this method to:
        - Subscribe to market data
        - Register indicators
        - Initialize state
        
        This is called AFTER the strategy is injected into the system.
        """
        self.log.info(f"Starting {self.__class__.__name__}")
        
        # Subscribe to bar data for the configured instrument
        self.subscribe_bars(self.bar_type)
        
        # Register the indicator to automatically receive bar updates
        # Without this, the indicator won't be updated
        self.register_indicator_for_bars(self.bar_type, self.ema)
        
        self.log.info(f"Subscribed to {self.bar_type}")
        self.log.info(f"EMA period: {self.ema_period}")
    
    def on_bar(self, bar: Bar) -> None:
        """
        Called when a new OHLC bar closes.
        
        This is where your main trading logic goes.
        
        Args:
            bar: The OHLC bar data (open, high, low, close, volume, etc.)
        """
        # Get current position (will be None if no position exists)
        position = self.cache.position(self.instrument_id)
        
        # Check if indicator has enough data (has been updated enough times)
        if not self.ema.ready:
            self.log.debug("Indicator not ready yet, waiting for more bars")
            return
        
        # ===== YOUR TRADING LOGIC HERE =====
        
        # Example: Simple trend following strategy
        # Buy if price is above EMA and we have no position
        # Sell if price is below EMA and we have a long position
        
        if bar.close > self.ema.value:
            # Price is above EMA (uptrend)
            if position is None or position.is_flat:
                # We have no position, enter long
                self._enter_long(bar)
        
        elif bar.close < self.ema.value:
            # Price is below EMA (downtrend)
            if position and position.is_long:
                # We have a long position, exit it
                self._exit_position(position)
    
    def on_quote_tick(self, tick) -> None:
        """
        Called when a quote tick (bid/ask) is received.
        
        This is useful if you need real-time bid/ask data between bars.
        Note: Must subscribe in on_start() to receive these events.
        """
        # This handler is optional - only override if you need quote tick data
        pass
    
    def on_trade_tick(self, tick) -> None:
        """
        Called when a trade tick is received.
        
        This is useful for tick-based analysis.
        Note: Must subscribe in on_start() to receive these events.
        """
        # This handler is optional - only override if you need trade tick data
        pass
    
    def on_order_filled(self, event) -> None:
        """
        Called when an order is filled (executed).
        
        This is useful for tracking fills and updating state.
        """
        if self.log_trades:
            self.log.info(f"Order filled: {event}")
    
    def on_stop(self) -> None:
        """
        Called when the strategy is stopped.
        
        Use this method to:
        - Close any open positions
        - Log final statistics
        - Cleanup resources
        """
        self.log.info(f"Stopping {self.__class__.__name__}")
        
        if self.close_positions_on_stop:
            # Close any open positions
            position = self.cache.position(self.instrument_id)
            if position and not position.is_flat:
                self.log.info(f"Closing position: {position}")
                self.close_position(position.id)
        
        # Log final statistics
        self.log.info(f"Total trades: {self.trades_count}")
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _enter_long(self, bar: Bar) -> None:
        """
        Enter a long position.
        
        Args:
            bar: Current bar for reference
        """
        self.log.info(f"ENTER LONG at {bar.close}, EMA: {self.ema.value}")
        self.buy(quantity=self.trade_size)
        self.trades_count += 1
    
    def _exit_position(self, position) -> None:
        """
        Exit an open position.
        
        Args:
            position: The position object to close
        """
        self.log.info(
            f"EXIT POSITION: {position.side}, "
            f"Entry: {position.entry_price}, "
            f"Current: {position.quantity}"
        )
        self.close_position(position.id)
        self.trades_count += 1
    
    def _get_position_stats(self) -> str:
        """
        Get a string representation of current position statistics.
        
        Returns:
            String with position stats
        """
        position = self.cache.position(self.instrument_id)
        if position is None:
            return "No position"
        
        return (
            f"Position: {position.side}, "
            f"Qty: {position.quantity}, "
            f"Entry: {position.entry_price}"
        )


# ============================================================================
# EXAMPLE USAGE (for testing/backtesting)
# ============================================================================

if __name__ == "__main__":
    """
    Example of how to use this strategy in a backtest.
    
    NOTE: This would need the full Nautilus Trader infrastructure to run.
    """
    
    # Example configuration
    config = TemplateStrategyConfig(
        instrument_id=InstrumentId.from_str("EURUSD.SIM"),
        bar_type=BarType.from_str("EURUSD.SIM,1-HOUR"),
        trade_size=Decimal("100000"),
        ema_period=20,
    )
    
    # To actually run this, you would need:
    # from nautilus_trader.backtest.node import BacktestNode
    # node = BacktestNode()
    # results = node.run([config])
    
    print(f"Configuration: {config}")
    print("Ready to backtest with BacktestNode!")


# ============================================================================
# COMMON PATTERNS
# ============================================================================

"""
PATTERN 1: Simple MA Crossover
================================
def on_bar(self, bar: Bar) -> None:
    if self.fast_ma.value > self.slow_ma.value:
        if position is None or position.is_flat:
            self.buy(self.trade_size)
    else:
        if position and position.is_long:
            self.close_position(position.id)


PATTERN 2: Entry with Stop Loss
==================================
def on_bar(self, bar: Bar) -> None:
    position = self.cache.position(self.instrument_id)
    
    # Entry
    if entry_signal and (position is None or position.is_flat):
        self.buy(self.trade_size)
    
    # Stop loss
    elif position and position.is_long:
        if bar.close <= position.entry_price - self.stop_loss_points:
            self.close_position(position.id)


PATTERN 3: Multi-Timeframe Analysis
======================================
def on_bar(self, bar: Bar) -> None:
    # Check if this is a specific timeframe
    if bar.bar_type == self.entry_bar_type:
        # Entry logic
        pass
    
    elif bar.bar_type == self.exit_bar_type:
        # Exit logic
        pass


PATTERN 4: Risk Management with Position Sizing
================================================
def calculate_position_size(self, account_risk: Decimal) -> Decimal:
    portfolio = self.cache.portfolio()
    balance = portfolio.balance()
    
    # Risk 2% of account per trade
    risk_amount = balance * Decimal("0.02")
    
    # Position size = risk / stop loss distance
    stop_distance = self.stop_loss_points
    position_size = risk_amount / stop_distance
    
    return position_size
"""

