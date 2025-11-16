"""
Order Block Trading Strategy - Main Strategy Implementation
============================================================

Strategy Logic:
1. Identify Order Blocks on H4/D1 timeframes
2. Wait for price to return to OB + FVG formation
3. Confirm Liquidity Sweep (Stop Hunt)
4. Confirm CHoCH on 15m timeframe
5. Enter at 0.5-0.618 Fibonacci retracement level

Risk Management:
- SL: Order Block bottom -1%
- TP1: 1:2 (close 50%)
- TP2: 1:4 (trailing stop)
- Daily max loss: 2% of account
"""

from decimal import Decimal
from typing import Optional, Dict
from datetime import datetime, timedelta

from nautilus_trader.core.data import Bar, BarType
from nautilus_trader.model.data import InstrumentId
from nautilus_trader.model.enums import OrderSide, TimeInForce, PositionSide
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.orders import LimitOrder, StopMarketOrder
from nautilus_trader.trading.strategy import Strategy, StrategyConfig

from .indicators import (
    OrderBlockDetector,
    FVGDetector,
    LiquiditySweepDetector,
    CHoCHDetector,
    FibonacciCalculator,
    OrderBlock,
)


class OrderBlockStrategyConfig(StrategyConfig):
    """
    Configuration for Order Block Trading Strategy.
    """

    # Required parameters
    instrument_id: InstrumentId
    htf_bar_type: BarType  # H4 or D1 for OB detection
    ltf_bar_type: BarType  # 15m for entry confirmation
    base_trade_size: Decimal

    # Order Block detection parameters
    ob_swing_lookback: int = 5
    ob_min_strength_pips: float = 20.0
    ob_max_blocks: int = 10

    # FVG detection parameters
    fvg_max_gaps: int = 20

    # Liquidity Sweep parameters
    ls_lookback: int = 20
    ls_reversal_pips: float = 10.0

    # CHoCH detection parameters
    choch_swing_lookback: int = 5

    # Entry parameters
    use_fibonacci_filter: bool = True  # Only enter in 0.5-0.618 zone
    max_bars_since_choch: int = 10

    # Risk management parameters
    stop_loss_percent: float = 1.0  # 1% below OB
    tp1_risk_reward: float = 2.0  # 1:2
    tp2_risk_reward: float = 4.0  # 1:4
    tp1_close_percent: float = 50.0  # Close 50% at TP1
    use_trailing_stop: bool = True
    trailing_stop_activation_rr: float = 2.0  # Activate at 1:2
    trailing_stop_distance_pips: float = 20.0

    # Daily risk management
    daily_max_loss_percent: float = 2.0  # 2% of account
    max_positions: int = 1

    # Logging
    log_signals: bool = True
    close_positions_on_stop: bool = True


class OrderBlockStrategy(Strategy):
    """
    Order Block Trading Strategy with Smart Money Concepts.

    Combines Order Blocks, FVG, Liquidity Sweeps, and CHoCH
    for high-probability trade entries.
    """

    def __init__(self, config: OrderBlockStrategyConfig) -> None:
        """Initialize the strategy."""
        super().__init__(config)

        # Store configuration
        self.instrument_id = config.instrument_id
        self.htf_bar_type = config.htf_bar_type
        self.ltf_bar_type = config.ltf_bar_type
        self.base_trade_size = config.base_trade_size

        # Risk management parameters
        self.stop_loss_percent = config.stop_loss_percent
        self.tp1_risk_reward = config.tp1_risk_reward
        self.tp2_risk_reward = config.tp2_risk_reward
        self.tp1_close_percent = config.tp1_close_percent
        self.use_trailing_stop = config.use_trailing_stop
        self.trailing_stop_activation_rr = config.trailing_stop_activation_rr
        self.trailing_stop_distance_pips = config.trailing_stop_distance_pips
        self.daily_max_loss_percent = config.daily_max_loss_percent
        self.max_positions = config.max_positions

        # Entry parameters
        self.use_fibonacci_filter = config.use_fibonacci_filter
        self.max_bars_since_choch = config.max_bars_since_choch
        self.log_signals = config.log_signals

        # Initialize HTF indicators (for OB detection)
        self.htf_ob_detector = OrderBlockDetector(
            swing_lookback=config.ob_swing_lookback,
            min_strength_pips=config.ob_min_strength_pips,
            max_blocks=config.ob_max_blocks,
        )
        self.htf_fvg_detector = FVGDetector(max_gaps=config.fvg_max_gaps)
        self.htf_liquidity_sweep = LiquiditySweepDetector(
            lookback=config.ls_lookback,
            reversal_pips=config.ls_reversal_pips,
        )

        # Initialize LTF indicators (for entry confirmation)
        self.ltf_choch_detector = CHoCHDetector(
            swing_lookback=config.choch_swing_lookback
        )

        # Strategy state
        self.active_order_block: Optional[OrderBlock] = None
        self.entry_price: Optional[float] = None
        self.stop_loss_price: Optional[float] = None
        self.tp1_price: Optional[float] = None
        self.tp2_price: Optional[float] = None
        self.tp1_hit: bool = False
        self.trailing_stop_active: bool = False

        # Daily loss tracking
        self.daily_pnl: Decimal = Decimal("0")
        self.current_date: Optional[datetime] = None

        # Statistics
        self.total_signals = 0
        self.total_entries = 0

    def on_start(self) -> None:
        """Called when strategy starts."""
        self.log.info(f"Starting {self.__class__.__name__}")

        # Subscribe to both timeframes
        self.subscribe_bars(self.htf_bar_type)
        self.subscribe_bars(self.ltf_bar_type)

        self.log.info(f"Subscribed to HTF: {self.htf_bar_type}")
        self.log.info(f"Subscribed to LTF: {self.ltf_bar_type}")
        self.log.info(
            f"Risk Management: SL={self.stop_loss_percent}%, "
            f"TP1={self.tp1_risk_reward}:1, TP2={self.tp2_risk_reward}:1"
        )

    def on_bar(self, bar: Bar) -> None:
        """Called when a new bar closes."""
        # Update daily PnL tracking
        self._update_daily_pnl(bar)

        # Check daily loss limit
        if self._is_daily_loss_limit_reached():
            self.log.warning("Daily loss limit reached. No new entries allowed.")
            return

        # Route to appropriate handler based on timeframe
        if bar.bar_type == self.htf_bar_type:
            self._on_htf_bar(bar)
        elif bar.bar_type == self.ltf_bar_type:
            self._on_ltf_bar(bar)

        # Update trailing stop if active
        if self.trailing_stop_active:
            self._update_trailing_stop(bar)

    def _on_htf_bar(self, bar: Bar) -> None:
        """
        Process Higher TimeFrame (H4/D1) bar.
        Updates Order Blocks, FVG, and Liquidity Sweep detectors.
        """
        # Update all HTF detectors
        new_ob = self.htf_ob_detector.update(bar)
        new_fvg = self.htf_fvg_detector.update(bar)
        sweep = self.htf_liquidity_sweep.update(bar)

        # Log new detections
        if new_ob and self.log_signals:
            self.log.info(
                f"[HTF] New Order Block detected: {new_ob.direction} "
                f"at {new_ob.low:.5f}-{new_ob.high:.5f}, strength={new_ob.strength:.5f}"
            )

        if new_fvg and self.log_signals:
            self.log.info(
                f"[HTF] New FVG detected: {new_fvg.direction} "
                f"at {new_fvg.low:.5f}-{new_fvg.high:.5f}"
            )

        if sweep and self.log_signals:
            self.log.info(f"[HTF] Liquidity Sweep: {sweep}")

    def _on_ltf_bar(self, bar: Bar) -> None:
        """
        Process Lower TimeFrame (15m) bar.
        Checks for CHoCH and evaluates entry conditions.
        """
        # Update LTF detector
        choch = self.ltf_choch_detector.update(bar)

        if choch and self.log_signals:
            self.log.info(f"[LTF] CHoCH detected: {choch}")

        # Check if we should enter a trade
        position = self.cache.position(self.instrument_id)

        # Only enter if no position or flat
        if position is None or position.is_flat:
            # Check for long entry
            if self._check_long_entry_conditions(bar):
                self._enter_long(bar)
            # Check for short entry
            elif self._check_short_entry_conditions(bar):
                self._enter_short(bar)

    def _check_long_entry_conditions(self, bar: Bar) -> bool:
        """
        Check if all conditions for long entry are met.

        Conditions:
        1. Bullish Order Block exists and price is testing it
        2. Bullish FVG exists
        3. Bullish liquidity sweep occurred recently
        4. Bullish CHoCH confirmed on LTF
        5. Price is in Fibonacci golden zone (0.5-0.618)
        """
        # Get active bullish OBs
        bullish_obs = self.htf_ob_detector.get_active_order_blocks('bullish')
        if not bullish_obs:
            return False

        # Get the most recent and strongest bullish OB
        bullish_ob = max(bullish_obs, key=lambda x: x.strength)

        # Check if price is testing the OB (within the zone)
        current_price = bar.close.as_double()
        if not (bullish_ob.low <= current_price <= bullish_ob.high):
            return False

        # Check for bullish FVG
        bullish_fvgs = self.htf_fvg_detector.get_active_fvgs('bullish')
        if not bullish_fvgs:
            return False

        # Check for recent bullish liquidity sweep
        if not self.htf_liquidity_sweep.has_recent_sweep('bullish_sweep', bars_ago=5):
            return False

        # Check for bullish CHoCH on LTF
        if not self.ltf_choch_detector.has_recent_choch('bullish_choch',
                                                         bars_ago=self.max_bars_since_choch):
            return False

        # Fibonacci filter (optional but recommended)
        if self.use_fibonacci_filter:
            # Calculate Fibonacci from recent swing low to swing high
            swing_lows = self.htf_ob_detector.swing_lows
            swing_highs = self.htf_ob_detector.swing_highs

            if swing_lows and swing_highs:
                recent_low = min(swing_lows[-3:], key=lambda x: x.price).price
                recent_high = max(swing_highs[-3:], key=lambda x: x.price).price

                if not FibonacciCalculator.is_in_golden_zone(
                    current_price, recent_high, recent_low
                ):
                    if self.log_signals:
                        self.log.debug("Price not in Fibonacci golden zone")
                    return False

        # All conditions met!
        self.active_order_block = bullish_ob
        self.total_signals += 1
        return True

    def _check_short_entry_conditions(self, bar: Bar) -> bool:
        """
        Check if all conditions for short entry are met.

        Same logic as long but inverted.
        """
        # Get active bearish OBs
        bearish_obs = self.htf_ob_detector.get_active_order_blocks('bearish')
        if not bearish_obs:
            return False

        # Get the most recent and strongest bearish OB
        bearish_ob = max(bearish_obs, key=lambda x: x.strength)

        # Check if price is testing the OB
        current_price = bar.close.as_double()
        if not (bearish_ob.low <= current_price <= bearish_ob.high):
            return False

        # Check for bearish FVG
        bearish_fvgs = self.htf_fvg_detector.get_active_fvgs('bearish')
        if not bearish_fvgs:
            return False

        # Check for recent bearish liquidity sweep
        if not self.htf_liquidity_sweep.has_recent_sweep('bearish_sweep', bars_ago=5):
            return False

        # Check for bearish CHoCH on LTF
        if not self.ltf_choch_detector.has_recent_choch('bearish_choch',
                                                         bars_ago=self.max_bars_since_choch):
            return False

        # Fibonacci filter
        if self.use_fibonacci_filter:
            swing_lows = self.htf_ob_detector.swing_lows
            swing_highs = self.htf_ob_detector.swing_highs

            if swing_lows and swing_highs:
                recent_low = min(swing_lows[-3:], key=lambda x: x.price).price
                recent_high = max(swing_highs[-3:], key=lambda x: x.price).price

                if not FibonacciCalculator.is_in_golden_zone(
                    current_price, recent_high, recent_low
                ):
                    if self.log_signals:
                        self.log.debug("Price not in Fibonacci golden zone")
                    return False

        # All conditions met!
        self.active_order_block = bearish_ob
        self.total_signals += 1
        return True

    def _enter_long(self, bar: Bar) -> None:
        """Enter a long position with proper risk management."""
        if not self.active_order_block:
            return

        entry_price = bar.close.as_double()

        # Calculate stop loss: OB bottom - 1%
        stop_loss = self.active_order_block.low * (1 - self.stop_loss_percent / 100)

        # Calculate risk per trade
        risk_distance = entry_price - stop_loss

        # Calculate take profit levels
        tp1 = entry_price + (risk_distance * self.tp1_risk_reward)
        tp2 = entry_price + (risk_distance * self.tp2_risk_reward)

        # Store trade parameters
        self.entry_price = entry_price
        self.stop_loss_price = stop_loss
        self.tp1_price = tp1
        self.tp2_price = tp2
        self.tp1_hit = False
        self.trailing_stop_active = False

        # Log entry
        self.log.info(
            f"ENTER LONG at {entry_price:.5f}, "
            f"SL: {stop_loss:.5f}, "
            f"TP1: {tp1:.5f}, "
            f"TP2: {tp2:.5f}, "
            f"Risk: {risk_distance:.5f}"
        )

        # Execute market buy order
        self.buy(quantity=self.base_trade_size)

        self.total_entries += 1

        # Note: In a real implementation, you would also submit:
        # - Stop loss order
        # - Take profit orders
        # This requires using submit_order() with StopMarketOrder and LimitOrder

    def _enter_short(self, bar: Bar) -> None:
        """Enter a short position with proper risk management."""
        if not self.active_order_block:
            return

        entry_price = bar.close.as_double()

        # Calculate stop loss: OB top + 1%
        stop_loss = self.active_order_block.high * (1 + self.stop_loss_percent / 100)

        # Calculate risk per trade
        risk_distance = stop_loss - entry_price

        # Calculate take profit levels
        tp1 = entry_price - (risk_distance * self.tp1_risk_reward)
        tp2 = entry_price - (risk_distance * self.tp2_risk_reward)

        # Store trade parameters
        self.entry_price = entry_price
        self.stop_loss_price = stop_loss
        self.tp1_price = tp1
        self.tp2_price = tp2
        self.tp1_hit = False
        self.trailing_stop_active = False

        # Log entry
        self.log.info(
            f"ENTER SHORT at {entry_price:.5f}, "
            f"SL: {stop_loss:.5f}, "
            f"TP1: {tp1:.5f}, "
            f"TP2: {tp2:.5f}, "
            f"Risk: {risk_distance:.5f}"
        )

        # Execute market sell order
        self.sell(quantity=self.base_trade_size)

        self.total_entries += 1

    def _update_trailing_stop(self, bar: Bar) -> None:
        """Update trailing stop logic."""
        if not self.entry_price or not self.trailing_stop_active:
            return

        position = self.cache.position(self.instrument_id)
        if not position or position.is_flat:
            return

        current_price = bar.close.as_double()

        # Update trailing stop based on position direction
        if position.is_long:
            # For long: move SL up as price increases
            new_sl = current_price - (self.trailing_stop_distance_pips * 0.0001)
            if new_sl > self.stop_loss_price:
                self.stop_loss_price = new_sl
                self.log.info(f"Trailing stop updated (LONG): {new_sl:.5f}")

        elif position.is_short:
            # For short: move SL down as price decreases
            new_sl = current_price + (self.trailing_stop_distance_pips * 0.0001)
            if new_sl < self.stop_loss_price:
                self.stop_loss_price = new_sl
                self.log.info(f"Trailing stop updated (SHORT): {new_sl:.5f}")

    def _update_daily_pnl(self, bar: Bar) -> None:
        """Update daily PnL tracking."""
        # Get current date from bar timestamp
        bar_date = datetime.fromtimestamp(bar.ts_init / 1_000_000_000).date()

        # Reset daily PnL if new day
        if self.current_date is None or bar_date != self.current_date:
            self.current_date = bar_date
            self.daily_pnl = Decimal("0")
            self.log.info(f"New trading day: {bar_date}, daily PnL reset")

        # Calculate unrealized PnL
        position = self.cache.position(self.instrument_id)
        if position and not position.is_flat:
            # This is simplified - actual implementation would use portfolio
            pass

    def _is_daily_loss_limit_reached(self) -> bool:
        """Check if daily loss limit has been reached."""
        if self.daily_pnl >= 0:
            return False

        # Get account balance from portfolio
        portfolio = self.cache.portfolio()
        if portfolio is None:
            return False

        account = portfolio.account(self.instrument_id.venue)
        if account is None:
            return False

        # Calculate max daily loss
        balance = account.balance_total()
        max_loss = balance * Decimal(str(self.daily_max_loss_percent / 100))

        # Check if loss limit exceeded
        if abs(self.daily_pnl) >= max_loss:
            return True

        return False

    def on_stop(self) -> None:
        """Called when strategy stops."""
        self.log.info(f"Stopping {self.__class__.__name__}")

        # Close any open positions if configured
        position = self.cache.position(self.instrument_id)
        if position and not position.is_flat:
            self.log.info(f"Closing position: {position}")
            self.close_position(position.id)

        # Log final statistics
        self.log.info(f"Total signals detected: {self.total_signals}")
        self.log.info(f"Total entries executed: {self.total_entries}")
        self.log.info(f"Daily PnL: {self.daily_pnl}")

    def on_order_filled(self, event) -> None:
        """Called when an order is filled."""
        self.log.info(f"Order filled: {event}")

        # Check if TP1 was hit
        position = self.cache.position(self.instrument_id)
        if position and not position.is_flat:
            current_price = position.last_px

            # Check TP1
            if not self.tp1_hit and self.tp1_price:
                if (position.is_long and current_price >= self.tp1_price) or \
                   (position.is_short and current_price <= self.tp1_price):
                    self._handle_tp1_hit(position)

            # Activate trailing stop at configured RR
            if not self.trailing_stop_active and self.entry_price:
                risk = abs(self.entry_price - self.stop_loss_price)
                profit = abs(current_price - self.entry_price)
                current_rr = profit / risk if risk > 0 else 0

                if current_rr >= self.trailing_stop_activation_rr:
                    self.trailing_stop_active = True
                    self.log.info("Trailing stop activated!")

    def _handle_tp1_hit(self, position) -> None:
        """Handle TP1 being hit - close partial position."""
        self.tp1_hit = True
        self.log.info(f"TP1 HIT! Closing {self.tp1_close_percent}% of position")

        # Close partial position
        partial_quantity = position.quantity * Decimal(str(self.tp1_close_percent / 100))

        if position.is_long:
            self.sell(quantity=partial_quantity)
        else:
            self.buy(quantity=partial_quantity)

        # Activate trailing stop for remaining position
        if self.use_trailing_stop:
            self.trailing_stop_active = True
            self.log.info("Trailing stop activated after TP1")
