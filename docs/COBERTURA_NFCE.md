# Cobertura de NFC-e — levantamento inicial em 02/10/2026

A tabela distingue o funcionamento atual do OmniXML das referências encontradas. “Em análise” não significa inexistência de serviço estadual. Nenhum download novo foi anunciado sem implementação e validação.

| UF | OmniXML | Evidência e próximo passo |
| --- | --- | --- |
| RO | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| AC | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| AM | Em análise | Portal oficial oferece download pelo DT-e; avaliar interface e permissões. |
| RR | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| PA | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| AP | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| TO | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| MA | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| PI | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| CE | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| RN | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| PB | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| PE | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| AL | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| SE | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| BA | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| MG | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| ES | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| RJ | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| SP | Download e situação | SAE oficial e download já validado com usuário. |
| PR | Em análise | Relação oficial apresenta consulta de protocolo para o autorizador; avaliar download separado e validar serviço da UF. |
| SC | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |
| RS | Em análise | Relação oficial apresenta consulta de protocolo para o autorizador; avaliar download separado e validar serviço da UF. |
| MS | Em análise | Relação oficial apresenta consulta de protocolo para o autorizador; avaliar download separado e validar serviço da UF. |
| MT | Em análise | Relação oficial apresenta consulta de protocolo para o autorizador; avaliar download separado e validar serviço da UF. |
| GO | Em análise | Relação oficial apresenta consulta de protocolo para o autorizador; avaliar download separado e validar serviço da UF. |
| DF | Em análise | Validar autorizador da UF e opção estadual de download; não há conector automático habilitado. |

## Fontes oficiais consultadas

- [SAE de SP](https://portal.fazenda.sp.gov.br/servicos/nfce/Paginas/sae-nfce.aspx): XML completo por chave com e-CNPJ do contribuinte.
- [Relação nacional de serviços NFC-e / SVRS](https://dfe-portal.svrs.rs.gov.br/NFCE/Servicos): AM, GO, MS, MT, PR, RS, SP e SVRS; os serviços de consulta listados não comprovam uma API de download completo.
- [Serviços NFC-e / PR](https://sped.fazenda.pr.gov.br/NFCe/Pagina/Web-Services-NFC-e).
- [Portal NFC-e / SVRS](https://dfe-portal.svrs.rs.gov.br/Nfce): menu Download XML; [aviso de download pela consulta completa](https://dfe-portal.svrs.rs.gov.br/Nfce/Noticias/2976), com certificado relacionado à nota. O endpoint de download não pôde ser inspecionado nesta pesquisa; validar manualmente antes de implementar.
- [Download XML / AM](https://www.sefaz.am.gov.br/portfolio-servicos/detalhes/2503): acesso pelo DT-e.

## Limites deste levantamento

SP foi validado em produção. As demais 26 UFs estão registradas para investigação; a pesquisa inicial é por autorizador e não uma auditoria completa dos portais de cada estado. Não foram feitas consultas reais com A1 de outros estados. Não reconstruir XML fiscal a partir do DANFE ou de consulta de protocolo.
