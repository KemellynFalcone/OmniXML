"""Verified recovery paths; a portal is never advertised as an integrated API.

Checked 2026-10-02. Only SP has a verified automatic NFC-e download adapter.
"""
RECOVERY_PATHS = {
    '35': dict(uf='SP', mode='automatic', title='Download automático no OmniXML',
               description='Informe a chave e o A1 do emitente. O download é feito pelo SAE.',
               url='https://portal.fazenda.sp.gov.br/servicos/nfce/Paginas/saenfce.aspx',
               link_label='Documentação do SAE'),
    '52': dict(uf='GO', mode='portal', title='Recuperação pelo portal de Goiás',
               description='Goiás oferece recuperação de XML de NFC-e de saída com certificado da empresa. Abra o portal, autentique-se com o certificado instalado no computador e solicite o arquivo. O portal trabalha com uma fila de solicitações; este fluxo ainda não está automatizado no OmniXML.',
               url='https://nfeweb.sefaz.go.gov.br/nfeweb/sites/nfe/consulta-publica/principal',
               link_label='Abrir recuperação na SEFAZ-GO'),
    '31': dict(uf='MG', mode='unconfirmed', title='Recuperação de NFC-e em MG em análise',
               description='Não foi confirmado um serviço para baixar o XML original de NFC-e pela chave. O serviço mineiro de backup encontrado está documentado como NF-e; é necessário confirmar com a SEF se também atende NFC-e. A consulta pública não substitui o XML original.',
               url='https://www.mg.gov.br/servico/solicitar-backup-de-arquivo-xml-nf-e',
               link_label='Ver serviço de backup NF-e da SEF-MG'),
    '41': dict(uf='PR', mode='unconfirmed', title='Download de NFC-e no PR em análise',
               description='Consulta pública e consulta de protocolo estão disponíveis. Ainda não foi confirmado um serviço oficial de download do XML original de NFC-e para integrar ao OmniXML. Consulte a Receita Estadual sobre a recuperação do arquivo perdido.',
               url='https://sped.fazenda.pr.gov.br/NFCe',
               link_label='Abrir portal oficial da NFC-e / PR'),
    '51': dict(uf='MT', mode='administrative', title='Cópia do XML pela SEFAZ-MT',
               description='A SEFAZ-MT informa fornecimento de cópia em caso de perda ou extravio com Taxa de Serviços Estaduais por documento, exceto para MEI. Verifique com a SEFAZ o procedimento e o valor. O OmniXML não solicita cópias nem gera ou paga taxas automaticamente.',
               url='https://www5.sefaz.mt.gov.br/servicos?c=16773297&e=74924341&s=74925891',
               link_label='Ver orientação oficial da SEFAZ-MT'),
    '50': dict(uf='MS', mode='unconfirmed', title='Download de NFC-e em MS em análise',
               description='A consulta por chave está disponível. Ainda não foi confirmado o acesso atual a um serviço oficial de download do XML original para integrar ao OmniXML. A visualização da nota não é um XML recuperado.',
               url='https://www.dfe.ms.gov.br/nfce/consulta/',
               link_label='Abrir consulta oficial da NFC-e / MS'),
}
