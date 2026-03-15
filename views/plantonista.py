from modules.pagina_evolucao_base import render_pagina
from modules import fichas

render_pagina(
    titulo="Evolução Plantonista",
    render_formulario=fichas.render_formulario_plantonista,
    secoes_agentes=["identificacao", "hd", "comorbidades", "dispositivos"],
    extras_pre_form=None,
    extras_pos_form=None,
    page_suffix="_plan",
)
