"""
Order Block Trading Strategy - Technical Indicators
Implements Order Block, FVG, Liquidity Sweep, and CHoCH detection.
"""

from decimal import Decimal
from typing import Optional, List
from collections import deque
from dataclasses import dataclass
from nautilus_trader.model.data import Bar


@dataclass
class OrderBlock:
    """Represents an identified Order Block zone."""
    high: float
    low: float
    time: int
    direction: str  # 'bullish' or 'bearish'
    strength: float  # Movement strength after the block
    tested: bool = False  # Has price returned to this OB?


@dataclass
class FairValueGap:
    """Represents a Fair Value Gap (imbalance)."""
    high: float
    low: float
    time: int
    direction: str  # 'bullish' or 'bearish'
    filled: bool = False


@dataclass
class SwingPoint:
    """Represents a swing high or low point."""
    price: float
    time: int
    type: str  # 'high' or 'low'
    bar_index: int


class OrderBlockDetector:
    """
    Detects Order Blocks on multiple timeframes.

    Order Block: The last opposing candle before a strong price move.
    Identified by finding swing points and tracking the setup candle.
    """

    def __init__(
        self,
        swing_lookback: int = 5,
        min_strength_pips: float = 20.0,
        max_blocks: int = 10,
    ):
        self.swing_lookback = swing_lookback
        self.min_strength_pips = min_strength_pips
        self.max_blocks = max_blocks

        self.bars: deque = deque(maxlen=100)
        self.swing_highs: List[SwingPoint] = []
        self.swing_lows: List[SwingPoint] = []
        self.order_blocks: List[OrderBlock] = []

    def update(self, bar: Bar) -> Optional[OrderBlock]:
        """Update with new bar and detect order blocks."""
        self.bars.append(bar)

        if len(self.bars) < self.swing_lookback * 2 + 1:
            return None

        # Detect swing points
        new_swing = self._detect_swing_point()
        if new_swing:
            ob = self._identify_order_block(new_swing)
            if ob:
                self.order_blocks.append(ob)
                # Keep only recent blocks
                if len(self.order_blocks) > self.max_blocks:
                    self.order_blocks.pop(0)
                return ob

        # Update tested status for existing OBs
        self._update_ob_status(bar)
        return None

    def _detect_swing_point(self) -> Optional[SwingPoint]:
        """Detect swing high/low using lookback period."""
        if len(self.bars) < self.swing_lookback * 2 + 1:
            return None

        bars_list = list(self.bars)
        center_idx = len(bars_list) - self.swing_lookback - 1
        center_bar = bars_list[center_idx]

        # Check for swing high
        is_swing_high = True
        for i in range(center_idx - self.swing_lookback, center_idx + self.swing_lookback + 1):
            if i != center_idx and bars_list[i].high.as_double() >= center_bar.high.as_double():
                is_swing_high = False
                break

        if is_swing_high:
            swing = SwingPoint(
                price=center_bar.high.as_double(),
                time=center_bar.ts_init,
                type='high',
                bar_index=center_idx
            )
            self.swing_highs.append(swing)
            return swing

        # Check for swing low
        is_swing_low = True
        for i in range(center_idx - self.swing_lookback, center_idx + self.swing_lookback + 1):
            if i != center_idx and bars_list[i].low.as_double() <= center_bar.low.as_double():
                is_swing_low = False
                break

        if is_swing_low:
            swing = SwingPoint(
                price=center_bar.low.as_double(),
                time=center_bar.ts_init,
                type='low',
                bar_index=center_idx
            )
            self.swing_lows.append(swing)
            return swing

        return None

    def _identify_order_block(self, swing: SwingPoint) -> Optional[OrderBlock]:
        """Identify the order block candle before the swing point."""
        bars_list = list(self.bars)
        swing_idx = swing.bar_index

        if swing_idx < 1:
            return None

        if swing.type == 'high':
            # Bearish OB: Find last bullish candle before bearish move
            for i in range(swing_idx - 1, max(0, swing_idx - 10), -1):
                bar = bars_list[i]
                if bar.close.as_double() > bar.open.as_double():  # Bullish candle
                    # Check strength of move after this candle
                    move_strength = swing.price - bar.high.as_double()
                    if move_strength >= self.min_strength_pips * 0.0001:  # Convert pips
                        return OrderBlock(
                            high=bar.high.as_double(),
                            low=bar.low.as_double(),
                            time=bar.ts_init,
                            direction='bearish',
                            strength=move_strength
                        )

        elif swing.type == 'low':
            # Bullish OB: Find last bearish candle before bullish move
            for i in range(swing_idx - 1, max(0, swing_idx - 10), -1):
                bar = bars_list[i]
                if bar.close.as_double() < bar.open.as_double():  # Bearish candle
                    # Check strength of move after this candle
                    move_strength = bar.low.as_double() - swing.price
                    if move_strength >= self.min_strength_pips * 0.0001:
                        return OrderBlock(
                            high=bar.high.as_double(),
                            low=bar.low.as_double(),
                            time=bar.ts_init,
                            direction='bullish',
                            strength=move_strength
                        )

        return None

    def _update_ob_status(self, bar: Bar):
        """Update whether OBs have been tested by price."""
        for ob in self.order_blocks:
            if not ob.tested:
                bar_high = bar.high.as_double()
                bar_low = bar.low.as_double()

                # Check if price returned to OB zone
                if bar_low <= ob.high and bar_high >= ob.low:
                    ob.tested = True

    def get_active_order_blocks(self, direction: Optional[str] = None) -> List[OrderBlock]:
        """Get untested order blocks, optionally filtered by direction."""
        blocks = [ob for ob in self.order_blocks if not ob.tested]
        if direction:
            blocks = [ob for ob in blocks if ob.direction == direction]
        return blocks


class FVGDetector:
    """
    Detects Fair Value Gaps (FVG) - price imbalances.

    FVG occurs when there's a gap between candle 1 and candle 3:
    - Bullish FVG: candle1.high < candle3.low
    - Bearish FVG: candle1.low > candle3.high
    """

    def __init__(self, max_gaps: int = 20):
        self.max_gaps = max_gaps
        self.bars: deque = deque(maxlen=3)
        self.fvgs: List[FairValueGap] = []

    def update(self, bar: Bar) -> Optional[FairValueGap]:
        """Update with new bar and detect FVG."""
        self.bars.append(bar)

        if len(self.bars) < 3:
            return None

        bars_list = list(self.bars)
        candle1 = bars_list[0]
        candle2 = bars_list[1]
        candle3 = bars_list[2]

        c1_high = candle1.high.as_double()
        c1_low = candle1.low.as_double()
        c3_high = candle3.high.as_double()
        c3_low = candle3.low.as_double()

        # Bullish FVG
        if c1_high < c3_low:
            fvg = FairValueGap(
                high=c3_low,
                low=c1_high,
                time=candle2.ts_init,
                direction='bullish'
            )
            self.fvgs.append(fvg)
            if len(self.fvgs) > self.max_gaps:
                self.fvgs.pop(0)
            return fvg

        # Bearish FVG
        if c1_low > c3_high:
            fvg = FairValueGap(
                high=c1_low,
                low=c3_high,
                time=candle2.ts_init,
                direction='bearish'
            )
            self.fvgs.append(fvg)
            if len(self.fvgs) > self.max_gaps:
                self.fvgs.pop(0)
            return fvg

        # Update filled status
        self._update_fvg_status(bar)
        return None

    def _update_fvg_status(self, bar: Bar):
        """Check if FVGs have been filled."""
        bar_high = bar.high.as_double()
        bar_low = bar.low.as_double()

        for fvg in self.fvgs:
            if not fvg.filled:
                # FVG is filled when price completely covers the gap
                if fvg.direction == 'bullish' and bar_low <= fvg.low:
                    fvg.filled = True
                elif fvg.direction == 'bearish' and bar_high >= fvg.high:
                    fvg.filled = True

    def get_active_fvgs(self, direction: Optional[str] = None) -> List[FairValueGap]:
        """Get unfilled FVGs, optionally filtered by direction."""
        gaps = [fvg for fvg in self.fvgs if not fvg.filled]
        if direction:
            gaps = [fvg for fvg in gaps if fvg.direction == direction]
        return gaps


class LiquiditySweepDetector:
    """
    Detects Liquidity Sweeps (Stop Hunts).

    Occurs when price briefly breaks above/below recent high/low
    and then reverses, collecting stops before the real move.
    """

    def __init__(self, lookback: int = 20, reversal_pips: float = 10.0):
        self.lookback = lookback
        self.reversal_pips = reversal_pips
        self.bars: deque = deque(maxlen=lookback + 10)
        self.last_sweep_time: Optional[int] = None
        self.last_sweep_direction: Optional[str] = None

    def update(self, bar: Bar) -> Optional[str]:
        """
        Update with new bar and detect liquidity sweep.
        Returns 'bullish_sweep' or 'bearish_sweep' if detected.
        """
        self.bars.append(bar)

        if len(self.bars) < self.lookback + 3:
            return None

        bars_list = list(self.bars)
        current_bar = bars_list[-1]
        recent_bars = bars_list[-self.lookback-1:-1]

        # Find recent high and low
        recent_high = max(b.high.as_double() for b in recent_bars)
        recent_low = min(b.low.as_double() for b in recent_bars)

        current_high = current_bar.high.as_double()
        current_low = current_bar.low.as_double()
        current_close = current_bar.close.as_double()

        # Bullish sweep: Break below recent low, then close back above
        if current_low < recent_low:
            reversal_amount = current_close - current_low
            if reversal_amount >= self.reversal_pips * 0.0001:
                self.last_sweep_time = current_bar.ts_init
                self.last_sweep_direction = 'bullish_sweep'
                return 'bullish_sweep'

        # Bearish sweep: Break above recent high, then close back below
        if current_high > recent_high:
            reversal_amount = current_high - current_close
            if reversal_amount >= self.reversal_pips * 0.0001:
                self.last_sweep_time = current_bar.ts_init
                self.last_sweep_direction = 'bearish_sweep'
                return 'bearish_sweep'

        return None

    def has_recent_sweep(self, direction: str, bars_ago: int = 5) -> bool:
        """Check if there was a recent sweep in the specified direction."""
        if not self.last_sweep_direction or not self.last_sweep_time:
            return False

        if self.last_sweep_direction != direction:
            return False

        # Check if sweep was recent enough
        if len(self.bars) > 0:
            current_time = list(self.bars)[-1].ts_init
            bars_since = len([b for b in self.bars if b.ts_init > self.last_sweep_time])
            return bars_since <= bars_ago

        return False


class CHoCHDetector:
    """
    Detects Change of Character (CHoCH) - trend reversal signals.

    CHoCH occurs when price breaks the most recent higher low (in uptrend)
    or lower high (in downtrend), indicating potential trend reversal.
    """

    def __init__(self, swing_lookback: int = 5):
        self.swing_lookback = swing_lookback
        self.bars: deque = deque(maxlen=50)
        self.swing_highs: List[SwingPoint] = []
        self.swing_lows: List[SwingPoint] = []
        self.current_trend: Optional[str] = None  # 'bullish' or 'bearish'
        self.last_choch_time: Optional[int] = None
        self.last_choch_direction: Optional[str] = None

    def update(self, bar: Bar) -> Optional[str]:
        """
        Update with new bar and detect CHoCH.
        Returns 'bullish_choch' or 'bearish_choch' if detected.
        """
        self.bars.append(bar)

        if len(self.bars) < self.swing_lookback * 2 + 1:
            return None

        # Detect swing points
        self._detect_swing_points()

        # Detect CHoCH
        choch = self._detect_choch(bar)
        if choch:
            self.last_choch_time = bar.ts_init
            self.last_choch_direction = choch

        return choch

    def _detect_swing_points(self):
        """Detect swing highs and lows."""
        bars_list = list(self.bars)
        if len(bars_list) < self.swing_lookback * 2 + 1:
            return

        center_idx = len(bars_list) - self.swing_lookback - 1
        center_bar = bars_list[center_idx]

        # Check for swing high
        is_swing_high = True
        for i in range(center_idx - self.swing_lookback, center_idx + self.swing_lookback + 1):
            if i != center_idx and bars_list[i].high.as_double() >= center_bar.high.as_double():
                is_swing_high = False
                break

        if is_swing_high:
            swing = SwingPoint(
                price=center_bar.high.as_double(),
                time=center_bar.ts_init,
                type='high',
                bar_index=center_idx
            )
            self.swing_highs.append(swing)
            if len(self.swing_highs) > 10:
                self.swing_highs.pop(0)

        # Check for swing low
        is_swing_low = True
        for i in range(center_idx - self.swing_lookback, center_idx + self.swing_lookback + 1):
            if i != center_idx and bars_list[i].low.as_double() <= center_bar.low.as_double():
                is_swing_low = False
                break

        if is_swing_low:
            swing = SwingPoint(
                price=center_bar.low.as_double(),
                time=center_bar.ts_init,
                type='low',
                bar_index=center_idx
            )
            self.swing_lows.append(swing)
            if len(self.swing_lows) > 10:
                self.swing_lows.pop(0)

    def _detect_choch(self, bar: Bar) -> Optional[str]:
        """Detect Change of Character."""
        if len(self.swing_highs) < 2 or len(self.swing_lows) < 2:
            return None

        current_price = bar.close.as_double()

        # Get recent swing points
        recent_swing_high = self.swing_highs[-1].price
        recent_swing_low = self.swing_lows[-1].price

        # Bullish CHoCH: Price breaks above recent lower high in downtrend
        if self.current_trend == 'bearish' or self.current_trend is None:
            if len(self.swing_highs) >= 2:
                prev_high = self.swing_highs[-2].price
                if prev_high > recent_swing_high:  # Lower high pattern
                    if current_price > prev_high:  # Break of structure
                        self.current_trend = 'bullish'
                        return 'bullish_choch'

        # Bearish CHoCH: Price breaks below recent higher low in uptrend
        if self.current_trend == 'bullish' or self.current_trend is None:
            if len(self.swing_lows) >= 2:
                prev_low = self.swing_lows[-2].price
                if prev_low < recent_swing_low:  # Higher low pattern
                    if current_price < prev_low:  # Break of structure
                        self.current_trend = 'bearish'
                        return 'bearish_choch'

        return None

    def has_recent_choch(self, direction: str, bars_ago: int = 10) -> bool:
        """Check if there was a recent CHoCH in the specified direction."""
        if not self.last_choch_direction or not self.last_choch_time:
            return False

        if self.last_choch_direction != direction:
            return False

        if len(self.bars) > 0:
            bars_since = len([b for b in self.bars if b.ts_init > self.last_choch_time])
            return bars_since <= bars_ago

        return False


class FibonacciCalculator:
    """
    Calculates Fibonacci retracement levels.
    Used for optimal entry points within order blocks.
    """

    @staticmethod
    def calculate_levels(swing_high: float, swing_low: float) -> dict:
        """Calculate Fibonacci retracement levels."""
        diff = swing_high - swing_low

        return {
            0.0: swing_low,
            0.236: swing_low + diff * 0.236,
            0.382: swing_low + diff * 0.382,
            0.5: swing_low + diff * 0.5,
            0.618: swing_low + diff * 0.618,
            0.786: swing_low + diff * 0.786,
            1.0: swing_high,
        }

    @staticmethod
    def is_in_golden_zone(price: float, swing_high: float, swing_low: float) -> bool:
        """
        Check if price is in the golden zone (0.5 - 0.618 Fibonacci).
        Optimal entry zone for order block strategies.
        """
        levels = FibonacciCalculator.calculate_levels(swing_high, swing_low)
        fib_50 = levels[0.5]
        fib_618 = levels[0.618]

        return min(fib_50, fib_618) <= price <= max(fib_50, fib_618)
