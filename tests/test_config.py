"""Tests for config and universe modules."""
from src.core.config import config, load_config
from src.core.universe import SECTORS, get_all_tickers, get_sector_for_ticker


class TestConfig:
    def test_config_loads(self):
        assert config is not None

    def test_has_llm_section(self):
        assert "llm" in config
        assert "model" in config["llm"]
        assert "temperature" in config["llm"]

    def test_has_scanner_section(self):
        assert "scanner" in config
        assert "thresholds" in config["scanner"]
        assert "position_sizing" in config["scanner"]

    def test_thresholds_present(self):
        t = config["scanner"]["thresholds"]
        assert "panic_sell" in t
        assert "short_squeeze" in t
        assert "breakout" in t

    def test_position_sizing(self):
        ps = config["scanner"]["position_sizing"]
        assert ps["portfolio_value"] > 0
        assert 0 < ps["max_risk_per_trade_pct"] <= 5


class TestUniverse:
    def test_sectors_defined(self):
        assert len(SECTORS) == 8

    def test_each_sector_has_etf(self):
        for name, data in SECTORS.items():
            assert "etf" in data
            assert "stocks" in data
            assert len(data["stocks"]) >= 4

    def test_get_all_tickers(self):
        tickers = get_all_tickers()
        assert len(tickers) >= 50
        assert "AAPL" in tickers
        assert "QQQ" in tickers

    def test_get_sector_for_known_ticker(self):
        sector, etf = get_sector_for_ticker("NVDA")
        assert sector in ["tech", "semiconductors"]
        assert etf in ["QQQ", "SMH"]

    def test_get_sector_for_unknown_ticker(self):
        sector, etf = get_sector_for_ticker("ZZZZZ")
        assert sector == "unknown"
        assert etf == "SPY"
