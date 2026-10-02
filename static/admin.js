'use strict';
(() => {
 const el=id=>document.getElementById(id);
 async function api(path,body) {
  const response=await fetch(path,{credentials:'same-origin',...(body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});
  const data=await response.json();if(!response.ok)throw new Error(data.error||'Não foi possível concluir.');return data;
 }
 async function loadClients() {
  const info=await api('/api/admin/clients');el('client-list').replaceChildren();el('client-add').disabled=!info.editable;
  if(!info.editable)el('admin-message').textContent='Cadastro pelo painel desativado. Configure as variáveis do Cloudflare D1 no Render. Os e-mails já liberados continuam funcionando.';
  for(const client of info.clients){
   const row=document.createElement('tr');const cells=Array.from({length:4},()=>document.createElement('td'));
   cells[0].textContent=client.email;cells[1].textContent=client.active?'Liberado':'Bloqueado';cells[2].textContent=client.created?new Date(client.created*1000).toLocaleDateString('pt-BR'):'Configuração do servidor';
   if(client.source==='registry')for(const [action,label] of [[client.active?'block':'enable',client.active?'Bloquear':'Liberar'],['delete','Excluir']]){
    const button=document.createElement('button');button.type='button';button.className='secondary';button.textContent=label;
    button.addEventListener('click',async()=>{if(action==='delete'&&!window.confirm('Excluir o cadastro e revogar o acesso de '+client.email+'?'))return;button.disabled=true;try{await api('/api/admin/clients',{email:client.email,action});el('admin-message').textContent='Cadastro atualizado.';await loadClients();}catch(e){el('admin-message').textContent=e.message;button.disabled=false;}});cells[3].append(button);
   }else cells[3].textContent='Gerenciado no Render';
   if(client.active){
    const button=document.createElement('button');button.type='button';button.className='secondary';button.textContent='Criar / redefinir senha';
    button.addEventListener('click',async()=>{if(!window.confirm('Gerar novo link de senha para '+client.email+'? O link anterior deixará de funcionar.'))return;button.disabled=true;try{await invite(client.email);}catch(e){el('admin-message').textContent=e.message;}finally{button.disabled=false;}});cells[3].append(button);
   }
   row.append(...cells);el('client-list').append(row);
  }
 }
 async function monitor(){
  const button=el('traffic-refresh');button.disabled=true;
  try{const data=await api('/api/admin/traffic');el('traffic-cards').replaceChildren();
   for(const [key,label] of [['requests','Requisições'],['active','Em andamento'],['success','Respostas abaixo de 400'],['rejected','Respostas 4xx'],['errors','Erros 5xx/interrupções'],['fiscal','Consultas fiscais'],['access','Requisições de acesso'],['bytes_in','Bytes recebidos (declarados)'],['bytes_out','Bytes enviados'],['average_ms','Tempo médio (ms)']]){const card=document.createElement('article'),title=document.createElement('span'),value=document.createElement('strong');title.textContent=label;value.textContent=Number(data[key]).toLocaleString('pt-BR');card.append(title,value);el('traffic-cards').append(card);}
   el('traffic-status').textContent=`Processo ${data.worker} · ativo há ${data.uptime_seconds}s · atualizado às ${new Date().toLocaleTimeString('pt-BR')}`;
  }catch(e){el('traffic-status').textContent=e.message;}finally{button.disabled=false;}
 }
 async function invite(email){
  const result=await api('/api/admin/password-invite',{email});
  el('invite-panel').hidden=false;el('invite-url').value=result.url;
  el('admin-message').textContent='Link criado para '+result.email+'. A senha anterior funciona até o cliente concluir a redefinição.';
  el('invite-url').focus();el('invite-url').select();
 }
 el('invite-copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(el('invite-url').value);el('admin-message').textContent='Link copiado. Compartilhe somente com o titular.';}catch(e){el('invite-url').focus();el('invite-url').select();el('admin-message').textContent='Selecione e copie o link acima.';}});
 el('client-form').addEventListener('submit',async event=>{event.preventDefault();el('client-add').disabled=true;const email=el('client-email').value.trim();try{await api('/api/admin/clients',{email,action:'add'});await invite(email);el('client-email').value='';await loadClients();}catch(e){el('admin-message').textContent=e.message;el('client-add').disabled=false;}});
 el('traffic-refresh').addEventListener('click',monitor);
 loadClients().catch(e=>{el('admin-message').textContent=e.message;});monitor();
})();
