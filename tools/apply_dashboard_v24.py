from pathlib import Path

path = Path('templates/dashboard.html')
html = path.read_text(encoding='utf-8')

if 'dashboard-preview-v24' in html:
    print('Dashboard v24 já materializado')
    raise SystemExit(0)

# 1) Insere preview logo após os três KPIs, antes dos gráficos reais.
marker = '''                    </div>\n\n                    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 mb-6 mx-4 md:mx-0">\n                        <h4 class="font-bold text-slate-700 mb-6 flex items-center gap-2">'''
if marker not in html:
    raise SystemExit('Ponto de inserção do preview do Dashboard não encontrado')

preview = '''                    </div>\n\n                    <section id="dashboard-preview-v24" class="dashboard-preview-v24" aria-label="Prévia ilustrativa do dashboard">\n                        <div class="dashboard-preview-v24__head">\n                            <div>\n                                <span class="dashboard-preview-v24__eyebrow">Prévia do dashboard</span>\n                                <h4>Previsão de impacto e próximos passos</h4>\n                                <p>Uma visão do que o OmniXML destacará após a importação dos XMLs.</p>\n                            </div>\n                            <span class="dashboard-preview-v24__badge">Dados ilustrativos</span>\n                        </div>\n                        <div class="dashboard-preview-v24__grid" aria-hidden="true">\n                            <div class="dashboard-preview-v24__card">\n                                <strong>Prioridades de análise</strong>\n                                <div class="dashboard-preview-v24__donut"><span></span></div>\n                                <div class="dashboard-preview-v24__legend"><i></i> CST/CSOSN <i></i> CFOP <i></i> Revisões</div>\n                            </div>\n                            <div class="dashboard-preview-v24__card dashboard-preview-v24__flow">\n                                <strong>Motor de conformidade</strong>\n                                <div class="dashboard-preview-v24__flow-row"><span>Sistema / XMLs</span><b>→</b><span>Motor de conformidade</span><b>→</b><span>Revisão</span></div>\n                                <small>Importar → classificar → cruzar → priorizar</small>\n                            </div>\n                            <div class="dashboard-preview-v24__card">\n                                <strong>Previsão de impacto</strong>\n                                <div class="dashboard-preview-v24__bars"><i class="v24-a"></i><i class="v24-b"></i><i class="v24-c"></i><i class="v24-d"></i><i class="v24-e"></i></div>\n                                <div class="dashboard-preview-v24__axis"><span>Jan</span><span>Fev</span><span>Mar</span><span>Abr</span><span>Mai</span></div>\n                            </div>\n                        </div>\n                        <p class="dashboard-preview-v24__note">Nenhum valor desta prévia representa resultado fiscal da empresa. Os dados reais aparecem somente após a auditoria dos XMLs.</p>\n                    </section>\n\n                    <div id="dashboard-real-v24" class="hidden">\n                    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200 mb-6 mx-4 md:mx-0">\n                        <h4 class="font-bold text-slate-700 mb-6 flex items-center gap-2">'''
html = html.replace(marker, preview, 1)

# 2) Fecha o wrapper dos gráficos reais depois dos cards CFOP/CST.
end_marker = '''                    </div>\n                </div>\n            </div>\n\n            <!-- SPED FISCAL -->'''
if end_marker not in html:
    raise SystemExit('Fim do Dashboard Geral não encontrado')
html = html.replace(end_marker, '''                    </div>\n                    </div>\n                </div>\n            </div>\n\n            <!-- SPED FISCAL -->''', 1)

# 3) Depois da auditoria, troca preview pelos gráficos reais.
js_marker = "                document.getElementById('card-boas-vindas').classList.add('hidden');\n"
if js_marker not in html:
    raise SystemExit('Ponto de conclusão da auditoria não encontrado')
html = html.replace(js_marker, js_marker + "                document.getElementById('dashboard-preview-v24')?.classList.add('hidden');\n                document.getElementById('dashboard-real-v24')?.classList.remove('hidden');\n", 1)

# 4) CSS próprio, no bloco de estilo original (externalizado depois pelo servidor).
style_close = '    </style>'
css = r'''
        /* UX Dashboard v24 - preview de valor antes da importação */
        .dashboard-preview-v24 { margin: 0 0 1.5rem; border: 1px solid #e2e8f0; border-radius: 0.9rem; background: #ffffff; padding: 1.15rem; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03); }
        .dashboard-preview-v24__head { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 0.9rem; }
        .dashboard-preview-v24__eyebrow { display: block; color: #2563eb; font-size: 0.66rem; line-height: 1; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.35rem; }
        .dashboard-preview-v24__head h4 { color: #0f172a; font-size: 1rem; line-height: 1.35; font-weight: 800; }
        .dashboard-preview-v24__head p { color: #64748b; font-size: 0.76rem; margin-top: 0.2rem; }
        .dashboard-preview-v24__badge { flex-shrink: 0; color: #475569; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 0.4rem; padding: 0.32rem 0.55rem; font-size: 0.62rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; }
        .dashboard-preview-v24__grid { display: grid; grid-template-columns: 0.9fr 1.45fr 0.9fr; gap: 0.75rem; }
        .dashboard-preview-v24__card { min-width: 0; min-height: 9.2rem; border: 1px solid #e2e8f0; border-radius: 0.7rem; background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); padding: 0.8rem; overflow: hidden; }
        .dashboard-preview-v24__card > strong { display: block; color: #334155; font-size: 0.72rem; margin-bottom: 0.55rem; }
        .dashboard-preview-v24__donut { width: 4.8rem; height: 4.8rem; margin: 0.2rem auto 0.45rem; border-radius: 50%; background: conic-gradient(#3b82f6 0 44%, #94a3b8 44% 78%, #e2e8f0 78% 100%); display: grid; place-items: center; }
        .dashboard-preview-v24__donut span { width: 2.55rem; height: 2.55rem; border-radius: 50%; background: #ffffff; }
        .dashboard-preview-v24__legend { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 0.25rem 0.4rem; color: #64748b; font-size: 0.56rem; }
        .dashboard-preview-v24__legend i { width: 0.38rem; height: 0.38rem; border-radius: 50%; background: #60a5fa; }
        .dashboard-preview-v24__flow { display: flex; flex-direction: column; justify-content: space-between; }
        .dashboard-preview-v24__flow-row { display: grid; grid-template-columns: 1fr auto 1.15fr auto 0.8fr; gap: 0.35rem; align-items: center; margin: auto 0; }
        .dashboard-preview-v24__flow-row span { min-width: 0; text-align: center; border: 1px solid #dbeafe; border-radius: 0.55rem; background: #eff6ff; color: #1e40af; padding: 0.7rem 0.35rem; font-size: 0.6rem; font-weight: 700; }
        .dashboard-preview-v24__flow-row b { color: #94a3b8; font-size: 0.85rem; }
        .dashboard-preview-v24__flow small { text-align: center; color: #94a3b8; font-size: 0.58rem; }
        .dashboard-preview-v24__bars { height: 5.5rem; display: flex; align-items: flex-end; justify-content: center; gap: 0.45rem; border-bottom: 1px solid #e2e8f0; padding: 0.35rem 0.2rem 0; }
        .dashboard-preview-v24__bars i { display: block; width: 0.9rem; border-radius: 0.2rem 0.2rem 0 0; background: #94a3b8; }
        .dashboard-preview-v24__bars .v24-a { height: 34%; } .dashboard-preview-v24__bars .v24-b { height: 55%; background: #60a5fa; } .dashboard-preview-v24__bars .v24-c { height: 46%; } .dashboard-preview-v24__bars .v24-d { height: 72%; } .dashboard-preview-v24__bars .v24-e { height: 86%; background: #3b82f6; }
        .dashboard-preview-v24__axis { display: flex; justify-content: space-between; color: #94a3b8; font-size: 0.52rem; margin-top: 0.3rem; }
        .dashboard-preview-v24__note { color: #94a3b8; font-size: 0.62rem; text-align: center; margin-top: 0.7rem; }
        @media (max-width: 1050px) { .dashboard-preview-v24__grid { grid-template-columns: 1fr; } .dashboard-preview-v24__flow { min-height: 7.5rem; } }
        @media (max-width: 700px) { .dashboard-preview-v24__head { flex-direction: column; } .dashboard-preview-v24 { padding: 0.9rem; } }
'''
if style_close not in html:
    raise SystemExit('Bloco style não encontrado')
html = html.replace(style_close, css + style_close, 1)

path.write_text(html, encoding='utf-8')
print('Dashboard UX v24 materializado com sucesso')
