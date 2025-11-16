"""
Order Block Strategy - Backtest Example
========================================

This example demonstrates how to backtest the Order Block strategy
using Nautilus Trader's backtesting engine.

Usage:
    python backtest_example.py
"""

from decimal import Decimal
from pathlib import Path

from nautilus_trader.backtest.node import BacktestNode, BacktestVenueConfig, BacktestDataConfig, BacktestRunConfig, BacktestEngineConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType, BookType
from nautilus_trader.model.identifiers import InstrumentId, Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from strategies.order_block import OrderBlockStrategy, OrderBlockStrategyConfig


def run_backtest():
    """
    Run a backtest of the Order Block strategy.

    This example uses:
    - EURUSD forex pair
    - H4 bars for Order Block detection
    - 15m bars for entry confirmation
    - 2 years of historical data
    """

    # =========================================================================
    # 1. CONFIGURATION
    # =========================================================================

    # Define instrument
    instrument_id = InstrumentId.from_str("EUR/USD.SIM")

    # Define bar types
    htf_bar_type = BarType.from_str("EUR/USD.SIM-4-HOUR-MID-EXTERNAL")
    ltf_bar_type = BarType.from_str("EUR/USD.SIM-15-MINUTE-MID-EXTERNAL")

    # Strategy configuration
    strategy_config = OrderBlockStrategyConfig(
        instrument_id=instrument_id,
        htf_bar_type=htf_bar_type,
        ltf_bar_type=ltf_bar_type,
        base_trade_size=Decimal("100000"),  # 1 standard lot

        # Order Block detection
        ob_swing_lookback=5,
        ob_min_strength_pips=20.0,
        ob_max_blocks=10,

        # FVG detection
        fvg_max_gaps=20,

        # Liquidity Sweep
        ls_lookback=20,
        ls_reversal_pips=10.0,

        # CHoCH detection
        choch_swing_lookback=5,

        # Entry filters
        use_fibonacci_filter=True,
        max_bars_since_choch=10,

        # Risk management
        stop_loss_percent=1.0,
        tp1_risk_reward=2.0,
        tp2_risk_reward=4.0,
        tp1_close_percent=50.0,
        use_trailing_stop=True,
        trailing_stop_activation_rr=2.0,
        trailing_stop_distance_pips=20.0,

        # Daily risk
        daily_max_loss_percent=2.0,
        max_positions=1,

        # Logging
        log_signals=True,
        close_positions_on_stop=True,
    )

    # =========================================================================
    # 2. BACKTEST VENUE CONFIGURATION
    # =========================================================================

    venue_config = BacktestVenueConfig(
        name="SIM",
        oms_type=OmsType.HEDGING,
        account_type=AccountType.MARGIN,
        base_currency=USD,
        starting_balances=[Money(100_000, USD)],  # $100,000 starting capital
    )

    # =========================================================================
    # 3. DATA CONFIGURATION
    # =========================================================================

    # Note: In a real backtest, you would load historical data
    # This example assumes you have data in Parquet format
    # You can obtain data from various sources and convert to Nautilus format

    data_config = BacktestDataConfig(
        catalog_path=str(Path.cwd() / "catalog"),
        data_cls=BarType,
        instrument_id=instrument_id,
        bar_spec=htf_bar_type.spec,
        start_time="2022-01-01",
        end_time="2023-12-31",
    )

    # =========================================================================
    # 4. ENGINE CONFIGURATION
    # =========================================================================

    engine_config = BacktestEngineConfig(
        strategies=[strategy_config],
    )

    # =========================================================================
    # 5. RUN BACKTEST
    # =========================================================================

    print("=" * 80)
    print("Order Block Strategy - Backtest")
    print("=" * 80)
    print(f"Instrument: {instrument_id}")
    print(f"HTF Timeframe: {htf_bar_type}")
    print(f"LTF Timeframe: {ltf_bar_type}")
    print(f"Starting Capital: $100,000")
    print(f"Risk per Trade: {strategy_config.stop_loss_percent}%")
    print(f"TP1: 1:{strategy_config.tp1_risk_reward}")
    print(f"TP2: 1:{strategy_config.tp2_risk_reward}")
    print(f"Daily Max Loss: {strategy_config.daily_max_loss_percent}%")
    print("=" * 80)
    print()

    # Create backtest node
    node = BacktestNode(configs=[venue_config])

    # Note: You need to add your data to the node before running
    # Example:
    # catalog = ParquetDataCatalog("./catalog")
    # node.add_data(catalog.bars([htf_bar_type, ltf_bar_type]))

    # Run backtest
    # results = node.run()

    # =========================================================================
    # 6. ANALYZE RESULTS
    # =========================================================================

    # After running, you can analyze results
    # print("\n" + "=" * 80)
    # print("BACKTEST RESULTS")
    # print("=" * 80)
    # print(results.summary())

    print("\nBacktest configuration created successfully!")
    print("\nNext steps:")
    print("1. Prepare historical data in Nautilus Trader format")
    print("2. Load data into the catalog")
    print("3. Uncomment the node.run() line to execute backtest")
    print("4. Analyze results and optimize parameters")

    return strategy_config


def optimize_parameters():
    """
    Example of parameter optimization.

    Tests different parameter combinations to find optimal settings.
    """

    print("\n" + "=" * 80)
    print("PARAMETER OPTIMIZATION")
    print("=" * 80)

    # Define parameter ranges to test
    ob_lookbacks = [3, 5, 7]
    stop_loss_percentages = [0.5, 1.0, 1.5]
    tp1_ratios = [1.5, 2.0, 2.5]

    best_sharpe = -999
    best_params = None

    print("\nTesting parameter combinations...")
    print(f"Total combinations: {len(ob_lookbacks) * len(stop_loss_percentages) * len(tp1_ratios)}")
    print()

    for ob_lookback in ob_lookbacks:
        for sl_pct in stop_loss_percentages:
            for tp1_ratio in tp1_ratios:

                config = OrderBlockStrategyConfig(
                    instrument_id=InstrumentId.from_str("EUR/USD.SIM"),
                    htf_bar_type=BarType.from_str("EUR/USD.SIM-4-HOUR-MID-EXTERNAL"),
                    ltf_bar_type=BarType.from_str("EUR/USD.SIM-15-MINUTE-MID-EXTERNAL"),
                    base_trade_size=Decimal("100000"),
                    ob_swing_lookback=ob_lookback,
                    stop_loss_percent=sl_pct,
                    tp1_risk_reward=tp1_ratio,
                    tp2_risk_reward=tp1_ratio * 2,
                    log_signals=False,  # Reduce logging during optimization
                )

                # Run backtest with these parameters
                # results = run_backtest_with_config(config)
                # sharpe = results.sharpe_ratio

                # Placeholder for demonstration
                sharpe = 0.5  # Replace with actual Sharpe ratio from backtest

                print(f"OB Lookback: {ob_lookback}, SL: {sl_pct}%, TP1: 1:{tp1_ratio} -> Sharpe: {sharpe:.2f}")

                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = {
                        'ob_lookback': ob_lookback,
                        'stop_loss_pct': sl_pct,
                        'tp1_ratio': tp1_ratio,
                    }

    print("\n" + "=" * 80)
    print("OPTIMIZATION RESULTS")
    print("=" * 80)
    print(f"Best Sharpe Ratio: {best_sharpe:.2f}")
    print(f"Best Parameters: {best_params}")

    return best_params


def live_trading_setup():
    """
    Example configuration for live trading.

    WARNING: Always test thoroughly in simulation before live trading!
    """

    print("\n" + "=" * 80)
    print("LIVE TRADING SETUP")
    print("=" * 80)

    print("""
To use this strategy for live trading:

1. PAPER TRADING FIRST (Highly Recommended)
   - Test with simulated account for at least 1 month
   - Verify all signals and risk management work correctly
   - Monitor for any issues or bugs

2. CONFIGURE YOUR BROKER
   - Install appropriate Nautilus Trader adapter (e.g., CCXT, Interactive Brokers)
   - Set up API credentials securely
   - Configure venue in live trading config

3. RISK MANAGEMENT
   - Start with minimum position size
   - Never risk more than 1-2% per trade
   - Set strict daily/weekly loss limits
   - Monitor live positions actively

4. MONITORING
   - Set up logging and alerts
   - Monitor strategy performance daily
   - Keep track of all signals and entries
   - Review weekly/monthly performance

5. MAINTENANCE
   - Regularly update strategy based on market conditions
   - Reoptimize parameters quarterly
   - Keep detailed trading journal
   - Adjust risk as account grows

Example live config:
    """)

    example_config = """
from nautilus_trader.live.node import TradingNode

# Live strategy configuration
live_config = OrderBlockStrategyConfig(
    instrument_id=InstrumentId.from_str("EUR/USD.OANDA"),
    htf_bar_type=BarType.from_str("EUR/USD.OANDA-4-HOUR-MID-EXTERNAL"),
    ltf_bar_type=BarType.from_str("EUR/USD.OANDA-15-MINUTE-MID-EXTERNAL"),
    base_trade_size=Decimal("10000"),  # Start small!

    # Use optimized parameters from backtesting
    ob_swing_lookback=5,
    stop_loss_percent=1.0,
    tp1_risk_reward=2.0,
    tp2_risk_reward=4.0,

    # Conservative risk management for live
    daily_max_loss_percent=1.0,  # More conservative than backtest
    max_positions=1,

    log_signals=True,
)

# Create live trading node
# node = TradingNode(configs=[live_config])
# node.start()
    """

    print(example_config)

    print("\nRemember: Past performance does not guarantee future results!")
    print("Always practice proper risk management and never risk more than you can afford to lose.")


if __name__ == "__main__":
    """
    Main entry point for running backtests and optimization.
    """

    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]

        if mode == "backtest":
            run_backtest()
        elif mode == "optimize":
            optimize_parameters()
        elif mode == "live":
            live_trading_setup()
        else:
            print(f"Unknown mode: {mode}")
            print("Available modes: backtest, optimize, live")
    else:
        # Default: show backtest configuration
        print("Order Block Strategy - Backtest Example\n")
        print("Available modes:")
        print("  python backtest_example.py backtest  - Run backtest")
        print("  python backtest_example.py optimize  - Optimize parameters")
        print("  python backtest_example.py live      - Show live trading setup")
        print()

        # Show default configuration
        run_backtest()
