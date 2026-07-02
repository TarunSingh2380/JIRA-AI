"""Diamond / Gold / Solitaire Ring — image-generation prompt studio.

This module powers the "Ring Studio" admin dashboard tab (capability key
``rings``). It ports the CELESTE-style luxury jewelry spec-sheet prompt kit into
a small, self-contained service:

* value banks for every ``{{slot}}`` in the master prompt,
* a deterministic assembler (``build_prompt``) that mirrors the reference Python
  generator — ``seed`` makes any design reproducible,
* batch generation (N unique prompts) for the 1000-image run, and
* optional image rendering through the OpenAI image model when
  ``OPENAI_API_KEY`` is configured (otherwise the assembled prompt is returned
  for manual use).

Everything here is stateless apart from rendered PNGs, which are written under
``app/static/rings/`` so the SPA can display/download them.
"""

from __future__ import annotations

import base64
import json
import logging
import random
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.config import Settings

log = logging.getLogger(__name__)

# ─── Value banks ─────────────────────────────────────────────────────────────
# Randomize across these for variety. Keys match the meta dict returned by
# build_prompt so the UI can render one dropdown per bank.

BANKS: dict[str, list[str]] = {
    "ring_name": [
        "Celeste", "Aurelia", "Seraphine", "Lumière", "Isolde", "Ophelia", "Amara",
        "Vesper", "Elara", "Solene", "Noor", "Liora", "Camélia", "Estelle", "Anaïs",
        "Marisol", "Aveline", "Rosalind", "Thalia", "Belle Étoile",
    ],
    "ring_subtitle": [
        "Solitaire Diamond Ring", "Halo Diamond Ring", "Three-Stone Diamond Ring",
        "Pavé Solitaire Ring", "Vintage-Inspired Diamond Ring", "Cathedral Solitaire Ring",
        "Twisted Band Diamond Ring", "Bezel Solitaire Ring", "Hidden Halo Solitaire",
    ],
    "diamond_shape": [
        "Round Brilliant", "Oval", "Cushion", "Princess", "Emerald", "Pear",
        "Marquise", "Radiant", "Asscher", "Heart",
    ],
    "carat": ["0.50", "0.70", "0.90", "1.00", "1.25", "1.50", "1.75", "2.00", "2.50", "3.00"],
    "color": ["D", "E", "F", "G", "H", "I"],
    "clarity": ["FL", "IF", "VVS1", "VVS2", "VS1", "VS2"],
    "cut": ["Excellent", "Ideal", "Very Good"],
    "metal": [
        "18K White Gold", "18K Yellow Gold", "18K Rose Gold", "Platinum 950",
        "14K White Gold", "14K Yellow Gold", "14K Rose Gold", "Two-Tone White & Rose Gold",
    ],
    "band_width": [
        "1.6 mm (Tapered)", "1.8 mm", "2.0 mm (Tapered)", "2.2 mm", "2.5 mm", "1.5 mm (Knife-Edge)",
    ],
    "setting": [
        "4 Prong Solitaire", "6 Prong Solitaire", "4 Prong Tulip Setting with Hidden Halo",
        "Bezel Setting", "Cathedral Setting", "Halo Setting", "Double Halo", "Pavé Cathedral",
        "Trellis Setting", "Compass-Set (North-South-East-West)",
    ],
    "background": ["ivory/cream", "warm off-white", "soft grey-white", "champagne-tinted white"],
    "accent_color": ["soft gold", "rose-gold", "warm taupe", "muted bronze"],
    "ring_size": ["US 5 (15.7 mm)", "US 6 (16.5 mm)", "US 6.5 (16.9 mm)", "US 7 (17.3 mm)"],
    "motif": ["tulip", "rose", "lily", "orchid", "vine", "laurel"],
}

# (total_diamonds, accent_carat) pairs — paired sensibly.
DIAMOND_PAIRS: list[tuple[int, str]] = [
    (14, "0.14"), (17, "0.18"), (22, "0.24"), (30, "0.35"), (44, "0.50"), (1, "0.00"),
]

# (detail_label, detail_feature) pairs for the DETAIL VIEW thumbnail.
DETAILS: list[tuple[str, str]] = [
    ("HIDDEN HALO", "hidden halo of micro-pavé beneath the center stone"),
    ("GALLERY", "open gallery and prong basket"),
    ("BAND", "pavé-set shoulders"),
    ("PROFILE", "knife-edge band meeting the head"),
    ("BASKET", "diamond-encrusted basket"),
]

INSPIRATIONS: list[str] = [
    "Inspired by the night sky, {name} captures the brilliance of a star in its purest form.",
    "Drawn from morning dew on petals, {name} holds light like the first bloom of spring.",
    "Echoing ocean tides, {name} carries a quiet, endless motion.",
    "Inspired by candlelight, {name} glows soft and timeless.",
]

MOOD: list[str] = [
    "a starfield/galaxy", "a dewy flower petal", "an ocean wave", "a candle flame",
    "frost crystals", "a golden sunrise",
]

HIGHLIGHTS: list[str] = [
    "Tulip setting elevates the diamond for maximum brilliance",
    "Hidden halo adds sparkle from every angle",
    "Pavé-set band for a delicate yet radiant look",
    "Balanced, elegant and timeless design",
    "Cathedral shoulders protect the center stone",
    "Knife-edge band for a sleek modern profile",
    "Comfort-fit interior for all-day wear",
    "Hand-set micro-pavé along the shank",
]

DESCRIPTIONS: list[str] = [
    "A timeless solitaire that celebrates the brilliance of a {shape} diamond. The delicate band with hidden details adds elegance from every angle.",
    "An heirloom-worthy design pairing a luminous {shape} centre with a hand-finished band built to last a lifetime.",
    "Understated and radiant, this ring frames a {shape} diamond in {metal} for effortless everyday glamour.",
]

TEMPLATE = """Create a single high-resolution luxury jewelry catalog spec-sheet image in landscape 4:3 for a women's engagement ring. ONE ring design shown from multiple angles — every view depicts the EXACT SAME ring with consistent proportions, metal, diamond shape and setting.

STYLE: clean premium editorial. Soft {background} studio background, diffused lighting, realistic diamond fire and reflections. Thin {accent_color} hairline panel borders. Elegant serif headings, clean sans-serif body. Photorealistic 3D render, tack-sharp, no clutter.

LAYOUT (composite grid):
- Header top-left: ring name "{ring_name}" in large elegant serif capitals; subtitle "{ring_subtitle}" in spaced small-caps beneath; small diamond glyph accent.
- Description paragraph: "{description}"
- Left spec column with faceted-diamond bullets:
  CENTER DIAMOND — {diamond_shape}, {carat} ct (Approx.), {color} Color / {clarity} Clarity / {cut} Cut
  METAL — {metal}
  BAND WIDTH — {band_width}
  SETTING — {setting}
  TOTAL DIAMONDS — {total_diamonds} (~{accent_carat} ct)
- HERO shot (largest, upper-center): dramatic 3/4 perspective, ring upright, centre stone catching light; band engraved "{ring_name}" with a small "18K" hallmark.
- Right side two stacked panels: angled perspective close-up (top) and upright front elevation (bottom) on white.
- Bottom row of four labeled thumbnails in spaced caps:
  TOP VIEW — from directly above, symmetrical band, centred stone.
  SIDE VIEW — pure profile showing setting height, prongs, band taper.
  FRONT VIEW — upright straight-on elevation.
  DETAIL VIEW ({detail_label}) — macro of the {detail_feature} with fine metalwork and micro-pavé.
- Footer band in three hairline-separated sections:
  INSPIRATION — "{inspiration}" beside a small square {mood_image} mood image.
  RING SIZE — "{ring_size}" beside a tiny line-icon of the ring.
  DESIGN HIGHLIGHTS — 4 bullets: {highlight_1}; {highlight_2}; {highlight_3}; {highlight_4}. Faint single-line {motif} botanical illustration in the far bottom-right corner.

Render metal as realistic {metal}. Diamonds must look like genuine cut gemstones. Balanced, airy, gallery-grade. No text errors, no watermark, no hands."""

# The full ordered list of meta keys the template consumes.
META_KEYS = [
    "ring_name", "ring_subtitle", "description", "diamond_shape", "carat", "color",
    "clarity", "cut", "metal", "band_width", "setting", "total_diamonds", "accent_carat",
    "detail_label", "detail_feature", "background", "accent_color", "inspiration",
    "mood_image", "ring_size", "highlight_1", "highlight_2", "highlight_3", "highlight_4",
    "motif",
]


# ─── Prompt assembly ─────────────────────────────────────────────────────────

def list_banks() -> dict[str, Any]:
    """Everything the UI needs to render the design form (dropdown options)."""
    return {
        "banks": BANKS,
        "diamond_pairs": [{"total_diamonds": t, "accent_carat": a} for t, a in DIAMOND_PAIRS],
        "details": [{"detail_label": lbl, "detail_feature": feat} for lbl, feat in DETAILS],
        "inspirations": INSPIRATIONS,
        "mood_image": MOOD,
        "highlights": HIGHLIGHTS,
        "descriptions": DESCRIPTIONS,
    }


def build_prompt(
    seed: Optional[int] = None,
    overrides: Optional[dict[str, Any]] = None,
) -> tuple[str, dict[str, Any]]:
    """Assemble one master prompt.

    ``seed`` makes the random picks reproducible (same seed → same design).
    ``overrides`` pins any meta field(s) to explicit values; everything else is
    randomized. Unknown override keys are ignored.
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    overrides = {k: v for k, v in (overrides or {}).items() if v not in (None, "")}

    def pick(key: str) -> str:
        if key in overrides:
            return str(overrides[key])
        return rng.choice(BANKS[key])

    name = pick("ring_name")

    if "total_diamonds" in overrides or "accent_carat" in overrides:
        total = overrides.get("total_diamonds")
        acc = overrides.get("accent_carat")
        if total is None or acc is None:
            base_total, base_acc = rng.choice(DIAMOND_PAIRS)
            total = base_total if total is None else total
            acc = base_acc if acc is None else acc
    else:
        total, acc = rng.choice(DIAMOND_PAIRS)

    dlabel = overrides.get("detail_label")
    dfeat = overrides.get("detail_feature")
    if dlabel is None or dfeat is None:
        base_label, base_feat = rng.choice(DETAILS)
        dlabel = base_label if dlabel is None else dlabel
        dfeat = base_feat if dfeat is None else dfeat

    shape = pick("diamond_shape")
    metal = pick("metal")

    if all(f"highlight_{i}" in overrides for i in range(1, 5)):
        hi = [str(overrides[f"highlight_{i}"]) for i in range(1, 5)]
    else:
        hi = rng.sample(HIGHLIGHTS, 4)
        for i in range(1, 5):
            if f"highlight_{i}" in overrides:
                hi[i - 1] = str(overrides[f"highlight_{i}"])

    description = overrides.get("description") or rng.choice(DESCRIPTIONS).format(
        shape=shape.lower(), metal=metal.lower()
    )
    inspiration = overrides.get("inspiration") or rng.choice(INSPIRATIONS).format(name=name)

    fields: dict[str, Any] = {
        "ring_name": name,
        "ring_subtitle": pick("ring_subtitle"),
        "description": description,
        "diamond_shape": shape,
        "carat": pick("carat"),
        "color": pick("color"),
        "clarity": pick("clarity"),
        "cut": pick("cut"),
        "metal": metal,
        "band_width": pick("band_width"),
        "setting": pick("setting"),
        "total_diamonds": total,
        "accent_carat": acc,
        "detail_label": dlabel,
        "detail_feature": dfeat,
        "background": pick("background"),
        "accent_color": pick("accent_color"),
        "inspiration": inspiration,
        "mood_image": overrides.get("mood_image") or rng.choice(MOOD),
        "ring_size": pick("ring_size"),
        "highlight_1": hi[0],
        "highlight_2": hi[1],
        "highlight_3": hi[2],
        "highlight_4": hi[3],
        "motif": pick("motif"),
    }
    return TEMPLATE.format(**fields), fields


def generate_batch(count: int, start_seed: int = 0) -> list[dict[str, Any]]:
    """Generate ``count`` reproducible prompts (seed = start_seed + index).

    Returns a list of ``{index, seed, prompt, meta}`` dicts — the same shape as
    the reference ``ring_prompts.jsonl`` rows.
    """
    count = max(1, min(int(count), 1000))
    out: list[dict[str, Any]] = []
    for i in range(count):
        seed = start_seed + i
        prompt, meta = build_prompt(seed=seed)
        out.append({"index": i, "seed": seed, "prompt": prompt, "meta": meta})
    return out


def batch_to_jsonl(rows: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"


# ─── Image rendering (optional) ──────────────────────────────────────────────

# gpt-image-1 landscape size closest to the 4:3 CELESTE reference.
_IMAGE_SIZE = "1536x1024"


def _rings_static_dir() -> Path:
    d = Path(__file__).resolve().parent / "static" / "rings"
    d.mkdir(parents=True, exist_ok=True)
    return d


class RingImageResult(BaseModel):
    status: str  # "rendered" | "not_configured" | "error"
    prompt: str
    meta: dict[str, Any] = Field(default_factory=dict)
    seed: Optional[int] = None
    image_url: Optional[str] = None
    filename: Optional[str] = None
    model: Optional[str] = None
    message: Optional[str] = None


def render_image(
    settings: Settings,
    prompt: str,
    meta: dict[str, Any],
    seed: Optional[int] = None,
    *,
    model: str = "gpt-image-1",
) -> RingImageResult:
    """Render the assembled prompt to a PNG via the OpenAI image model.

    If ``OPENAI_API_KEY`` is not configured this is a graceful no-op that returns
    the prompt with ``status="not_configured"`` so the operator can paste it into
    the image model manually. Any API/SDK error is captured (never raised) so the
    dashboard can surface it inline.
    """
    if not settings.openai_api_key:
        return RingImageResult(
            status="not_configured",
            prompt=prompt,
            meta=meta,
            seed=seed,
            message=(
                "OPENAI_API_KEY is not set — image rendering is disabled. Copy the "
                "prompt above into ChatGPT's image model to generate this design."
            ),
        )

    try:
        from openai import OpenAI
    except ImportError:
        return RingImageResult(
            status="error", prompt=prompt, meta=meta, seed=seed,
            message="The 'openai' package is not installed on the server.",
        )

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.images.generate(
            model=model,
            prompt=prompt,
            size=_IMAGE_SIZE,
            n=1,
        )
        b64 = resp.data[0].b64_json
        if not b64:
            # Some models/endpoints return a URL instead of base64.
            url = getattr(resp.data[0], "url", None)
            if url:
                return RingImageResult(
                    status="rendered", prompt=prompt, meta=meta, seed=seed,
                    image_url=url, model=model,
                    message="Rendered by the provider (external URL).",
                )
            raise RuntimeError("Image response contained no data")

        name = meta.get("ring_name", "ring")
        safe = "".join(c for c in str(name) if c.isalnum()) or "ring"
        filename = f"{safe.lower()}-{int(time.time())}-{uuid.uuid4().hex[:6]}.png"
        path = _rings_static_dir() / filename
        path.write_bytes(base64.b64decode(b64))
        log.info("Ring Studio rendered %s (%d bytes)", filename, path.stat().st_size)
        return RingImageResult(
            status="rendered", prompt=prompt, meta=meta, seed=seed,
            image_url=f"/static/rings/{filename}", filename=filename, model=model,
        )
    except Exception as exc:  # noqa: BLE001 - surface, don't crash the request
        log.exception("Ring Studio image render failed")
        return RingImageResult(
            status="error", prompt=prompt, meta=meta, seed=seed,
            message=f"Image render failed: {exc}",
        )


# ─── Pydantic request/response models ────────────────────────────────────────

class PromptRequest(BaseModel):
    seed: Optional[int] = None
    overrides: dict[str, Any] = Field(default_factory=dict)


class PromptResponse(BaseModel):
    prompt: str
    meta: dict[str, Any]
    seed: Optional[int] = None


class BatchRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=1000)
    start_seed: int = 0


class ImageRequest(BaseModel):
    # Either supply a prompt directly, or seed/overrides to assemble one.
    prompt: Optional[str] = None
    seed: Optional[int] = None
    overrides: dict[str, Any] = Field(default_factory=dict)
