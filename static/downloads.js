'use strict';
(() => {
  const el = id => document.getElementById(id);
  const files = new Map();
  const urls = [];
  let running = false, stop = false;
  const saveLink = (blob, name) => {
    const url = URL.createObjectURL(blob); urls.push(url);
    const link = document.createElement('a'); link.href = url; link.download = name;
    link.textContent = 'Baixar XML'; link.className = 'file-link'; return link;
  };
  const cleanup = () => { urls.splice(0).forEach(url => URL.revokeObjectURL(url)); files.clear(); el('zip').disabled = true; };
  const busy = value => {
    running = value;
    ['download','status','clear','certificate','password','token','uf','keys'].forEach(id => { el(id).disabled = value; });
    el('stop').disabled = !value; el('zip').disabled = value || !files.size;
  };
  async function run(action) {
    if (running || !el('recovery-form').reportValidity()) return;
    const certificate = el('certificate').files[0];
    if (!certificate || certificate.size > 2 * 1024 * 1024) { el('progress').textContent = 'Selecione um A1 de até 2 MB.'; return; }
    const keys = [...new Set(el('keys').value.split(/\r?\n/).map(key => key.replace(/\s/g,'')).filter(Boolean))];
    if (!keys.length || keys.length > 20 || keys.some(key => !/^[0-9]{44}$/.test(key))) {
      el('progress').textContent = 'Informe de 1 a 20 chaves de 44 dígitos, uma por linha.'; return;
    }
    cleanup(); el('results').replaceChildren(); stop = false; busy(true);
    try {
      for (const [index,key] of keys.entries()) {
        if (stop) break;
        el('progress').textContent = `Consultando ${index+1} de ${keys.length}…`;
        const row = document.createElement('tr');
        const cells = Array.from({length:3}, () => document.createElement('td'));
        cells[0].textContent = key; cells[1].textContent = 'Aguardando SEFAZ…'; cells[2].textContent = '—';
        row.append(...cells); el('results').append(row);
        const form = new FormData();
        form.append('certificate',certificate); form.append('password',el('password').value);
        form.append('key',key); form.append('uf',el('uf').value); form.append('action',action);
        const headers = el('token').value ? {Authorization:'Bearer '+el('token').value} : {};
        try {
          const response = await fetch('/api/sefaz/recover',{method:'POST',body:form,headers,credentials:'same-origin'});
          if (!response.ok) {
            const info = await response.json(); cells[1].textContent = info.error || 'Consulta não concluída.'; cells[1].className = 'error';
            if (info.stop_batch || response.status === 403 || response.status === 429 || info.code === 'connection') stop = true;
          } else if (action === 'status') {
            const info = await response.json(); cells[1].textContent = `${info.cStat} · ${info.xMotivo}`;
          } else {
            const blob = await response.blob(); const name = key+'-procNFe.xml'; files.set(name,blob);
            cells[1].textContent = `${response.headers.get('X-SEFAZ-cStat')} · ${decodeURIComponent(response.headers.get('X-SEFAZ-Motivo') || '')}`;
            cells[1].className = 'success'; cells[2].replaceChildren(saveLink(blob,name));
          }
        } catch (_) { cells[1].textContent = 'Conexão interrompida. Confira o resultado antes de tentar novamente.'; cells[1].className = 'error'; stop = true; }
      }
      el('progress').textContent = `${stop ? 'Consultas interrompidas.' : 'Consultas concluídas.'} ${files.size} XML(s) completo(s) disponível(is).`;
    } finally { busy(false); }
  }
  el('recovery-form').addEventListener('submit',event => { event.preventDefault(); run('download'); });
  el('status').addEventListener('click',() => run('status'));
  el('stop').addEventListener('click',() => { stop = true; el('progress').textContent = 'A consulta atual será concluída; as próximas foram interrompidas.'; });
  el('clear').addEventListener('click',() => { cleanup(); el('recovery-form').reset(); el('results').replaceChildren(); el('progress').textContent = 'Dados limpos.'; });
  el('zip').addEventListener('click',async () => {
    el('zip').disabled = true;
    try {
      const zip = new JSZip(); files.forEach((blob,name) => zip.file(name,blob));
      const blob = await zip.generateAsync({type:'blob'});
      const link = saveLink(blob,'OmniXML-recuperados.zip'); link.click();
    } catch (_) { el('progress').textContent = 'Não foi possível gerar o ZIP. Use os downloads individuais.'; }
    finally { el('zip').disabled = running || !files.size; }
  });
  fetch('/api/sefaz/capabilities').then(response => response.json()).then(info => {
    el('availability').textContent = info.enabled ? 'Recuperação disponível. Informe seu A1 e as chaves.' : 'Recuperação desativada no servidor. O administrador precisa configurar OMNIXML_SEFAZ_TOKEN.';
  }).catch(() => { el('availability').textContent = 'Não foi possível verificar a disponibilidade.'; });
  window.addEventListener('pagehide',cleanup);
})();
