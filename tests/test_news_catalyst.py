"""Tests for news catalyst agent with mocked APIs."""
from unittest.mock import patch, MagicMock
from src.agents.news_catalyst import detect_news_catalysts, _classify_news


class TestNewsCatalyst:
    @patch("src.agents.news_catalyst._tavily")
    @patch("src.agents.news_catalyst.ChatGoogleGenerativeAI")
    def test_detects_catalyst(self, mock_llm_class, mock_tavily):
        # Mock Tavily returns news
        mock_tavily.search.return_value = {
            "results": [{"title": "CHIPS Act funding approved", "content": "Major boost for semiconductor industry"}]
        }

        # Mock LLM classifies as catalyst
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="CATALYST: YES\nIMPACT: CHIPS Act boosts semiconductor funding\nTICKERS: NVDA, AMD, INTC\nCONFIDENCE: HIGH"
        )
        mock_llm_class.return_value = mock_llm

        indicators = {
            "NVDA": {"price": 130.0},
            "AMD": {"price": 160.0},
            "INTC": {"price": 30.0},
        }

        signals = detect_news_catalysts(indicators)
        assert len(signals) >= 1
        assert signals[0]["signal_type"] == "news_catalyst"

    @patch("src.agents.news_catalyst._tavily")
    def test_no_news_no_signal(self, mock_tavily):
        mock_tavily.search.return_value = {"results": []}
        indicators = {"AAPL": {"price": 150.0}}
        signals = detect_news_catalysts(indicators)
        assert len(signals) == 0

    @patch("src.agents.news_catalyst.ChatGoogleGenerativeAI")
    def test_classify_no_catalyst(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="CATALYST: NO\nIMPACT: None\nTICKERS: \nCONFIDENCE: LOW")
        mock_llm_class.return_value = mock_llm

        result = _classify_news("Some boring news", "tech")
        assert result is None

    @patch("src.agents.news_catalyst.ChatGoogleGenerativeAI")
    def test_classify_handles_error(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API error")
        mock_llm_class.return_value = mock_llm

        result = _classify_news("Some news", "tech")
        assert result is None

    def test_classify_empty_news(self):
        result = _classify_news("", "tech")
        assert result is None
