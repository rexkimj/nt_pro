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
- OrderBlockStrategy: Main strategy implementation

Author: Nautilus Trader
License: MIT
"""

from .indicators import (
    OrderBlockDetector,
    FVGDetector,
    LiquiditySweepDetector,
    CHoCHDetector,
    FibonacciCalculator,
    OrderBlock,
    FairValueGap,
    SwingPoint,
)

from .strategy import (
    OrderBlockStrategy,
    OrderBlockStrategyConfig,
)

__all__ = [
    # Indicators
    "OrderBlockDetector",
    "FVGDetector",
    "LiquiditySweepDetector",
    "CHoCHDetector",
    "FibonacciCalculator",
    # Data classes
    "OrderBlock",
    "FairValueGap",
    "SwingPoint",
    # Strategy
    "OrderBlockStrategy",
    "OrderBlockStrategyConfig",
]

__version__ = "1.0.0"
