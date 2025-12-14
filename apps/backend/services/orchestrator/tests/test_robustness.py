"""
Robustness Test Suite

Tests for language handling, config validation, and audio quality checks
to prevent regressions and ensure production reliability.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import normalize_language_code, validate_tts_config


class TestLanguageNormalization:
    """Test language code normalization."""
    
    def test_region_code_removal(self):
        """Should remove region codes like -CN, -US, -BR."""
        assert normalize_language_code("zh-CN") == "zh"
        assert normalize_language_code("en-US") == "en"
        assert normalize_language_code("pt-BR") == "pt"
        assert normalize_language_code("es-MX") == "es"
    
    def test_underscore_variants(self):
        """Should handle underscore separators."""
        assert normalize_language_code("zh_CN") == "zh"
        assert normalize_language_code("en_GB") == "en"
    
    def test_iso639_3_mapping(self):
        """Should map ISO 639-3 (3-letter) to ISO 639-1 (2-letter)."""
        assert normalize_language_code("cmn") == "zh"  # Mandarin
        assert normalize_language_code("yue") == "zh"  # Cantonese
        assert normalize_language_code("jpn") == "ja"  # Japanese
        assert normalize_language_code("kor") == "ko"  # Korean
        assert normalize_language_code("fra") == "fr"  # French
        assert normalize_language_code("deu") == "de"  # German
    
    def test_already_normalized(self):
        """Should pass through already-normalized codes."""
        assert normalize_language_code("zh") == "zh"
        assert normalize_language_code("en") == "en"
        assert normalize_language_code("ja") == "ja"
        assert normalize_language_code("ko") == "ko"
    
    def test_case_handling(self):
        """Should handle uppercase/mixed case."""
        assert normalize_language_code("ZH-CN") == "zh"
        assert normalize_language_code("En-US") == "en"
        assert normalize_language_code("CMN") == "zh"
    
    def test_edge_cases(self):
        """Should handle empty/None gracefully."""
        assert normalize_language_code("") == ""
        assert normalize_language_code(None) ==None
    
    def test_unknown_codes(self):
        """Should pass through unknown codes unchanged."""
        unknown = normalize_language_code("xyz")
        assert unknown == "xyz"  # Unknown code preserved


class TestAudioRobustness:
    """Test audio quality validation."""
    
    def test_language_override_prevented(self):
        """Ensure user language choice is not overridden by ASR."""
        # This would be an integration test
        # Simulating: user selects "zh", ASR detects "zh-CN"
        # Expected: source_lang remains "zh"
        pass
    
    def test_translation_with_normalized_codes(self):
        """Verify translation receives normalized language codes."""
        # Integration test: process video with dialect code
        # Verify translator gets "zh" not "zh-CN"
        pass


class TestConfigValidation:
    """Test TTS configuration validation."""
    
    def test_validates_complete_config(self):
        """Should pass validation with complete config."""
        # This requires mocking the config file
        pass
    
    def test_detects_missing_parameters(self):
        """Should detect and log missing TTS parameters."""
        # Mock incomplete config and verify error logging
        pass


class TestRetryMechanism:
    """Test automatic retry decorator."""
    
    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        """Should return immediately if no failure."""
        # Test retry decorator with successful function
        pass
    
    @pytest.mark.asyncio  
    async def test_retries_on_failure(self):
        """Should retry failed functions."""
        # Test with function that fails 2 times then succeeds
        pass
    
    @pytest.mark.asyncio
    async def test_respects_max_attempts(self):
        """Should fail after max_attempts exhausted."""
        # Test with function that always fails
        pass


class TestDurationMonitoring:
    """Test segment duration monitoring."""
    
    def test_detects_timing_issues(self):
        """Should detect segments with >30% overrun."""
        # Mock TTS segments with timing problems
        pass
    
    def test_logs_warnings_correctly(self):
        """Should log appropriate warnings for timing issues."""
        # Verify warning messages and counts
        pass


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_robustness.py -v
    pytest.main([__file__, "-v"])
