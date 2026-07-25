# 🔍 Attribyt
![License](https://img.shields.io/badge/license-MIT-green)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Status](https://img.shields.io/badge/status-MVP-orange)

**Privacy-first, on-premises CLI tool for multi-touch attribution.**

Attribyt helps marketers and analysts understand which channels truly drive conversions. Unlike Last-Click attribution, it uses **Markov chains** (via Removal Effect) to fairly distribute credit across all touchpoints.

---

## 📊 Why Attribyt?

Most ad platforms use **Last-Click** attribution — they give 100% of the credit to the last click before a purchase. This is misleading and causes you to:

- **Overpay** for bottom-of-funnel channels (like brand search).
- **Underinvest** in top-of-funnel channels (like organic content or social media) that actually create demand.

Attribyt solves this by offering **4 different attribution models** side-by-side, so you can see the real value of each channel.

---

## 🚀 Features

- **4 attribution models**: Last-Click, Linear, Time Decay, Markov (Removal Effect)
- **Multiple data sources**: CSV, PostgreSQL, ClickHouse
- **Interactive Sankey diagram** for visualizing user journeys
- **Export results** to CSV for further analysis
- **Privacy-first**: all data stays on your machine — no cloud, no tracking
- **Interactive mode** for beginners — no coding required
- **Fast and lightweight** — works with up to 50,000 rows

---

## 🛠 Installation

```bash
# Clone the repository
git clone https://github.com/eapte/attribyt.git
cd attribyt

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install the package
pip install -e .
```

---

## 📖 Usage

### Quick start (interactive mode)

Just type:
```bash
attribyt
```

You'll be guided through a setup wizard — no command-line skills needed.

### Command-line mode

```bash
attribyt --from csv --file examples/test_data100.csv --model both --sankey --export results.csv --user-id client_id --timestamp event_time --channel traffic_source --event action --revenue amount
```

### Options

| Option | Description |
| :--- | :--- |
| `--from` | Data source: `csv`, `postgres`, `clickhouse` |
| `--file` | Path to CSV file |
| `--model` | `last-click`, `linear`, `time-decay`, `markov`, `both` |
| `--sankey` | Generate Sankey diagram (HTML) |
| `--export` | Export results to CSV file |
| `--user-id` | Column name for user ID |
| `--timestamp` | Column name for timestamp |
| `--channel` | Column name for channel |
| `--event` | Column name for event type |
| `--revenue` | Column name for revenue |
| `--start` | Start date (YYYY-MM-DD) |
| `--end` | End date (YYYY-MM-DD) |

---

## 📁 Example CSV format

| client_id | event_time | traffic_source | action | amount |
| :--- | :--- | :--- | :--- | :--- |
| user_001 | 2024-01-01 10:00 | google_ads | click | 0 |
| user_001 | 2024-01-01 11:00 | email | purchase | 120.50 |
| user_002 | 2024-01-01 10:00 | organic | click | 0 |
| user_002 | 2024-01-01 12:00 | organic | purchase | 45.00 |

> **Important:** 
> - `action` should contain `purchase` or any event indicating a conversion.
> - `amount` should be the revenue for the conversion (0 for non-converting events).
> - Timestamp column must be sortable (ISO format recommended).

---

## 📊 Example Output

```
Summary
Total users: 100 | Total touches: 267 | Converted: 100 users (100.0%) | Total revenue: $9,951.00

Attribution Comparison
┌──────────────┬────────────┬──────────┬────────────┬─────────┬──────────┐
│ Channel      │ Last-Click │ Linear   │ Time Decay │ Markov  │ Delta    │
├──────────────┼────────────┼──────────┼────────────┼─────────┼──────────┤
│ organic      │ 1,990.20   │ 1,923.86 │ 1,981.67   │ 3,317.00│ +1,326.80│
│ google_ads   │ 1,691.67   │ 1,816.06 │ 1,734.32   │ 1,895.43│ +203.76  │
│ telegram     │ 1,094.61   │ 1,243.87 │ 1,150.53   │ 1,895.43│ +800.82  │
│ direct       │ 1,890.69   │ 1,210.71 │ 1,603.53   │ 0.00    │ -1,890.69│
└──────────────┴────────────┴──────────┴────────────┴─────────┴──────────┘

Interpretation
Top channel: organic — 33.3% of total value ($3,317.00)
  telegram: 19.0% ($1,895.43)
  google_ads: 19.0% ($1,895.43)
  yandex_direct: 11.9% ($1,184.64)
  facebook_ads: 11.9% ($1,184.64)
  email: 4.8% ($473.86)
Lowest channel: direct — 0.0% of total value ($0.00)
```

---

## 🧠 Understanding the Models

| Model | Logic | Best for |
| :--- | :--- | :--- |
| **Last-Click** | All credit goes to the last channel | Reporting to ad platforms |
| **Linear** | Credit is split evenly across all touches | Understanding overall channel participation |
| **Time Decay** | More credit to touches closer to conversion | Compromise between Last-Click and Linear |
| **Markov (Removal Effect)** | Credit based on "removal effect" — how much conversions drop without this channel | Strategic budget allocation |

---

## 📁 Project Structure

```
attribyt/
├── attribution/
│   ├── connectors/          # Data source connectors
│   ├── main.py              # CLI entry point
│   ├── markov.py            # Attribution models
│   ├── journey.py           # Journey builder
│   └── metrics.py           # Metrics calculator
├── examples/
│   └── test_data100.csv     # Sample data
├── pyproject.toml           # Package config
└── requirements.txt         # Dependencies
```

---

## 📜 License

MIT License — free for personal and commercial use.

---

## 🔗 Links

- [GitHub Repository](https://github.com/eapte/attribyt)
- [Report a Bug](https://github.com/eapte/attribyt/issues)
