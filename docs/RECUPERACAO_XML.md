# Recuperação de XML com A1

Acesse **Recuperar XMLs · A1** no menu ou `/downloads`. Informe um A1 e-CNPJ, a senha, a UF do titular e até 20 chaves, uma por linha. O CNPJ é extraído do certificado. Use **Recuperar XMLs**, ou **Consultar situação** para NFC-e/SP. Cada resultado tem um download individual; o ZIP é gerado no navegador e contém somente os arquivos finais recuperados.

## Cobertura desta versão

| Documento | Cobertura | Limites |
|---|---|---|
| NF-e, modelo 55 | Todas as UFs, via distribuição nacional | Somente documentos liberados ao titular pelo Ambiente Nacional; o emitente não pode recuperar sua própria NF-e por esse serviço. Resumo/eventos não são convertidos em nota. A disponibilização pode depender de manifestação já feita no sistema fiscal. |
| NFC-e, modelo 65 | SP, SAE-NFC-e + consulta de protocolo | Exige certificado do emitente; sujeito à janela e às regras do SAE. Consulta de situação disponível separadamente. |
| NFC-e de outras UFs, CT-e, MDF-e etc. | Ainda não implementados | A interface informa cobertura e rejeita essas chaves antes de qualquer consulta. |

Somente produção. O aplicativo não envia manifestações ou outros eventos fiscais. Não obtém dados de páginas públicas nem contorna permissões da SEFAZ. Não há consulta de situação de NF-e nesta versão; o cStat 138 indica distribuição de documentos, não a situação atual da nota.

## Servidor

Instale `requirements-prod.txt` e use `web_app_browser:app`. O portal inteiro exige autenticação individual por código; sem sessão, páginas redirecionam ao login e APIs retornam 401. Configure o provedor de email e o segredo conforme [ACESSO_EMAIL.md](ACESSO_EMAIL.md). A auditoria é executada localmente no navegador depois do login.

No Render use HTTPS e as configurações Gmail/D1 já descritas. `OMNIXML_SEFAZ_TOKEN` é legado: não precisa ser informado pelo cliente e não substitui a sessão na proteção global. O A1 continua necessário para as permissões fiscais. O fluxo de autenticação exige HTTPS também em testes manuais locais; HTTP simples por localhost não contorna o login do portal.

O `render.yaml` configura um único worker, quatro threads e timeout de 180 s. `OMNIXML_TRUST_PROXY=1` confia em um único proxy somente para o esquema HTTPS; habilite apenas atrás de proxy confiável que substitui `X-Forwarded-Proto`. Hosts e IPs encaminhados não são utilizados.

Há uma consulta fiscal ativa por processo, orçamento local de 20 consultas/hora por CNPJ na distribuição nacional e 120/hora no SAE (incluindo situação), além de pausa de uma hora após cStat 137/656. Esses limites locais não substituem as regras da SEFAZ. Sem repetição automática. Interromper lote termina a consulta atual e não inicia as seguintes. Mantenha um worker/uma instância: os controles são em memória; múltiplas instâncias exigem um coordenador compartilhado antes de ativar o módulo.

## Dados e resultado

Esta área é uma exceção explícita ao processamento local: o certificado, a senha e a chave vão ao backend para conexão mTLS com a SEFAZ. O upload do A1 usa memória, sem o spool em disco padrão do Flask. A senha e as respostas intermediárias também ficam em memória, sem cache, logs de SOAP ou persistência no aplicativo. Para carregar a identidade no TLS, `requests-pkcs12` utiliza um arquivo temporário com chave PEM criptografada por uma senha aleatória, removido imediatamente após carregar o contexto SSL (inclusive em falhas). Nenhum XML intermediário é gravado. Isso não garante limpeza física imediata da memória do runtime; configure a infraestrutura sem captura de corpos HTTP ou dumps de memória. A auditoria existente não passa a enviar seus XMLs locais.

No SAE, a nota original é combinada com o `protNFe` real da consulta. São conferidos chave, modelo, produção, campos do protocolo, número do protocolo SAE e coincidência entre `digVal` e o `DigestValue` da assinatura. Na distribuição nacional, só se aceita `nfeProc` completo da chave. Não são fabricados protocolos, dados fiscais ou assinaturas. Não há validação criptográfica completa da assinatura, cadeia ICP-Brasil ou validação completa por XSD nesta etapa; valide a importação no sistema fiscal.

Nota cancelada pode trazer o protocolo de autorização original. O resultado de situação é mostrado com aviso de cancelamento, e o XML final não inclui o evento de cancelamento. Recuperação não deve ser interpretada como confirmação da validade atual.

Os downloads têm `Cache-Control: no-store`. Limites: 2 MB para A1, 3 MB para envio, 20 MB para resposta/documento descompactado; XML com DTD/entidades é rejeitado, destinos fixos HTTPS, redirecionamentos bloqueados, validação TLS habilitada. Não envie certificados reais para issues, testes ou commits.

## Referências oficiais

- [SAE-NFC-e/SP](https://portal.fazenda.sp.gov.br/servicos/nfce/Paginas/sae-nfce.aspx)
- [Web Services NFC-e/SP](https://portal.fazenda.sp.gov.br/servicos/nfce/Paginas/WebServices.aspx)
- [Serviços nacionais NF-e](https://www.nfe.fazenda.gov.br/portal/webServices.aspx)
- [Notas técnicas: NT 2014.002 (distribuição DF-e)](https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=04BIflQt1aY=)

## Validação

Execute `python -m pytest -q` e `python -m pip_audit -r requirements-prod.txt`. Os testes usam certificados e XMLs sintéticos, com transporte fiscal simulado. Depois de configurar o servidor, faça homologação operacional com um A1 próprio e uma chave autorizada em produção: confirme cStat e conteúdo, importe o XML no sistema fiscal e confira que apenas o arquivo final foi baixado. A consulta real não foi executada pela implementação automatizada por falta de A1 autorizado.

### Diagnóstico de falhas de conexão

A tela distingue validação da cadeia TLS, negociação TLS, timeout, erro HTTP (somente código), rede/DNS e contrato SOAP. Informa também a etapa: carregar A1 no TLS, obter WSDL ou executar SOAP. O log registra apenas etapa e categoria fixa (`sefaz_recovery_failure`), sem mensagens brutas de exceção, certificado, senha, token ou envelope SOAP. A falha interrompe as próximas consultas do lote. O diagnóstico não desabilita a validação TLS nem altera automaticamente o certificado ou sua cadeia.

O contexto TLS do A1 carrega explicitamente as autoridades confiáveis do sistema operacional e o bundle CA do Requests. Mantém verificação de cadeia e hostname habilitadas. As CAs incluídas no A1 enviado pelo usuário não são promovidas a autoridades de confiança do servidor. Em falhas de verificação, a interface mostra o código numérico OpenSSL e uma descrição fixa, quando disponível. Essa configuração não garante que toda cadeia publicada pela SEFAZ esteja completa ou confiável: uma CA oficial ausente exige validação e instalação pelo administrador.

### Cadeia pública ICP-Brasil v10 para NFC-e/SP

O provedor NFC-e/SP carrega também a raiz ICP-Brasil v10 e a intermediária AC SOLUTI SSL EV publicadas no pacote oficial SEFAZ/SP, incluídas em `certs/sefaz-sp-ca.pem`. Fontes, validade e fingerprints estão em `certs/README.md`. Essa cadeia é conferida antes do uso e adicionada apenas ao adapter do host da NFC-e/SP, preservando sistema + Requests, verificação da cadeia e hostname. Não precisa configurar outra variável no Render. O TLS 20 pode persistir se o serviço usar outra raiz ou omitir uma intermediária não incluída; nesse caso, é preciso conferir a cadeia efetivamente servida. O teste operacional com A1 no Render ainda é necessário.
