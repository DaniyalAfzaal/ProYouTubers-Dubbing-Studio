from deep_translator import (
    GoogleTranslator,
    ChatGptTranslator,
    MicrosoftTranslator,
    PonsTranslator,
    LingueeTranslator,
    MyMemoryTranslator,
    YandexTranslator,
    PapagoTranslator,
    DeeplTranslator,
    QcriTranslator,
    single_detection,
    batch_detection,
)  # any of them is usable but be aware that some require API keys
from common_schemas.models import ASRResponse, TranslateRequest, Segment
from common_schemas.service_utils import get_service_logger
import json, sys, os, contextlib, logging, time
from typing import Any


def normalize_lang_code(lang: str) -> str:
    """Normalize language codes for DeepL compatibility.
    DeepL only accepts base ISO 639-1 codes (e.g., 'zh', not 'zh-CN')."""
    if not lang:
        return lang
    # Strip region/script suffixes (zh-CN → zh, pt-BR → pt, etc.)
    return lang.split('-')[0].split('_')[0].lower()

def build_translator(req: TranslateRequest, logger: logging.Logger) -> Any:
    """Build translator instance based on provider."""
    # Map provider names to translator classes
    translators = {
        "google": GoogleTranslator,
        "deepl": DeeplTranslator,
        "deepltranslator": DeeplTranslator,  # ADD: Support 'DeeplTranslator' name from UI
        "deep_translator": DeeplTranslator,  # ADD: Support 'deep_translator' name
        "microsoft": MicrosoftTranslator,
        "chatgpt": ChatGptTranslator,
        "pons": PonsTranslator,
        "linguee": LingueeTranslator,
        "mymemory": MyMemoryTranslator,
        "yandex": YandexTranslator,
        "papago": PapagoTranslator,
        "qcri": QcriTranslator,
    }
    
    # FIX: Extract provider from request
    extra_0 = req.extra or {}
    provider = extra_0.get("model_name", "google").lower()

    # FIX: Get translator class
    TranslatorCls = translators.get(provider, GoogleTranslator)
    if TranslatorCls is GoogleTranslator and provider not in translators:
        logger.warning("Unknown translator provider '%s'. Falling back to Google Translator.", provider)
    logger.info("Using provider=%s for translation.", TranslatorCls.__name__)

    # FIX: Normalize language codes for DeepL BEFORE setting kwargs
    source_lang = req.source_lang
    target_lang = req.target_lang
    if provider in ["deepl", "deepltranslator", "deep_translator"]:
        source_lang = normalize_lang_code(source_lang)
        target_lang = normalize_lang_code(target_lang)
        logger.info(f"Normalized for DeepL: {req.source_lang} → {source_lang}, {req.target_lang} → {target_lang}")

    # Ensure source/target are present unless explicitly provided
    kwargs = {}
    kwargs.setdefault("source", source_lang or "auto")
    kwargs.setdefault("target", target_lang)

    # Optionally source API keys from env if not provided
    if provider in ["deepl", "deepltranslator", "deep_translator"]:
        api_key = os.getenv("DEEPL_API_KEY")
        if api_key:
            kwargs.setdefault("api_key", api_key)
            # FIX: DeepL Free API requires use_free_api=True for keys ending with :fx
            if api_key.endswith(":fx"):
                kwargs.setdefault("use_free_api", True)
                logger.info("🆓 Using DeepL FREE API (key ends with :fx)")
            else:
                kwargs.setdefault("use_free_api", False)
                logger.info("💎 Using DeepL PRO API")
        else:
            logger.warning("⚠️ DeepL selected but DEEPL_API_KEY not set! Falling back to Google Translate (free, excellent quality)")
            # Fall back to Google Translator (free, no API key needed, excellent quality)
            TranslatorCls = GoogleTranslator
            logger.info(f"Using fallback provider={TranslatorCls.__name__}")
    elif provider == "microsoft":
        kwargs.setdefault("api_key", os.getenv("AZURE_TRANSLATOR_KEY"))
        region = os.getenv("AZURE_TRANSLATOR_REGION")
        if region is not None:
            kwargs.setdefault("region", region)
    elif provider == "chatgpt":
        kwargs.setdefault("api_key", os.getenv("OPENAI_API_KEY"))
        # Model can be passed via provider_kwargs or env
        if "model" not in kwargs and os.getenv("OPENAI_MODEL"):
            kwargs["model"] = os.getenv("OPENAI_MODEL")

    logger.debug("Translator kwargs=%s", {k: ("***" if "key" in k else v) for k, v in kwargs.items()})
    return TranslatorCls(**kwargs)

if __name__ == "__main__":

    req = TranslateRequest(**json.loads(sys.stdin.read()))
    # Read from extra config (default to INFO if not set)
    log_level = req.extra.get("log_level", "INFO").upper()
    log_level = getattr(logging, log_level, logging.INFO)
    # Configure logging
    logger = get_service_logger("translation.deep_translator", log_level)

    out = ASRResponse()

    if req.source_lang == "zh":
        req.source_lang = "zh-CN" # or "zh-TW" based on your needs
    if req.target_lang == "zh":
        req.target_lang = "zh-CN" # or "zh-TW" based on your needs

    with contextlib.redirect_stdout(sys.stderr):
        start = time.perf_counter()
        logger.info(
            "Starting translation run segments=%d source=%s target=%s",
            len(req.segments or []),
            req.source_lang,
            req.target_lang,
        )

        translator = build_translator(req, logger)

        for i, segment in enumerate(req.segments):
            seg_start = time.perf_counter()
            try:
                translated_text = translator.translate(segment.text)
            except Exception as exc:
                # Fallback to Google if selected provider fails
                logger.warning(
                    "Provider translation failed for segment=%d (%s). Falling back to Google. error=%s",
                    i,
                    type(exc).__name__,
                    exc,
                )
                fallback = GoogleTranslator(source=getattr(req, "source_lang", None) or "auto",
                                            target=req.target_lang)
                translated_text = fallback.translate(segment.text)

            out.segments.append(Segment(
                start=segment.start,
                end=segment.end,
                text=translated_text,
                speaker_id=segment.speaker_id,
                lang=req.target_lang
            ))
            out.language = req.target_lang
            logger.info(
                "Translated segment %d duration=%.2fs chars_in=%d",
                i,
                time.perf_counter() - seg_start,
                len(segment.text or ""),
            )
        logger.info(
            "Completed translation run in %.2fs (segments=%d).",
            time.perf_counter() - start,
            len(out.segments),
        )

    sys.stdout.write(out.model_dump_json() + "\n")
    sys.stdout.flush()
