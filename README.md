# Alpaca Markets (for Home Assistant)

[![GitHub Release](https://img.shields.io/github/release/FaserF/ha-alpaca-markets.svg?style=flat-square)](https://github.com/FaserF/ha-alpaca-markets/releases)
[![Downloads (Current release)](https://img.shields.io/github/downloads/FaserF/ha-alpaca-markets/latest/alpaca_markets.zip?label=Downloads%20(Current%20release)&style=flat-square)](https://github.com/FaserF/ha-alpaca-markets/releases)
[![License](https://img.shields.io/github/license/FaserF/ha-alpaca-markets.svg?style=flat-square)](LICENSE)
[![hacs](https://img.shields.io/badge/HACS-custom-orange.svg?style=flat-square)](https://hacs.xyz)
[![Add to Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=alpaca_markets)
[![CI Orchestrator](https://github.com/FaserF/ha-alpaca-markets/actions/workflows/ci-orchestrator.yml/badge.svg)](https://github.com/FaserF/ha-alpaca-markets/actions/workflows/ci-orchestrator.yml)

A secure, production-grade Home Assistant integration for [Alpaca Markets](https://alpaca.markets/). Monitor your trading account, portfolio values, positions, market status, and execute orders directly from Home Assistant automations and dashboards with support for both **Paper Trading** and **Live Trading**.

---

## 🧭 Quick Links

| | | | |
| :--- | :--- | :--- | :--- |
| [✨ Features](#-features) | [📦 Installation](#-installation) | [⚙️ Configuration](#️-configuration) | [🛠️ Options](#️-options-flow) |
| [🧱 Services](#-services) | [📊 Entity List](#-entities--sensors) | [📖 Automations](#-automation-examples) | [❓ FAQ](#-troubleshooting--faq) |

---

## ✨ Features

- **Dual-Trading Mode**: Seamless support for both **Paper Trading** (simulation) and **Live Trading** (real money).
- **Portfolio & Account Monitoring**:
  - **Equity & Portfolio Value**: Real-time tracking of portfolio valuation and net equity.
  - **Cash & Buying Power**: Monitor available cash, regular buying power, and Day Trading buying power.
  - **P&L Tracking**: Unrealized profit/loss (amount and percentage) and realized intraday gains.
  - **Margins & Risk**: Monitor initial margin, maintenance margin, short market value, and long market value.
  - **Pattern Day Trading**: Track day trade count and receive binary sensor alerts if PDT rules trigger.
- **Market Clock & Schedule**:
  - Binary sensor indicating if US markets are currently open or closed.
  - Timestamp sensors for the next market opening and closing times with full timezone support.
- **Position & Order Tracking**:
  - Live count and valuation of open positions.
  - Number of pending/open orders.
- **Emergency Controls & Action Buttons**:
  - **Cancel All Orders**: One-click cancel button for all pending orders.
  - **Close All Positions**: One-click liquidation button to exit all open positions.
- **Automations & Trading Services**:
  - `alpaca_markets.place_order`: Place Market, Limit, Stop, and Stop-Limit orders via automations.
  - `alpaca_markets.cancel_order`: Cancel specific orders by order ID.
  - `alpaca_markets.close_position`: Liquidate or partially close positions by symbol.
- **Production Architecture**:
  - Native `DataUpdateCoordinator` with configurable polling interval.
  - Full localization (English & German).
  - Diagnostic export support (`diagnostics.py`).
  - HACS compliant brand assets and automated release workflows.

---

## 📦 Installation

### Method 1: Via HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Click on the three dots in the top right corner and select **Custom repositories**.
3. Enter `https://github.com/FaserF/ha-alpaca-markets`, select **Integration** as the category, and click **Add**.
4. Search for **Alpaca Markets**, click **Download**, and restart Home Assistant.

### Method 2: Manual Installation

1. Download the latest `alpaca_markets.zip` release from the [Releases](https://github.com/FaserF/ha-alpaca-markets/releases) page.
2. Extract the archive into your Home Assistant directory:
   ```text
   config/custom_components/alpaca_markets/
   ```
3. Restart Home Assistant.

---

## ⚙️ Configuration

1. Log into your [Alpaca Dashboard](https://app.alpaca.markets/).
2. Select your account type (**Paper Trading** or **Live Trading**).
3. Generate your **API Key ID** (`PK...` for paper) and **Secret Key**.
4. In Home Assistant, go to **Settings → Devices & Services → Add Integration**.
5. Search for **Alpaca Markets** and enter:
   - **API Key ID**: Your Alpaca key ID.
   - **API Secret Key**: Your Alpaca secret key.
   - **Trading Mode**: Select `Paper Trading` or `Live Trading`.

---

## 🛠️ Options Flow

You can change the integration options at any time under **Settings → Devices & Services → Alpaca Markets → Configure**:

- **Update Interval**: Polling frequency in seconds (default: `60`, range: `10` to `3600` seconds).

---

## 📊 Entities & Sensors

### 📈 Monetary & Account Sensors
| Entity | Type | Unit | Description |
|---|---|---|---|
| `sensor.alpaca_markets_portfolio_value` | Monetary | `$` | Total market value of equities + cash |
| `sensor.alpaca_markets_cash` | Monetary | `$` | Available cash balance |
| `sensor.alpaca_markets_equity` | Monetary | `$` | Net equity value |
| `sensor.alpaca_markets_buying_power` | Monetary | `$` | Available buying power |
| `sensor.alpaca_markets_daytrading_buying_power` | Monetary | `$` | Day trading buying power *(disabled by default)* |
| `sensor.alpaca_markets_long_market_value` | Monetary | `$` | Total market value of long positions |
| `sensor.alpaca_markets_short_market_value` | Monetary | `$` | Total market value of short positions *(disabled by default)* |
| `sensor.alpaca_markets_unrealized_pl` | Monetary | `$` | Total unrealized profit / loss |
| `sensor.alpaca_markets_unrealized_plpc` | Percentage | `%` | Percentage unrealized profit / loss |
| `sensor.alpaca_markets_realized_pl` | Monetary | `$` | Realized profit / loss today *(disabled by default)* |
| `sensor.alpaca_markets_daytrade_count` | Counter | - | Number of day trades in last 5 rolling days |
| `sensor.alpaca_markets_account_status` | Text | - | Account status (e.g. `active`, `restricted`) |

### 🕒 Market Status Sensors
| Entity | Type | Description |
|---|---|---|
| `binary_sensor.alpaca_markets_market_open` | Running | `on` when market is currently open, `off` when closed |
| `sensor.alpaca_markets_next_market_open` | Timestamp | Date and time of next market opening |
| `sensor.alpaca_markets_next_market_close` | Timestamp | Date and time of next market closing |

### 🛡️ Safety & Account Binary Sensors
| Entity | Type | Description |
|---|---|---|
| `binary_sensor.alpaca_markets_trading_blocked` | Problem | `on` if trading is blocked on account |
| `binary_sensor.alpaca_markets_account_blocked` | Problem | `on` if account is blocked |
| `binary_sensor.alpaca_markets_account_restricted` | Problem | `on` if account has regulatory restrictions |
| `binary_sensor.alpaca_markets_pattern_day_trader` | Problem | `on` if flagged as Pattern Day Trader *(disabled by default)* |

### 🔘 Action Buttons
| Button | Description |
|---|---|
| `button.alpaca_markets_cancel_all_orders` | Submits `DELETE /v2/orders` to immediately cancel all open orders |
| `button.alpaca_markets_close_all_positions` | Submits liquidation request to immediately close all active positions |

---

## 🧱 Services

### `alpaca_markets.place_order`
Submit a new buy or sell order.

```yaml
service: alpaca_markets.place_order
data:
  entry_id: "YOUR_ENTRY_ID"
  symbol: "AAPL"
  side: "buy"
  order_type: "limit"
  time_in_force: "day"
  qty: 5
  limit_price: 175.50
```

### `alpaca_markets.cancel_order`
Cancel an open order by its UUID.

```yaml
service: alpaca_markets.cancel_order
data:
  entry_id: "YOUR_ENTRY_ID"
  order_id: "6178c772-9b21-4f38-9cb5-1158f9c2d716"
```

### `alpaca_markets.close_position`
Close (liquidate) an open position by symbol.

```yaml
service: alpaca_markets.close_position
data:
  entry_id: "YOUR_ENTRY_ID"
  symbol: "AAPL"
  percentage: 50
```

---

## 📖 Automation Examples

### 🚨 Alert When Daily Loss Exceeds Threshold
```yaml
alias: "Alpaca: High Loss Warning"
trigger:
  - platform: numeric_state
    entity_id: sensor.alpaca_markets_paper_nicht_realisierter_g_v
    below: -500
action:
  - service: notify.notify
    data:
      title: "Alpaca Risk Alert"
      message: "Unrealized portfolio loss exceeded -$500! Current P&L: {{ states('sensor.alpaca_markets_paper_nicht_realisierter_g_v') }} $"
```

### 🔔 Notify on Market Opening
```yaml
alias: "Alpaca: US Market Opened"
trigger:
  - platform: state
    entity_id: binary_sensor.alpaca_markets_paper_markt_geoffnet
    from: "off"
    to: "on"
action:
  - service: notify.notify
    data:
      message: "US Stock Markets are now OPEN. Portfolio: {{ states('sensor.alpaca_markets_paper_portfolio_wert') }} $"
```

---

## ❓ Troubleshooting & FAQ

### Q: Why do monetary sensors show `$` instead of `€`?
Alpaca trading accounts are primarily denominated in USD. Home Assistant can automatically convert currencies if your system currency is set accordingly.

### Q: How can I distinguish between Paper and Live accounts?
Each configured instance displays its trading mode in the device title (e.g. `Alpaca Markets (Paper)` vs `Alpaca Markets (Live)`).

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
