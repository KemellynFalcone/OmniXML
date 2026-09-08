from pathlib import Path

path = Path('templates/dashboard.html')
html = path.read_text(encoding='utf-8')

marker = 'sped-empty-v23'
if marker in html:
    print('UX SPED v23 já materializada')
    raise SystemExit(0)

old_button = '<button onclick="confrontarSPED()" class="bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold py-2 px-4 rounded-lg transition-all shadow-sm border border-blue-200 flex items-center gap-2 text-sm">'
new_button = '<button onclick="confrontarSPED()" class="sped-import-cta bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-5 rounded-lg transition-all shadow-md flex items-center gap-2 text-sm">'
if old_button not in html:
    raise SystemExit('CTA histórico do SPED não encontrado')
html = html.replace(old_button, new_button, 1)

start_marker = '                    <div id="placeholder-sped" class="text-center py-16">'
end_marker = '                    <div id="resultado-sped" class="hidden space-y-6">'
start = html.find(start_marker)
end = html.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('Placeholder histórico do SPED não encontrado')

preview = '''                    <div id="placeholder-sped" class="sped-empty-v23">
                        <div class="sped-empty-v23__hero">
                            <div class="sped-empty-v23__copy">
                                <div class="sped-empty-v23__status"><span></span>Aguardando importação</div>
                                <h4>Antecipe a análise antes de importar o SPED</h4>
                                <p>Após a importação, este painel confrontará o SPED Fiscal com os XMLs já apurados pelo OmniXML e destacará diferenças para revisão.</p>
                                <p class="sped-empty-v23__note"><strong>Prévia visual:</strong> os elementos abaixo são apenas ilustrativos e não representam dados fiscais da empresa.</p>
                            </div>
                            <div class="sped-empty-v23__preview" aria-hidden="true">
                                <div class="sped-empty-v23__preview-head"><span>Visão da análise</span><span>Prévia</span></div>
                                <div class="sped-empty-v23__bars">
                                    <i class="sped-bar-a"></i><i class="sped-bar-b"></i><i class="sped-bar-c"></i><i class="sped-bar-d"></i><i class="sped-bar-e"></i>
                                </div>
                                <div class="sped-empty-v23__preview-foot"><span>XMLs</span><span>SPED</span><span>Revisão</span></div>
                            </div>
                        </div>
                        <div class="sped-empty-v23__steps">
                            <div><b>1</b><span><strong>Importe o SPED</strong><small>Selecione o arquivo .txt da escrituração fiscal.</small></span></div>
                            <div><b>2</b><span><strong>Confronte os dados</strong><small>O OmniXML compara o SPED com os XMLs processados.</small></span></div>
                            <div><b>3</b><span><strong>Revise divergências</strong><small>Abra o detalhe somente quando houver diferenças.</small></span></div>
                        </div>
                    </div>

'''
html = html[:start] + preview + html[end:]

style_close = '    </style>'
css = r'''
        /* UX SPED v23 - estado vazio conservador */
        .sped-import-cta { white-space: nowrap; }
        .sped-empty-v23 { width: 100%; padding: 1.25rem 0 0.5rem; text-align: left; }
        .sped-empty-v23__hero { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.75fr); gap: 1.25rem; align-items: stretch; }
        .sped-empty-v23__copy { border: 1px solid #e2e8f0; border-radius: 0.875rem; background: #f8fafc; padding: 1.35rem 1.5rem; min-width: 0; }
        .sped-empty-v23__status { display: inline-flex; align-items: center; gap: 0.45rem; color: #92400e; background: #fffbeb; border: 1px solid #fde68a; border-radius: 9999px; padding: 0.35rem 0.65rem; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; }
        .sped-empty-v23__status span { width: 0.45rem; height: 0.45rem; border-radius: 50%; background: #f59e0b; }
        .sped-empty-v23__copy h4 { margin-top: 0.9rem; color: #0f172a; font-size: 1.2rem; line-height: 1.35; font-weight: 800; }
        .sped-empty-v23__copy > p { margin-top: 0.45rem; color: #64748b; font-size: 0.875rem; line-height: 1.55; max-width: 48rem; }
        .sped-empty-v23__copy .sped-empty-v23__note { margin-top: 0.9rem; color: #475569; font-size: 0.76rem; }
        .sped-empty-v23__preview { border: 1px solid #dbeafe; border-radius: 0.875rem; background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%); padding: 1rem; min-width: 0; }
        .sped-empty-v23__preview-head { display: flex; justify-content: space-between; gap: 1rem; color: #1e3a8a; font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; }
        .sped-empty-v23__preview-head span:last-child { color: #64748b; }
        .sped-empty-v23__bars { height: 7rem; display: flex; align-items: flex-end; justify-content: center; gap: 0.65rem; padding: 1rem 0.5rem 0.65rem; border-bottom: 1px solid #dbeafe; }
        .sped-empty-v23__bars i { display: block; width: 1.4rem; border-radius: 0.3rem 0.3rem 0 0; background: #93c5fd; }
        .sped-empty-v23__bars .sped-bar-a { height: 35%; } .sped-empty-v23__bars .sped-bar-b { height: 62%; } .sped-empty-v23__bars .sped-bar-c { height: 48%; } .sped-empty-v23__bars .sped-bar-d { height: 78%; } .sped-empty-v23__bars .sped-bar-e { height: 68%; }
        .sped-empty-v23__preview-foot { display: flex; justify-content: space-between; gap: 0.5rem; margin-top: 0.55rem; color: #64748b; font-size: 0.65rem; }
        .sped-empty-v23__steps { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.75rem; margin-top: 0.9rem; }
        .sped-empty-v23__steps > div { display: flex; gap: 0.65rem; align-items: flex-start; border: 1px solid #e2e8f0; border-radius: 0.75rem; background: #ffffff; padding: 0.8rem; min-width: 0; }
        .sped-empty-v23__steps b { display: inline-flex; flex: 0 0 1.55rem; width: 1.55rem; height: 1.55rem; align-items: center; justify-content: center; border-radius: 50%; background: #dbeafe; color: #1d4ed8; font-size: 0.7rem; }
        .sped-empty-v23__steps span { min-width: 0; }
        .sped-empty-v23__steps strong { display: block; color: #334155; font-size: 0.78rem; }
        .sped-empty-v23__steps small { display: block; margin-top: 0.15rem; color: #64748b; font-size: 0.7rem; line-height: 1.35; }
        @media (max-width: 1050px) { .sped-empty-v23__hero { grid-template-columns: 1fr; } .sped-empty-v23__preview { display: none; } }
        @media (max-width: 760px) { .sped-empty-v23__steps { grid-template-columns: 1fr; } .sped-empty-v23__copy { padding: 1rem; } }
'''
if style_close not in html:
    raise SystemExit('Bloco style do dashboard não encontrado')
html = html.replace(style_close, css + style_close, 1)

path.write_text(html, encoding='utf-8')
print('UX SPED v23 materializada com sucesso')
