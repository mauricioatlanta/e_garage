(() => {
  const rows = [
    ['REP_HEADER', document.querySelector('.doc-pos-header.hidden.sm\\:grid')],
    ['SERV_HEADER', document.querySelector('.doc-pos-header-services')],
    ['SERV_ROW', document.querySelector('#servicios-container .doc-row-grid')],
  ];

  const out = rows.map(([name, el]) => {
    if (!el) return { name, found: false };
    const cs = getComputedStyle(el);
    return {
      name,
      found: true,
      display: cs.display,
      gridTemplateColumns: cs.gridTemplateColumns,
      gap: cs.gap,
      alignItems: cs.alignItems,
      width: Math.round(el.getBoundingClientRect().width)
    };
  });

  console.table(out);
})();
