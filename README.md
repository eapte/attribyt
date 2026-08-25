# 🔍 Attribyt
![License](https://img.shields.io/badge/license-MIT-green)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Status](https://img.shields.io/badge/status-MVP-orange)

Privacy-first, on-premises multi-touch attribution — runs entirely on your
own machine, no cloud, no external data sharing.

Attribyt helps marketers and analysts see which channels actually drive
conversions. Instead of trusting Last-Click attribution (which gives 100%
of the credit to the last touch before a purchase), it compares four
models side by side — including a real Markov-chain removal-effect model —
so you can see each channel's true contribution.

---

## 📊 Why Attribyt?

Most ad platforms default to Last-Click attribution, which:
- Overpays bottom-of-funnel channels (like brand search or direct traffic)
- Underinvests in top-of-funnel channels (organic content, social, display)
  that create demand but rarely get the final click

Attribyt runs all four models on the same data so the difference is visible
at a glance.

---

## 🚀 Features

- **Four attribution models**: Last-Click, Linear, Time Decay, and Markov
  Chain (removal effect via Monte Carlo simulation on the channel
  transition graph)
- **Automatic column mapping** — upload a CSV and the app guesses which
  column is the user ID, timestamp, channel, event type, and revenue;
  every guess can be corrected before running the analysis
- **Data validation** — malformed rows (missing IDs, unparseable dates,
  negative revenue, exact duplicates) are cleaned automatically, with a
  visible report of what was fixed, instead of crashing the analysis
- **Top converting paths** — a ranked list of the most common channel
  sequences that led to a purchase
- **Privacy-first** — all processing happens locally in your own Docker
  containers; no data ever leaves your machine
- **CSV, PostgreSQL, and ClickHouse** as data sources


---

## 📁 Project Structure



---

## 📜 License

MIT License — free for personal and commercial use.

---

## 🔗 Links

- [GitHub Repository](https://github.com/eapte/attribyt)
- [Report a Bug](https://github.com/eapte/attribyt/issues)
