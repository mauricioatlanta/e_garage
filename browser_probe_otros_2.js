(() => {
  const btn = document.querySelector('#add-otro');
  const container = document.querySelector('#otros-container');

  if (!btn || !container) {
    console.log({
      ok: false,
      reason: 'missing-elements',
      btn: !!btn,
      container: !!container
    });
    return;
  }

  const before = container.children.length;
  btn.click();

  setTimeout(() => {
    const after = container.children.length;
    const last = container.lastElementChild;
    const inputs = last ? Array.from(last.querySelectorAll('input,select,textarea')).map(function (el) {
      return {
        name: el.name || null,
        id: el.id || null,
        cls: el.className || null,
        type: el.type || el.tagName
      };
    }) : [];

    console.log({
      ok: after > before,
      before: before,
      after: after,
      lastRowExists: !!last,
      inputs: inputs
    });
  }, 200);
})();
