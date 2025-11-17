"""
Visualization Utilities for Trend Lines and Channels
=====================================================

Provides functions to visualize detected trend lines, channels,
and other technical indicators on price charts.
"""

from typing import List, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

from .indicators import TrendLine, Channel, TrendLineDetector, ChannelDetector
from nautilus_trader.model.data import Bar


class TrendLineVisualizer:
    """
    Visualizes trend lines and channels on price charts.
    """

    def __init__(self, figsize=(14, 8)):
        """
        Initialize visualizer.

        Args:
            figsize: Figure size (width, height) in inches
        """
        self.figsize = figsize

    def plot_trend_lines_and_channels(
        self,
        bars: List[Bar],
        trend_line_detector: TrendLineDetector,
        channel_detector: Optional[ChannelDetector] = None,
        title: str = "Price Chart with Trend Lines and Channels",
        show_support: bool = True,
        show_resistance: bool = True,
        show_channels: bool = True,
        save_path: Optional[str] = None,
    ):
        """
        Plot price chart with trend lines and channels.

        Args:
            bars: List of OHLC bars
            trend_line_detector: TrendLineDetector instance with detected lines
            channel_detector: Optional ChannelDetector instance
            title: Chart title
            show_support: Show support trend lines
            show_resistance: Show resistance trend lines
            show_channels: Show channels
            save_path: If provided, save chart to this path
        """
        if not bars:
            print("No bars to plot")
            return

        # Extract OHLC data
        times = [datetime.fromtimestamp(bar.ts_init / 1_000_000_000) for bar in bars]
        opens = [bar.open.as_double() for bar in bars]
        highs = [bar.high.as_double() for bar in bars]
        lows = [bar.low.as_double() for bar in bars]
        closes = [bar.close.as_double() for bar in bars]

        # Create figure
        fig, ax = plt.subplots(figsize=self.figsize)

        # Plot candlesticks (simplified)
        for i, (t, o, h, l, c) in enumerate(zip(times, opens, highs, lows, closes)):
            color = 'green' if c >= o else 'red'
            # Draw high-low line
            ax.plot([t, t], [l, h], color='black', linewidth=0.5)
            # Draw open-close body
            body_height = abs(c - o)
            body_bottom = min(o, c)
            ax.add_patch(plt.Rectangle(
                (mdates.date2num(t) - 0.0003, body_bottom),
                0.0006,
                body_height,
                facecolor=color,
                edgecolor='black',
                linewidth=0.5
            ))

        # Plot support trend lines
        if show_support:
            support_lines = trend_line_detector.get_active_trend_lines('support')
            for i, line in enumerate(support_lines):
                self._plot_trend_line(ax, line, times, color='blue', label=f'Support {i+1}')

        # Plot resistance trend lines
        if show_resistance:
            resistance_lines = trend_line_detector.get_active_trend_lines('resistance')
            for i, line in enumerate(resistance_lines):
                self._plot_trend_line(ax, line, times, color='red', label=f'Resistance {i+1}')

        # Plot channels
        if show_channels and channel_detector:
            channels = channel_detector.get_active_channels()
            for i, channel in enumerate(channels):
                self._plot_channel(ax, channel, times, trend_line_detector)

        # Format chart
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Price', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.xticks(rotation=45)

        # Add legend if there are trend lines
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc='best', fontsize=10)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {save_path}")
        else:
            plt.show()

        plt.close()

    def _plot_trend_line(
        self,
        ax,
        trend_line: TrendLine,
        times: List[datetime],
        color: str = 'blue',
        label: Optional[str] = None,
    ):
        """
        Plot a single trend line.
        """
        # Calculate line points
        x_points = []
        y_points = []

        for i in range(len(times)):
            price = trend_line.slope * i + trend_line.intercept
            x_points.append(times[i])
            y_points.append(price)

        # Plot line
        line_style = '--' if trend_line.direction == 'down' else '-'
        alpha = min(0.3 + (trend_line.strength / 10), 1.0)  # Stronger lines more opaque

        label_text = label
        if label:
            label_text = f"{label} (touches={trend_line.touch_count}, strength={trend_line.strength:.1f})"

        ax.plot(
            x_points,
            y_points,
            linestyle=line_style,
            color=color,
            linewidth=2,
            alpha=alpha,
            label=label_text
        )

    def _plot_channel(
        self,
        ax,
        channel: Channel,
        times: List[datetime],
        trend_line_detector: TrendLineDetector,
    ):
        """
        Plot a channel (two parallel lines).
        """
        # Determine color based on channel direction
        if channel.direction == 'ascending':
            color = 'green'
        elif channel.direction == 'descending':
            color = 'red'
        else:
            color = 'gray'

        # Calculate upper and lower line points
        upper_x = []
        upper_y = []
        lower_x = []
        lower_y = []

        for i in range(len(times)):
            upper_price = trend_line_detector.get_price_at_time(channel.upper_line, i)
            lower_price = trend_line_detector.get_price_at_time(channel.lower_line, i)

            upper_x.append(times[i])
            upper_y.append(upper_price)
            lower_x.append(times[i])
            lower_y.append(lower_price)

        # Plot channel lines
        alpha = min(0.3 + (channel.strength / 15), 0.8)

        ax.plot(upper_x, upper_y, color=color, linewidth=2, alpha=alpha, linestyle='-.')
        ax.plot(lower_x, lower_y, color=color, linewidth=2, alpha=alpha, linestyle='-.')

        # Fill channel area
        ax.fill_between(
            upper_x,
            upper_y,
            lower_y,
            color=color,
            alpha=0.1,
            label=f'{channel.direction.capitalize()} Channel (strength={channel.strength:.1f})'
        )

    def plot_swing_points(
        self,
        bars: List[Bar],
        swing_highs: List,
        swing_lows: List,
        title: str = "Price Chart with Swing Points",
        save_path: Optional[str] = None,
    ):
        """
        Plot price chart with swing points marked.

        Args:
            bars: List of OHLC bars
            swing_highs: List of SwingPoint objects (highs)
            swing_lows: List of SwingPoint objects (lows)
            title: Chart title
            save_path: If provided, save chart to this path
        """
        if not bars:
            print("No bars to plot")
            return

        # Extract data
        times = [datetime.fromtimestamp(bar.ts_init / 1_000_000_000) for bar in bars]
        closes = [bar.close.as_double() for bar in bars]

        # Create figure
        fig, ax = plt.subplots(figsize=self.figsize)

        # Plot close prices
        ax.plot(times, closes, color='black', linewidth=1, label='Close Price')

        # Plot swing highs
        if swing_highs:
            swing_high_times = [datetime.fromtimestamp(sh.time / 1_000_000_000) for sh in swing_highs]
            swing_high_prices = [sh.price for sh in swing_highs]
            ax.scatter(
                swing_high_times,
                swing_high_prices,
                color='red',
                marker='v',
                s=100,
                label='Swing Highs',
                zorder=5
            )

        # Plot swing lows
        if swing_lows:
            swing_low_times = [datetime.fromtimestamp(sl.time / 1_000_000_000) for sl in swing_lows]
            swing_low_prices = [sl.price for sl in swing_lows]
            ax.scatter(
                swing_low_times,
                swing_low_prices,
                color='green',
                marker='^',
                s=100,
                label='Swing Lows',
                zorder=5
            )

        # Format chart
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Price', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {save_path}")
        else:
            plt.show()

        plt.close()


def create_example_visualization():
    """
    Example function showing how to use the visualizer.
    """
    from nautilus_trader.test_kit.providers import TestDataProvider

    # This is just an example - you would normally get bars from your strategy
    print("To use visualization:")
    print("1. Import: from strategies.order_block.visualization import TrendLineVisualizer")
    print("2. Create visualizer: viz = TrendLineVisualizer()")
    print("3. Plot: viz.plot_trend_lines_and_channels(bars, trend_line_detector, channel_detector)")
    print("")
    print("Example:")
    print("  viz = TrendLineVisualizer(figsize=(16, 10))")
    print("  viz.plot_trend_lines_and_channels(")
    print("      bars=list(strategy.htf_trendline_detector.bars),")
    print("      trend_line_detector=strategy.htf_trendline_detector,")
    print("      channel_detector=strategy.htf_channel_detector,")
    print("      title='EUR/USD H4 Trend Lines and Channels',")
    print("      save_path='trend_analysis.png'")
    print("  )")


if __name__ == "__main__":
    create_example_visualization()
