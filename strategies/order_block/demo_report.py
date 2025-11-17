"""
Order Block Strategy - Demo Report Generator
============================================

Generates a demo backtest report with sample trade data
to demonstrate the reporting capabilities.
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal

from report_generator import (
    TradeRecord,
    ReportManager,
    PerformanceCalculator,
)


def generate_sample_trades(num_trades: int = 50, win_rate: float = 0.60) -> list:
    """
    Generate sample trade data for demonstration.

    Args:
        num_trades: Number of trades to generate
        win_rate: Desired win rate (0.0 to 1.0)
    """

    trades = []
    start_date = datetime.now() - timedelta(days=365)
    current_date = start_date

    # Strategy parameters
    avg_entry_price = 1.0850
    avg_position_size = 100000.0

    for i in range(num_trades):
        # Determine if this is a winning trade
        is_winner = random.random() < win_rate

        # Random direction
        direction = random.choice(['LONG', 'SHORT'])

        # Entry details
        entry_price = avg_entry_price + random.uniform(-0.01, 0.01)
        quantity = avg_position_size + random.uniform(-20000, 20000)

        # Generate PnL based on win/loss
        if is_winner:
            # Winners: TP1 (1:2) or TP2 (1:4)
            is_tp2 = random.random() < 0.4  # 40% reach TP2
            if is_tp2:
                risk_reward = 4.0
                setup_type = 'TP2'
                pnl_percent = random.uniform(3.5, 4.5)
            else:
                risk_reward = 2.0
                setup_type = 'TP1'
                pnl_percent = random.uniform(1.8, 2.2)

            pip_move = pnl_percent / 100 * entry_price
            if direction == 'LONG':
                exit_price = entry_price + pip_move
            else:
                exit_price = entry_price - pip_move
        else:
            # Losers: Hit stop loss
            risk_reward = -1.0
            setup_type = 'SL'
            pnl_percent = random.uniform(-1.2, -0.8)

            pip_move = abs(pnl_percent) / 100 * entry_price
            if direction == 'LONG':
                exit_price = entry_price - pip_move
            else:
                exit_price = entry_price + pip_move

        # Calculate actual PnL
        if direction == 'LONG':
            pnl = (exit_price - entry_price) * quantity
        else:
            pnl = (entry_price - exit_price) * quantity

        # Trade duration (15min to 48 hours)
        duration = random.randint(15, 2880)

        # Dates
        entry_time = current_date.strftime("%Y-%m-%d %H:%M:%S")
        exit_time = (current_date + timedelta(minutes=duration)).strftime("%Y-%m-%d %H:%M:%S")

        # Move forward in time
        current_date += timedelta(hours=random.randint(4, 24))

        trade = TradeRecord(
            entry_time=entry_time,
            exit_time=exit_time,
            direction=direction,
            entry_price=round(entry_price, 5),
            exit_price=round(exit_price, 5),
            quantity=round(quantity, 2),
            pnl=round(pnl, 2),
            pnl_percent=round(pnl_percent, 2),
            setup_type=setup_type,
            risk_reward=round(risk_reward, 2),
            duration_minutes=duration,
        )

        trades.append(trade)

    return trades


def generate_demo_report(scenario: str = 'balanced'):
    """
    Generate demo report with different scenarios.

    Scenarios:
        - 'profitable': High win rate, good Sharpe
        - 'balanced': Moderate performance
        - 'struggling': Lower win rate, drawdowns
    """

    print(f"\n{'='*80}")
    print(f"Generating Demo Report: {scenario.upper()}")
    print(f"{'='*80}\n")

    # Configure scenario
    if scenario == 'profitable':
        num_trades = 80
        win_rate = 0.68
        starting_balance = 100000.0
        print("📈 Scenario: Profitable Strategy")
        print("   - 68% win rate")
        print("   - Strong risk management")
        print("   - Good Sharpe ratio")

    elif scenario == 'balanced':
        num_trades = 50
        win_rate = 0.60
        starting_balance = 100000.0
        print("⚖️  Scenario: Balanced Performance")
        print("   - 60% win rate")
        print("   - Moderate returns")
        print("   - Acceptable drawdowns")

    elif scenario == 'struggling':
        num_trades = 40
        win_rate = 0.45
        starting_balance = 100000.0
        print("📉 Scenario: Struggling Strategy")
        print("   - 45% win rate")
        print("   - Needs optimization")
        print("   - High drawdowns")

    else:
        print(f"Unknown scenario: {scenario}")
        return None

    # Generate sample trades
    print(f"\n⏳ Generating {num_trades} sample trades...")
    trades = generate_sample_trades(num_trades, win_rate)
    print(f"✅ Generated {len(trades)} trades")

    # Calculate metrics
    print("📊 Calculating performance metrics...")
    metrics = PerformanceCalculator.calculate_metrics(trades, starting_balance)

    # Strategy configuration
    config = {
        'Instrument': 'EUR/USD',
        'HTF Timeframe': '4-HOUR',
        'LTF Timeframe': '15-MINUTE',
        'Starting Balance': f'${starting_balance:,.2f}',
        'Position Size': '100,000 units',
        'OB Swing Lookback': '5',
        'Stop Loss': '1.0%',
        'TP1 (1:2)': '50% close',
        'TP2 (1:4)': 'Trailing stop',
        'Trailing Distance': '20 pips',
        'Daily Max Loss': '2.0%',
        'Fibonacci Filter': 'Enabled',
    }

    # Generate report
    print("📝 Generating HTML report...")
    report_manager = ReportManager(output_dir='reports')
    report_path = report_manager.generate_report(
        trades=trades,
        config=config,
        starting_balance=starting_balance,
        report_name=f'demo_report_{scenario}.html'
    )

    # Print summary
    report_manager.print_summary(metrics)

    print(f"✅ Report generated successfully!")
    print(f"📁 Location: {report_path}")
    print(f"\n💡 Open the HTML file in your browser to view the full report.\n")

    return report_path


def generate_all_scenarios():
    """Generate reports for all scenarios."""
    scenarios = ['profitable', 'balanced', 'struggling']

    print("\n" + "🎯 "* 20)
    print("Generating Demo Reports for All Scenarios")
    print("🎯 " * 20 + "\n")

    reports = []

    for scenario in scenarios:
        report_path = generate_demo_report(scenario)
        if report_path:
            reports.append((scenario, report_path))
        print()

    print("\n" + "="*80)
    print("ALL REPORTS GENERATED")
    print("="*80)

    for scenario, path in reports:
        print(f"📊 {scenario.capitalize():15} → {path}")

    print("\n💡 Open any HTML file in your browser to view the detailed report.")
    print("="*80 + "\n")


def compare_strategies():
    """Generate comparison report between different parameter sets."""

    print("\n" + "="*80)
    print("STRATEGY COMPARISON DEMO")
    print("="*80 + "\n")

    print("Comparing three parameter configurations:\n")

    # Configuration 1: Conservative
    print("📘 Config 1: Conservative")
    print("   - Tight stops (0.5%)")
    print("   - Early TP (1.5:1)")
    print("   - High selectivity")
    trades_1 = generate_sample_trades(30, 0.70)

    # Configuration 2: Balanced (default)
    print("\n📗 Config 2: Balanced (Default)")
    print("   - Standard stops (1.0%)")
    print("   - Standard TP (2:1, 4:1)")
    print("   - Moderate selectivity")
    trades_2 = generate_sample_trades(50, 0.60)

    # Configuration 3: Aggressive
    print("\n📕 Config 3: Aggressive")
    print("   - Wider stops (1.5%)")
    print("   - Ambitious TP (3:1, 6:1)")
    print("   - Lower selectivity")
    trades_3 = generate_sample_trades(70, 0.50)

    print("\n📊 Calculating metrics for all configurations...\n")

    configs = [
        ('Conservative', trades_1, {'SL': '0.5%', 'TP1': '1.5:1', 'TP2': '3:1'}),
        ('Balanced', trades_2, {'SL': '1.0%', 'TP1': '2:1', 'TP2': '4:1'}),
        ('Aggressive', trades_3, {'SL': '1.5%', 'TP1': '3:1', 'TP2': '6:1'}),
    ]

    print("="*80)
    print(f"{'Configuration':<20} {'Trades':<10} {'Win Rate':<12} {'Profit Factor':<15} {'Total PnL':<15}")
    print("="*80)

    for name, trades, params in configs:
        metrics = PerformanceCalculator.calculate_metrics(trades, 100000.0)
        print(f"{name:<20} {metrics.total_trades:<10} {metrics.win_rate:<11.1f}% "
              f"{metrics.profit_factor:<15.2f} ${metrics.total_pnl:<14,.2f}")

    print("="*80)
    print("\n💡 The balanced configuration typically provides the best risk-adjusted returns.")
    print("="*80 + "\n")


if __name__ == "__main__":
    """Main entry point."""

    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]

        if mode == 'profitable':
            generate_demo_report('profitable')
        elif mode == 'balanced':
            generate_demo_report('balanced')
        elif mode == 'struggling':
            generate_demo_report('struggling')
        elif mode == 'all':
            generate_all_scenarios()
        elif mode == 'compare':
            compare_strategies()
        else:
            print(f"Unknown mode: {mode}")
            print("\nAvailable modes:")
            print("  python demo_report.py profitable   - Generate profitable scenario")
            print("  python demo_report.py balanced     - Generate balanced scenario")
            print("  python demo_report.py struggling   - Generate struggling scenario")
            print("  python demo_report.py all          - Generate all scenarios")
            print("  python demo_report.py compare      - Compare different configs")
    else:
        # Default: Generate balanced scenario
        print("Order Block Strategy - Demo Report Generator")
        print("\nGenerating balanced scenario demo report...")
        print("(Use 'python demo_report.py all' to generate all scenarios)\n")
        generate_demo_report('balanced')
