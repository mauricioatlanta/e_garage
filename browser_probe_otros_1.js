(() => {
  const sel = (s) => document.querySelector(s);
  const vis = (el) => {
    if (!el) return false;
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && r.height > 0;
  };

  const card =
    sel('#add-otro')?.closest('.doc-smart-card') ||
    sel('#otros-container')?.closest('.doc-smart-card,[class*="card"],section,div');

  const out = {
    addOtro: !!sel('#add-otro'),
    otrosContainer: !!sel('#otros-container'),
    cardVisible: vis(card),
    addOtroVisible: vis(sel('#add-otro')),
    containerVisible: vis(sel('#otros-container')),
    containerChildren: sel('#otros-container')?.children.length ?? null,
    bodyScrollW: document.documentElement.scrollWidth,
    bodyClientW: document.documentElement.clientWidth,
    hasHorizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
  };

  console.table(out);
})();
