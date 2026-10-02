# Segurança — visão consolidada

## Princípios atuais

O OmniXML trata dados fiscais como entrada não confiável. Campos vindos de XML, SPED, nomes de arquivo e textos auxiliares não devem ser interpretados como HTML executável.

A arquitetura de segurança prioriza:

- `textContent` e APIs seguras de DOM para conteúdo dinâmico;
- escape explícito quando renderizadores precisam retornar marcação controlada;
- migração de handlers inline para listeners externos;
- Content Security Policy progressivamente mais restritiva;
- dependências de front-end fixadas e, quando possível, servidas localmente;
- processamento fiscal no navegador, sem envio dos XMLs ao servidor;
- testes automatizados para impedir regressões de segurança.

## XSS e DOM

A base segura é:

`dado fiscal não confiável → tratamento/escape → DOM`

Evitar concatenação de HTML com valores fiscais, nomes, motivos, produtos, razão social ou qualquer texto vindo de arquivo importado.

## CSP e scripts

A evolução de segurança removeu dependências de `unsafe-inline` conforme handlers e scripts foram migrados. A CSP deve permanecer alinhada aos assets realmente utilizados em produção.

## Dependências locais

A evolução mais recente documentada mantém Chart.js 4.5.1 servido localmente. jQuery e JSZip também passaram por fixação/localização em fases anteriores. Dependências externas remanescentes devem ser reduzidas de forma controlada e acompanhadas por testes.

## Arquitetura browser-local

O princípio central permanece: o processamento dos arquivos fiscais ocorre localmente no navegador. O backend não deve receber o conteúdo integral dos XMLs apenas para executar a auditoria.

## Validação

Mudanças de segurança devem preservar:

- regras fiscais;
- classificação Entrada/Saída;
- compatibilidade com CNPJ alfanumérico;
- inutilização e sequência;
- exportações e relatórios;
- funcionamento do dashboard.

## Histórico

As fases de segurança 4 a 21 foram preservadas integralmente em `docs/historico/seguranca/`. Esses arquivos registram a evolução passo a passo e servem como trilha de auditoria técnica; este documento representa a visão consolidada atual.

## Login, administração e recuperação com A1

O portal de produção é `web_app_browser:app`. Páginas privadas exigem sessão e APIs privadas retornam 401 sem login. APIs administrativas verificam o papel no servidor; ocultar o link não é o controle de permissão. Administradores são definidos por `OMNIXML_ADMIN_EMAILS`, com fallback para o remetente, e nunca pelo cadastro de clientes.

Senhas individuais usam scrypt. Convites de uma hora são consumidos atomicamente; redefinir a senha altera a versão durável e revoga sessões anteriores. Sessões opacas de oito horas usam HMAC no armazenamento e cookie Secure, HttpOnly e SameSite=Strict. POSTs de autenticação, administração e recuperação exigem HTTPS e origem correspondente. Limites de tentativa e mensagens genéricas reduzem abuso e descoberta de contas. O reCAPTCHA v2 opcional exige validação no servidor, inclusive do hostname e de erros de quota.

O cadastro mínimo fica no D1; autenticação fica no SQLite temporário e os contadores em RAM. A auditoria de arquivos importados é local ao navegador. Na recuperação, A1, senha e chave chegam ao servidor por HTTPS: o upload e o processamento fiscal usam memória, sem acervo permanente criado pelo aplicativo. O adapter requests-pkcs12 usa um arquivo PEM temporário criptografado, removido após carregar o contexto TLS; esse detalhe está documentado em RECUPERACAO_XML.md. Essa distinção deve permanecer clara na documentação. O processamento temporário não garante limpeza física imediata de memória nem elimina registros dos prestadores.

Consultas fiscais restringem destinos a hosts oficiais, recusam redirecionamentos, validam TLS/hostname e impõem limites de tempo, tamanho e descompressão. XML recebido recusa DTD e entidades externas. O certificado enviado não vira âncora de confiança do servidor. O token D1 fica exclusivamente no servidor.

HTTPS recebe HSTS com max-age de um ano, sem includeSubDomains. HTTP local não recebe HSTS. CSP impede scripts inline e enquadramento; algumas dependências visuais ainda usam CDNs permitidas explicitamente.

## Revisão de 02/10/2026

Revisão de código e regressão, sem teste de invasão independente:

- Corrigida diferença no cooldown que permitia inferir cadastro por solicitações consecutivas.
- Adicionado HSTS e regressão que distingue HTTPS de HTTP local.
- Documentação atualizada para login único, painel na barra lateral, D1 e senhas individuais.
- Atualizado o limite mínimo de pytest de desenvolvimento para versão corrigida indicada pelo scanner.
- Site público conferido sem sessão: / e /admin redirecionam ao login; APIs de clientes e cobertura retornam 401; /health e /privacy permanecem públicos.

Limites da revisão: testes simulam SEFAZ, reCAPTCHA e D1. Não validam todas as UFs, as credenciais reais, o escopo efetivo do token Cloudflare nem uma chave real de reCAPTCHA. A auditoria Python identifica vulnerabilidades conhecidas; não prova ausência de falhas e não cobre automaticamente arquivos JavaScript vendorizados.

Antes de ampliar operação: validar com conta cliente autorizada a criação e redefinição de senha, revogação por bloqueio e consulta fiscal real; conferir token D1 restrito à conta, logs/backups dos prestadores e completar identificação do controlador e retenção do cadastro. Esses dados de operação não podem ser inferidos só do código.

Para escala: o limite por origem pode ser compartilhado no Render, porque IP encaminhado não é aceito sem configuração de proxy confiável. SQLite de sessão e limites fiscais por processo pressupõem a implantação atual de uma instância/um worker. Mais instâncias exigem estado e limites compartilhados antes da expansão.

## Autenticação individual atual

Login por senha com scrypt, sessão de até oito horas, revogação durável por versão no D1, convites de uma hora e uso único e reCAPTCHA v2 opcional validado no servidor. O envio de códigos/Gmail foi removido. Senhas e convites em texto não são persistidos; permissões administrativas continuam restritas aos e-mails configurados no servidor. Veja [ACESSO_SENHA.md](ACESSO_SENHA.md), incluindo configuração inicial e limites atrás de proxies.
