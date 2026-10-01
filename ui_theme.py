"""Voice Studio look and feel, following Apple's Liquid Glass design language.

Rules applied:
- Liquid Glass (translucent, blurred, specular edge light) only on the navigation/controls layer: tab bars,
  buttons, segmented controls, menus, the toolbar. Content sits beneath on a softer material. No glass on glass.
- Capsule controls and concentric corners (inner radius = outer radius - padding).
- SF Pro system typography (New York for reading text), system label/fill/separator colours, system blue accent.
- Spring motion: the selection lens slides between tabs/segments, controls swell slightly on press,
  a highlight follows the pointer across glass buttons.
- Light and dark appearance follow the system; reduce motion and reduce transparency are honoured.
"""
import gradio as gr

CARD_RADIUS = 22
CARD_PADDING = 10
FIELD_RADIUS = CARD_RADIUS - CARD_PADDING  # concentric with the card around it

# Colours are CSS custom properties so light/dark switch in CSS; Gradio theme variables point at them.
_VARS = dict(
    body_background_fill="transparent",
    body_text_color="var(--lg-label)",
    body_text_color_subdued="var(--lg-label-2)",
    background_fill_primary="transparent",
    background_fill_secondary="transparent",
    border_color_primary="var(--lg-sep)",
    border_color_accent="var(--lg-accent)",
    border_color_accent_subdued="var(--lg-accent-soft)",
    color_accent="var(--lg-accent)",
    color_accent_soft="var(--lg-accent-soft)",
    link_text_color="var(--lg-accent)",
    link_text_color_hover="var(--lg-accent)",
    link_text_color_visited="var(--lg-accent)",
    block_background_fill="transparent",
    block_border_color="transparent",
    block_border_width="0px",
    block_label_background_fill="transparent",
    block_label_border_color="transparent",
    block_label_text_color="var(--lg-label-2)",
    block_title_text_color="var(--lg-label-2)",
    block_info_text_color="var(--lg-label-3)",
    block_shadow="none",
    block_radius=f"{CARD_RADIUS}px",
    block_padding="14px",
    panel_background_fill="transparent",
    panel_border_color="transparent",
    input_background_fill="var(--lg-fill)",
    input_background_fill_focus="var(--lg-field-focus)",
    input_border_color="transparent",
    input_border_color_focus="transparent",
    input_border_width="0px",
    input_shadow="none",
    input_shadow_focus="0 0 0 4px var(--lg-accent-ring)",
    input_placeholder_color="var(--lg-label-3)",
    input_radius=f"{FIELD_RADIUS}px",
    button_primary_background_fill="var(--lg-accent)",
    button_primary_background_fill_hover="var(--lg-accent)",
    button_primary_text_color="#ffffff",
    button_primary_border_color="transparent",
    button_primary_shadow="none",
    button_secondary_background_fill="var(--lg-glass)",
    button_secondary_background_fill_hover="var(--lg-glass)",
    button_secondary_text_color="var(--lg-label)",
    button_secondary_border_color="transparent",
    button_cancel_background_fill="var(--lg-glass)",
    button_cancel_background_fill_hover="var(--lg-glass)",
    button_cancel_text_color="var(--lg-red)",
    button_cancel_border_color="transparent",
    button_large_radius="999px",
    button_small_radius="999px",
    button_large_text_weight="600",
    checkbox_background_color="var(--lg-fill-2)",
    checkbox_background_color_selected="var(--lg-green)",
    checkbox_border_color="transparent",
    checkbox_border_color_selected="transparent",
    checkbox_border_color_focus="transparent",
    checkbox_label_background_fill="transparent",
    checkbox_label_background_fill_hover="transparent",
    checkbox_label_background_fill_selected="transparent",
    checkbox_label_border_color="transparent",
    checkbox_label_border_color_selected="transparent",
    checkbox_label_text_color="var(--lg-label)",
    checkbox_label_text_color_selected="var(--lg-label)",
    slider_color="var(--lg-accent)",
    table_border_color="var(--lg-sep)",
    table_even_background_fill="transparent",
    table_odd_background_fill="transparent",
    code_background_fill="var(--lg-fill)",
    shadow_drop="none",
    shadow_drop_lg="var(--lg-shadow-float)",
    loader_color="var(--lg-accent)",
    stat_background_fill="var(--lg-accent-soft)",
    error_background_fill="var(--lg-material-strong)",
    error_border_color="var(--lg-red)",
    error_text_color="var(--lg-red)",
)

SYSTEM_SANS = ["-apple-system", "BlinkMacSystemFont", "SF Pro Text", "SF Pro Display", "Helvetica Neue",
               "Helvetica", "Arial", "sans-serif"]
SYSTEM_MONO = ["ui-monospace", "SF Mono", "SFMono-Regular", "Menlo", "monospace"]


def build_theme():
    theme = gr.themes.Base(
        primary_hue=gr.themes.colors.blue,
        neutral_hue=gr.themes.colors.gray,
        radius_size=gr.themes.sizes.radius_lg,
        font=SYSTEM_SANS,
        font_mono=SYSTEM_MONO,
    )
    values = {}
    for key, value in _VARS.items():
        for name in (key, f"{key}_dark"):
            if hasattr(theme, name):
                values[name] = value
    return theme.set(**values)


# Waveforms are drawn on a canvas (no CSS variables): system gray + system blue read well in both modes
WAVEFORM = dict(waveform_color="#8E8E93", waveform_progress_color="#0A84FF")

# Tokens, dark mode and the page canvas go in <head>: Gradio scopes the `css` argument to its container,
# rewriting :root/html/body, which would break the colour variables and the full-page background.
GLOBAL_CSS = """
/* ================= tokens: Apple system colours, light ================= */
:root {
  color-scheme: light dark;
  --lg-accent: #007AFF; --lg-accent-rgb: 0, 122, 255;
  --lg-accent-soft: rgba(0, 122, 255, 0.12); --lg-accent-ring: rgba(0, 122, 255, 0.28);
  --lg-red: #FF3B30; --lg-green: #34C759;
  --lg-label: rgba(0, 0, 0, 0.88); --lg-label-2: rgba(60, 60, 67, 0.64); --lg-label-3: rgba(60, 60, 67, 0.38);
  --lg-sep: rgba(60, 60, 67, 0.14);
  --lg-fill: rgba(118, 118, 128, 0.10); --lg-fill-2: rgba(118, 118, 128, 0.20);
  --lg-field-focus: rgba(255, 255, 255, 0.9);
  --lg-bg: #E6E9F2;
  --lg-solid: #F2F2F7;
  --lg-material: rgba(255, 255, 255, 0.66);
  --lg-material-strong: rgba(255, 255, 255, 0.82);
  --lg-card-edge: rgba(255, 255, 255, 0.7);
  --lg-glass: rgba(255, 255, 255, 0.40);
  --lg-glass-edge: rgba(255, 255, 255, 0.65);
  --lg-glass-spec: rgba(255, 255, 255, 0.95);
  --lg-glass-sheen: rgba(255, 255, 255, 0.35);
  --lg-lens: rgba(255, 255, 255, 0.92);
  --lg-lens-clear: rgba(255, 255, 255, 0.55);
  --lg-shadow-card: 0 1px 2px rgba(15, 23, 42, 0.05), 0 12px 32px rgba(15, 23, 42, 0.07);
  --lg-shadow-glass: 0 1px 1px rgba(15, 23, 42, 0.06), 0 8px 24px rgba(15, 23, 42, 0.10);
  --lg-shadow-float: 0 18px 50px rgba(15, 23, 42, 0.18);
  --lg-blob-1: rgba(0, 122, 255, 0.42); --lg-blob-2: rgba(175, 82, 222, 0.36);
  --lg-blob-3: rgba(255, 149, 0, 0.30); --lg-blob-4: rgba(52, 199, 89, 0.24); --lg-blob-5: rgba(255, 45, 85, 0.22);
  --lg-spring: cubic-bezier(0.34, 1.45, 0.64, 1);
  --lg-ease: cubic-bezier(0.25, 0.1, 0.25, 1);
  --lg-blur: blur(22px) saturate(185%);
  --lg-blur-card: blur(34px) saturate(160%);
}

/* ================= dark ================= */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --lg-accent: #0A84FF; --lg-accent-rgb: 10, 132, 255;
    --lg-accent-soft: rgba(10, 132, 255, 0.18); --lg-accent-ring: rgba(10, 132, 255, 0.40);
    --lg-red: #FF453A; --lg-green: #30D158;
    --lg-label: rgba(255, 255, 255, 0.92); --lg-label-2: rgba(235, 235, 245, 0.62);
    --lg-label-3: rgba(235, 235, 245, 0.32);
    --lg-sep: rgba(255, 255, 255, 0.09);
    --lg-fill: rgba(118, 118, 128, 0.22); --lg-fill-2: rgba(118, 118, 128, 0.34);
    --lg-field-focus: rgba(118, 118, 128, 0.30);
    --lg-bg: #06070B;
    --lg-solid: #1C1C1E;
    --lg-material: rgba(30, 30, 36, 0.62);
    --lg-material-strong: rgba(44, 44, 50, 0.86);
    --lg-card-edge: rgba(255, 255, 255, 0.08);
    --lg-glass: rgba(255, 255, 255, 0.07);
    --lg-glass-edge: rgba(255, 255, 255, 0.14);
    --lg-glass-spec: rgba(255, 255, 255, 0.30);
    --lg-glass-sheen: rgba(255, 255, 255, 0.08);
    --lg-lens: rgba(255, 255, 255, 0.16);
    --lg-lens-clear: rgba(255, 255, 255, 0.24);
    --lg-shadow-card: 0 1px 1px rgba(0, 0, 0, 0.4), 0 16px 40px rgba(0, 0, 0, 0.35);
    --lg-shadow-glass: 0 1px 1px rgba(0, 0, 0, 0.5), 0 10px 30px rgba(0, 0, 0, 0.45);
    --lg-shadow-float: 0 24px 60px rgba(0, 0, 0, 0.6);
    --lg-blob-1: rgba(10, 132, 255, 0.26); --lg-blob-2: rgba(191, 90, 242, 0.22);
    --lg-blob-3: rgba(255, 159, 10, 0.10); --lg-blob-4: rgba(48, 209, 88, 0.10); --lg-blob-5: rgba(255, 55, 95, 0.12);
  }
}
:root[data-theme="dark"] {
    --lg-accent: #0A84FF; --lg-accent-rgb: 10, 132, 255;
    --lg-accent-soft: rgba(10, 132, 255, 0.18); --lg-accent-ring: rgba(10, 132, 255, 0.40);
    --lg-red: #FF453A; --lg-green: #30D158;
    --lg-label: rgba(255, 255, 255, 0.92); --lg-label-2: rgba(235, 235, 245, 0.62);
    --lg-label-3: rgba(235, 235, 245, 0.32);
    --lg-sep: rgba(255, 255, 255, 0.09);
    --lg-fill: rgba(118, 118, 128, 0.22); --lg-fill-2: rgba(118, 118, 128, 0.34);
    --lg-field-focus: rgba(118, 118, 128, 0.30);
    --lg-bg: #06070B;
    --lg-solid: #1C1C1E;
    --lg-material: rgba(30, 30, 36, 0.62);
    --lg-material-strong: rgba(44, 44, 50, 0.86);
    --lg-card-edge: rgba(255, 255, 255, 0.08);
    --lg-glass: rgba(255, 255, 255, 0.07);
    --lg-glass-edge: rgba(255, 255, 255, 0.14);
    --lg-glass-spec: rgba(255, 255, 255, 0.30);
    --lg-glass-sheen: rgba(255, 255, 255, 0.08);
    --lg-lens: rgba(255, 255, 255, 0.16);
    --lg-lens-clear: rgba(255, 255, 255, 0.24);
    --lg-shadow-card: 0 1px 1px rgba(0, 0, 0, 0.4), 0 16px 40px rgba(0, 0, 0, 0.35);
    --lg-shadow-glass: 0 1px 1px rgba(0, 0, 0, 0.5), 0 10px 30px rgba(0, 0, 0, 0.45);
    --lg-shadow-float: 0 24px 60px rgba(0, 0, 0, 0.6);
    --lg-blob-1: rgba(10, 132, 255, 0.26); --lg-blob-2: rgba(191, 90, 242, 0.22);
    --lg-blob-3: rgba(255, 159, 10, 0.10); --lg-blob-4: rgba(48, 209, 88, 0.10); --lg-blob-5: rgba(255, 55, 95, 0.12);
}
:root[data-theme="light"] { color-scheme: light; }
:root[data-theme="dark"] { color-scheme: dark; }

/* ================= canvas: soft colour field for the glass to refract ================= */
html { overflow-y: scroll; scrollbar-gutter: stable; }
html, body { background: var(--lg-bg) !important; min-height: 100%; }
body::before {
  content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background:
    radial-gradient(70% 60% at 0% 0%, var(--lg-blob-1), transparent 72%),
    radial-gradient(60% 55% at 100% 0%, var(--lg-blob-2), transparent 72%),
    radial-gradient(65% 60% at 100% 100%, var(--lg-blob-3), transparent 72%),
    radial-gradient(55% 55% at 0% 100%, var(--lg-blob-4), transparent 72%),
    radial-gradient(45% 40% at 55% 45%, var(--lg-blob-5), transparent 78%),
    var(--lg-bg);
}
gradio-app, .gradio-container, .gradio-container .main, .gradio-container .wrap.main, .contain {
  background: transparent !important; }
.gradio-container { width: 100% !important; max-width: 1280px !important; margin: 0 auto !important;
  padding: 0 28px 64px !important; box-sizing: border-box; color: var(--lg-label);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif !important; -webkit-font-smoothing: antialiased;
  letter-spacing: -0.01em; }
.gradio-container > .main, .gradio-container .wrap.main, .gradio-container .contain,
#vs-main-tabs, #vs-main-tabs > .tabitem { width: 100% !important; }
footer { display: none !important; }
/* Gradio pads its inner wrapper as well; with our container padding that double-pads (fatal on phones) */
.gradio-container .main, .gradio-container .main.fillable, .gradio-container .main > .wrap { padding-left: 0 !important;
  padding-right: 0 !important; }
@media (max-width: 900px) {
  .gradio-container { padding: 0 14px 40px !important; }
  .gradio-container .row { flex-direction: column !important; flex-wrap: nowrap !important; gap: 12px !important; }
  .gradio-container .row > .column, .gradio-container .row > .form, .gradio-container .row > .block {
    width: 100% !important; min-width: 0 !important; flex: 1 1 auto !important; }
  /* rows holding only buttons stay horizontal and wrap, instead of stacking one per line */
  .gradio-container .row:has(> button):not(:has(> .column, > .form, > .block)) {
    flex-direction: row !important; flex-wrap: wrap !important; gap: 8px !important; }
  .gradio-container .row:has(> button):not(:has(> .column, > .form, > .block)) > button {
    flex: 0 1 auto !important; width: auto !important; min-width: 0 !important; }
}
@media (prefers-reduced-transparency: reduce) {
  :root { --lg-material: var(--lg-solid); --lg-material-strong: var(--lg-solid); --lg-glass: var(--lg-solid);
    --lg-glass-sheen: transparent; }
}
"""

# Selection lens that slides between tabs/segments, and pointer-tracking light on glass buttons
HEAD = """
<meta name="color-scheme" content="light dark">
<style>""" + GLOBAL_CSS + """</style>
<script>
(() => {
  // Appearance: "auto" follows the system; "light"/"dark" override it. Saved per browser.
  const THEME_KEY = 'vs-appearance';
  let appearance = 'auto';
  try { appearance = localStorage.getItem(THEME_KEY) || 'auto'; } catch (_) {}
  const applyAppearance = () => {
    const root = document.documentElement;
    if (appearance === 'light' || appearance === 'dark') root.dataset.theme = appearance; else delete root.dataset.theme;
  };
  applyAppearance();
  document.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('.vs-appearance button');
    if (!b) return;
    appearance = b.dataset.appearance;
    try { localStorage.setItem(THEME_KEY, appearance); } catch (_) {}
    applyAppearance(); schedule();
  });
  const place = (host, target, lensClass) => {
    let lens = host.querySelector(':scope > .' + lensClass);
    if (!lens) { lens = document.createElement('span'); lens.className = lensClass; host.prepend(lens); }
    if (!target || !target.offsetParent) { lens.style.opacity = 0; return; }
    const x = target.offsetLeft, y = target.offsetTop, w = target.offsetWidth, h = target.offsetHeight;
    const first = !lens.dataset.placed;
    const moved = !first && (+lens.dataset.x !== x || +lens.dataset.w !== w);
    Object.assign(lens.dataset, { x, y, w });
    if (lens.dataset.dragging) return;  // the finger is in charge
    if (first) lens.style.transition = 'none';
    lens.style.opacity = 1;
    lens.style.width = w + 'px';
    lens.style.height = h + 'px';
    lens.style.transform = `translate(${x}px, ${y}px)`;
    if (first) { lens.dataset.placed = 1; lens.offsetWidth; lens.style.transition = ''; }
    if (moved) {  // liquid morph while travelling: swell into clear glass, then settle
      lens.classList.add('moving'); clearTimeout(lens._settle);
      lens._settle = setTimeout(() => lens.classList.remove('moving'), 420);
    }
  };
  const update = () => {
    document.querySelectorAll('.vs-appearance').forEach(group => {
      group.querySelectorAll('button').forEach(b =>
        b.setAttribute('aria-pressed', b.dataset.appearance === appearance ? 'true' : 'false'));
      place(group, group.querySelector('button[aria-pressed="true"]'), 'lg-lens');
    });
    document.querySelectorAll('[role=tablist]').forEach(t =>
      place(t, t.querySelector('[role=tab][aria-selected=true]'), 'lg-lens'));
    document.querySelectorAll('fieldset.block:not(#vs-takes) > .wrap:not([data-testid=status-tracker])').forEach(w =>
      place(w, w.querySelector(':scope > label.selected'), 'lg-thumb'));
  };
  let queued = false;
  const schedule = () => { if (!queued) { queued = true; requestAnimationFrame(() => { queued = false; update(); }); } };
  new MutationObserver(schedule).observe(document.documentElement,
    { subtree: true, childList: true, attributes: true, attributeFilter: ['aria-selected', 'class'] });
  addEventListener('resize', schedule);
  addEventListener('load', schedule);
  // Touch: open dropdown menus without focusing their text field, so iOS shows no keyboard/autofill bar.
  // Gradio opens the menu on the field's focus event and closes it on blur, so we send those events ourselves.
  let open = null, startX = 0, startY = 0;
  const fieldOf = t => t.closest && t.closest('.wrap-inner') && t.closest('.wrap-inner').querySelector('input[role=listbox]');
  const send = (input, type) => input.dispatchEvent(new FocusEvent(type));
  document.addEventListener('touchstart', e => { startX = e.touches[0].clientX; startY = e.touches[0].clientY; },
    { passive: true, capture: true });
  document.addEventListener('touchend', e => {
    const t = e.changedTouches[0];
    if (Math.abs(t.clientX - startX) > 10 || Math.abs(t.clientY - startY) > 10) return;  // a scroll, not a tap
    const input = fieldOf(e.target);
    if (input) {
      e.preventDefault();  // no focus -> no keyboard, no autofill bar
      if (open === input) { send(input, 'blur'); open = null; }
      else { if (open) send(open, 'blur'); send(input, 'focus'); open = input; }
    } else if (open && !e.target.closest('ul.options')) {
      send(open, 'blur'); open = null;
    }
  }, { passive: false, capture: true });
  // Gradio picks the option on mousedown and removes the menu right away, so note the choice here
  document.addEventListener('mousedown', e => {
    if (open && e.target.closest('ul.options')) { const input = open; open = null; setTimeout(() => send(input, 'blur'), 0); }
  }, true);
  // Library: load the next page of takes when the list is scrolled near its end
  let loadingMore = false;
  document.addEventListener('scroll', e => {
    const list = e.target;
    if (!(list instanceof Element) || !list.matches('#vs-takes > .wrap') || loadingMore) return;
    if (list.scrollTop + list.clientHeight < list.scrollHeight - 160) return;
    if (!document.querySelector('#vs-takes-count [data-more="1"]')) return;
    const button = document.getElementById('vs-load-more');
    if (!button) return;
    loadingMore = true; button.click(); setTimeout(() => { loadingMore = false; }, 900);
  }, true);
  // Drag the lens along a tab bar (iOS 26): it lifts, follows the finger, and selects the nearest tab on release
  let drag = null, swallowClick = 0;
  document.addEventListener('pointerdown', e => {
    const bar = e.target.closest && e.target.closest('[role=tablist]');
    const lens = bar && bar.querySelector(':scope > .lg-lens');
    if (!lens || !lens.dataset.placed) return;
    drag = { bar, lens, id: e.pointerId, startX: e.clientX, baseX: +lens.dataset.x, x: +lens.dataset.x, moved: false };
  }, true);
  document.addEventListener('pointermove', e => {
    if (!drag || e.pointerId !== drag.id) return;
    const dx = e.clientX - drag.startX;
    if (!drag.moved) {
      if (Math.abs(dx) < 6) return;
      drag.moved = true; drag.lens.dataset.dragging = 1; drag.lens.classList.add('dragging');
      try { drag.bar.setPointerCapture(e.pointerId); } catch (_) {}
    }
    const pad = 4, max = drag.bar.clientWidth - pad - +drag.lens.dataset.w;
    drag.x = Math.max(pad, Math.min(max, drag.baseX + dx));
    drag.lens.style.transform = `translate(${drag.x}px, ${drag.lens.dataset.y}px)`;
  }, true);
  const endDrag = e => {
    if (!drag || e.pointerId !== drag.id) return;
    const d = drag; drag = null;
    if (!d.moved) return;
    delete d.lens.dataset.dragging; d.lens.classList.remove('dragging');
    const centre = d.x + +d.lens.dataset.w / 2;
    const tabs = [...d.bar.querySelectorAll('[role=tab]')].filter(t => t.offsetParent);
    const nearest = tabs.reduce((best, t) => Math.abs(t.offsetLeft + t.offsetWidth / 2 - centre) <
      Math.abs(best.offsetLeft + best.offsetWidth / 2 - centre) ? t : best, tabs[0]);
    if (nearest && nearest.getAttribute('aria-selected') !== 'true') nearest.click(); else schedule();
    swallowClick = Date.now();  // the browser's own click after a drag should not select a second tab
  };
  document.addEventListener('pointerup', endDrag, true);
  document.addEventListener('pointercancel', endDrag, true);
  document.addEventListener('click', e => {
    if (swallowClick && Date.now() - swallowClick < 350 && e.isTrusted && e.target.closest('[role=tablist]')) {
      e.stopPropagation(); e.preventDefault(); swallowClick = 0;
    }
  }, true);
  document.addEventListener('pointermove', e => {
    const b = e.target.closest && e.target.closest('button.primary, button.secondary, button.stop');
    if (!b) return;
    const r = b.getBoundingClientRect();
    b.style.setProperty('--mx', (e.clientX - r.left) + 'px');
    b.style.setProperty('--my', (e.clientY - r.top) + 'px');
  }, { passive: true });
})();
</script>
"""

CSS = f"""

/* ================= content layer: frosted material cards ================= */
.block.padded, .form {{
  background: var(--lg-material) !important;
  border: 1px solid var(--lg-card-edge) !important; border-radius: {CARD_RADIUS}px !important;
  box-shadow: var(--lg-shadow-card) !important; }}
.form {{ padding: {CARD_PADDING - 6}px !important; gap: 0 !important; }}
.form > .block, .form .block.padded, .vs-panel .block.padded, .vs-panel .form,
#vs-topbar .form, #vs-topbar .block {{
  background: transparent !important; border: none !important; box-shadow: none !important;
  -webkit-backdrop-filter: none; backdrop-filter: none; }}
.vs-panel {{ position: sticky; top: 84px; align-self: flex-start;
  background: var(--lg-material); -webkit-backdrop-filter: var(--lg-blur-card); backdrop-filter: var(--lg-blur-card);
  border: 1px solid var(--lg-card-edge); border-radius: 28px; box-shadow: var(--lg-shadow-card);
  padding: 6px 20px 22px !important; }}
.gr-group, .group, .styler {{ background: transparent !important; border: none !important; gap: 8px !important; }}

/* headings, hints and the header sit directly on the canvas, not in cards */
.block:has(.lg-section), .block:has(.vs-header), .block:has(> .prose > .vs-hint:only-child),
.block:has(.vs-hint):not(:has(input, textarea, audio, table, .vs-passage)) {{
  background: transparent !important; border: none !important; box-shadow: none !important;
  -webkit-backdrop-filter: none !important; backdrop-filter: none !important; padding: 0 !important; }}
/* standalone audio players get the same material card as other content */
.block:has(audio):not(.vs-panel .block), .block:has(.waveform-container):not(.vs-panel .block) {{
  background: var(--lg-material) !important; border: 1px solid var(--lg-card-edge) !important;
  box-shadow: var(--lg-shadow-card) !important; padding: 12px 16px !important; }}

/* ================= typography ================= */
.vs-header {{ display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; }}
.vs-brand {{ display: flex; flex-direction: column; gap: 4px; }}
.vs-wordmark {{ font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif; font-size: 34px;
  line-height: 41px; font-weight: 700; letter-spacing: -0.022em; color: var(--lg-label); margin: 0; }}
.vs-tagline {{ font-size: 15px; line-height: 20px; color: var(--lg-label-2); margin: 0; letter-spacing: -0.01em; }}
.lg-section {{ font-size: 20px; line-height: 25px; font-weight: 600; letter-spacing: -0.017em;
  color: var(--lg-label); margin: 26px 4px 10px; }}
[data-testid="block-info"], .block-label span, label > span:first-child {{
  font-size: 13px !important; line-height: 18px; font-weight: 500 !important; letter-spacing: -0.005em;
  color: var(--lg-label-2) !important; text-transform: none !important; font-family: inherit !important; }}
.info-text, .info {{ font-size: 12px !important; color: var(--lg-label-3) !important; }}
.block-label {{ border: none !important; background: transparent !important; box-shadow: none !important; }}
textarea, input[type="text"], input[type="number"], input[role="listbox"] {{
  font-size: 15px !important; line-height: 1.5 !important; color: var(--lg-label) !important;
  font-family: inherit !important; }}
#vs-script textarea {{ font-size: 17px !important; line-height: 1.55 !important; min-height: 230px;
  padding: 14px 16px !important; }}
.vs-hint {{ color: var(--lg-label-3); font-size: 13px; line-height: 18px; margin: 6px 4px; }}
.vs-hint code, #vs-status code, #vs-details code {{ font-family: {", ".join(SYSTEM_MONO)}; font-size: 12px;
  color: var(--lg-label-2); background: var(--lg-fill); border-radius: 6px; padding: 1px 6px; border: none; }}
.vs-hint a {{ color: var(--lg-accent); }}
.vs-passage {{ font-family: ui-serif, "New York", Georgia, serif; font-size: 20px; line-height: 1.5;
  color: var(--lg-label); background: var(--lg-fill); border-radius: {FIELD_RADIUS}px; padding: 14px 18px;
  margin: 4px 0 8px; border: none; }}

/* ================= text fields & dropdown fields ================= */
textarea, input[type="text"], input[type="number"], .wrap-inner, .container > .wrap {{
  transition: background .25s var(--lg-ease), box-shadow .3s var(--lg-ease); }}
label.container .input-container textarea, .container > .wrap {{ border-radius: {FIELD_RADIUS}px !important; }}
.wrap-inner input {{ text-overflow: ellipsis; padding-right: 28px !important; }}
::selection {{ background: var(--lg-accent-ring); }}

/* dropdown menu: a glass popover, always above cards and the sticky tab bar */
#vs-topbar {{ position: relative; z-index: 100; }}
.block:has(ul.options), .form:has(ul.options), .row:has(ul.options) {{ position: relative; z-index: 200 !important; }}
ul.options {{ background: var(--lg-material-strong) !important; -webkit-backdrop-filter: var(--lg-blur);
  backdrop-filter: var(--lg-blur); border: 1px solid var(--lg-glass-edge) !important; border-radius: 14px !important;
  box-shadow: var(--lg-shadow-float) !important; padding: 6px !important; }}
/* menus are sized to their items (up to 60% of the screen), never squeezed into a scroll strip */
ul.options {{ max-height: min(60vh, 460px) !important;
  overflow-y: auto; overflow-x: hidden !important; scrollbar-width: none; -webkit-overflow-scrolling: touch; }}
ul.options::-webkit-scrollbar {{ display: none; }}
/* pop-up buttons, not text fields: no caret, no keyboard */
input[role="listbox"][readonly] {{ caret-color: transparent; cursor: pointer; }}
ul.options li.item {{ display: flex !important; align-items: center; gap: 8px; min-height: 36px; box-sizing: border-box;
  border-radius: 9px !important; padding: 8px 12px !important; font-size: 14px; line-height: 20px;
  color: var(--lg-label) !important; transition: background .15s var(--lg-ease); }}
ul.options li.item + li.item {{ margin-top: 2px; }}
ul.options li.item .inner-item {{ flex: none; width: 16px; color: var(--lg-accent); }}
/* touch screens: Apple's 44pt tap targets and 17pt menu text */
@media (pointer: coarse) {{
  ul.options {{ padding: 8px !important; border-radius: 18px !important; }}
  ul.options li.item {{ min-height: 44px; padding: 11px 14px !important; font-size: 17px; line-height: 22px;
    border-radius: 12px !important; }}
}}
/* menu hangs directly under its field, same width, never off-screen */
.container > .wrap {{ position: relative; }}
ul.options {{ position: absolute !important; top: calc(100% + 6px) !important; bottom: auto !important;
  left: 0 !important; right: 0 !important; width: auto !important; min-width: 0 !important; margin: 0 !important;
  box-sizing: border-box; z-index: 1000 !important; }}
.block:has(ul.options), .form:has(ul.options), .container:has(ul.options), .wrap:has(> ul.options),
.column:has(ul.options), .row:has(ul.options), .styler:has(ul.options) {{ overflow: visible !important; }}
.column:has(ul.options), .block:has(ul.options) {{ position: relative; z-index: 200 !important; }}
/* selected option: accent checkmark (iOS style); row highlight only under the pointer or finger */
ul.options li.item.selected {{ font-weight: 600; }}
ul.options li.item .inner-item, ul.options li.item.selected .inner-item {{ color: var(--lg-accent) !important; }}
@media (hover: hover) {{
  ul.options li.item:hover, ul.options li.item.active {{ background: var(--lg-accent) !important; color: #fff !important; }}
  ul.options li.item:hover .inner-item, ul.options li.item.active .inner-item {{ color: #fff !important; }}
}}
@media (hover: none) {{
  ul.options li.item.active {{ background: transparent !important; color: var(--lg-label) !important; }}
  ul.options li.item:active {{ background: var(--lg-fill-2) !important; }}
}}

/* ================= glass: shared recipe for controls ================= */
button.primary, button.secondary, button.stop, [role=tablist], .vs-chip, #vs-compute .wrap {{
  position: relative; isolation: isolate; }}
button.secondary, button.stop, [role=tablist], .vs-chip {{
  background: linear-gradient(180deg, var(--lg-glass-sheen), transparent 55%), var(--lg-glass) !important;
  -webkit-backdrop-filter: var(--lg-blur); backdrop-filter: var(--lg-blur);
  border: 1px solid var(--lg-glass-edge) !important;
  box-shadow: inset 0 1px 0 var(--lg-glass-spec), inset 0 -1px 1px rgba(255, 255, 255, 0.06),
              var(--lg-shadow-glass) !important; }}

/* ================= buttons ================= */
button.primary, button.secondary, button.stop {{
  border-radius: 999px !important; font-family: inherit !important; letter-spacing: -0.01em;
  transition: transform .5s var(--lg-spring), filter .25s var(--lg-ease), box-shadow .3s var(--lg-ease),
              opacity .25s var(--lg-ease) !important; }}
button.primary {{
  min-height: 50px; font-size: 17px !important; font-weight: 600 !important; color: #fff !important;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.30), rgba(255, 255, 255, 0) 55%), var(--lg-accent) !important;
  border: 1px solid rgba(255, 255, 255, 0.28) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5), inset 0 -1px 2px rgba(0, 0, 0, 0.12),
              0 10px 28px rgba(var(--lg-accent-rgb), 0.35), 0 1px 2px rgba(0, 0, 0, 0.12) !important; }}
button.secondary, button.stop {{ font-size: 14px !important; font-weight: 500 !important; min-height: 34px;
  padding: 0 16px !important; }}
button.secondary {{ color: var(--lg-label) !important; }}
button.stop {{ color: var(--lg-red) !important; }}
button.primary::after, button.secondary::after, button.stop::after {{
  content: ""; position: absolute; inset: 0; border-radius: inherit; pointer-events: none; z-index: 1;
  background: radial-gradient(140px circle at var(--mx, 50%) var(--my, 50%), rgba(255, 255, 255, 0.32), transparent 60%);
  opacity: 0; transition: opacity .35s var(--lg-ease); }}
button.primary:hover:not(:disabled)::after, button.secondary:hover:not(:disabled)::after,
button.stop:hover:not(:disabled)::after {{ opacity: 1; }}
button.primary:hover:not(:disabled) {{ filter: brightness(1.05) saturate(1.05); }}
button.primary:active:not(:disabled), button.secondary:active:not(:disabled), button.stop:active:not(:disabled) {{
  transform: scale(1.035); filter: brightness(1.12); transition-duration: .18s !important; }}
button:disabled {{ opacity: 0.38 !important; cursor: default; }}
button.primary:disabled {{ opacity: 0.72 !important; cursor: progress; }}
button:focus-visible {{ outline: 3px solid var(--lg-accent-ring) !important; outline-offset: 2px; }}
.vs-generate {{ margin-top: 14px !important; }}
/* download: glass capsule with an arrow-down-to-tray symbol */
button.secondary.vs-download, .vs-download {{ color: var(--lg-accent) !important; }}
.vs-download {{ min-height: 40px !important; padding: 0 18px 0 14px !important; gap: 8px;
  font-size: 15px !important; font-weight: 600 !important; color: var(--lg-accent) !important; margin: 6px 0 4px !important; }}
.vs-download::before {{ content: ""; width: 16px; height: 16px; flex: none; background: currentColor;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M8 2v8M4.8 6.8L8 10l3.2-3.2M2.5 11.5v1.5h11v-1.5'/%3E%3C/svg%3E") center / contain no-repeat;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M8 2v8M4.8 6.8L8 10l3.2-3.2M2.5 11.5v1.5h11v-1.5'/%3E%3C/svg%3E") center / contain no-repeat; }}
.vs-download > img, .vs-download svg {{ display: none; }}

/* ================= tab bars: glass capsule with sliding lens ================= */
.tab-wrapper {{ border: none !important; background: transparent !important; padding: 0 !important;
  margin: 2px 0 14px !important; height: auto !important; }}
.tab-container::after, .tab-wrapper::after {{ display: none !important; }}
[role=tablist] {{ display: inline-flex !important; align-items: stretch; width: auto !important; gap: 2px;
  padding: 4px !important; height: auto !important; min-height: 0 !important; box-sizing: border-box;
  border-radius: 999px !important; overflow: visible !important; }}
.tab-wrapper, .tab-container {{ height: auto !important; min-height: 0 !important; }}
[role=tab], .tab-container button {{ position: relative; z-index: 1; border: none !important; background: transparent !important;
  border-radius: 999px !important; padding: 7px 18px !important; margin: 0 !important; height: auto !important;
  font-family: inherit !important; font-size: 14px !important; font-weight: 600 !important; letter-spacing: -0.01em;
  color: var(--lg-label-2) !important; transition: color .3s var(--lg-ease), transform .45s var(--lg-spring); }}
[role=tab], .tab-container button {{ display: inline-flex !important; align-items: center; justify-content: center;
  text-align: center !important; }}
[role=tab]:hover {{ color: var(--lg-label) !important; }}
[role=tab]:active {{ transform: scale(0.96); }}
[role=tab][aria-selected="true"] {{ color: var(--lg-label) !important; }}
[role=tab][aria-selected="true"]::after {{ display: none !important; }}
.lg-lens, .lg-thumb {{ position: absolute; left: 0; top: 0; z-index: 0; pointer-events: none; border-radius: 999px;
  background: var(--lg-lens);
  box-shadow: inset 0 1px 0 var(--lg-glass-spec), 0 1px 2px rgba(0, 0, 0, 0.10), 0 4px 12px rgba(0, 0, 0, 0.10);
  transition: transform .55s var(--lg-spring), width .55s var(--lg-spring), height .3s var(--lg-ease),
              opacity .2s var(--lg-ease); }}
/* liquid behaviour: swell into clear glass while moving; lift and follow the finger while dragged */
.lg-lens, .lg-thumb {{ scale: 1 1; }}
.lg-lens.moving, .lg-thumb.moving {{ scale: 1.06 1.16; background: var(--lg-lens-clear);
  box-shadow: inset 0 0 0 1px var(--lg-glass-edge), inset 0 1px 0 var(--lg-glass-spec), 0 6px 18px rgba(0, 0, 0, 0.12); }}
.lg-lens.dragging {{ scale: 1.1 1.3; background: var(--lg-lens-clear);
  box-shadow: inset 0 0 0 1px var(--lg-glass-edge), inset 0 1px 0 var(--lg-glass-spec), 0 10px 28px rgba(0, 0, 0, 0.18);
  transition: scale .35s var(--lg-spring), background .2s var(--lg-ease), box-shadow .2s var(--lg-ease) !important; }}
.lg-lens, .lg-thumb {{ transition: transform .55s var(--lg-spring), width .55s var(--lg-spring), height .3s var(--lg-ease),
  scale .45s var(--lg-spring), background .3s var(--lg-ease), box-shadow .3s var(--lg-ease), opacity .2s var(--lg-ease); }}
[role=tablist] {{ touch-action: pan-y; -webkit-user-select: none; user-select: none; cursor: grab; }}
[role=tablist]:active {{ cursor: grabbing; }}
#vs-main-tabs > .tab-wrapper {{ position: sticky; top: 14px; z-index: 60; margin-bottom: 8px !important; }}
#vs-main-tabs > .tab-wrapper [role=tab], #vs-main-tabs > .tab-wrapper .tab-container button {{
  font-size: 15px !important; padding: 8px 22px !important; }}
.tabitem {{ border: none !important; padding: 4px 0 0 !important; background: transparent !important;
  animation: lg-in .5s var(--lg-ease) both; }}
@keyframes lg-in {{ from {{ opacity: 0; transform: translateY(8px) scale(0.995); }} to {{ opacity: 1; transform: none; }} }}

/* ================= segmented controls (radio groups) ================= */
fieldset.block > .wrap:not([data-testid=status-tracker]) {{
  position: relative; display: inline-flex !important; flex-wrap: wrap; gap: 2px !important; padding: 3px !important;
  border-radius: 999px; background: var(--lg-fill-2); width: auto !important; max-width: 100%; }}
fieldset.block > .wrap > label {{ position: relative; z-index: 1; margin: 0 !important; padding: 7px 16px !important;
  border: none !important; border-radius: 999px !important; background: transparent !important; box-shadow: none !important;
  font-size: 14px; font-weight: 500; color: var(--lg-label) !important; cursor: pointer;
  transition: transform .45s var(--lg-spring), color .25s var(--lg-ease); }}
fieldset.block > .wrap > label:active {{ transform: scale(0.96); }}
fieldset.block > .wrap > label.selected {{ font-weight: 600; }}
fieldset.block > .wrap > label > input[type=radio] {{ position: absolute; opacity: 0; pointer-events: none; }}
fieldset.block > .wrap > label > span {{ margin: 0 !important; }}

/* ================= switch (checkbox) ================= */
input[type=checkbox] {{ -webkit-appearance: none; appearance: none; position: relative; flex: none;
  width: 46px !important; height: 28px !important; border-radius: 999px !important; margin: 0 10px 0 0 !important;
  background: var(--lg-fill-2) !important; background-image: none !important; border: none !important;
  cursor: pointer; transition: background .3s var(--lg-ease); box-shadow: none !important; }}
input[type=checkbox]::before {{ content: ""; position: absolute; top: 2px; left: 2px; width: 24px; height: 24px;
  border-radius: 999px; background: #fff; box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15), 0 1px 1px rgba(0, 0, 0, 0.16);
  transition: transform .5s var(--lg-spring), width .25s var(--lg-ease); }}
input[type=checkbox]:checked {{ background: var(--lg-green) !important; }}
input[type=checkbox]:checked::before {{ transform: translateX(18px); }}
input[type=checkbox]:active::before {{ width: 30px; }}
input[type=checkbox]:checked:active::before {{ transform: translateX(12px); }}
input[type=checkbox]:focus-visible {{ outline: 3px solid var(--lg-accent-ring); outline-offset: 2px; }}

/* ================= sliders ================= */
input[type=range] {{ -webkit-appearance: none; appearance: none; height: 4px !important; border-radius: 999px;
  cursor: pointer; }}
input[type=range]::-webkit-slider-thumb {{ -webkit-appearance: none; width: 26px; height: 26px; border-radius: 999px;
  background: #fff; border: none; box-shadow: 0 2px 7px rgba(0, 0, 0, 0.18), 0 0 0 0.5px rgba(0, 0, 0, 0.06);
  transition: transform .45s var(--lg-spring), background .2s var(--lg-ease); }}
input[type=range]:active::-webkit-slider-thumb {{ transform: scale(1.4, 1.15); background: rgba(255, 255, 255, 0.72);
  box-shadow: inset 0 1px 0 #fff, 0 4px 16px rgba(0, 0, 0, 0.22), 0 0 0 0.5px rgba(255, 255, 255, 0.8); }}
input[type=range]::-moz-range-thumb {{ width: 26px; height: 26px; border-radius: 999px; background: #fff; border: none;
  box-shadow: 0 2px 7px rgba(0, 0, 0, 0.18); transition: transform .45s var(--lg-spring); }}
input[type=range]:active::-moz-range-thumb {{ transform: scale(1.4, 1.15); }}
.tab-like-container input[type=number] {{ border-radius: 8px !important; background: var(--lg-fill) !important;
  border: none !important; }}
.reset-button {{ color: var(--lg-label-2) !important; }}

/* ================= toolbar (header) ================= */
#vs-topbar {{ flex-wrap: nowrap !important; align-items: flex-end !important; padding: 36px 4px 18px; gap: 20px; }}
#vs-brand {{ flex: 1 1 0 !important; min-width: 0 !important; }}
#vs-brand, #vs-compute {{ background: transparent !important; border: none !important; padding: 0 !important;
  box-shadow: none !important; }}
#vs-compute, #vs-topbar .form, .form:has(> #vs-compute) {{ flex: 0 0 290px !important; min-width: 0 !important; }}
/* the toolbar's form wrapper is not a card: no padding, and never a scroll container */
#vs-topbar .form, .form:has(> #vs-compute) {{ padding: 0 !important; overflow: visible !important; }}
#vs-compute .container > .wrap {{ border-radius: 999px !important; padding-left: 8px;
  background: linear-gradient(180deg, var(--lg-glass-sheen), transparent 55%), var(--lg-material-strong) !important;
  border: 1px solid var(--lg-glass-edge) !important;
  box-shadow: inset 0 1px 0 var(--lg-glass-spec), var(--lg-shadow-glass) !important; }}
#vs-compute span[data-testid="block-info"] {{ display: block; margin: 0 0 6px 12px; }}
#vs-compute .info-text {{ display: none; }}
.vs-meta {{ display: flex; gap: 8px; }}
.vs-chip {{ font-size: 12px; font-weight: 500; color: var(--lg-label-2); border-radius: 999px; padding: 6px 12px;
  display: inline-flex; align-items: center; gap: 7px; }}
.vs-meta {{ align-items: center; }}
.vs-appearance {{ position: relative; isolation: isolate; display: inline-flex; gap: 2px; padding: 3px; border-radius: 999px;
  background: linear-gradient(180deg, var(--lg-glass-sheen), transparent 55%), var(--lg-glass);
  -webkit-backdrop-filter: var(--lg-blur); backdrop-filter: var(--lg-blur); border: 1px solid var(--lg-glass-edge);
  box-shadow: inset 0 1px 0 var(--lg-glass-spec), var(--lg-shadow-glass); }}
.vs-appearance button {{ position: relative; z-index: 1; display: inline-flex; align-items: center; justify-content: center;
  width: 34px; height: 28px; padding: 0; border: none; border-radius: 999px; background: transparent; cursor: pointer;
  color: var(--lg-label-2); transition: color .25s var(--lg-ease), transform .45s var(--lg-spring); }}
.vs-appearance button:hover {{ color: var(--lg-label); }}
.vs-appearance button:active {{ transform: scale(0.92); }}
.vs-appearance button[aria-pressed="true"] {{ color: var(--lg-label); }}
.vs-appearance button:focus-visible {{ outline: 3px solid var(--lg-accent-ring); outline-offset: 1px; }}
.vs-appearance svg {{ width: 17px; height: 17px; }}
@media (pointer: coarse) {{
  .vs-appearance {{ padding: 4px; }}
  .vs-appearance button {{ width: 44px; height: 36px; }}
  .vs-appearance svg {{ width: 19px; height: 19px; }}
}}
.vs-chip .dot {{ width: 7px; height: 7px; border-radius: 50%; background: var(--lg-green);
  box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.18); }}

/* ================= output panel ================= */
#vs-status {{ font-size: 14px; color: var(--lg-label-2); }}
#vs-status strong {{ color: var(--lg-label); }}
#vs-status > .wrap, #vs-status [data-testid=status-tracker] {{ display: none !important; }}
.vs-empty {{ text-align: center; padding: 34px 16px 30px; color: var(--lg-label-3); font-size: 13px; line-height: 18px; }}
.vs-empty::before {{ content: ""; display: block; width: 44px; height: 44px; margin: 0 auto 12px;
  background: var(--lg-label-3);
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.6' stroke-linecap='round'%3E%3Cpath d='M3 12h1M7 8v8M11 5v14M15 9v6M19 7v10M21 12h0'/%3E%3C/svg%3E") center / contain no-repeat;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.6' stroke-linecap='round'%3E%3Cpath d='M3 12h1M7 8v8M11 5v14M15 9v6M19 7v10M21 12h0'/%3E%3C/svg%3E") center / contain no-repeat; }}
.vs-empty b {{ display: block; font-size: 17px; line-height: 22px; font-weight: 600; color: var(--lg-label-2);
  margin-bottom: 4px; }}
.vs-progress {{ background: var(--lg-fill); border-radius: 16px; padding: 16px 18px; }}
.vs-progress-top {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px;
  font-size: 15px; font-weight: 600; color: var(--lg-label); }}
.vs-progress-top span {{ color: var(--lg-label-2); font-weight: 400; font-variant-numeric: tabular-nums; }}
.vs-progress-track {{ height: 6px; border-radius: 999px; background: var(--lg-fill-2); overflow: hidden; }}
.vs-progress-fill {{ height: 100%; border-radius: 999px; background: var(--lg-accent);
  transition: width .6s var(--lg-spring); }}
.vs-progress-fill.indeterminate {{ width: 30% !important; animation: lg-slide 1.3s var(--lg-ease) infinite; }}
@keyframes lg-slide {{ 0% {{ transform: translateX(-110%); }} 100% {{ transform: translateX(360%); }} }}
.vs-progress p {{ margin: 10px 0 0; color: var(--lg-label-3); font-size: 13px; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; }}

/* ================= library ================= */
#vs-details {{ font-size: 14px; color: var(--lg-label-2); line-height: 1.55; }}
#vs-details strong {{ color: var(--lg-label); }}
#vs-details blockquote {{ font-family: ui-serif, "New York", Georgia, serif; font-size: 18px; line-height: 1.5;
  color: var(--lg-label); background: var(--lg-fill); border: none; border-radius: {FIELD_RADIUS}px;
  margin: 12px 0 0; padding: 12px 16px; max-height: 320px; overflow-y: auto; }}
/* takes: an inset grouped list (not a segmented control) */
#vs-takes > .wrap {{ display: flex !important; flex-direction: column !important; flex-wrap: nowrap !important;
  gap: 0 !important; padding: 0 !important; width: 100% !important; background: transparent !important;
  border-radius: 0 !important; max-height: min(62vh, 560px); overflow-y: auto; }}
#vs-takes > .wrap > .lg-thumb {{ display: none !important; }}
#vs-takes > .wrap > label {{ display: flex !important; align-items: center; gap: 10px; width: 100%; box-sizing: border-box;
  min-height: 48px; padding: 12px 40px 12px 14px !important; border-radius: 12px !important;
  font-size: 15px !important; font-weight: 400 !important; line-height: 20px; color: var(--lg-label) !important;
  position: relative; transition: background .15s var(--lg-ease); }}
#vs-takes > .wrap > label + label::before {{ content: ""; position: absolute; top: 0; left: 14px; right: 14px;
  height: 1px; background: var(--lg-sep); }}
#vs-takes > .wrap > label:hover {{ background: var(--lg-fill) !important; }}
#vs-takes > .wrap > label:active {{ transform: none; background: var(--lg-fill-2) !important; }}
#vs-takes > .wrap > label.selected {{ background: var(--lg-accent-soft) !important; font-weight: 500 !important; }}
#vs-takes > .wrap > label.selected::after {{ content: ""; position: absolute; right: 16px; top: 50%; width: 14px;
  height: 14px; margin-top: -7px; background: var(--lg-accent);
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 8.5l3.2 3.2L13 4.8'/%3E%3C/svg%3E") center / contain no-repeat;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 8.5l3.2 3.2L13 4.8'/%3E%3C/svg%3E") center / contain no-repeat; }}
#vs-takes > .wrap > label + label.selected::before, #vs-takes > .wrap > label.selected + label::before {{ opacity: 0; }}
/* two-line rows: script preview on top, "voice · length · date" underneath */
#vs-takes > .wrap > label {{ min-height: 62px; padding-top: 10px !important; padding-bottom: 10px !important; }}
#vs-takes > .wrap > label > span {{ display: block; min-width: 0; flex: 1 1 auto; white-space: pre; overflow: hidden;
  text-overflow: ellipsis; font-size: 13px; line-height: 18px; color: var(--lg-label-2); font-weight: 400; }}
#vs-takes > .wrap > label > span::first-line {{ font-size: 15px; line-height: 22px; font-weight: 500;
  color: var(--lg-label); }}
#vs-takes > .wrap > label.selected > span::first-line {{ font-weight: 600; }}
.vs-count {{ font-size: 12px; color: var(--lg-label-3); margin: 2px 6px 8px; }}
#vs-load-more {{ display: none !important; }}
/* search: Apple's rounded search field with a magnifying glass */
#vs-search, .form:has(> #vs-search), #vs-takes-count, .form:has(> #vs-takes-count) {{ background: transparent !important;
  border: none !important; box-shadow: none !important; padding: 0 !important; margin-bottom: 4px; }}
#vs-takes-count, #vs-library-empty {{ min-height: 0 !important; }}
#vs-library-empty:not(:has(.vs-hint)), #vs-takes-count:not(:has(.vs-count)) {{ display: none !important; }}
#vs-library-empty, .form:has(> #vs-library-empty) {{ background: transparent !important; border: none !important;
  box-shadow: none !important; padding: 0 !important; }}
#vs-search label.container, #vs-search .input-container {{ background: transparent !important; box-shadow: none !important;
  border: none !important; padding: 0 !important; }}
#vs-search input, #vs-search textarea {{ min-height: 38px; border-radius: 12px !important; padding: 8px 12px 8px 36px !important;
  font-size: 16px !important; background-color: var(--lg-fill-2) !important;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='%238E8E93' stroke-width='1.8' stroke-linecap='round'%3E%3Ccircle cx='7' cy='7' r='5'/%3E%3Cpath d='M11 11l3.5 3.5'/%3E%3C/svg%3E") !important;
  background-repeat: no-repeat !important; background-position: 12px center !important; background-size: 15px 15px !important;
  resize: none; }}

/* ================= audio ================= */
.block:has(audio), .block:has(.waveform-container) {{ border-radius: {CARD_RADIUS}px !important; }}
.waveform-container, .controls {{ color: var(--lg-label); }}

/* ================= loading overlays elsewhere ================= */
.wrap.default.full:not(.hide) {{ background: var(--lg-material) !important; -webkit-backdrop-filter: var(--lg-blur);
  backdrop-filter: var(--lg-blur); border-radius: inherit; }}

* {{ scrollbar-color: var(--lg-fill-2) transparent; }}

/* ================= accessibility ================= */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ transition-duration: .01ms !important; animation-duration: .01ms !important;
    animation-iteration-count: 1 !important; }}
}}
@media (prefers-reduced-transparency: reduce) {{
  * {{ -webkit-backdrop-filter: none !important; backdrop-filter: none !important; }}
}}

@media (max-width: 900px) {{
  #vs-topbar {{ flex-direction: column !important; align-items: stretch !important; width: 100% !important;
    padding: 18px 2px 10px; gap: 12px; }}
  #vs-topbar > * {{ width: 100% !important; max-width: none !important; flex: 0 0 auto !important; }}
  .vs-header {{ flex-direction: column; align-items: flex-start; gap: 10px; }}
  .vs-wordmark {{ font-size: 30px; line-height: 36px; }}
  .vs-panel {{ position: static; border-radius: {CARD_RADIUS}px; padding: 4px 16px 18px !important; }}
  #vs-compute, #vs-topbar .form, .form:has(> #vs-compute) {{ flex: 1 1 auto !important; width: 100% !important; }}
  .lg-section {{ font-size: 20px; margin: 18px 4px 8px; }}
  #vs-script textarea {{ min-height: 170px; font-size: 16px !important; }}
  /* tab bars fill the width; segments share it */
  [role=tablist] {{ display: flex !important; width: 100% !important; box-sizing: border-box; }}
  [role=tab], .tab-container button {{ flex: 1 1 auto; padding: 8px 6px !important; font-size: 13px !important;
    white-space: nowrap; }}
  #vs-main-tabs > .tab-wrapper {{ top: 8px; }}
  #vs-main-tabs > .tab-wrapper [role=tab], #vs-main-tabs > .tab-wrapper .tab-container button {{
    font-size: 15px !important; padding: 8px 10px !important; }}
  #vs-brand {{ flex: 0 0 auto !important; width: 100% !important; }}
  .vs-meta {{ order: -1; }}
  fieldset.block > .wrap:not([data-testid=status-tracker]) {{ border-radius: 18px; }}
  fieldset.block > .wrap > label {{ padding: 7px 12px !important; font-size: 13px; }}
  button.primary {{ min-height: 52px; }}
  .vs-passage {{ font-size: 18px; }}
  #vs-takes > .wrap > label {{ font-size: 15px !important; padding: 12px 38px 12px 12px !important; }}
}}
"""

HEADER_HTML = """
<header class="vs-header">
  <div class="vs-brand">
    <h1 class="vs-wordmark">Voice Studio</h1>
    <p class="vs-tagline">Studio-grade English narration. Preset voices, designed voices, or your own.</p>
  </div>
  <div class="vs-meta">
    <span class="vs-chip"><span class="dot"></span>Running locally</span>
    <div class="vs-appearance" role="group" aria-label="Appearance">
      <button type="button" data-appearance="auto" title="Automatic" aria-label="Automatic appearance"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="6.5" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 3.5a6.5 6.5 0 0 1 0 13z" fill="currentColor"/></svg></button>
      <button type="button" data-appearance="light" title="Light" aria-label="Light appearance"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="3.4" fill="none" stroke="currentColor" stroke-width="1.6"/><g stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M10 2.2v1.6M10 16.2v1.6M2.2 10h1.6M16.2 10h1.6M4.5 4.5l1.1 1.1M14.4 14.4l1.1 1.1M4.5 15.5l1.1-1.1M14.4 5.6l1.1-1.1"/></g></svg></button>
      <button type="button" data-appearance="dark" title="Dark" aria-label="Dark appearance"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M15.8 12.6A6.6 6.6 0 0 1 7.4 4.2a6.6 6.6 0 1 0 8.4 8.4z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg></button>
    </div>
  </div>
</header>
"""


def eyebrow(number, title):
    """Section header in Apple's title style (the number is kept for call-site compatibility, not shown)."""
    return f'<h2 class="lg-section">{title}</h2>'
