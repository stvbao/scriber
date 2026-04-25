"""Text translation to English using NLLB-200 (facebook/nllb-200-distilled-600M)."""
from __future__ import annotations
import dataclasses
from scriber.core.transcribe import Segment

MODEL_ID = "facebook/nllb-200-distilled-600M"

# Whisper language code → NLLB BCP-47 code
_LANG_MAP: dict[str, str] = {
    "af": "afr_Latn", "am": "amh_Ethi", "ar": "arb_Arab",
    "az": "azj_Latn", "bg": "bul_Cyrl", "bn": "ben_Beng",
    "bs": "bos_Latn", "ca": "cat_Latn", "cs": "ces_Latn",
    "cy": "cym_Latn", "da": "dan_Latn", "de": "deu_Latn",
    "el": "ell_Grek", "en": "eng_Latn", "es": "spa_Latn",
    "et": "est_Latn", "fa": "pes_Arab", "fi": "fin_Latn",
    "fr": "fra_Latn", "ga": "gle_Latn", "gl": "glg_Latn",
    "gu": "guj_Gujr", "he": "heb_Hebr", "hi": "hin_Deva",
    "hr": "hrv_Latn", "hu": "hun_Latn", "hy": "hye_Armn",
    "id": "ind_Latn", "is": "isl_Latn", "it": "ita_Latn",
    "ja": "jpn_Jpan", "ka": "kat_Geor", "kk": "kaz_Cyrl",
    "km": "khm_Khmr", "ko": "kor_Hang", "lt": "lit_Latn",
    "lv": "lvs_Latn", "mk": "mkd_Cyrl", "ml": "mal_Mlym",
    "mn": "khk_Cyrl", "mr": "mar_Deva", "ms": "zsm_Latn",
    "mt": "mlt_Latn", "my": "mya_Mymr", "nl": "nld_Latn",
    "no": "nob_Latn", "pl": "pol_Latn", "ps": "pbt_Arab",
    "pt": "por_Latn", "ro": "ron_Latn", "ru": "rus_Cyrl",
    "si": "sin_Sinh", "sk": "slk_Latn", "sl": "slv_Latn",
    "sq": "als_Latn", "sr": "srp_Cyrl", "sv": "swe_Latn",
    "sw": "swh_Latn", "ta": "tam_Taml", "te": "tel_Telu",
    "tg": "tgk_Cyrl", "th": "tha_Thai", "tr": "tur_Latn",
    "uk": "ukr_Cyrl", "ur": "urd_Arab", "uz": "uzn_Latn",
    "vi": "vie_Latn", "zh": "zho_Hans",
}

_pipeline = None


def nllb_lang(whisper_lang: str) -> str:
    return _LANG_MAP.get(whisper_lang, "srp_Cyrl")


def translate_segments(
    segments: list[Segment],
    src_lang: str,
) -> list[Segment]:
    global _pipeline

    nllb_src = nllb_lang(src_lang)
    if nllb_src == "eng_Latn":
        return segments

    if _pipeline is None:
        from transformers import pipeline
        _pipeline = pipeline(
            "translation",
            model=MODEL_ID,
            device="cpu",
        )

    texts = [seg.text for seg in segments]
    results = _pipeline(
        texts,
        src_lang=nllb_src,
        tgt_lang="eng_Latn",
        max_length=512,
        batch_size=16,
    )

    return [
        dataclasses.replace(seg, text=r["translation_text"])
        for seg, r in zip(segments, results)
    ]
