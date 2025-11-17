"""
Order Block Trading Strategy - Technical Indicators
Implements Order Block, FVG, Liquidity Sweep, and CHoCH detection.
"""

from decimal import Decimal
from typing import Optional, List, Tuple
from collections import deque
from dataclasses import dataclass
from nautilus_trader.model.data import Bar
import numpy as np


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


@dataclass
class TrendLine:
    """Represents a detected trend line."""
    slope: float  # Line slope
    intercept: float  # Y-intercept
    start_time: int  # First point timestamp
    end_time: int  # Last point timestamp
    start_price: float  # First point price
    end_price: float  # Last point price
    direction: str  # 'up' or 'down'
    strength: float  # Number of touches / validation score
    touch_count: int  # Number of swing points touching this line
    type: str  # 'support' or 'resistance'


@dataclass
class Channel:
    """Represents a detected price channel."""
    upper_line: TrendLine  # Upper trend line (resistance)
    lower_line: TrendLine  # Lower trend line (support)
    width: float  # Average channel width
    direction: str  # 'ascending', 'descending', or 'horizontal'
    strength: float  # Channel validation score
    start_time: int  # Channel start timestamp
    end_time: int  # Channel end timestamp


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


class TrendLineDetector:
    """
    Detects and tracks trend lines using swing points.

    Identifies support and resistance trend lines by connecting
    swing lows and swing highs respectively.
    """

    def __init__(
        self,
        min_touches: int = 2,
        max_lines: int = 10,
        touch_tolerance_pips: float = 5.0,
        min_bars_between_touches: int = 3,
    ):
        """
        Initialize TrendLineDetector.

        Args:
            min_touches: Minimum swing points to validate a trend line
            max_lines: Maximum number of trend lines to track
            touch_tolerance_pips: Price tolerance for considering a point as touching the line
            min_bars_between_touches: Minimum bars between touch points to avoid clustering
        """
        self.min_touches = min_touches
        self.max_lines = max_lines
        self.touch_tolerance_pips = touch_tolerance_pips
        self.min_bars_between_touches = min_bars_between_touches

        self.bars: deque = deque(maxlen=200)
        self.swing_highs: List[SwingPoint] = []
        self.swing_lows: List[SwingPoint] = []
        self.trend_lines: List[TrendLine] = []

    def update(self, bar: Bar, swing_point: Optional[SwingPoint] = None) -> List[TrendLine]:
        """
        Update with new bar and optionally a swing point.
        Returns list of newly detected or updated trend lines.
        """
        self.bars.append(bar)

        # Add swing point to appropriate list
        if swing_point:
            if swing_point.type == 'high':
                self.swing_highs.append(swing_point)
                # Keep recent swing highs
                if len(self.swing_highs) > 50:
                    self.swing_highs.pop(0)
            else:
                self.swing_lows.append(swing_point)
                # Keep recent swing lows
                if len(self.swing_lows) > 50:
                    self.swing_lows.pop(0)

        # Detect trend lines
        new_lines = []

        # Detect support lines (from swing lows)
        if len(self.swing_lows) >= self.min_touches:
            support_lines = self._detect_trend_lines(self.swing_lows, 'support')
            new_lines.extend(support_lines)

        # Detect resistance lines (from swing highs)
        if len(self.swing_highs) >= self.min_touches:
            resistance_lines = self._detect_trend_lines(self.swing_highs, 'resistance')
            new_lines.extend(resistance_lines)

        # Update trend lines list
        for line in new_lines:
            self._add_or_update_trend_line(line)

        # Extend existing trend lines with current bar
        self._extend_trend_lines(bar)

        return new_lines

    def _detect_trend_lines(self, swing_points: List[SwingPoint], line_type: str) -> List[TrendLine]:
        """
        Detect trend lines from swing points using combinatorial approach.
        """
        if len(swing_points) < self.min_touches:
            return []

        detected_lines = []
        n = len(swing_points)

        # Try all combinations of recent swing points (last 20 to keep it efficient)
        recent_points = swing_points[-20:] if len(swing_points) > 20 else swing_points

        # Try connecting each pair of points and see how many others align
        for i in range(len(recent_points) - 1):
            for j in range(i + 1, len(recent_points)):
                p1 = recent_points[i]
                p2 = recent_points[j]

                # Skip if points are too close together
                if abs(p2.bar_index - p1.bar_index) < self.min_bars_between_touches:
                    continue

                # Calculate line parameters
                slope, intercept = self._calculate_line(p1, p2)

                # Count how many other points touch this line
                touching_points = [p1, p2]
                for k, point in enumerate(recent_points):
                    if k == i or k == j:
                        continue

                    if self._point_touches_line(point, slope, intercept):
                        touching_points.append(point)

                # Validate trend line
                if len(touching_points) >= self.min_touches:
                    # Determine direction
                    direction = 'up' if slope > 0 else 'down'

                    # Calculate strength based on touches and line quality
                    strength = self._calculate_line_strength(touching_points, slope, intercept)

                    trend_line = TrendLine(
                        slope=slope,
                        intercept=intercept,
                        start_time=touching_points[0].time,
                        end_time=touching_points[-1].time,
                        start_price=touching_points[0].price,
                        end_price=touching_points[-1].price,
                        direction=direction,
                        strength=strength,
                        touch_count=len(touching_points),
                        type=line_type,
                    )

                    detected_lines.append(trend_line)

        # Sort by strength and return top lines
        detected_lines.sort(key=lambda x: x.strength, reverse=True)
        return detected_lines[:5]  # Return top 5 strongest lines

    def _calculate_line(self, p1: SwingPoint, p2: SwingPoint) -> Tuple[float, float]:
        """
        Calculate line slope and intercept from two points.
        Using bar indices as x-coordinates.
        """
        x1, y1 = float(p1.bar_index), p1.price
        x2, y2 = float(p2.bar_index), p2.price

        if x2 - x1 == 0:
            slope = 0
        else:
            slope = (y2 - y1) / (x2 - x1)

        intercept = y1 - slope * x1

        return slope, intercept

    def _point_touches_line(self, point: SwingPoint, slope: float, intercept: float) -> bool:
        """
        Check if a point touches the line within tolerance.
        """
        expected_price = slope * point.bar_index + intercept
        tolerance = self.touch_tolerance_pips * 0.0001  # Convert pips to price

        return abs(point.price - expected_price) <= tolerance

    def _calculate_line_strength(self, touching_points: List[SwingPoint], slope: float, intercept: float) -> float:
        """
        Calculate strength score for a trend line.
        Higher score = stronger, more reliable line.
        """
        # Base strength from number of touches
        touch_strength = len(touching_points)

        # Calculate average distance from line (lower is better)
        distances = []
        for point in touching_points:
            expected_price = slope * point.bar_index + intercept
            distance = abs(point.price - expected_price)
            distances.append(distance)

        avg_distance = np.mean(distances) if distances else 0

        # Distance penalty (normalize by pip size)
        distance_penalty = avg_distance / (0.0001 * self.touch_tolerance_pips)

        # Final strength (touches minus distance penalty)
        strength = touch_strength - (distance_penalty * 0.5)

        return max(strength, 0)

    def _add_or_update_trend_line(self, new_line: TrendLine):
        """
        Add new trend line or update existing similar one.
        """
        # Check if similar line already exists
        for i, existing_line in enumerate(self.trend_lines):
            if self._lines_are_similar(existing_line, new_line):
                # Update if new line is stronger
                if new_line.strength > existing_line.strength:
                    self.trend_lines[i] = new_line
                return

        # Add new line
        self.trend_lines.append(new_line)

        # Keep only strongest lines
        self.trend_lines.sort(key=lambda x: x.strength, reverse=True)
        if len(self.trend_lines) > self.max_lines:
            self.trend_lines = self.trend_lines[:self.max_lines]

    def _lines_are_similar(self, line1: TrendLine, line2: TrendLine) -> bool:
        """
        Check if two trend lines are similar (same type and close slope/intercept).
        """
        if line1.type != line2.type:
            return False

        # Check slope similarity (within 20%)
        slope_diff = abs(line1.slope - line2.slope)
        avg_slope = (abs(line1.slope) + abs(line2.slope)) / 2
        if avg_slope > 0 and slope_diff / avg_slope > 0.2:
            return False

        # Check intercept similarity
        intercept_diff = abs(line1.intercept - line2.intercept)
        if intercept_diff > 0.001:  # 100 pips tolerance
            return False

        return True

    def _extend_trend_lines(self, bar: Bar):
        """
        Extend existing trend lines to current bar time.
        Remove lines that are no longer valid.
        """
        current_bar_index = len(self.bars) - 1

        for line in self.trend_lines:
            # Calculate expected price at current bar
            expected_price = line.slope * current_bar_index + line.intercept

            # Update end time and price if still valid
            line.end_time = bar.ts_init
            line.end_price = expected_price

    def get_active_trend_lines(self, line_type: Optional[str] = None) -> List[TrendLine]:
        """
        Get active trend lines, optionally filtered by type.

        Args:
            line_type: 'support', 'resistance', or None for all
        """
        lines = self.trend_lines
        if line_type:
            lines = [line for line in lines if line.type == line_type]
        return lines

    def get_price_at_time(self, trend_line: TrendLine, bar_index: int) -> float:
        """
        Calculate the price of a trend line at a given bar index.
        """
        return trend_line.slope * bar_index + trend_line.intercept

    def is_price_near_line(self, price: float, trend_line: TrendLine, bar_index: int, tolerance_pips: float = 10.0) -> bool:
        """
        Check if a price is near a trend line.
        """
        line_price = self.get_price_at_time(trend_line, bar_index)
        tolerance = tolerance_pips * 0.0001
        return abs(price - line_price) <= tolerance


class ChannelDetector:
    """
    Detects price channels by finding parallel support and resistance trend lines.

    A channel consists of two parallel lines where price oscillates between them.
    Channels can be ascending, descending, or horizontal.
    """

    def __init__(
        self,
        min_channel_touches: int = 4,
        max_channels: int = 5,
        parallel_tolerance: float = 0.15,  # 15% slope difference tolerance
        min_channel_width_pips: float = 20.0,
        max_channel_width_pips: float = 500.0,
    ):
        """
        Initialize ChannelDetector.

        Args:
            min_channel_touches: Minimum total touches (both lines) to validate a channel
            max_channels: Maximum number of channels to track
            parallel_tolerance: Tolerance for lines to be considered parallel (as ratio)
            min_channel_width_pips: Minimum channel width in pips
            max_channel_width_pips: Maximum channel width in pips
        """
        self.min_channel_touches = min_channel_touches
        self.max_channels = max_channels
        self.parallel_tolerance = parallel_tolerance
        self.min_channel_width_pips = min_channel_width_pips
        self.max_channel_width_pips = max_channel_width_pips

        self.channels: List[Channel] = []
        self.trend_line_detector: Optional[TrendLineDetector] = None

    def update(self, trend_line_detector: TrendLineDetector) -> List[Channel]:
        """
        Update channels based on current trend lines.

        Args:
            trend_line_detector: TrendLineDetector instance with detected trend lines

        Returns:
            List of newly detected channels
        """
        self.trend_line_detector = trend_line_detector

        # Get active trend lines
        support_lines = trend_line_detector.get_active_trend_lines('support')
        resistance_lines = trend_line_detector.get_active_trend_lines('resistance')

        # Detect channels by matching parallel support and resistance lines
        new_channels = []

        for support in support_lines:
            for resistance in resistance_lines:
                channel = self._try_create_channel(support, resistance)
                if channel:
                    new_channels.append(channel)

        # Update channels list
        for channel in new_channels:
            self._add_or_update_channel(channel)

        return new_channels

    def _try_create_channel(self, lower_line: TrendLine, upper_line: TrendLine) -> Optional[Channel]:
        """
        Try to create a channel from two trend lines.
        """
        # Check if lines are approximately parallel
        if not self._are_lines_parallel(lower_line, upper_line):
            return None

        # Calculate channel width (average distance between lines)
        width = self._calculate_channel_width(lower_line, upper_line)

        # Validate channel width
        min_width = self.min_channel_width_pips * 0.0001
        max_width = self.max_channel_width_pips * 0.0001
        if width < min_width or width > max_width:
            return None

        # Check minimum total touches
        total_touches = lower_line.touch_count + upper_line.touch_count
        if total_touches < self.min_channel_touches:
            return None

        # Determine channel direction
        avg_slope = (lower_line.slope + upper_line.slope) / 2
        if avg_slope > 0.00001:  # Positive slope threshold
            direction = 'ascending'
        elif avg_slope < -0.00001:  # Negative slope threshold
            direction = 'descending'
        else:
            direction = 'horizontal'

        # Calculate channel strength
        strength = self._calculate_channel_strength(lower_line, upper_line, width)

        # Determine channel time range
        start_time = max(lower_line.start_time, upper_line.start_time)
        end_time = min(lower_line.end_time, upper_line.end_time)

        channel = Channel(
            upper_line=upper_line,
            lower_line=lower_line,
            width=width,
            direction=direction,
            strength=strength,
            start_time=start_time,
            end_time=end_time,
        )

        return channel

    def _are_lines_parallel(self, line1: TrendLine, line2: TrendLine) -> bool:
        """
        Check if two lines are approximately parallel.
        """
        slope1 = line1.slope
        slope2 = line2.slope

        # Handle near-horizontal lines
        if abs(slope1) < 0.00001 and abs(slope2) < 0.00001:
            return True

        # Calculate relative difference
        if abs(slope1) > abs(slope2):
            larger = abs(slope1)
            smaller = abs(slope2)
        else:
            larger = abs(slope2)
            smaller = abs(slope1)

        if larger == 0:
            return smaller == 0

        relative_diff = abs(larger - smaller) / larger

        return relative_diff <= self.parallel_tolerance

    def _calculate_channel_width(self, lower_line: TrendLine, upper_line: TrendLine) -> float:
        """
        Calculate average width of the channel.
        """
        # Sample at multiple points along the channel
        # Use intercept difference for simplicity (works well for similar slopes)
        width = abs(upper_line.intercept - lower_line.intercept)

        return width

    def _calculate_channel_strength(self, lower_line: TrendLine, upper_line: TrendLine, width: float) -> float:
        """
        Calculate strength score for a channel.
        Based on line strengths, total touches, and consistency.
        """
        # Average line strength
        avg_line_strength = (lower_line.strength + upper_line.strength) / 2

        # Total touches bonus
        total_touches = lower_line.touch_count + upper_line.touch_count
        touch_bonus = total_touches * 0.5

        # Parallelism bonus (closer slopes = better)
        slope_diff = abs(lower_line.slope - upper_line.slope)
        avg_slope = (abs(lower_line.slope) + abs(upper_line.slope)) / 2
        if avg_slope > 0:
            parallelism_score = 1.0 - min(slope_diff / avg_slope, 1.0)
        else:
            parallelism_score = 1.0

        # Final strength
        strength = avg_line_strength + touch_bonus + parallelism_score

        return strength

    def _add_or_update_channel(self, new_channel: Channel):
        """
        Add new channel or update existing similar one.
        """
        # Check if similar channel already exists
        for i, existing_channel in enumerate(self.channels):
            if self._channels_are_similar(existing_channel, new_channel):
                # Update if new channel is stronger
                if new_channel.strength > existing_channel.strength:
                    self.channels[i] = new_channel
                return

        # Add new channel
        self.channels.append(new_channel)

        # Keep only strongest channels
        self.channels.sort(key=lambda x: x.strength, reverse=True)
        if len(self.channels) > self.max_channels:
            self.channels = self.channels[:self.max_channels]

    def _channels_are_similar(self, channel1: Channel, channel2: Channel) -> bool:
        """
        Check if two channels are similar.
        """
        # Check if direction matches
        if channel1.direction != channel2.direction:
            return False

        # Check if widths are similar (within 30%)
        width_diff = abs(channel1.width - channel2.width)
        avg_width = (channel1.width + channel2.width) / 2
        if avg_width > 0 and width_diff / avg_width > 0.3:
            return False

        # Check if slopes are similar
        slope1 = (channel1.upper_line.slope + channel1.lower_line.slope) / 2
        slope2 = (channel2.upper_line.slope + channel2.lower_line.slope) / 2

        if abs(slope1) > 0.00001 or abs(slope2) > 0.00001:
            avg_slope = (abs(slope1) + abs(slope2)) / 2
            if avg_slope > 0:
                slope_diff_ratio = abs(slope1 - slope2) / avg_slope
                if slope_diff_ratio > 0.3:
                    return False

        return True

    def get_active_channels(self, direction: Optional[str] = None) -> List[Channel]:
        """
        Get active channels, optionally filtered by direction.

        Args:
            direction: 'ascending', 'descending', 'horizontal', or None for all
        """
        channels = self.channels
        if direction:
            channels = [ch for ch in channels if ch.direction == direction]
        return channels

    def is_price_in_channel(self, price: float, channel: Channel, bar_index: int, tolerance_pips: float = 5.0) -> bool:
        """
        Check if a price is inside a channel.
        """
        if not self.trend_line_detector:
            return False

        upper_price = self.trend_line_detector.get_price_at_time(channel.upper_line, bar_index)
        lower_price = self.trend_line_detector.get_price_at_time(channel.lower_line, bar_index)

        tolerance = tolerance_pips * 0.0001

        return (lower_price - tolerance) <= price <= (upper_price + tolerance)

    def get_channel_position(self, price: float, channel: Channel, bar_index: int) -> float:
        """
        Get relative position of price within channel.

        Returns:
            0.0 = at lower line
            0.5 = middle of channel
            1.0 = at upper line
            <0 or >1 = outside channel
        """
        if not self.trend_line_detector:
            return 0.5

        upper_price = self.trend_line_detector.get_price_at_time(channel.upper_line, bar_index)
        lower_price = self.trend_line_detector.get_price_at_time(channel.lower_line, bar_index)

        if upper_price == lower_price:
            return 0.5

        position = (price - lower_price) / (upper_price - lower_price)
        return position

    def is_near_channel_boundary(
        self,
        price: float,
        channel: Channel,
        bar_index: int,
        boundary: str = 'either',
        tolerance_pips: float = 10.0
    ) -> bool:
        """
        Check if price is near a channel boundary.

        Args:
            price: Current price
            channel: Channel to check
            bar_index: Current bar index
            boundary: 'upper', 'lower', or 'either'
            tolerance_pips: Distance tolerance in pips
        """
        if not self.trend_line_detector:
            return False

        tolerance = tolerance_pips * 0.0001

        if boundary in ['upper', 'either']:
            upper_price = self.trend_line_detector.get_price_at_time(channel.upper_line, bar_index)
            if abs(price - upper_price) <= tolerance:
                return True

        if boundary in ['lower', 'either']:
            lower_price = self.trend_line_detector.get_price_at_time(channel.lower_line, bar_index)
            if abs(price - lower_price) <= tolerance:
                return True

        return False
