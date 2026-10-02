# Login, clientes e monitor temporário

## Administração

Abra `/login`, valide seu e-mail e acesse `/admin` pelo link Administração na recuperação. Apenas administradores autenticados podem consultar o cadastro ou monitor. Configure `OMNIXML_ADMIN_EMAILS=omnixml@gmail.com`; quando ausente, o remetente de `OMNIXML_EMAIL_FROM` é usado como administrador inicial. Administradores e e-mails de `OMNIXML_ALLOWED_EMAILS` continuam funcionando e são gerenciados no Render, para evitar exclusão acidental da conta inicial.

O painel libera, bloqueia, reativa e exclui clientes. Guarda somente e-mail, acesso ativo/bloqueado e data de inclusão. Bloqueio/exclusão revogam códigos pendentes e sessões. Não guarda último acesso, IP, CNPJ, documentos, A1 ou senha no cadastro. Administradores não são definidos pelo cadastro de clientes: o papel vem da configuração do servidor.

## Persistência do cadastro mínimo

Configure `OMNIXML_CLIENTS_DB` com o caminho de um banco SQLite **em disco persistente** (por exemplo `/var/data/clients.sqlite3`, com disco montado em `/var/data`). A pasta deve existir e ser gravável. O painel só permite alterações quando a variável está definida. Não use `/tmp` para a lista definitiva; o aplicativo não consegue verificar se um diretório é realmente persistente.

O arquivo do cadastro é separado de `OMNIXML_AUTH_DB`, que continua efêmero para códigos, sessões e limites de tentativas. Use caminhos diferentes. Deploys podem exigir novo login, mas o cadastro permanece se o disco for persistente. Para várias instâncias, migrar o cadastro para um banco compartilhado; SQLite em disco local é destinado a uma instância com múltiplos workers.

No [Render, discos persistentes exigem serviço pago](https://render.com/docs/disks). Não contratar ou alterar plano automaticamente: se o serviço não tiver armazenamento persistente, manter temporariamente a lista já configurada em `OMNIXML_ALLOWED_EMAILS` e escolher banco externo ou disco antes de ativar edição pelo painel.

## Monitor em RAM

`/admin` mostra requisições, processos em andamento, resultados por classe HTTP, consultas fiscais, requisições de acesso, média de duração e bytes declarados no envio/enviados na resposta. Atualização manual; nenhuma trilha de eventos ou histórico é criado. Não conta visitantes únicos. Não lê conteúdo de XML, certificado, senha, chave ou e-mail. Arquivos estáticos e polling do monitor são excluídos.

Contadores pertencem a cada worker/processo e zeram ao reiniciar. O painel exibe o ID do processo que respondeu; com múltiplos workers os valores podem variar entre atualizações. Não representam o tráfego total de rede, custos do Render ou métricas consolidadas entre instâncias.

Logs do Render/proxy e mensagens do Gmail são independentes do monitor e podem persistir. O aplicativo mantém avisos técnicos fixos para diagnóstico; isso não equivale a histórico de documentos. As autenticações ainda exigem controles temporários, incluindo identificadores HMAC para limite de tentativas. Esses identificadores são pseudonimizados, não necessariamente anônimos. Expirados são removidos no próximo acesso ao banco de autenticação.

## Privacidade

`/privacy` descreve o funcionamento técnico, prestadores envolvidos, controles temporários e o canal omnixml@gmail.com. O responsável deve complementar a identificação do controlador, base legal e prazo do cadastro conforme a relação com clientes. Não se afirma conformidade jurídica automática. Não há checkbox genérico de consentimento para substituir essa avaliação.

XMLs, A1 e senhas continuam no processamento fiscal temporário existente, sem novo acervo permanente. Exclusão do cadastro não apaga automaticamente e-mails enviados, cópias no computador do cliente ou backups dos prestadores.

## Verificar após implantar

1. Entrar com administrador e verificar acesso ao painel.
2. Configurar armazenamento persistente e liberar um cliente.
3. Cliente valida código, recupera XML e não consegue acessar APIs administrativas.
4. Bloquear cliente e confirmar revogação; reativar e exigir novo login.
5. Confirmar monitor agregado e indicação do worker, sem dados pessoais.
6. Reimplantar e conferir persistência do cadastro, com nova autenticação se necessário.


## Neon / PostgreSQL no Render gratuito

1. Crie um projeto OmniXML no Neon, plano Free.
2. Abra Connect, selecione conexão com pooling e copie a URI PostgreSQL completa. Preserve `sslmode=require` e `channel_binding=require` quando presentes.
3. No Render → OmniXML → Environment, adicione `OMNIXML_CLIENTS_DATABASE_URL` com essa URI. Não coloque a URI em prints, mensagens, GitHub ou JavaScript do navegador.
4. Defina `OMNIXML_ADMIN_EMAILS=omnixml@gmail.com` para deixar explícito o administrador. Mantenha as configurações Gmail existentes.
5. Salve e faça deploy. Entre em `/login` com o e-mail administrador e abra `/admin`. A tabela é criada automaticamente no primeiro acesso ao cadastro.
6. Cadastre um e-mail de teste, valide sua entrada, bloqueie e confirme que a sessão perdeu o acesso. Faça um novo deploy e confira que o cadastro permanece.

A URL PostgreSQL tem prioridade sobre OMNIXML_CLIENTS_DB. Não há migração automática de um cadastro SQLite existente. Os e-mails em OMNIXML_ALLOWED_EMAILS continuam como exceções gerenciadas pelo Render: para administrar clientes pelo painel, remova os e-mails desses clientes da variável e cadastre-os no painel. O administrador permanece na variável OMNIXML_ADMIN_EMAILS.

Somente a tabela clients (email, active, created) é persistida no Neon. Códigos e sessões continuam no armazenamento temporário de autenticação; XMLs, certificados, senhas fiscais e métricas não são enviados ao Neon. O serviço de banco pode manter logs e backups próprios, conforme sua configuração e política. A conexão exige TLS e tem timeout de 15 segundos. Use o endpoint com pooling para as conexões curtas do aplicativo.


## Cloudflare D1 (opção escolhida)

O aplicativo continua no Render. O cadastro usa a API HTTPS do D1 diretamente do servidor; o navegador nunca recebe token ou SQL. Nenhum Worker adicional é necessário.

1. Na Cloudflare, abra D1 e crie `omnixml-clientes`.
2. Copie o ID da conta e o UUID do banco.
3. Crie um API Token personalizado com permissão da conta D1 Edit (D1 Write), limitado à conta do OmniXML. Não use Global API Key. A permissão de D1 pode abranger os outros bancos D1 da mesma conta: use conta dedicada caso precise isolar esse escopo.
4. No Render, configure `OMNIXML_D1_ACCOUNT_ID`, `OMNIXML_D1_DATABASE_ID`, `OMNIXML_D1_API_TOKEN` e `OMNIXML_ADMIN_EMAILS=omnixml@gmail.com`. Preserve as configurações Gmail.
5. Remova `OMNIXML_CLIENTS_DATABASE_URL` se havia configurado Neon, para evitar confusão. As variáveis D1 têm prioridade; configuração parcial ou falha remota nunca cai silenciosamente para outro banco.
6. Faça deploy, entre em `/login` e abra `/admin`. A tabela clients é criada automaticamente. Cadastre, valide, bloqueie, reative e remova um cliente de teste. Depois de um deploy, confirme que o cadastro continua presente.

O D1 guarda somente email, active e created. Não há migração automática de registros de outro banco. E-mails em OMNIXML_ALLOWED_EMAILS permanecem exceções do servidor e devem sair dessa variável para serem geridos pelo painel. Códigos e sessões continuam temporários; XML, A1, senha fiscal e monitor não são enviados ao D1. Logs, recuperação e backups do provedor seguem as políticas da Cloudflare. As quotas gratuitas do D1 e da API são aplicáveis; não são ilimitadas. Falhas do D1 retornam erro 503 sem expor token nem resposta do provedor. Bloqueios dependem da consulta ao cadastro a cada validação de sessão, sem cache de autorização.


## Login único do portal

Todo o portal exige uma sessão validada por código. Sem sessão, páginas redirecionam para /login e APIs retornam 401. Login validado abre a auditoria (/), e a mesma sessão vale para downloads e consultas. Administração continua limitada aos e-mails administradores. Token fiscal legado não permite passar pela proteção global. Logout revoga a sessão; bloqueio no cadastro é verificado nas próximas requisições. Login, privacidade, saúde, arquivos estáticos e endpoints de autenticação permanecem públicos. A sessão continua temporária: reinício/deploy pode exigir novo código.
