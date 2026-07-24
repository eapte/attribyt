# Attribyt

**Privacy-first, on-premises CLI tool for multi-touch attribution.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## Features

- 📊 **Multi-source** – CSV, PostgreSQL, ClickHouse
- 🧠 **Two attribution models** – Last-Click and Markov (Removal Effect)
- 📈 **Compare models side‑by‑side** with delta and share
- 🎨 **Interactive Sankey diagram** (HTML) for user journeys
- 🔧 **Custom column mapping** – adapts to any data schema
- 🤖 **Interactive mode** – guided setup for beginners
- 🔒 **Privacy-first** – all data stays on your machine

---

## Installation

```bash
git clone https://github.com/eapte/attribyt.git
cd attribyt
python -m venv venv
source venv/bin/activate   # or `venv\Scripts\activate` on Windows
pip install -e .
