(() => {
  'use strict';

  function statusFromReading(text) {
    const value = String(text || '').toLowerCase();
    if (value.includes('provável diferença de arredondamento')) {
      return { label: 'Provável arredondamento', className: 'bloco-m-v40-2__status bloco-m-v40-2__status--rounding' };
    }
    if (value.includes('conciliad')) {
      return { label: 'Conciliado', className: 'bloco-m-v40-2__status bloco-m-v40-2__status--ok' };
    }
    return { label: 'Revisar', className: 'bloco-m-v40-2__status bloco-m-v40-2__status--review' };
  }

  function numberBlock(label, value, extraClass = '') {
    const block = document.createElement('div');
    block.className = `bloco-m-v40-2__number ${extraClass}`.trim();
    const span = document.createElement('span');
    span.textContent = label;
    const strong = document.createElement('b');
    strong.textContent = value || '—';
    block.append(span, strong);
    return block;
  }

  function taxCard(row) {
    const cells = Array.from(row?.children || []);
    if (cells.length < 5) return null;

    const tax = cells[0].textContent.trim();
    const documentary = cells[1].textContent.trim();
    const blockM = cells[2].textContent.trim();
    const difference = cells[3].textContent.trim();
    const reading = cells[4].textContent.trim();
    const status = statusFromReading(reading);

    const card = document.createElement('article');
    card.className = 'bloco-m-v40-2__tax-card';
    card.dataset.tax = tax;

    const title = document.createElement('div');
    title.className = 'bloco-m-v40-2__tax-title';
    const heading = document.createElement('strong');
    heading.textContent = tax;
    const badge = document.createElement('span');
    badge.className = status.className;
    badge.textContent = status.label;
    title.append(heading, badge);

    const numbers = document.createElement('div');
    numbers.className = 'bloco-m-v40-2__numbers';
    numbers.append(
      numberBlock('C170/C175', documentary),
      numberBlock(tax === 'PIS' ? 'M210' : 'M610', blockM),
      numberBlock('Diferença', difference, 'bloco-m-v40-2__number--diff')
    );

    card.append(title, numbers);
    return card;
  }

  function enhance() {
    const section = document.getElementById('bloco-m-v40');
    if (!section || section.dataset.visualV402 === '1') return;

    const rows = Array.from(section.querySelectorAll('.bloco-m-v40__table-wrap tbody tr'));
    if (!rows.length) return;

    const summary = document.createElement('div');
    summary.className = 'bloco-m-v40-2__summary';
    for (const row of rows) {
      const card = taxCard(row);
      if (card) summary.append(card);
    }

    const head = section.querySelector('.bloco-m-v40__head');
    if (summary.children.length) {
      if (head?.nextSibling) section.insertBefore(summary, head.nextSibling);
      else section.prepend(summary);
    }

    section.dataset.visualV402 = '1';
    section.classList.add('bloco-m-v40-2--enhanced');
  }

  const observer = new MutationObserver(records => {
    const addedBlock = records.some(record => Array.from(record.addedNodes || []).some(node =>
      node?.nodeType === Node.ELEMENT_NODE && node.id === 'bloco-m-v40'
    ));
    if (addedBlock) window.setTimeout(enhance, 60);
  });

  function start() {
    observer.observe(document.documentElement, { childList: true, subtree: true });
    window.OmniXMLBlocoMVisualV402 = { enhance };
    window.setTimeout(enhance, 60);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();
