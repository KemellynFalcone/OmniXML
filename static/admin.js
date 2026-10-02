'use strict';
(() => {
 const el=id=>document.getElementById(id);
 async function api(path,body) {
  const response=await fetch(path,{credentials:'same-origin',...(body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});
  const data=await response.json();if(!response.ok)throw new Error(data.error||'Não foi possível concluir.');return data;
 }
 async function loadClients() {
  const info=await api('/api/admin/clients');el('client-list').replaceChildren();el('client-add').disabled=!info.editable;
  if(!info.editable)el('admin-message').textContent='Cadastro pelo painel desativado. Configure OMNIXML_CLIENTS_DB em armazenamento persistente. Os e-mails já liberados continuam funcionando.';
  for(const client of info.clients){
   const row=document.createElement('tr');const cells=Array.from({length:4},()=>document.createElement('td'));
   cells[0].textContent=client.email;cells[1].textContent=client.active?'Liberado':'Bloqueado';cells[2].textContent=client.created?new Date(client.created*1000).toLocaleDateString('pt-BR'):'Configuração do servidor';
   if(client.source==='registry')for(const [action,label] of [[client.active?'block':'enable',client.active?'Bloquear':'Liberar'],['delete','Excluir']]){
    const button=document.createElement('button');button.type='button';button.className='secondary';button.textContent=label;
    button.addEventListener('click',async()=>{if(action==='delete'&&!window.confirm('Excluir o cadastro e revogar o acesso de '+client.email+'?'))return;button.disabled=true;try{await api('/api/admin/clients',{email:client.email,action});el('admin-message').textContent='Cadastro atualizado.';await loadClients();}catch(e){el('admin-message').textContent=e.message;button.disabled=false;}});cells[3].append(button);
   }else cells[3].textContent='Gerenciado no Render';
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
 el('client-form').addEventListener('submit',async event=>{event.preventDefault();el('client-add').disabled=true;try{await api('/api/admin/clients',{email:el('client-email').value,action:'add'});el('client-email').value='';el('admin-message').textContent='Cliente liberado.';await loadClients();}catch(e){el('admin-message').textContent=e.message;el('client-add').disabled=false;}});
 el('traffic-refresh').addEventListener('click',monitor);
 loadClients().catch(e=>{el('admin-message').textContent=e.message;});monitor();
})();
