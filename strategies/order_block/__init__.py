"""
Order Block Trading Strategy Package
=====================================

A professional Smart Money Concepts trading strategy for Nautilus Trader.

Components:
- OrderBlockDetector: Identifies institutional order blocks
- FVGDetector: Detects Fair Value Gaps (imbalances)
- LiquiditySweepDetector: Identifies stop hunts
- CHoCHDetector: Detects Change of Character (trend reversals)
- FibonacciCalculator: Calculates optimal entry zones
- TrendLineDetector: Automatically detects support/resistance trend lines
- ChannelDetector: Identifies parallel price channels
- OrderBlockStrategy: Main strategy implementation
- TrendLineVisualizer: Visualizes trend lines and channels

Author: Nautilus Trader
License: MIT
"""

from .indicators import (
    OrderBlockDetector,
    FVGDetector,
    LiquiditySweepDetector,
    CHoCHDetector,
    FibonacciCalculator,
    TrendLineDetector,
    ChannelDetector,
    OrderBlock,
    FairValueGap,
    SwingPoint,
    TrendLine,
    Channel,
)

from .strategy import (
    OrderBlockStrategy,
    OrderBlockStrategyConfig,
)

from .visualization import (
    TrendLineVisualizer,
)

__all__ = [
    # Indicators
    "OrderBlockDetector",
    "FVGDetector",
    "LiquiditySweepDetector",
    "CHoCHDetector",
    "FibonacciCalculator",
    "TrendLineDetector",
    "ChannelDetector",
    # Data classes
    "OrderBlock",
    "FairValueGap",
    "SwingPoint",
    "TrendLine",
    "Channel",
    # Strategy
    "OrderBlockStrategy",
    "OrderBlockStrategyConfig",
    # Visualization
    "TrendLineVisualizer",
]

__version__ = "1.1.0"
