from modules.pagina_evolucao_base import render_pagina
from modules import fichas, ui
from modules.secoes.condutas import render_condutas_registradas as _render_condutas_reg

render_pagina(
    titulo="Evolução Diária",
    render_formulario=fichas.render_formulario_completo,
    secoes_agentes=None,
    extras_pre_form=ui.render_guia_navegacao,
    extras_pos_form=_render_condutas_reg,
    page_suffix="",
)
