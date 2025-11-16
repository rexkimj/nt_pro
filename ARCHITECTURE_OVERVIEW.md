# Nautilus Trader Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      NAUTILUS TRADER PLATFORM                        │
└─────────────────────────────────────────────────────────────────────┘

                              YOUR STRATEGY
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
              ┌─────▼─────┐              ┌────────▼────────┐
              │  Strategy │              │   Indicators    │
              │  Config   │              │  (EMA, RSI...)  │
              └─────┬─────┘              └────────┬────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                        ┌──────────▼────────────┐
                        │   Message Bus         │
                        │ (Commands & Events)   │
                        └──┬────────────────┬───┘
                           │                │
        ┌──────────────────┼────────────────┼──────────────────┐
        │                  │                │                  │
   ┌────▼────┐      ┌─────▼──────┐  ┌─────▼──────┐      ┌─────▼────┐
   │   Data  │      │   Order    │  │    Risk    │      │ Execution│
   │  Engine │      │ Emulator   │  │   Engine   │      │  Engine  │
   └────┬────┘      └─────┬──────┘  └─────┬──────┘      └─────┬────┘
        │                 │               │                   │
        │        ┌────────┼───────────────┼───────────┐       │
        │        │        │               │           │       │
   ┌────▼────────▼──┐  ┌──▼───────────────▼──┐  ┌────▼───────▼─┐
   │     CACHE      │  │   Exec Algorithm    │  │ Execution    │
   │ (Central Data  │  │   (TWAP, VWAP...)   │  │ Client       │
   │  Repository)   │  └─────────────────────┘  │ (Live Orders)│
   └────────────────┘                           └──────────────┘
        │
        ├─ Positions
        ├─ Orders
        ├─ Market Data (Bars, Ticks)
        └─ Account Info
```

## Data Flow

```
External Data Source (Exchange/Data Feed)
          │
          ▼
┌──────────────────────┐
│   Execution Client   │  ◄─── ORDER SUBMISSION
│   (Adapter)          │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Message Bus         │
│ (Event Distribution) │
└──┬──────────────┬────┘
   │              │
   ▼              ▼
┌──────────────┐  ┌──────────────────┐
│ Data Engine  │  │ Execution Engine │
│ (Market Data)│  │ (Orders/Fills)   │
└────┬─────────┘  └──────┬───────────┘
     │                   │
     └──────┬────────────┘
            │
            ▼
┌──────────────────────┐
│  CACHE (Updated)     │
└──────────┬───────────┘
           │
           ▼
YOUR STRATEGY (Handler Methods)
  - on_bar()
  - on_quote_tick()
  - on_trade_tick()
```

## Event-Driven Processing

```
Time = T0  →  Strategy Receives Market Data
                        │
                        ▼
              on_bar() / on_quote_tick()
                        │
                        ▼
            Access Cache + Indicators
                        │
        ┌───────────────┼───────────────┐
        │               │               │
      Entry?         Update?         Exit?
        │               │               │
        ▼               ▼               ▼
   submit_order() manage_position() close_position()
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
              SubmitOrder Command
                        │
                        ▼
              Message Bus Distribution
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   OrderEmulator  ExecAlgorithm  RiskEngine
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
              ExecutionEngine
                        │
                        ▼
              ExecutionClient
                        │
                        ▼
              Send to Exchange/Venue
```

## Component Interactions

```
┌─────────────────────────────────────────────────────────────┐
│                    TRADING SYSTEM                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              YOUR STRATEGY CODE                      │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │  1. Subscribe to Data (on_start)            │   │   │
│  │  │  2. Register Indicators                     │   │   │
│  │  │  3. Process Events (on_bar, on_tick, etc)   │   │   │
│  │  │  4. Access Cache for State                  │   │   │
│  │  │  5. Submit Orders / Manage Positions        │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────┬──────────────────────────────────────┘   │
│                │                                            │
│                ▼                                            │
│  ┌──────────────────────────────────────────────────┐      │
│  │            CORE FRAMEWORK                        │      │
│  ├──────────────────────────────────────────────────┤      │
│  │                                                  │      │
│  │  ┌─ Data Engine        ┌─ Message Bus          │      │
│  │  │                     │                        │      │
│  │  │ • Market data       │ • Event routing       │      │
│  │  │   subscriptions     │ • Command queueing    │      │
│  │  │ • Data streaming    │ • Ordered processing  │      │
│  │  │ • Feed handling     │                        │      │
│  │  │                     └─ Execution Engine     │      │
│  │  ├─ Cache              │                        │      │
│  │  │ • Positions         │ • Order tracking      │      │
│  │  │ • Orders            │ • Fill processing     │      │
│  │  │ • Market data       │ • Risk validation     │      │
│  │  │ • Account info      │ • Position updates    │      │
│  │  │                     │                        │      │
│  │  └─ Risk Engine        └─ Execution Adapters  │      │
│  │    • Risk limits         • Venue connectivity  │      │
│  │    • Exposure checks     • Order transmission  │      │
│  │    • Validation          • Fill reception      │      │
│  │                                                  │      │
│  └──────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
               EXTERNAL VENUES / EXCHANGES
```

## Class Hierarchy

```
Actor (Base class for all entities)
│
├── DataEngine
│   └── Manages market data subscriptions
│
├── ExecutionEngine
│   └── Manages order execution
│
├── RiskEngine
│   └── Manages risk validation
│
└── Strategy (YOUR STRATEGIES INHERIT FROM HERE)
    ├── Inherits all Actor functionality
    ├── Defines trading logic
    ├── Contains indicators
    └── Manages positions/orders
```

## Strategy Lifecycle

```
┌─────────┐
│ Create  │ Create config and strategy instance
└────┬────┘
     │
     ▼
┌─────────┐
│ Inject  │ Framework injects actor into system
└────┬────┘
     │
     ▼
┌──────────────────┐
│  on_start()      │ Called once when strategy starts
│  - Subscribe     │ - Subscribe to market data
│  - Setup         │ - Register indicators
└────┬─────────────┘
     │
     ▼
┌─────────────────────────┐
│ Event Processing        │ Continuously called
│ - on_bar()              │ based on data arrival
│ - on_quote_tick()       │
│ - on_trade_tick()       │
│ - on_order_filled()     │
│ - ... etc               │
└────┬────────────────────┘
     │
     ▼
┌──────────────────┐
│  on_stop()       │ Called when strategy stops
│  - Cleanup       │ - Close open positions
│  - Final tasks   │ - Log final state
└──────────────────┘
```

## Configuration Pattern

```
StrategyConfig (Defines Strategy Parameters)
     │
     ├─ instrument_id    (What instrument to trade)
     ├─ bar_type         (What timeframe/data type)
     ├─ trade_size       (Position size)
     ├─ [Custom params]  (Your strategy parameters)
     │
     └─► Strategy Instance
         │
         ├─ on_start()   (Use config values)
         ├─ on_bar()     (Use config values)
         └─ on_stop()
```

## Indicator Update Mechanism

```
APPROACH 1: Automatic Registration (Recommended)
┌──────────────────────────────────────┐
│ on_start()                            │
│ {                                     │
│   register_indicator_for_bars(       │
│     bar_type, my_ema                 │
│   )                                  │
│ }                                    │
└──────────┬───────────────────────────┘
           │
           ▼
Framework automatically calls:
my_ema.handle_bar(bar) when new bar arrives

on_bar() receives:
my_ema.value (already updated)


APPROACH 2: Manual Update
┌──────────────────────────────────────┐
│ on_bar(bar)                           │
│ {                                     │
│   my_indicator.handle_bar(bar)       │
│   current_val = my_indicator.value    │
│ }                                    │
└──────────────────────────────────────┘
```

## Order Submission Path

```
strategy.buy(quantity=100)
              │
              ▼
     OrderFactory creates Order
              │
              ▼
    SubmitOrder Command
              │
              ▼
         Message Bus
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
OrderEmu  ExecAlgo  RiskEngine (Validate)
    │         │         │
    └─────────┼─────────┘
              │
              ▼
       ExecutionEngine
              │
              ▼
    ExecutionClient/Adapter
              │
              ▼
           VENUE
              │
              ▼
         Order ACK/Fill
              │
              ▼
         Back to Strategy
              (via event handlers)
```

## Key Architectural Principles

1. **Event-Driven**: Everything is triggered by events (bars, ticks, fills)
2. **Message-Bus Based**: All components communicate via message bus
3. **Cache-Centric**: Strategy accesses all data through central cache
4. **Decoupled**: Strategy code doesn't directly call execution components
5. **Same Code, Multiple Environments**: Backtest code = live code
6. **Type-Safe**: Full type annotations throughout
7. **High Performance**: Rust core for critical components

## Typical Execution Latency (Simplified)

```
Backtest:        Tick received → on_bar() called → Order submitted → 
                 Order emulated → Fill event → on_fill() called
                 (Sub-millisecond - limited by data rate)

Live Trading:    Tick received → on_bar() called → Order submitted → 
                 Network → Venue → Execution → Network → on_fill()
                 (Milliseconds to seconds depending on venue/network)
```

