"""
Order Block Strategy - Report Generator
========================================

Generates comprehensive backtest reports with performance metrics,
trade analysis, and visualizations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal


@dataclass
class TradeRecord:
    """Record of a single trade."""
    entry_time: str
    exit_time: str
    direction: str  # 'LONG' or 'SHORT'
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    setup_type: str  # 'TP1', 'TP2', 'SL', 'MANUAL'
    risk_reward: float
    duration_minutes: int


@dataclass
class PerformanceMetrics:
    """Overall performance metrics."""
    # Basic stats
    total_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int

    # Win rate
    win_rate: float
    loss_rate: float

    # PnL
    total_pnl: float
    total_pnl_percent: float
    gross_profit: float
    gross_loss: float

    # Risk metrics
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_percent: float

    # Trade metrics
    avg_win: float
    avg_loss: float
    avg_win_percent: float
    avg_loss_percent: float
    largest_win: float
    largest_loss: float

    # Risk/Reward
    avg_risk_reward: float
    expectancy: float

    # Duration
    avg_trade_duration_minutes: int
    longest_trade_minutes: int
    shortest_trade_minutes: int

    # Streak
    max_consecutive_wins: int
    max_consecutive_losses: int

    # Monthly
    best_month: float
    worst_month: float
    avg_monthly_return: float


class PerformanceCalculator:
    """Calculates performance metrics from trade records."""

    @staticmethod
    def calculate_metrics(trades: List[TradeRecord],
                         starting_balance: float = 100000.0) -> PerformanceMetrics:
        """Calculate all performance metrics."""

        if not trades:
            return PerformanceCalculator._empty_metrics()

        # Basic counts
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.pnl > 0)
        losing_trades = sum(1 for t in trades if t.pnl < 0)
        breakeven_trades = sum(1 for t in trades if t.pnl == 0)

        # Win rates
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        loss_rate = (losing_trades / total_trades * 100) if total_trades > 0 else 0

        # PnL calculations
        total_pnl = sum(t.pnl for t in trades)
        total_pnl_percent = (total_pnl / starting_balance * 100) if starting_balance > 0 else 0
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))

        # Profit factor
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

        # Average win/loss
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl < 0]

        avg_win = (sum(t.pnl for t in wins) / len(wins)) if wins else 0
        avg_loss = (sum(t.pnl for t in losses) / len(losses)) if losses else 0
        avg_win_percent = (sum(t.pnl_percent for t in wins) / len(wins)) if wins else 0
        avg_loss_percent = (sum(t.pnl_percent for t in losses) / len(losses)) if losses else 0

        # Largest win/loss
        largest_win = max((t.pnl for t in trades), default=0)
        largest_loss = min((t.pnl for t in trades), default=0)

        # Risk/Reward
        avg_risk_reward = (sum(t.risk_reward for t in trades) / total_trades) if total_trades > 0 else 0
        expectancy = (win_rate / 100 * avg_win) - (loss_rate / 100 * abs(avg_loss))

        # Duration
        durations = [t.duration_minutes for t in trades if t.duration_minutes > 0]
        avg_trade_duration = int(sum(durations) / len(durations)) if durations else 0
        longest_trade = max(durations, default=0)
        shortest_trade = min(durations, default=0)

        # Max drawdown
        max_dd, max_dd_pct = PerformanceCalculator._calculate_drawdown(trades, starting_balance)

        # Sharpe ratio (simplified)
        sharpe = PerformanceCalculator._calculate_sharpe(trades)

        # Consecutive streaks
        max_consec_wins, max_consec_losses = PerformanceCalculator._calculate_streaks(trades)

        # Monthly returns
        best_month, worst_month, avg_monthly = PerformanceCalculator._calculate_monthly_returns(trades)

        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            breakeven_trades=breakeven_trades,
            win_rate=round(win_rate, 2),
            loss_rate=round(loss_rate, 2),
            total_pnl=round(total_pnl, 2),
            total_pnl_percent=round(total_pnl_percent, 2),
            gross_profit=round(gross_profit, 2),
            gross_loss=round(gross_loss, 2),
            profit_factor=round(profit_factor, 2),
            sharpe_ratio=round(sharpe, 2),
            max_drawdown=round(max_dd, 2),
            max_drawdown_percent=round(max_dd_pct, 2),
            avg_win=round(avg_win, 2),
            avg_loss=round(avg_loss, 2),
            avg_win_percent=round(avg_win_percent, 2),
            avg_loss_percent=round(avg_loss_percent, 2),
            largest_win=round(largest_win, 2),
            largest_loss=round(largest_loss, 2),
            avg_risk_reward=round(avg_risk_reward, 2),
            expectancy=round(expectancy, 2),
            avg_trade_duration_minutes=avg_trade_duration,
            longest_trade_minutes=longest_trade,
            shortest_trade_minutes=shortest_trade,
            max_consecutive_wins=max_consec_wins,
            max_consecutive_losses=max_consec_losses,
            best_month=round(best_month, 2),
            worst_month=round(worst_month, 2),
            avg_monthly_return=round(avg_monthly, 2),
        )

    @staticmethod
    def _calculate_drawdown(trades: List[TradeRecord], starting_balance: float):
        """Calculate maximum drawdown."""
        balance = starting_balance
        peak = starting_balance
        max_dd = 0
        max_dd_pct = 0

        for trade in trades:
            balance += trade.pnl

            if balance > peak:
                peak = balance

            dd = peak - balance
            dd_pct = (dd / peak * 100) if peak > 0 else 0

            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct

        return max_dd, max_dd_pct

    @staticmethod
    def _calculate_sharpe(trades: List[TradeRecord], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio (simplified)."""
        if not trades:
            return 0

        returns = [t.pnl_percent / 100 for t in trades]

        if not returns:
            return 0

        avg_return = sum(returns) / len(returns)

        # Calculate standard deviation
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return 0

        # Annualized Sharpe (assuming ~250 trading days)
        sharpe = ((avg_return - risk_free_rate / 250) / std_dev) * (250 ** 0.5)

        return sharpe

    @staticmethod
    def _calculate_streaks(trades: List[TradeRecord]):
        """Calculate consecutive win/loss streaks."""
        if not trades:
            return 0, 0

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif trade.pnl < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
            else:
                current_wins = 0
                current_losses = 0

        return max_wins, max_losses

    @staticmethod
    def _calculate_monthly_returns(trades: List[TradeRecord]):
        """Calculate monthly return statistics."""
        if not trades:
            return 0, 0, 0

        # Group trades by month
        monthly_pnl = {}
        for trade in trades:
            try:
                month = trade.exit_time[:7]  # YYYY-MM
                monthly_pnl[month] = monthly_pnl.get(month, 0) + trade.pnl
            except:
                continue

        if not monthly_pnl:
            return 0, 0, 0

        returns = list(monthly_pnl.values())
        best = max(returns, default=0)
        worst = min(returns, default=0)
        avg = sum(returns) / len(returns) if returns else 0

        return best, worst, avg

    @staticmethod
    def _empty_metrics() -> PerformanceMetrics:
        """Return empty metrics when no trades."""
        return PerformanceMetrics(
            total_trades=0, winning_trades=0, losing_trades=0, breakeven_trades=0,
            win_rate=0, loss_rate=0, total_pnl=0, total_pnl_percent=0,
            gross_profit=0, gross_loss=0, profit_factor=0, sharpe_ratio=0,
            max_drawdown=0, max_drawdown_percent=0, avg_win=0, avg_loss=0,
            avg_win_percent=0, avg_loss_percent=0, largest_win=0, largest_loss=0,
            avg_risk_reward=0, expectancy=0, avg_trade_duration_minutes=0,
            longest_trade_minutes=0, shortest_trade_minutes=0,
            max_consecutive_wins=0, max_consecutive_losses=0,
            best_month=0, worst_month=0, avg_monthly_return=0,
        )


class HTMLReportGenerator:
    """Generates HTML reports."""

    @staticmethod
    def generate(metrics: PerformanceMetrics,
                trades: List[TradeRecord],
                config: Dict,
                output_path: str = "backtest_report.html"):
        """Generate HTML report."""

        html = HTMLReportGenerator._build_html(metrics, trades, config)

        # Write to file
        Path(output_path).write_text(html, encoding='utf-8')

        return output_path

    @staticmethod
    def _build_html(metrics: PerformanceMetrics, trades: List[TradeRecord], config: Dict) -> str:
        """Build HTML content."""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Determine overall result color
        result_color = "green" if metrics.total_pnl > 0 else "red"

        html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Block Strategy - Backtest Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            font-size: 1.8em;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: transform 0.2s;
        }}

        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .metric-label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}

        .metric-value.positive {{
            color: #10b981;
        }}

        .metric-value.negative {{
            color: #ef4444;
        }}

        .highlight-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
        }}

        .highlight-box h3 {{
            font-size: 1.2em;
            margin-bottom: 10px;
            opacity: 0.9;
        }}

        .highlight-box .value {{
            font-size: 3em;
            font-weight: bold;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}

        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .config-item {{
            background: #f8f9fa;
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
        }}

        .config-label {{
            font-weight: 600;
            color: #667eea;
        }}

        .trade-long {{
            color: #10b981;
            font-weight: bold;
        }}

        .trade-short {{
            color: #ef4444;
            font-weight: bold;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}

        .warning {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}

        .warning strong {{
            color: #f59e0b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Order Block Strategy</h1>
            <p>Backtest Performance Report</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated: {timestamp}</p>
        </header>

        <div class="content">
            <!-- Overall Results -->
            <div class="section">
                <div class="highlight-box">
                    <h3>총 손익</h3>
                    <div class="value" style="color: {result_color};">
                        ${metrics.total_pnl:,.2f} ({metrics.total_pnl_percent:+.2f}%)
                    </div>
                </div>
            </div>

            <!-- Key Metrics -->
            <div class="section">
                <h2>🎯 핵심 지표</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">총 거래</div>
                        <div class="metric-value">{metrics.total_trades}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">승률</div>
                        <div class="metric-value {'positive' if metrics.win_rate >= 50 else ''}">{metrics.win_rate}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Profit Factor</div>
                        <div class="metric-value {'positive' if metrics.profit_factor > 1 else 'negative'}">{metrics.profit_factor}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Sharpe Ratio</div>
                        <div class="metric-value {'positive' if metrics.sharpe_ratio > 1 else ''}">{metrics.sharpe_ratio}</div>
                    </div>
                </div>
            </div>

            <!-- Win/Loss Stats -->
            <div class="section">
                <h2>📈 승/패 통계</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">승리 거래</div>
                        <div class="metric-value positive">{metrics.winning_trades}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">패배 거래</div>
                        <div class="metric-value negative">{metrics.losing_trades}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">평균 승리</div>
                        <div class="metric-value positive">${metrics.avg_win:,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">평균 패배</div>
                        <div class="metric-value negative">${metrics.avg_loss:,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">최대 승리</div>
                        <div class="metric-value positive">${metrics.largest_win:,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">최대 패배</div>
                        <div class="metric-value negative">${metrics.largest_loss:,.2f}</div>
                    </div>
                </div>
            </div>

            <!-- Risk Metrics -->
            <div class="section">
                <h2>⚠️ 리스크 지표</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">최대 낙폭 (DD)</div>
                        <div class="metric-value negative">${metrics.max_drawdown:,.2f} ({metrics.max_drawdown_percent:.2f}%)</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">평균 R:R</div>
                        <div class="metric-value">{metrics.avg_risk_reward:.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Expectancy</div>
                        <div class="metric-value {'positive' if metrics.expectancy > 0 else 'negative'}">${metrics.expectancy:.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">연속 승리 (최대)</div>
                        <div class="metric-value">{metrics.max_consecutive_wins}</div>
                    </div>
                </div>
            </div>

            <!-- Trade Duration -->
            <div class="section">
                <h2>⏱️ 거래 기간</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">평균 기간</div>
                        <div class="metric-value">{metrics.avg_trade_duration_minutes} min</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">최장 기간</div>
                        <div class="metric-value">{metrics.longest_trade_minutes} min</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">최단 기간</div>
                        <div class="metric-value">{metrics.shortest_trade_minutes} min</div>
                    </div>
                </div>
            </div>

            <!-- Monthly Performance -->
            <div class="section">
                <h2>📅 월별 성과</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">최고 월</div>
                        <div class="metric-value positive">${metrics.best_month:,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">최악 월</div>
                        <div class="metric-value negative">${metrics.worst_month:,.2f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">평균 월 수익</div>
                        <div class="metric-value">${metrics.avg_monthly_return:,.2f}</div>
                    </div>
                </div>
            </div>

            <!-- Recent Trades -->
            <div class="section">
                <h2>📝 최근 거래 (최대 20개)</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>진입 시간</th>
                                <th>청산 시간</th>
                                <th>방향</th>
                                <th>진입가</th>
                                <th>청산가</th>
                                <th>수량</th>
                                <th>손익</th>
                                <th>손익%</th>
                                <th>R:R</th>
                                <th>종료</th>
                            </tr>
                        </thead>
                        <tbody>
"""

        # Add trade rows (last 20 trades)
        recent_trades = trades[-20:] if len(trades) > 20 else trades
        for trade in reversed(recent_trades):
            pnl_class = 'positive' if trade.pnl > 0 else 'negative'
            direction_class = 'trade-long' if trade.direction == 'LONG' else 'trade-short'

            html += f"""
                            <tr>
                                <td>{trade.entry_time}</td>
                                <td>{trade.exit_time}</td>
                                <td class="{direction_class}">{trade.direction}</td>
                                <td>{trade.entry_price:.5f}</td>
                                <td>{trade.exit_price:.5f}</td>
                                <td>{trade.quantity:.2f}</td>
                                <td class="metric-value {pnl_class}" style="font-size: 1em;">${trade.pnl:,.2f}</td>
                                <td class="metric-value {pnl_class}" style="font-size: 1em;">{trade.pnl_percent:+.2f}%</td>
                                <td>{trade.risk_reward:.2f}</td>
                                <td>{trade.setup_type}</td>
                            </tr>
"""

        html += """
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Configuration -->
            <div class="section">
                <h2>⚙️ 전략 설정</h2>
"""

        # Add config items
        for key, value in config.items():
            html += f"""
                <div class="config-item">
                    <span class="config-label">{key}</span>
                    <span>{value}</span>
                </div>
"""

        html += """
            </div>

            <!-- Warning -->
            <div class="warning">
                <strong>⚠️ 면책조항:</strong> 이 백테스트 결과는 과거 데이터를 기반으로 한 것이며, 미래 수익을 보장하지 않습니다.
                실제 트레이딩은 상당한 손실 위험이 있습니다. 항상 적절한 리스크 관리를 사용하고,
                라이브 트레이딩 전에 충분히 테스트하세요.
            </div>
        </div>

        <div class="footer">
            <p><strong>Order Block Strategy</strong> - Powered by Nautilus Trader</p>
            <p>Report generated: {timestamp}</p>
        </div>
    </div>
</body>
</html>
"""

        return html


class ReportManager:
    """Manages report generation and storage."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_report(self,
                       trades: List[TradeRecord],
                       config: Dict,
                       starting_balance: float = 100000.0,
                       report_name: Optional[str] = None) -> str:
        """Generate comprehensive backtest report."""

        # Calculate metrics
        metrics = PerformanceCalculator.calculate_metrics(trades, starting_balance)

        # Generate report name
        if report_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"backtest_report_{timestamp}.html"

        output_path = self.output_dir / report_name

        # Generate HTML report
        HTMLReportGenerator.generate(metrics, trades, config, str(output_path))

        # Also save JSON data
        json_path = output_path.with_suffix('.json')
        self._save_json(metrics, trades, config, json_path)

        return str(output_path)

    def _save_json(self, metrics: PerformanceMetrics, trades: List[TradeRecord],
                   config: Dict, output_path: Path):
        """Save report data as JSON."""
        data = {
            'metrics': asdict(metrics),
            'trades': [asdict(t) for t in trades],
            'config': config,
            'generated_at': datetime.now().isoformat(),
        }

        output_path.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def print_summary(self, metrics: PerformanceMetrics):
        """Print summary to console."""
        print("\n" + "=" * 80)
        print("BACKTEST SUMMARY")
        print("=" * 80)
        print(f"Total Trades:        {metrics.total_trades}")
        print(f"Win Rate:            {metrics.win_rate}%")
        print(f"Profit Factor:       {metrics.profit_factor}")
        print(f"Sharpe Ratio:        {metrics.sharpe_ratio}")
        print(f"\nTotal P&L:           ${metrics.total_pnl:,.2f} ({metrics.total_pnl_percent:+.2f}%)")
        print(f"Max Drawdown:        ${metrics.max_drawdown:,.2f} ({metrics.max_drawdown_percent:.2f}%)")
        print(f"\nAverage Win:         ${metrics.avg_win:,.2f}")
        print(f"Average Loss:        ${metrics.avg_loss:,.2f}")
        print(f"Avg Risk/Reward:     {metrics.avg_risk_reward:.2f}")
        print(f"Expectancy:          ${metrics.expectancy:.2f}")
        print("=" * 80 + "\n")
