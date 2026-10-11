"""Currency conversion. All prices in the data are Turkish lira (TRY)."""
import json

SYMBOLS = {"TRY": "₺", "USD": "$", "EUR": "€", "GBP": "£"}


def load_rates(path):
    """Return (rates, info): rates maps currency -> TRY per 1 unit (TRY -> 1.0)."""
    with open(path, encoding="utf-8") as f:
        info = json.load(f)
    rates = {"TRY": 1.0, **{k: float(v) for k, v in info["TRY_per"].items() if v}}
    return rates, info


def to_try(amount, currency, rates):
    return amount * rates[currency]


def from_try(amount_try, currency, rates):
    return amount_try / rates[currency]


def fmt(amount_try, currency, rates):
    """'₺3,710' or '₺3,710 (≈ $76)'."""
    lira = f"₺{amount_try:,.0f}"
    if currency == "TRY":
        return lira
    return f"{lira} (≈ {SYMBOLS[currency]}{from_try(amount_try, currency, rates):,.0f})"
