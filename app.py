"""Voice Studio: a local TTS app with Qwen3-TTS preset voices, voice design, and voice cloning (Qwen or Chatterbox).

Start with ./run.sh, then open http://127.0.0.1:7860
"""
import html
import os
import time
from datetime import datetime
from pathlib import Path

import gradio as gr
import soundfile as sf

import ui_theme as ui
import voice_library as lib
from engines import chatterbox_client, qwen_engine as qwen
from text_utils import chunk_text, join_audio

CLONE_ENGINES = ["Qwen 1.7B", "Qwen 0.6B", "Chatterbox Turbo", "Chatterbox Original"]
SPEAKER_CHOICES = [(f"{name} · {desc}", sid) for sid, name, desc in qwen.SPEAKERS]
SPEAKER_NAMES = {sid: name for sid, name, _ in qwen.SPEAKERS}
CUSTOM_STYLE = "Custom"
PREVIEW_TEXT = ("Hi, I'm {name}. Today we're breaking down how large language models actually work, "
                "step by step, in plain English.")

_archived = {}  # Gradio's temp path for a recording -> its copy under data/recordings/


# ---------- shared rendering ----------

def progress_html(done, total, elapsed, current=""):
    pct = 100 * done / total if total else 0
    fill = f'<div class="vs-progress-fill" style="width:{pct:.0f}%"></div>' if done else \
        '<div class="vs-progress-fill indeterminate"></div>'
    label = f"Part {min(done + 1, total)} of {total}" if done < total else "Finishing"
    snippet = html.escape(current[:120])
    return (f'<div class="vs-progress"><div class="vs-progress-top"><b>Generating · {label}</b>'
            f'<span>{elapsed:.0f}s</span></div><div class="vs-progress-track">{fill}</div>'
            + (f"<p>{snippet}</p>" if snippet else "") + "</div>")


def render(text, voice_label, synth, settings):
    """Generator: yields ("progress", html) per chunk, then ("done", (path, status, first))."""
    text = (text or "").strip()
    if not text:
        raise gr.Error("Type or paste a script first.")
    chunks = chunk_text(text)
    pieces, sr, first = [], None, None
    start = time.time()
    try:
        for i, (chunk, pause) in enumerate(chunks):
            yield "progress", progress_html(i, len(chunks), time.time() - start, chunk)
            wav, sr = synth(chunk)
            wav = lib.normalize(wav, sr, peak=None, trim=True)
            pieces.append((wav, pause))
            if first is None:
                first = (wav, chunk, sr)
        yield "progress", progress_html(len(chunks), len(chunks), time.time() - start)
    except gr.Error:
        raise
    except Exception as e:
        raise gr.Error(f"{type(e).__name__}: {e}")

    audio = lib.normalize(join_audio(pieces, sr), sr)
    path = lib.new_export_path(voice_label)
    sf.write(path, audio, sr)
    seconds = len(audio) / sr
    lib.write_export_info(path, {
        "voice": voice_label,
        "settings": settings,
        "text": text,
        "duration": round(seconds, 1),
        "created": datetime.now().isoformat(timespec="seconds"),
    })
    status = (f"**Done:** {seconds:.1f}s of audio in {time.time() - start:.0f}s "
              f"({len(chunks)} part{'s' if len(chunks) > 1 else ''}). Saved to `{path.relative_to(lib.DATA_DIR.parent)}`")
    yield "done", (str(path), status, first)


def stream(events, extra=()):
    """Turn render()'s events into Gradio output tuples: (audio, status, download, *extra)."""
    for kind, payload in events:
        if kind == "progress":
            yield (gr.skip(), payload, gr.skip(), *[gr.skip() for _ in extra])
        else:
            path, status, first = payload
            yield (gr.Audio(value=path, visible=True), status, gr.DownloadButton(value=path, visible=True),
                   *[f(first) for f in extra])


def voice_dropdown(selected=None):
    choices = lib.list_voices()
    values = [slug for _, slug in choices]
    return gr.Dropdown(choices=choices, value=selected if selected in values else (values[0] if values else None))


# ---------- tab handlers ----------

def generate_preset(text, speaker, style, size):
    yield from stream(render(
        text, SPEAKER_NAMES[speaker],
        lambda chunk: qwen.preset_voice(chunk, speaker, style if size == "1.7B" else None, size),
        {"engine": f"Qwen CustomVoice {size}", "speaker": speaker, "style": style if size == "1.7B" else None}))


def preview_voice(speaker, progress=gr.Progress()):
    """Sample of a preset voice. Generated once with the Tech explainer style, then served from data/previews/."""
    path = lib.PREVIEWS_DIR / f"{speaker}.wav"
    if not path.exists():
        progress(0, desc=f"Creating a one-time preview of {SPEAKER_NAMES[speaker]}")
        try:
            wav, sr = qwen.preset_voice(PREVIEW_TEXT.format(name=SPEAKER_NAMES[speaker]), speaker,
                                        qwen.STYLE_PRESETS["Tech explainer"], "1.7B")
        except Exception as e:
            raise gr.Error(f"{type(e).__name__}: {e}")
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(path, lib.normalize(wav, sr, trim=True), sr)
    return str(path)


def preview_saved(slug):
    return lib.get_voice(slug)[0] if slug else None


def pick_style(preset):
    return gr.Textbox(value=qwen.STYLE_PRESETS.get(preset, ""), interactive=True)


def generate_design(text, description):
    if not (description or "").strip():
        raise gr.Error("Describe the voice you want.")

    def keep_sample(first):
        sample = lib.temp_wav()
        sf.write(sample, first[0], first[2])
        return {"path": sample, "text": first[1], "description": description}

    yield from stream(render(text, "designed-voice", lambda chunk: qwen.design_voice(chunk, description),
                             {"engine": "Qwen VoiceDesign 1.7B", "description": description}), extra=[keep_sample])


def save_designed(name, last):
    if not last:
        raise gr.Error("Generate with a designed voice first, then save it.")
    try:
        slug = lib.save_voice(name, last["path"], last["text"], "designed")
    except ValueError as e:
        raise gr.Error(str(e))
    return f"Saved **{name.strip()}** to My Voices. Use it from the Clone tab.", voice_dropdown(slug)


def archived_copy(recording):
    if recording not in _archived:
        _archived[recording] = str(lib.archive_recording(recording))
    return _archived[recording]


def resolve_reference(source, saved_slug, recording, transcript, no_transcript):
    """(reference wav path, transcript or None, label) for the Clone tab's current inputs."""
    if source == "Saved voice":
        if not saved_slug:
            raise gr.Error("No saved voice selected. Record one first, or pick 'New recording'.")
        ref, meta = lib.get_voice(saved_slug)
        return ref, meta.get("transcript") or None, meta["name"]
    if not recording:
        raise gr.Error("Record or upload your voice first.")
    return archived_copy(recording), None if no_transcript else transcript, "new-recording"


def generate_clone(text, engine, source, saved_slug, recording, transcript, no_transcript,
                   exaggeration, cfg_weight):
    ref, ref_text, label = resolve_reference(source, saved_slug, recording, transcript, no_transcript)
    settings = {"engine": engine, "reference": ref}
    if engine.startswith("Qwen"):
        size = engine.split()[1]
        settings["transcript"] = ref_text
        synth = lambda chunk: qwen.clone_voice(chunk, ref, ref_text, size)  # noqa: E731
    else:
        model = "turbo" if engine == "Chatterbox Turbo" else "original"
        if model == "original":
            settings.update(exaggeration=exaggeration, cfg_weight=cfg_weight)
        synth = lambda chunk: chatterbox_client.generate(chunk, ref, model, exaggeration, cfg_weight,  # noqa: E731
                                                         qwen.get_device())
    yield from stream(render(text, label, synth, settings))


def save_recording(name, recording, transcript, no_transcript):
    if not recording:
        raise gr.Error("Record or upload your voice first.")
    try:
        slug = lib.save_voice(name, archived_copy(recording), None if no_transcript else transcript, "recorded")
    except ValueError as e:
        raise gr.Error(str(e))
    return f"Saved **{name.strip()}** to My Voices.", voice_dropdown(slug), gr.Radio(value="Saved voice")


def toggle_source(source):
    return gr.Group(visible=source == "Saved voice"), gr.Group(visible=source != "Saved voice")


def toggle_engine(engine):
    return gr.Group(visible=engine == "Chatterbox Original"), gr.HTML(visible=engine == "Chatterbox Turbo")


def set_compute(device):
    try:
        qwen.set_device(device)
    except ValueError as e:
        raise gr.Error(str(e))
    gr.Info(f"Using {qwen.device_label(device)}. Models reload on first use.")


def busy_button():
    """Disable the button, hide the previous take and show a starting card straight away."""
    return (gr.Button(value="Generating…", interactive=False), gr.Audio(visible=False),
            progress_html(0, 1, 0).replace("Part 1 of 1", "Starting"), gr.DownloadButton(visible=False))


def idle_button():
    return gr.Button(value="Generate narration", interactive=True)


def refresh_clone_tab():
    has_voices = bool(lib.list_voices())
    source = "Saved voice" if has_voices else "New recording"
    return (voice_dropdown(), gr.Radio(value=source), *toggle_source(source))


# ---------- library ----------

PAGE_SIZE = 20


def take_label(e):
    """Two lines: the start of the script, then voice · length · date (styled via CSS ::first-line)."""
    words = " ".join(e["text"].split())
    snippet = words if len(words) <= 60 else words[:60].rsplit(" ", 1)[0] + "…"
    when = datetime.fromisoformat(e["created"]).strftime("%b %-d, %H:%M")
    return f"{snippet or 'Untitled take'}\n{e['voice']} · {e['duration']:.1f}s · {when}"


def find_takes(query):
    """All exports matching the search (script, voice, engine or date), newest first."""
    exports = lib.list_exports()
    terms = (query or "").lower().split()
    if not terms:
        return exports, len(exports)
    def haystack(e):
        when = datetime.fromisoformat(e["created"]).strftime("%b %-d %Y %H:%M")
        return " ".join([e["text"], e["voice"], e["engine"], when, e["created"]]).lower()
    return [e for e in exports if all(t in haystack(e) for t in terms)], len(exports)


def takes_view(query, limit, selected=None):
    """Radio list (first `limit` matches), empty-state, and counter for the current search."""
    matches, total = find_takes(query)
    shown = matches[:limit]
    values = [e["path"] for e in shown]
    takes_list = gr.Radio(choices=[(take_label(e), e["path"]) for e in shown],
                          value=selected if selected in values else None, visible=bool(shown))
    if not total:
        empty = '<p class="vs-hint">No takes yet. Generate something in the Studio tab.</p>'
    elif not matches:
        empty = f'<p class="vs-hint">No takes match “{html.escape(query.strip())}”.</p>'
    else:
        empty = ""
    more = len(matches) > len(shown)
    if query and query.strip():
        text = f"{len(matches)} match{'es' if len(matches) != 1 else ''}"
    else:
        text = f"{total} take{'s' if total != 1 else ''}"
    if more:
        text = f"Showing {len(shown)} of {len(matches)}"
    counter = (f'<p class="vs-count" data-more="{int(more)}" data-total="{total}">{text}'
               + (" · scroll for more" if more else "") + "</p>") if matches else ""
    return takes_list, empty, counter, limit


def load_library(query=""):
    return *takes_view(query, PAGE_SIZE), *clear_selection()


def load_more(query, limit, selected):
    return takes_view(query, limit + PAGE_SIZE, selected)


def clear_selection():
    return None, "_Select a take to play it._", None, gr.Button(interactive=False), gr.DownloadButton(visible=False)


def select_take(path):
    export = next((e for e in lib.list_exports() if e["path"] == path), None) if path else None
    if not export:
        return clear_selection()
    settings = ", ".join(f"{k}: {v}" for k, v in export["settings"].items()
                         if k not in ("engine", "reference", "transcript") and v not in (None, ""))
    details = (f"**{export['voice']}** · {export['engine']} · {export['duration']:.1f}s  \n"
               f"{export['created'].replace('T', ' at ')}" + (f"  \n{settings}" if settings else "") +
               f"\n\n`{Path(path).relative_to(lib.DATA_DIR.parent)}`\n\n" +
               "\n".join("> " + line if line.strip() else ">" for line in export["text"].splitlines()))
    return path, details, path, gr.Button(interactive=True), gr.DownloadButton(value=path, visible=True)


def delete_selected(path, query):
    if path:  # None when the confirm dialog was cancelled
        try:
            lib.delete_export(path)
        except ValueError as e:
            raise gr.Error(str(e))
        gr.Info("Take deleted.")
    return load_library(query)


def delete_all(confirmed, query):
    if confirmed is True:  # the value returned by the browser's confirm dialog
        count = lib.delete_all_exports()
        gr.Info(f"Deleted {count} take{'s' if count != 1 else ''}.")
    return load_library(query)


# ---------- layout ----------

audio_style = gr.WaveformOptions(**ui.WAVEFORM)
DEVICE_CHOICES = [(qwen.device_label(d), d) for d in qwen.available_devices()]

with gr.Blocks(title="Voice Studio") as demo:
    with gr.Row(elem_id="vs-topbar", equal_height=True):
        gr.HTML(ui.HEADER_HTML, elem_id="vs-brand")
        compute = gr.Dropdown(DEVICE_CHOICES, value=qwen.get_device(), label="Compute", scale=0, min_width=250, filterable=False,
                              elem_id="vs-compute", info="Auto-detected")

    with gr.Tabs(elem_id="vs-main-tabs"):
        with gr.Tab("Studio"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=7):
                    gr.HTML(ui.eyebrow("01", "Script"))
                    script = gr.Textbox(show_label=False, lines=9, elem_id="vs-script",
                                        placeholder="Paste your script. Separate paragraphs with a blank line; long "
                                                    "scripts are generated paragraph by paragraph and joined with "
                                                    "natural pauses.")

                    gr.HTML(ui.eyebrow("02", "Voice"))
                    with gr.Tabs():
                        with gr.Tab("Presets", render_children=True):
                            with gr.Row():
                                speaker = gr.Dropdown(SPEAKER_CHOICES, value="aiden", label="Voice", scale=4, filterable=False,
                                                      info="Aiden and Ryan are native English speakers")
                                size = gr.Radio(["1.7B", "0.6B"], value="1.7B", label="Model", scale=2,
                                                info="Style direction needs 1.7B")
                            speaker_preview = gr.Audio(label="Preview", type="filepath", interactive=False,
                                                       waveform_options=audio_style)
                            with gr.Row():
                                style_preset = gr.Dropdown(list(qwen.STYLE_PRESETS) + [CUSTOM_STYLE], filterable=False,
                                                           value="Tech explainer", label="Style", scale=2)
                                style = gr.Textbox(value=qwen.STYLE_PRESETS["Tech explainer"],
                                                   label="Style direction", lines=2, scale=3)
                            preset_btn = gr.Button("Generate narration", variant="primary", size="lg",
                                                   elem_classes="vs-generate")

                        with gr.Tab("Design", render_children=True):
                            description = gr.Textbox(value=qwen.DESIGN_EXAMPLES[0], label="Describe the voice",
                                                     lines=3)
                            gr.Examples(qwen.DESIGN_EXAMPLES, inputs=description, label="Starting points")
                            design_btn = gr.Button("Generate narration", variant="primary", size="lg",
                                                   elem_classes="vs-generate")
                            gr.HTML('<p class="vs-hint">Each generation invents a new voice. '
                                    'When you hear one you like, save it to reuse it exactly.</p>')
                            with gr.Row(equal_height=True):
                                design_name = gr.Textbox(show_label=False, scale=3,
                                                         placeholder="Name this voice, e.g. Tech narrator")
                                design_save_btn = gr.Button("Save voice", variant="secondary", scale=1)
                            design_saved = gr.Markdown()
                            last_design = gr.State()

                        with gr.Tab("Clone", render_children=True) as clone_tab:
                            engine = gr.Radio(CLONE_ENGINES, value="Qwen 1.7B", label="Engine",
                                              info="Qwen: most faithful clone · Turbo: fastest, supports [laugh] "
                                                   "tags · Original: emotion control")
                            source = gr.Radio(["Saved voice", "New recording"], value="New recording",
                                              label="Source")
                            with gr.Group(visible=False) as saved_group:
                                saved_voice = gr.Dropdown([], label="My voices", filterable=False)
                                saved_preview = gr.Audio(label="Reference clip", type="filepath",
                                                         interactive=False, waveform_options=audio_style)
                            with gr.Group() as new_group:
                                gr.HTML('<p class="vs-hint">Read this aloud, word for word. 10 to 20 seconds, '
                                        'in a quiet room.</p>'
                                        f'<blockquote class="vs-passage">{lib.SAMPLE_PASSAGE}</blockquote>')
                                recording = gr.Audio(sources=["microphone", "upload"], type="filepath",
                                                     label="Your recording", waveform_options=audio_style)
                                transcript = gr.Textbox(value=lib.SAMPLE_PASSAGE, lines=2, label="Transcript",
                                                        info="Qwen uses this. Edit it if you said something "
                                                             "different.")
                                no_transcript = gr.Checkbox(label="I didn't read a known text (skip transcript, "
                                                                  "lower quality)")
                                with gr.Row(equal_height=True):
                                    rec_name = gr.Textbox(show_label=False, scale=3,
                                                          placeholder="Name this voice, e.g. My voice")
                                    rec_save_btn = gr.Button("Save voice", variant="secondary", scale=1)
                                rec_saved = gr.Markdown()
                            with gr.Group(visible=False) as original_opts:
                                exaggeration = gr.Slider(0.25, 1.0, value=0.5, step=0.05, label="Exaggeration",
                                                         info="Higher is more dramatic")
                                cfg_weight = gr.Slider(0.0, 1.0, value=0.5, step=0.05, label="CFG weight",
                                                       info="Lower is slower and more deliberate")
                            turbo_note = gr.HTML('<p class="vs-hint">Turbo understands <code>[laugh]</code> '
                                                 '<code>[chuckle]</code> <code>[cough]</code> in the script. '
                                                 'Chatterbox needs a reference longer than 5 seconds.</p>',
                                                 visible=False)
                            clone_btn = gr.Button("Generate narration", variant="primary", size="lg",
                                                  elem_classes="vs-generate")

                with gr.Column(scale=5, elem_classes="vs-panel"):
                    gr.HTML(ui.eyebrow("03", "Output"))
                    output = gr.Audio(show_label=False, type="filepath", interactive=False, visible=False,
                                      waveform_options=audio_style)
                    output_download = gr.DownloadButton("Download", visible=False, variant="secondary",
                                                        elem_classes="vs-download")
                    status = gr.Markdown('<div class="vs-empty"><b>No take yet</b>Write a script, pick a voice, '
                                         'then Generate narration.</div>', elem_id="vs-status")
                    gr.HTML('<p class="vs-hint">Every take is saved automatically. '
                            'Play or delete past takes in the Library tab.</p>')

        with gr.Tab("Library") as library_tab:
            with gr.Row(equal_height=False):
                with gr.Column(scale=7):
                    gr.HTML(ui.eyebrow("", "Takes"))
                    search = gr.Textbox(show_label=False, placeholder="Search takes", elem_id="vs-search",
                                        max_lines=1)
                    takes_count = gr.HTML(elem_id="vs-takes-count")
                    takes = gr.Radio([], label="Takes", show_label=False, elem_id="vs-takes")
                    library_empty = gr.HTML(elem_id="vs-library-empty")
                    page_limit = gr.State(PAGE_SIZE)
                    load_more_btn = gr.Button("Load more", elem_id="vs-load-more")  # clicked by the scroll script
                    with gr.Row():
                        refresh_btn = gr.Button("Refresh", variant="secondary", size="sm")
                        delete_btn = gr.Button("Delete selected take", variant="stop", size="sm", interactive=False)
                        delete_all_btn = gr.Button("Delete all takes", variant="stop", size="sm")
                    confirm_all = gr.State(False)
                with gr.Column(scale=5, elem_classes="vs-panel"):
                    gr.HTML(ui.eyebrow("", "Selected take"))
                    library_player = gr.Audio(show_label=False, type="filepath", interactive=False,
                                              waveform_options=audio_style)
                    library_download = gr.DownloadButton("Download", visible=False, variant="secondary",
                                                         elem_classes="vs-download")
                    library_details = gr.Markdown("_Select a take to play it._",
                                                  elem_id="vs-details")
                    selected_export = gr.State()

    compute.change(set_compute, compute, None, show_progress="hidden")
    speaker.change(preview_voice, speaker, speaker_preview)
    saved_voice.change(preview_saved, saved_voice, saved_preview, show_progress="hidden")
    style_preset.change(pick_style, style_preset, style, show_progress="hidden")
    generate_events = [
        (preset_btn, generate_preset, [script, speaker, style, size], [output, status, output_download]),
        (design_btn, generate_design, [script, description], [output, status, output_download, last_design]),
        (clone_btn, generate_clone, [script, engine, source, saved_voice, recording, transcript, no_transcript,
                                     exaggeration, cfg_weight], [output, status, output_download]),
    ]
    # Button shows "Generating…" while busy; progress is drawn on the status area only. `.then` runs even
    # if generation fails, so the button always comes back.
    for button, fn, inputs, outputs in generate_events:
        button.click(busy_button, None, [button, output, status, output_download], queue=False,
                     show_progress="hidden").then(
            fn, inputs, outputs, show_progress="hidden").then(
            idle_button, None, button, queue=False, show_progress="hidden")
    design_save_btn.click(save_designed, [design_name, last_design], [design_saved, saved_voice])
    source.change(toggle_source, source, [saved_group, new_group], show_progress="hidden")
    engine.change(toggle_engine, engine, [original_opts, turbo_note], show_progress="hidden")
    rec_save_btn.click(save_recording, [rec_name, recording, transcript, no_transcript],
                       [rec_saved, saved_voice, source])

    list_outputs = [takes, library_empty, takes_count, page_limit]
    selection_outputs = [library_player, library_details, selected_export, delete_btn, library_download]
    library_outputs = list_outputs + selection_outputs
    library_tab.select(load_library, search, library_outputs, show_progress="hidden")
    refresh_btn.click(load_library, search, library_outputs, show_progress="hidden")
    search.change(load_library, search, library_outputs, show_progress="hidden")
    load_more_btn.click(load_more, [search, page_limit, selected_export], list_outputs, show_progress="hidden")
    takes.change(select_take, takes, selection_outputs, show_progress="hidden")
    delete_all_btn.click(delete_all, [confirm_all, search], library_outputs,
                         js="(_, q) => [confirm(`Delete all ${document.querySelector('#vs-takes-count [data-total]')"
                            "?.dataset.total || ''} takes permanently? This can't be undone.`), q]")
    delete_btn.click(delete_selected, [selected_export, search], library_outputs,
                     js="(path, q) => [(path && confirm('Delete this take permanently?')) ? path : null, q]")

    # Refresh the Clone tab when it's opened, not on page load: Gradio leaves a stuck loading timer on
    # components updated while their tab is hidden
    clone_tab.select(refresh_clone_tab, None, [saved_voice, source, saved_group, new_group], show_progress="hidden")
    demo.load(preview_voice, speaker, speaker_preview)


if __name__ == "__main__":
    lib.ensure_dirs()
    # Local-only by default. ./run.sh --lan sets VS_HOST=0.0.0.0 so phones on the same Wi-Fi can connect;
    # VS_AUTH="user:password" adds a login, VS_SSL_CERT/VS_SSL_KEY serve HTTPS (needed for the mic on iPhone).
    host = os.environ.get("VS_HOST", "127.0.0.1")
    auth = tuple(os.environ["VS_AUTH"].split(":", 1)) if os.environ.get("VS_AUTH") else None
    demo.queue().launch(server_name=host, inbrowser=host == "127.0.0.1", theme=ui.build_theme(), css=ui.CSS,
                        head=ui.HEAD, footer_links=[], allowed_paths=[str(lib.DATA_DIR)], auth=auth,
                        ssl_certfile=os.environ.get("VS_SSL_CERT"), ssl_keyfile=os.environ.get("VS_SSL_KEY"),
                        ssl_verify=False)
