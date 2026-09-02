# OmniXML — Documento de Engenharia

> Especificação viva da arquitetura e dos fluxos implementados. Alterações funcionais devem atualizar código, testes e este documento.

## 1. Escopo

O OmniXML é uma aplicação de auditoria fiscal. A arquitetura web de produção prioriza processamento local de documentos fiscais no navegador, reduzindo a exposição de XMLs ao backend.

## 2. Arquitetura de produção

```text
Navegador do usuário
  ├─ seleção File / webkitdirectory
  ├─ File.text()
  ├─ DOMParser
  ├─ validação e classificação
  ├─ consolidação fiscal
  └─ dashboard / exportação
          │
          │ somente HTTP de aplicação estática/dinâmica
          ▼
Flask + Gunicorn / Render
  └─ entrega dashboard, JavaScript e healthcheck
```

O backend `web_app_browser.py` não possui endpoint de upload de XML no fluxo de produção atual.

## 3. Pipeline principal

```text
Arquivo selecionado
 → leitura local
 → parsing XML
 → identificação do tipo documental
 → validação estrutural/autorização
 → extração fiscal
 → identificação da empresa auditada
 → classificação Entrada/Saída
 → conciliação de cancelamentos
 → consolidações
 → diagnóstico
 → dashboard
```

## 4. Tipos documentais

### 4.1 NF-e / NFC-e
Raízes tratadas no processamento principal: `NFe` e `nfeProc`. O elemento `infNFe` fornece identificação e conteúdo fiscal. O modelo (`ide/mod`) diferencia 55 e 65.

Campos relevantes atualmente extraídos incluem chave, `nNF`, série, emissão, `vNF`, emitente, destinatário e itens. Nos itens são utilizados campos como produto, NCM, CFOP, CST/CSOSN, quantidade e valores.

### 4.2 Cancelamento
Eventos com `tpEvento = 110111` são relacionados pela `chNFe`. O fluxo considera confirmação conforme os status tratados pelo processador. A nota cancelada permanece na coleção de notas e ocupa sua numeração; seu status é alterado para cancelado.

### 4.3 Inutilização
Um capturador local reconhece estruturas `procInutNFe`, `retInutNFe` e `inutNFe`. São extraídos modelo, série, faixa inicial/final, CNPJ, justificativa e status quando disponíveis. Para conciliação automática da sequência, somente inutilização homologada com `cStat = 102` é tratada como justificativa.

## 5. Identificação da empresa

O processador calcula frequência de CNPJs emitentes. NFC-e tem prioridade como fonte de identificação; na ausência, utiliza os emitentes das notas disponíveis. O CNPJ mais frequente torna-se candidato à empresa auditada.

Essa estratégia é uma heurística operacional e deve permanecer explicitamente documentada e testada. Futuramente pode ser substituída ou complementada por seleção explícita de CNPJ.

## 6. Classificação de operação

Depois da identificação da empresa:

```text
emitente == CNPJ auditado      → Saída
destinatário == CNPJ auditado  → Entrada
caso contrário                 → Não classificada
```

A classificação por participante prevalece sobre inferências baseadas em nome de pasta.

## 7. Consolidação

A coleção de notas é deduplicada por chave. O dashboard produz visões de CFOP, CST/CSOSN, série, faturamento diário, auditoria e produtos. Documentos cancelados e valores não positivos são excluídos das consolidações financeiras onde definido pelo processador.

## 8. Sequência e fechamento

A sequência é calculada somente para documentos de **Saída** e separada por **modelo + série**.

Para cada grupo:

```text
inicial = menor nNF encontrado na pasta
final   = maior nNF encontrado na pasta
intervalo = [inicial, final]
```

Números existentes em NF-e/NFC-e são utilizados, inclusive quando a nota está cancelada. Números ausentes são cruzados com faixas de inutilização homologadas do mesmo modelo e série. O restante fica como **A conferir**.

Entradas de fornecedores nunca devem contaminar essa sequência.

## 9. Validação fiscal estrutural no navegador

`browser_validation.js` intercepta a leitura local para verificar condições mínimas antes de o documento alimentar o dashboard. A implementação atual verifica, entre outros pontos:

- XML parseável;
- presença de `infNFe`;
- existência do processo/protocolo de autorização para documento final;
- `protNFe/infProt`;
- status de autorização aceito pela regra atual;
- assinatura XML;
- coerência de chave entre `infNFe` e protocolo;
- QR Code para NFC-e quando aplicável.

Isto não deve ser descrito como validação XSD oficial completa.

## 10. Modelo de erros

Falhas de leitura/validação são agregadas à coleção de erros, preservando caminho/arquivo e motivo. Módulos auxiliares enriquecem a tabela com metadados capturados do XML e deduplicam a contagem por arquivo.

## 11. Segurança

### 11.1 Fronteira de confiança
Todo XML selecionado deve ser considerado entrada não confiável, mesmo quando fornecido pelo próprio usuário. Texto extraído de XML não deve ser inserido como HTML executável sem escape/sanitização.

### 11.2 Privacidade
O desenho browser-local evita upload fiscal no fluxo web atual. Uma futura API, persistência, autenticação, certificado digital ou integração SEFAZ muda a fronteira de segurança e exige nova análise de ameaça.

### 11.3 Hardening HTTP
A aplicação aplica cabeçalhos de segurança, incluindo CSP, proteção contra framing, `nosniff`, política de referência, restrição de permissões e isolamento de origem. A CSP aplicada em produção bloqueia objetos, frames e mídia não necessários. Como o dashboard ainda possui scripts inline legados, a política aplicada ainda contém `unsafe-inline` em `script-src`.

A Fase 3 acrescenta uma segunda política `Content-Security-Policy-Report-Only` sem `unsafe-inline` em scripts. Ela não bloqueia o dashboard atual; serve para mapear violações e orientar a migração dos scripts inline antes de tornar a política estrita obrigatória.

### 11.4 XML hostil, XSS e disponibilidade
`browser_security_v2.js` permanece como primeira camada de compatibilidade: strings destinadas às principais DataTables são escapadas antes da renderização e a seleção local recebe limites preventivos de recursos.

Limites atuais:

- até 50.000 arquivos por execução;
- até 20 MB por XML individual;
- até 1,5 GB no conjunto selecionado.

A Fase 3 adiciona `browser_security_v3.js`, carregado antes do processador fiscal. Sua função é defesa em profundidade contra regressões de DOM/XSS e navegação insegura. Em nós adicionados dinamicamente ao DOM, o módulo remove tags executáveis ou embutíveis (`script`, `iframe`, `object`, `embed`, `base`), atributos de evento não confiáveis, `srcdoc` e URLs com esquemas perigosos como `javascript:`, `vbscript:` e HTML em `data:` URLs.

O único handler inline dinâmico preservado por compatibilidade é a ação de consulta SEFAZ, e somente quando segue o formato esperado: chave numérica de 44 dígitos e destino pertencente à lista de domínios fiscais permitidos. A função `copiarEAbrir` também é envolvida por uma validação equivalente antes de abrir destino externo.

Essas proteções não encerram a migração. A meta arquitetural continua sendo remover os sinks `innerHTML`/HTML dinâmico na origem, substituir dados por `textContent` ou renderizadores seguros e, então, retirar `unsafe-inline` da CSP aplicada.

## 12. Dependências

Produção Python: Flask, defusedxml e Gunicorn. Dependências permanecem com faixas de versão controladas. O Dependabot monitora Python e GitHub Actions e o CI executa `pip-audit` sobre `requirements-prod.txt`, fazendo vulnerabilidades conhecidas detectadas pelo scanner falharem a validação do PR.

Dependências JavaScript externas devem ser inventariadas; SRI ou hospedagem local são preferíveis quando compatíveis com a aplicação.

## 13. Testes e CI

GitHub Actions executa auditoria de dependências e `pytest` em Pull Requests para `main`. O ruleset `Protect main` exige PR e status check antes do merge, bloqueia force push e exclusão da branch principal.

A Fase 2 possui testes de presença/ordem do módulo, limites de seleção e sanitização das tabelas. A Fase 3 adiciona testes de regressão para CSP estrita em modo Report-Only, bloqueio de vetores DOM/XSS, validação de navegação SEFAZ e ordem de carregamento do novo módulo.

Regra de engenharia do projeto:

```text
mudança funcional = código + teste + documentação
```

## 14. Deploy

Produção é servida por Gunicorn com o módulo `web_app_browser:app`. O Render acompanha a branch principal conforme configuração do serviço. O arquivo `render.yaml` documenta a intenção de infraestrutura, mas serviços já criados podem possuir configuração própria no painel do provedor.

## 15. Limites e backlog técnico

- validação XSD oficial SEFAZ;
- processamento SPED/EFD integralmente local;
- inventário e redução de CDNs;
- remoção dos sinks `innerHTML`/renderizadores inseguros na origem;
- migração dos handlers e scripts inline do template para arquivos externos;
- remoção de `unsafe-inline` da CSP aplicada após a migração;
- testes end-to-end em navegador com payloads XSS adversariais;
- dependências JS locais/SRI;
- Web Workers para cargas grandes;
- testes de carga para calibrar limites de arquivos/memória;
- eventual PWA/offline.

## 16. Princípio de classificação de achados

Resultados devem distinguir:

1. **Erro:** condição objetivamente incompatível com a estrutura/regra implementada.
2. **Inconsistência:** divergência entre fontes ou documentos que exige investigação.
3. **Alerta:** combinação ou comportamento potencialmente atípico.
4. **Informação:** dado de apoio sem conclusão fiscal.

O software deve evitar transformar heurística em afirmação fiscal definitiva.
