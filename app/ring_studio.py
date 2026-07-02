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
from concurrent.futures import ThreadPoolExecutor
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


# ─── Per-view image rendering (optional) ─────────────────────────────────────
# Instead of one composite spec-sheet, we render FIVE separate images — one per
# camera view — all depicting the EXACT SAME ring. Each view prompt restates the
# full ring spec so the design stays identical across the five renders.

# gpt-image-1 square size — one ring per frame reads best in a square crop.
_IMAGE_SIZE = "1024x1024"

# (view key, display label, camera/view instruction). {slots} are filled from meta.
VIEWS: list[tuple[str, str, str]] = [
    ("hero", "Hero 3/4 View",
     "a dramatic 3/4 perspective of the ring standing upright, the centre stone "
     "catching the light and the band sweeping toward the viewer; the band subtly "
     "engraved with \"{ring_name}\" and a small \"18K\" hallmark"),
    ("top", "Top View",
     "the ring seen from directly above, the band curving symmetrically and the "
     "centre stone centred and facing straight up"),
    ("side", "Side View",
     "a pure side profile of the ring showing the setting height, the prongs, and "
     "the band taper"),
    ("front", "Front View",
     "an upright, straight-on front elevation of the ring, centre stone facing the "
     "viewer"),
    ("detail", "Detail View",
     "an extreme macro close-up of the {detail_feature}, showing the fine metalwork "
     "and hand-set micro-pavé"),
]

VIEW_TEMPLATE = """Create a single high-resolution, photorealistic 3D product render of ONE women's engagement ring — the "{ring_name}" ({ring_subtitle}).

THE RING (keep every detail identical across all renders of this design):
- Centre diamond: {diamond_shape} cut, {carat} ct, {color} colour / {clarity} clarity / {cut} cut.
- Metal: {metal}. Band width: {band_width}. Setting: {setting}.
- Accent stones: {total_diamonds} diamonds (~{accent_carat} ct total), hand-set micro-pavé.

VIEW: {view_instruction}.

STYLE: luxury jewelry catalog. Soft {background} studio background, gentle diffused lighting, realistic diamond fire, subtle reflections and caustics. Tack-sharp focus, the single ring centred in frame, generous negative space, no clutter. Render the metal as realistic {metal}; every diamond must look like a genuine cut gemstone. No text, no labels, no watermark, no hands, no other objects."""


def _rings_static_dir() -> Path:
    d = Path(__file__).resolve().parent / "static" / "rings"
    d.mkdir(parents=True, exist_ok=True)
    return d


def build_view_prompts(meta: dict[str, Any]) -> list[dict[str, str]]:
    """Build the five single-view prompts for one ring design (same meta)."""
    out: list[dict[str, str]] = []
    for view, label, instruction in VIEWS:
        view_instruction = instruction.format(**meta)
        prompt = VIEW_TEMPLATE.format(view_instruction=view_instruction, **meta)
        out.append({"view": view, "label": label, "prompt": prompt})
    return out


class RingImageResult(BaseModel):
    status: str  # "rendered" | "not_configured" | "error"
    view: Optional[str] = None
    label: Optional[str] = None
    prompt: str
    image_url: Optional[str] = None
    filename: Optional[str] = None
    message: Optional[str] = None


class RingViewsResult(BaseModel):
    status: str  # "rendered" | "partial" | "not_configured" | "error"
    meta: dict[str, Any] = Field(default_factory=dict)
    seed: Optional[int] = None
    model: Optional[str] = None
    views: list[RingImageResult] = Field(default_factory=list)
    message: Optional[str] = None


def _render_one(
    settings: Settings, item: dict[str, str], name_hint: str, model: str
) -> RingImageResult:
    """Render a single view prompt to a PNG. Errors are captured, not raised."""
    view, label, prompt = item["view"], item["label"], item["prompt"]
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.images.generate(model=model, prompt=prompt, size=_IMAGE_SIZE, n=1)
        b64 = resp.data[0].b64_json
        if not b64:
            url = getattr(resp.data[0], "url", None)
            if url:
                return RingImageResult(status="rendered", view=view, label=label,
                                       prompt=prompt, image_url=url)
            raise RuntimeError("Image response contained no data")
        safe = "".join(c for c in str(name_hint) if c.isalnum()) or "ring"
        filename = f"{safe.lower()}-{view}-{int(time.time())}-{uuid.uuid4().hex[:6]}.png"
        path = _rings_static_dir() / filename
        path.write_bytes(base64.b64decode(b64))
        log.info("Ring Studio rendered %s (%d bytes)", filename, path.stat().st_size)
        return RingImageResult(status="rendered", view=view, label=label, prompt=prompt,
                               image_url=f"/static/rings/{filename}", filename=filename)
    except Exception as exc:  # noqa: BLE001 - surface per-view, don't crash the batch
        log.exception("Ring Studio %s view render failed", view)
        return RingImageResult(status="error", view=view, label=label, prompt=prompt,
                               message=f"Render failed: {exc}")


def render_ring_views(
    settings: Settings,
    meta: dict[str, Any],
    seed: Optional[int] = None,
    *,
    model: str = "gpt-image-1",
) -> RingViewsResult:
    """Render the five per-view images for one ring design.

    If ``OPENAI_API_KEY`` is not configured this is a graceful no-op that returns
    the five view prompts (status ``not_configured``) for manual use. Otherwise
    the five views are rendered in parallel and any per-view error is captured so
    the dashboard can show the rest.
    """
    items = build_view_prompts(meta)

    if not settings.openai_api_key:
        views = [
            RingImageResult(status="not_configured", view=it["view"], label=it["label"],
                            prompt=it["prompt"])
            for it in items
        ]
        return RingViewsResult(
            status="not_configured", meta=meta, seed=seed, views=views,
            message=("OPENAI_API_KEY is not set — image rendering is disabled. Copy each "
                     "view prompt below into ChatGPT's image model to generate it."),
        )

    name_hint = str(meta.get("ring_name", "ring"))
    with ThreadPoolExecutor(max_workers=len(items)) as pool:
        views = list(pool.map(lambda it: _render_one(settings, it, name_hint, model), items))

    rendered = sum(1 for v in views if v.status == "rendered")
    if rendered == len(views):
        overall = "rendered"
    elif rendered == 0:
        overall = "error"
    else:
        overall = "partial"
    message = None
    if overall != "rendered":
        first_err = next((v.message for v in views if v.status == "error" and v.message), None)
        message = first_err
    return RingViewsResult(status=overall, meta=meta, seed=seed, model=model,
                           views=views, message=message)


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
    # Supply the ``meta`` of an already-generated design (preferred, keeps the
    # exact ring), or seed/overrides to assemble a fresh one first.
    meta: Optional[dict[str, Any]] = None
    seed: Optional[int] = None
    overrides: dict[str, Any] = Field(default_factory=dict)
