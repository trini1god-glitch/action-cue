(function () {
  const root = document.currentScript.parentNode.querySelector('.cascade');
  if (!root) return;

  const tooltip = document.createElement('div');
  tooltip.className = 'cascade-tooltip';
  tooltip.style.cssText = 'position:absolute; pointer-events:none; padding:6px 10px; '
    + 'background:#212121; color:#fff; border-radius:4px; font:12px sans-serif; '
    + 'opacity:0; transition:opacity 80ms; z-index:1000;';
  document.currentScript.parentNode.appendChild(tooltip);

  function showTip(el, text, ev) {
    tooltip.textContent = text;
    tooltip.style.left = (ev.pageX + 12) + 'px';
    tooltip.style.top  = (ev.pageY + 12) + 'px';
    tooltip.style.opacity = '1';
  }
  function hideTip() { tooltip.style.opacity = '0'; }

  // Bands: click-to-expand on fired bands. No hover tooltip — the rationale
  // and signal label live inside the band's on-demand layer, revealed by
  // click. Hover duplicating that content was visual noise; this restores
  // the overview-first / details-on-demand pattern (Shneiderman 1996).
  root.querySelectorAll('.band').forEach(band => {
    const fired = band.dataset.fired === 'true';
    if (fired) {
      band.style.cursor = 'pointer';
      band.addEventListener('click', () => {
        const expanded = band.dataset.expanded === 'true';
        band.dataset.expanded = expanded ? 'false' : 'true';
      });
    }
  });

  // Resolution arrow: hover tooltip
  const arrow = root.querySelector('.resolution-arrow');
  if (arrow) {
    arrow.addEventListener('mouseenter', ev => {
      showTip(arrow, arrow.dataset.tip || '', ev);
    });
    arrow.addEventListener('mouseleave', hideTip);
  }

  // Strip safety arrow: hover tooltip (only present when cue.safety_modified).
  // The <g class="strip-safety"> wrapper carries data-tip from cascade.py:
  //   "Force raised from {base} to {modified} due to {reason}"
  const stripSafety = root.querySelector('.strip-safety');
  if (stripSafety) {
    stripSafety.addEventListener('mouseenter', ev => {
      showTip(stripSafety, stripSafety.dataset.tip || '', ev);
    });
    stripSafety.addEventListener('mouseleave', hideTip);
  }

  // Safety banner has no hover affordance by design — the banner carries
  // its message in-place; a tooltip would duplicate prose that's already
  // visible. The strip-safety arrow above the banner gets the hover since
  // it's the visual gesture (no text); the banner is the prose itself.
})();
