# Recuperação do XML original de NFC-e por chave e A1

Levantamento em 02/10/2026, com foco em GO, MG, SP, PR, MT e MS.

O objetivo é obter o XML original quando o cliente perdeu o arquivo. Consultar `retConsSitNFe` ou completar o protocolo de um XML existente não resolve esse objetivo. Não reconstruímos itens, tributos ou assinaturas a partir da visualização pública.

## Resultado e implementação

| UF | XML original sem arquivo prévio | No OmniXML |
| --- | --- | --- |
| SP | Serviço web SAE documentado: chave + e-CNPJ do contribuinte | Download automático já integrado e previamente testado pelo usuário |
| GO | Sistema oficial de recuperação de XML, incluindo NFC-e de saída, com certificado da empresa; fila de solicitações | Orientação por chave e link para o portal; integração automática não validada |
| MG | Não foi confirmado download automático de NFC-e; backup administrativo encontrado está identificado como NF-e | Orientação explícita para confirmar escopo com a SEF, sem tratar NF-e como NFC-e |
| PR | Não foi confirmado serviço de download do XML original de NFC-e nas fontes consultadas | Link para portal oficial e indicação da limitação |
| MT | Fonte oficial prevê fornecimento de cópia em caso de perda com TSE por documento, exceto MEI | Orientação e fonte oficial; sem solicitação ou pagamento automático |
| MS | Consulta pública confirmada; recuperação atual de XML completo não confirmada | Link para consulta oficial, identificada como consulta |

Não encontrar documentação não prova que um serviço inexiste. A cobertura permanece pendente onde não foi verificado um contrato ou fluxo autenticado para o documento modelo 65.

Ao clicar em Baixar XMLs, as chaves de UFs com orientação são tratadas no navegador: não é enviado A1, senha ou chave à API fiscal do OmniXML para essas linhas. O link abre o portal oficial sem colocar a chave na URL. O botão Copiar chave depende da área de transferência do navegador; se indisponível, o usuário pode selecionar a chave na tabela. Chaves SP/NF-e nacional e consultas continuam pelo fluxo existente com A1. Orientações não contam como XMLs disponíveis nem entram no ZIP.

O complemento de protocolo fica em seção separada para quem já possui XML assinado.

## Fontes oficiais

- SP: https://portal.fazenda.sp.gov.br/servicos/nfce/Paginas/saenfce.aspx
- GO: https://agenciacoradenoticias.go.gov.br/economia-disponibiliza-novo-sistema-de-download-de-nf-e-nfc-e-e-ct-e/ (publicado em 28/08/2025). Explica fila, saída com certificado da empresa e entrada/saída com login do contabilista.
- GO, catálogo e link do serviço: https://goias.gov.br/economia/documentos-fiscais/
- GO, portal vinculado pelo catálogo: https://nfeweb.sefaz.go.gov.br/nfeweb/sites/nfe/consulta-publica/principal
- MG, web services: https://portalsped.fazenda.mg.gov.br/spedmg/nfce/web-services/ . Serviços publicados de consulta, autorização, eventos, inutilização e status; não apresenta serviço de download NFC-e nessa relação.
- MG, backup identificado como NF-e: https://www.mg.gov.br/servico/solicitar-backup-de-arquivo-xml-nf-e . Não assumir que seu escopo inclui NFC-e sem confirmação.
- PR: https://sped.fazenda.pr.gov.br/NFCe/Pagina/Web-Services-NFC-e e https://sped.fazenda.pr.gov.br/NFCe
- MT: https://www5.sefaz.mt.gov.br/servicos?c=16773297&e=74924341&s=74925891 . Informa TSE por cópia e exceção MEI. Não foi apurado valor nem realizado pagamento.
- MS, consulta por chave: https://www.dfe.ms.gov.br/nfce/consulta/
- Serviços de consulta NFC-e: https://dfe-portal.svrs.rs.gov.br/NFCE/Servicos

## Limites da investigação e próximo requisito técnico

O portal novo de GO não pôde ser inspecionado neste ambiente: acesso sem certificado apresentou timeout/erro de recuperação. A página antiga de certificado de consulta de lotes retornou HTML JSF com sessão, sem fornecer contrato para recuperar XML por chave. Não foi enviada chave de cliente nem certificado real a esses serviços. Não é correto implementar um endpoint presumido ou declarar suporte automático com base apenas no anúncio de um portal.

Para avançar em GO, é preciso observar o fluxo real autenticado no computador autorizado do cliente e verificar como solicita o arquivo, aguarda a fila e obtém o download. Se houver contrato de integração oficial, criar adaptador limitado aos destinos verificados, com processamento temporário, validação do XML original e limites de consumo. Se for exclusivamente portal interativo, manter recuperação assistida sem contornar CAPTCHA ou permissões.

Em MG, PR, MT e MS, confirmar com a SEFAZ o serviço e a permissão para recuperação do modelo 65; uma resposta de consulta de status não demonstra download. Nenhum contato externo foi enviado nesta tarefa.
