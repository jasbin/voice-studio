"""Split long scripts into chunks the models handle well, and join the audio back with natural pauses."""
import re

import numpy as np

MAX_CHARS = 400
SENTENCE_PAUSE_MS = 250
PARAGRAPH_PAUSE_MS = 600


def _split_long(sentence, max_chars):
    """Split a single over-long sentence at commas/semicolons, then at spaces as a last resort."""
    parts, current = [], ""
    for piece in re.split(r"(?<=[,;:])\s+", sentence):
        while len(piece) > max_chars:
            cut = piece.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            parts.append(piece[:cut].strip())
            piece = piece[cut:].strip()
        if current and len(current) + len(piece) + 1 > max_chars:
            parts.append(current)
            current = piece
        else:
            current = f"{current} {piece}".strip()
    if current:
        parts.append(current)
    return parts


def chunk_text(text, max_chars=MAX_CHARS):
    """Return [(chunk_text, pause_after_ms)] grouped by paragraph and sentence."""
    chunks = []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    for paragraph in paragraphs:
        paragraph = re.sub(r"\s+", " ", paragraph)
        sentences = []
        for s in re.split(r"(?<=[.!?…])\s+", paragraph):
            sentences.extend(_split_long(s, max_chars) if len(s) > max_chars else [s])

        current = ""
        for s in sentences:
            if current and len(current) + len(s) + 1 > max_chars:
                chunks.append((current, SENTENCE_PAUSE_MS))
                current = s
            else:
                current = f"{current} {s}".strip()
        if current:
            chunks.append((current, PARAGRAPH_PAUSE_MS))
    return chunks


def join_audio(pieces, sr):
    """pieces: [(waveform, pause_after_ms)] -> one waveform. No trailing pause after the last piece."""
    out = []
    for i, (wav, pause_ms) in enumerate(pieces):
        out.append(np.asarray(wav, dtype=np.float32).reshape(-1))
        if i < len(pieces) - 1:
            out.append(np.zeros(int(sr * pause_ms / 1000), dtype=np.float32))
    return np.concatenate(out) if out else np.zeros(0, dtype=np.float32)
