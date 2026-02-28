import streamlit as st
from datetime import datetime


def _caps_para_certo(val):
    """
    Converte texto em CAPS LOCK para escrita correta.
    Ex: GABRIEL -> Gabriel, TOMOGRAFIA DE CRANIO -> Tomografia de Cranio.
    Preposições (de, da, do, e, em, etc.) ficam em minúsculas.
    """
    if val is None:
        return val
    if not isinstance(val, str):
        return val
    s = str(val).strip()
    if not s:
        return val
    # Só aplica se estiver em maiúsculas (CAPS LOCK)
    if s != s.upper():
        return val
    # Não altera números ou valores numéricos
    if s.replace(".", "").replace(",", "").replace("-", "").replace("+", "").replace(" ", "").isdigit():
        return val
    # Title case com exceções para preposições em português
    exceto = {"de", "da", "do", "das", "dos", "e", "em", "com", "para", "por", "a", "o", "as", "os", "no", "na"}
    palavras = s.split()
    resultado = []
    for i, p in enumerate(palavras):
        p_lower = p.lower()
        if i > 0 and p_lower in exceto:
            resultado.append(p_lower)
        else:
            resultado.append(p_lower.capitalize())
    return " ".join(resultado)


def _caps_obs_linha(val: str) -> str:
    """
    Converte linha de obs (diagnósticos) de CAPS para forma gramatical.
    Nomes científicos de bactérias: Gênero com 1ª maiúscula, espécie em minúsculas.
    Ex: ENTEROCCOCUS FEACALIS e PROTEUS MIRABILIS -> Enterococcus faecalis e Proteus mirabilis
    """
    if val is None or not isinstance(val, str):
        return val
    s = str(val).strip()
    if not s or s != s.upper():
        return val
    exceto = {"de", "da", "do", "das", "dos", "e", "em", "com", "para", "por", "a", "o", "as", "os", "no", "na"}
    palavras = s.split()
    resultado = []
    i = 0
    while i < len(palavras):
        p = palavras[i]
        p_lower = p.lower()
        # Palavra só com letras = candidata a nome científico
        so_letras = p.replace("-", "").replace(".", "").isalpha()
        # Par GÊNERO ESPÉCIE (ambos caps, ambos não-conjunção) -> "Gênero espécie"
        if so_letras and p_lower not in exceto and i + 1 < len(palavras):
            prox = palavras[i + 1]
            prox_lower = prox.lower()
            prox_letras = prox.replace("-", "").replace(".", "").isalpha()
            if prox_letras and prox_lower not in exceto:
                resultado.append(p_lower.capitalize())
                resultado.append(prox_lower)  # espécie em minúsculas
                i += 2
                continue
        if p_lower in exceto:
            resultado.append(p_lower)
        else:
            resultado.append(p_lower.capitalize())
        i += 1
    return " ".join(resultado)


def _get(key, default=""):
    """Lê do session_state de forma segura. Normaliza CAPS LOCK em texto."""
    val = st.session_state.get(key, default)
    if isinstance(val, str) and val:
        return _caps_para_certo(val)
    return val


def _sigla_upper(val: str) -> str:
    """Retorna sigla em maiúsculas se for 2-5 letras (CVC, SVD, ITU, PAV)."""
    if not val or not isinstance(val, str):
        return val
    s = val.strip()
    if 2 <= len(s) <= 5 and s.replace(" ", "").isalpha():
        return s.upper()
    return val


def _secao_identificacao() -> list[str]:
    """
    Gera as linhas da seção '# Identificação & Scores'.
    Regra geral: campo vazio → linha não aparece.
    O cabeçalho só aparece se ao menos uma linha de conteúdo for gerada.
    """
    corpo = []

    # 1. Nome + Idade + Sexo — todos na mesma linha
    nome  = _get("nome")
    idade = _get("idade", 0)
    sexo  = _get("sexo")
    if nome:
        linha = f"Nome: {nome}"
        if idade:
            linha += f", {idade} anos"
        if sexo:
            linha += f", {sexo}"
        corpo.append(linha)

    # 3. Prontuário + Leito
    prontuario = _get("prontuario")
    leito = _get("leito")
    if prontuario or leito:
        partes = []
        if prontuario:
            partes.append(f"Prontuário: {prontuario}")
        if leito:
            partes.append(f"Leito: {leito}")
        corpo.append(" | ".join(partes))

    # 4. Origem
    origem = _get("origem")
    if origem:
        corpo.append(f"Origem: {origem}")

    # 5. Equipe Titular e Interconsultora (linhas separadas)
    equipe = _get("equipe")
    interconsultora = _get("interconsultora")
    if equipe:
        corpo.append(f"Equipe Titular: {equipe}")
    if interconsultora:
        corpo.append(f"Interconsultora: {interconsultora}")

    # 6. Data Internação Hospitalar
    di_hosp = _get("di_hosp")
    if di_hosp:
        corpo.append(f"Data Internação Hospitalar: {di_hosp}")

    # 7. Data Internação UTI
    di_uti = _get("di_uti")
    if di_uti:
        corpo.append(f"Data Internação UTI: {di_uti}")

    # 8. Data Internação Enfermaria — só aparece se preenchida
    di_enf = _get("di_enf")
    if di_enf:
        corpo.append(f"Data Internação Enfermaria: {di_enf}")

    # 9. SAPS 3
    saps3 = _get("saps3")
    if saps3:
        corpo.append(f"SAPS 3: {saps3}")

    # 10. SOFA admissão
    sofa_adm = _get("sofa_adm", 0)
    try:
        sofa_adm = int(sofa_adm)
    except (ValueError, TypeError):
        sofa_adm = 0
    if sofa_adm:
        corpo.append(f"SOFA admissão: {sofa_adm}")

    # 11. PPS
    pps = _get("pps")
    if pps:
        corpo.append(f"PPS: {pps}")

    # 12. mRS prévio
    mrs = _get("mrs")
    if mrs:
        corpo.append(f"mRS prévio: {mrs}")

    # 13. CFS
    cfs = _get("cfs")
    if cfs:
        corpo.append(f"CFS: {cfs}")

    # 14. Paliativo — somente se True, em caixa alta, sem espaço extra
    if _get("paliativo", False):
        corpo.append("PACIENTE EM CUIDADOS PROPORCIONAIS")

    # Cabeçalho só aparece se houver conteúdo
    if not corpo:
        return []
    if not corpo:
        return []

    # Departamento aparece ANTES do header de seção (sempre em MAIÚSCULO)
    departamento = _get("departamento")
    header = []
    if departamento:
        header = [f"# {str(departamento).strip().upper()} #", ""]
    return header + ["# Identificação & Scores"] + corpo


def _obs_para_linhas(obs: str, excluir_conduta: bool = False) -> list[str]:
    """
    Converte o campo obs (multiline) em linhas prefixadas com '> '.
    Se excluir_conduta=True, não inclui linhas que começam com 'Conduta:' (vão para Condutas Registradas).
    Cada linha é convertida de CAPS para forma gramatical (evitar tudo em maiúsculas).
    """
    linhas = []
    raw_obs = obs if isinstance(obs, str) else ""
    for linha in raw_obs.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        if excluir_conduta and linha.lower().startswith("conduta:"):
            continue
        linha = _caps_obs_linha(linha)  # CAPS -> forma gramatical; bactérias: Gênero espécie
        linhas.append(f"> {linha}")
    return linhas


def _secao_diagnosticos() -> list[str]:
    """
    Gera as linhas da seção '# Diagnósticos'.
    Mesmo modelo de dispositivos: agrupa por status (Atual / Resolvida).
    Campos: hd_{1..8}_nome, _class, _data_inicio, _data_resolvido, _status, _obs.
    Formato:
      # Diagnósticos Atuais
      {i}- {nome}[; {classif}][; {início}]
      # Diagnósticos Resolvidos
      {i}- {nome}[; {classif}][; {início} - {resolvido}]
    A conduta NUNCA aparece aqui — vai para Condutas Registradas.
    """
    ordem = st.session_state.get("hd_ordem", list(range(1, 9)))
    atuais = []
    resolvidos = []

    for id_real in ordem:
        nome = _get(f"hd_{id_real}_nome")
        if not nome:
            continue

        status = _get(f"hd_{id_real}_status")
        classif = _get(f"hd_{id_real}_class")
        data_ini = _get(f"hd_{id_real}_data_inicio")
        data_res = _get(f"hd_{id_real}_data_resolvido")

        partes = [nome]
        if classif:
            partes.append(classif)
        if data_ini:
            partes.append(data_ini)
        if status == "Resolvida" and data_res:
            if data_ini:
                partes[-1] = f"{data_ini} - {data_res}"
            else:
                partes.append(data_res)

        bloco = ["; ".join(partes)]
        bloco += _obs_para_linhas(st.session_state.get(f"hd_{id_real}_obs", ""), excluir_conduta=True)

        if status == "Resolvida":
            resolvidos.append(bloco)
        else:
            atuais.append(bloco)

    corpo = []
    if atuais:
        corpo.append("# Diagnósticos Atuais")
        for i, bloco in enumerate(atuais, 1):
            corpo.append(f"{i}- {bloco[0]}")
            corpo.extend(bloco[1:])
            corpo.append("")

    if resolvidos:
        if corpo and corpo[-1] != "":
            corpo.append("")
        corpo.append("# Diagnósticos Resolvidos")
        for i, bloco in enumerate(resolvidos, 1):
            corpo.append(f"{i}- {bloco[0]}")
            corpo.extend(bloco[1:])
            corpo.append("")

    while corpo and corpo[-1] == "":
        corpo.pop()

    if not corpo:
        return []
    return corpo


def _secao_culturas() -> list[str]:
    """
    Agrupa culturas em 3 sub-seções por status:
      # Culturas Positivas   → Positivo com Antibiograma | Positivo aguarda isolamento
      # Culturas em Andamento → Pendente negativo
      # Culturas Negativas    → Negativo
    """
    ordem = st.session_state.get("cult_ordem", list(range(1, 9)))

    positivas  = []
    andamento  = []
    negativas  = []

    for id_real in ordem:
        sitio = _get(f"cult_{id_real}_sitio")
        if not sitio:
            continue

        status        = _get(f"cult_{id_real}_status")
        data_coleta   = _get(f"cult_{id_real}_data_coleta")
        data_resultado= _get(f"cult_{id_real}_data_resultado")
        micro         = _get(f"cult_{id_real}_micro")
        sensib        = _get(f"cult_{id_real}_sensib")

        # Linha principal
        partes = [sitio]
        if data_coleta:
            partes.append(f"coletada {data_coleta}")
        if data_resultado:
            partes.append(f"resultado {data_resultado}")
        linha_principal = "; ".join(partes)

        if status in ("Positivo com Antibiograma", "Positivo aguarda isolamento"):
            detalhe_partes = [micro] if micro else []
            if status == "Positivo com Antibiograma" and sensib:
                detalhe_partes.append(sensib)
            elif status == "Positivo aguarda isolamento":
                detalhe_partes.append("aguarda isolamento")
            detalhe = f"> {'; '.join(detalhe_partes)}" if detalhe_partes else ""
            positivas.append((linha_principal, detalhe))

        elif status == "Pendente negativo":
            partes_and = list(partes)
            if not data_resultado:
                partes_and.append("Parcialmente negativa")
            andamento.append(("; ".join(partes_and), ""))

        elif status == "Negativo":
            negativas.append((linha_principal, ""))

    if not positivas and not andamento and not negativas:
        return []

    corpo = []

    def _add_grupo(titulo, itens):
        if not itens:
            return
        if corpo:
            corpo.append("")
        corpo.append(titulo)
        for i, (linha, detalhe) in enumerate(itens, 1):
            corpo.append(f"{i}- {linha}")
            if detalhe:
                corpo.append(detalhe)

    _add_grupo("# Culturas Positivas",    positivas)
    _add_grupo("# Culturas em Andamento", andamento)
    _add_grupo("# Culturas Negativas",    negativas)

    return corpo


def _secao_dispositivos() -> list[str]:
    """
    Formato:
      # Dispositivos Atuais
      {i}- {nome}[; {local}][; {data_insercao}] - Atual

      # Dispositivos Retirados
      {i}- {nome}[; {local}][; {data_insercao} - {data_retirada}]
    """
    ordem = st.session_state.get("disp_ordem", list(range(1, 9)))

    ativos = []
    retirados = []

    for id_real in ordem:
        nome = _sigla_upper(_get(f"disp_{id_real}_nome"))
        if not nome:
            continue

        status        = _get(f"disp_{id_real}_status")
        local         = _get(f"disp_{id_real}_local")
        data_insercao = _get(f"disp_{id_real}_data_insercao")
        data_retirada = _get(f"disp_{id_real}_data_retirada")

        partes = [nome]
        if local:
            partes.append(local)

        if status == "Removido":
            datas = " - ".join(filter(None, [data_insercao, data_retirada]))
            if datas:
                partes.append(datas)
            retirados.append("; ".join(partes))
        else:
            if data_insercao:
                partes.append(f"{data_insercao} - Atual")
            else:
                partes.append("Atual")
            ativos.append("; ".join(partes))

    if not ativos and not retirados:
        return []

    corpo = []
    if ativos:
        corpo.append("# Dispositivos Atuais")
        for i, linha in enumerate(ativos, 1):
            corpo.append(f"{i}- {linha}")

    if retirados:
        if corpo:
            corpo.append("")
        corpo.append("# Dispositivos Prévios")
        for i, linha in enumerate(retirados, 1):
            corpo.append(f"{i}- {linha}")

    return corpo


def _secao_hmpa() -> list[str]:
    """
    Gera as linhas da seção '# História da Moléstia Pregressa Atual'.
    Prioriza o texto reescrito pelo agente; se vazio, usa o texto bruto.
    """
    texto = _get("hmpa_reescrito") or _get("hmpa_texto")
    if not texto or not texto.strip():
        return []
    return ["# História da Moléstia Pregressa Atual"] + texto.strip().splitlines()


def _secao_muc() -> list[str]:
    """
    Gera as linhas da seção '# Medicações de Uso Contínuo'.
    Formato: {i}- {nome}[; {dose}][; {freq}]
    Adesão global aparece se preenchida.
    """
    linhas = []

    ordem = st.session_state.get("muc_ordem", list(range(1, 21)))
    for id_real in ordem:
        nome = _get(f"muc_{id_real}_nome")
        if not nome:
            continue
        partes = [nome]
        dose = _get(f"muc_{id_real}_dose")
        if dose:
            partes.append(dose)
        freq = _get(f"muc_{id_real}_freq")
        if freq:
            partes.append(freq)
        linhas.append(f"{len(linhas)+1}- {'; '.join(partes)}")

    if not linhas:
        return []

    corpo = ["# Medicações de Uso Contínuo"]

    adesao = _get("muc_adesao_global")
    alergia = st.session_state.get("muc_alergia")
    alergia_obs = _get("muc_alergia_obs")

    # Adesão e alergia na mesma linha quando ambos existem
    partes_muc = []
    if adesao:
        partes_muc.append(adesao)  # Uso Regular / Uso Irregular / Desconhecido
    if alergia == "Presente":
        partes_muc.append(f"Alergias: {alergia_obs}" if alergia_obs else "Alergias: presente")
    elif alergia == "Nega":
        partes_muc.append("Nega alergias")
    elif alergia == "Desconhecido":
        partes_muc.append("Desconhece alergias")
    if partes_muc:
        corpo.append(" | ".join(partes_muc))

    corpo += linhas
    return corpo


def _secao_comorbidades() -> list[str]:
    """
    Gera as linhas da seção '# Comorbidades'.
    Etilismo, Tabagismo, SPA na mesma linha. Ausente→Nega, Presente→Ativo.
    Formato: Etilismo: Nega | Tabagismo: Ativo; 20 anos-maço | SPA: Nega
    """
    corpo = []

    def _etil_tbg_spa(label, key, obs_key):
        val = st.session_state.get(key)
        if not val:
            return None
        exibir = "Nega" if val == "Ausente" else ("Ativo" if val == "Presente" else val)
        obs = _get(obs_key)
        if exibir == "Ativo" and obs:
            return f"{label}: {exibir}; {obs}"
        return f"{label}: {exibir}"

    partes = []
    for label, key, obs_key in [
        ("Etilismo", "cmd_etilismo", "cmd_etilismo_obs"),
        ("Tabagismo", "cmd_tabagismo", "cmd_tabagismo_obs"),
        ("SPA", "cmd_spa", "cmd_spa_obs"),
    ]:
        p = _etil_tbg_spa(label, key, obs_key)
        if p:
            partes.append(p)
    if partes:
        corpo.append(" | ".join(partes))

    # Lista de comorbidades
    linhas = []
    for i in range(1, 11):
        nome = _get(f"cmd_{i}_nome")
        if not nome:
            continue
        linha = nome
        classif = _get(f"cmd_{i}_class")
        if classif:
            linha += f"; {classif}"
        linhas.append(f"{len(linhas)+1}- {linha}")

    corpo.extend(linhas)

    if not corpo:
        return []
    return ["# Comorbidades"] + corpo


def _calcular_dias(data_ini: str, data_fim: str) -> str:
    """Calcula diferença em dias entre duas datas DD/MM/AAAA. Retorna '' se não for possível."""
    try:
        d1 = datetime.strptime(data_ini.strip(), "%d/%m/%Y")
        d2 = datetime.strptime(data_fim.strip(), "%d/%m/%Y")
        dias = (d2 - d1).days
        if dias > 0:
            return f"{dias} dias"
    except Exception:
        pass
    return ""


def _secao_antibioticos() -> list[str]:
    """
    Gera as linhas da seção Antibióticos.
    Lista única com status Atual/Prévio. Saída:
    # Antibiótico Atual
    1- {nome}[; Foco {foco}][; {tipo}][; {data_ini} → {data_fim}[ (X dias)]]
    # Antibiótico Prévio
    1- {nome}[; Foco {foco}][; {tipo}][; {data_ini} - {data_fim}]
    """
    _TIPO_EXPANDIDO = {"Empírico": "Empírico", "Guiado por Cultura": "Guiado por Cultura"}

    def _linha_atual(i, idx):
        nome     = _get(f"atb_{idx}_nome")
        foco     = _sigla_upper(_get(f"atb_{idx}_foco"))
        tipo     = _get(f"atb_{idx}_tipo") or ""
        data_ini = _get(f"atb_{idx}_data_ini")
        data_fim = _get(f"atb_{idx}_data_fim")
        num_dias = _get(f"atb_{idx}_num_dias")
        if not nome:
            return None
        partes = [nome]
        if foco:
            partes.append(f"Foco {foco}")
        if tipo in _TIPO_EXPANDIDO:
            partes.append(_TIPO_EXPANDIDO[tipo])
        if data_ini and data_fim:
            prog = num_dias.strip() if num_dias else _calcular_dias(data_ini, data_fim)
            datas = f"{data_ini} → {data_fim}"
            if prog:
                suf = prog if "dia" in str(prog).lower() else f"{prog} dias"
                datas += f" (Programado {suf})"
            partes.append(datas)
        elif data_ini:
            partes.append(data_ini)
        return f"{i}- " + "; ".join(partes)

    def _linha_previo(i, idx):
        nome     = _get(f"atb_{idx}_nome")
        foco     = _sigla_upper(_get(f"atb_{idx}_foco"))
        tipo     = _get(f"atb_{idx}_tipo") or ""
        data_ini = _get(f"atb_{idx}_data_ini")
        data_fim = _get(f"atb_{idx}_data_fim")
        if not nome:
            return None
        partes = [nome]
        if foco:
            partes.append(f"Foco {foco}")
        if tipo in _TIPO_EXPANDIDO:
            partes.append(_TIPO_EXPANDIDO[tipo])
        if data_ini and data_fim:
            dias_uso = _calcular_dias(data_ini, data_fim)
            if dias_uso:
                n = dias_uso.split()[0]
                partes.append(f"{data_ini} - {data_fim} (Uso por {n} dias)")
            else:
                partes.append(f"{data_ini} - {data_fim}")
        elif data_ini:
            partes.append(data_ini)
        elif data_fim:
            partes.append(data_fim)
        return f"{i}- " + "; ".join(partes)

    ordem = st.session_state.get("atb_ordem", list(range(1, 9)))

    atuais = []
    previos = []
    for idx in ordem:
        status = _get(f"atb_{idx}_status")
        if status == "Atual":
            linha = _linha_atual(len(atuais) + 1, idx)
            if linha:
                atuais.append(linha)
        elif status == "Prévio":
            linha = _linha_previo(len(previos) + 1, idx)
            if linha:
                previos.append(linha)

    if not atuais and not previos:
        return []

    resultado = []
    if atuais:
        resultado.append("# Antibiótico Atual")
        resultado.extend(atuais)
    if previos:
        if resultado:
            resultado.append("")
        resultado.append("# Antibiótico Prévio")
        resultado.extend(previos)

    return resultado


def _secao_complementares() -> list[str]:
    """
    Gera as linhas da seção Exames Complementares.
    Formato por exame:
        {i}- {Nome do Exame} (data)
        Laudo
    Linha em branco entre exames.
    """
    ordem = st.session_state.get("comp_ordem", list(range(1, 9)))

    blocos = []
    contador = 1
    for idx in ordem:
        exame = _get(f"comp_{idx}_exame").strip()
        data = _get(f"comp_{idx}_data").strip()
        laudo = _get(f"comp_{idx}_laudo").strip()
        if not exame and not laudo:
            continue
        nome = exame or "Exame complementar"
        cabecalho = f"{contador}- {nome} ({data})" if data else f"{contador}- {nome}"
        bloco = [cabecalho]
        if laudo:
            bloco.append(laudo)
        blocos.append(bloco)
        contador += 1

    if not blocos:
        return []

    resultado = ["# Exames Complementares"]
    for i, bloco in enumerate(blocos):
        resultado.extend(bloco)
        if i < len(blocos) - 1:
            resultado.append("")

    return resultado


def _secao_laboratoriais() -> list[str]:
    """
    Gera a saída determinística dos laboratoriais.

    Por slot:
        > {data}
        {linha principal: campos preenchidos separados por ' | '}
        {outros}  ← linha livre, se preenchida
        Gas Art/Ven - pH x / pCO2 x / ...  ← se algum campo de gaso preenchido
        Gas Ven - pCO2 x / SvO2 x          ← se perfusão preenchida
        Urn: Den: x / Leu Est: x / ...      ← se algum campo de EAS preenchido
    """
    def _v(i, campo):
        v = _get(f"lab_{i}_{campo}")
        if v is None:
            return ""
        return str(v).strip()

    def _par(label, val, sep=" "):
        return f"{label}{sep}{val}" if val else None

    # Ordem e rótulos da linha principal
    _MAIN = [
        ("Hb",    "hb"),    ("Ht",    "ht"),    ("VCM",  "vcm"),
        ("HCM",   "hcm"),   ("RDW",   "rdw"),   ("Leuco","leuco"),
        ("Plaq",  "plaq"),  ("Cr",    "cr"),     ("Ur",   "ur"),
        ("Na",    "na"),    ("K",     "k"),      ("Mg",   "mg"),
        ("Pi",    "pi"),    ("CaT",   "cat"),    ("CaI",  "cai"),
        ("TGO",   "tgo"),   ("TGP",   "tgp"),   ("FAL",  "fal"),
        ("GGT",   "ggt"),   ("BT",    "__bt_bd__"), ("Prot Tot", "prot_tot"), ("Amil", "amil"),
        ("Lipas", "lipas"), ("Alb",  "alb"),    ("CPK",    "cpk"),    ("CPK-MB", "cpk_mb"),
        ("BNP",    "bnp"),   ("Trop",   "trop"),   ("PCR",    "pcr"),
        ("VHS",    "vhs"),   ("Lac",    "gas_lac"), ("TP",     "tp"),
        ("TTPa",   "ttpa"),
    ]
    _GAS = [
        ("pH",    "gas_ph"),  ("pCO2", "gas_pco2"), ("Bic",  "gas_hco3"),
        ("BE",    "gas_be"),  ("Cl",   "gas_cl"),   ("AG",   "gas_ag"),
        ("pO2",   "gas_po2"), ("SatO2","gas_sat"),  ("Na",   "gas_na"),
        ("K",     "gas_k"),   ("CaI",  "gas_cai"),  ("Lac",  "gas_lac"),
    ]
    _EAS = [
        ("Den",      "ur_dens"), ("Leu Est", "ur_le"),  ("Nit",  "ur_nit"),
        ("Leuco",    "ur_leu"),  ("Hm",      "ur_hm"),  ("Prot", "ur_prot"),
        ("Cet",      "ur_cet"),  ("Glic",    "ur_glic"),
    ]

    slots = []
    for i in range(1, 11):
        data    = _v(i, "data")
        outros  = _v(i, "outros")
        gas_tipo = _v(i, "gas_tipo")

        _main_parts = []
        for _lbl, _k in _MAIN:
            if _k == "__bt_bd__":
                bt_v = _v(i, "bt")
                bd_v = _v(i, "bd")
                if bt_v:
                    _main_parts.append(f"BT {bt_v} (BD {bd_v})" if bd_v else f"BT {bt_v}")
            else:
                _val = _v(i, _k)
                if _val:
                    _main_parts.append(f"{_lbl} {_val}")
        linha_main = " | ".join(_main_parts)
        partes_gas = [
            f"{lbl} {_v(i, k)}" for lbl, k in _GAS if _v(i, k)
        ]
        partes_perf = [p for p in [
            _par("pCO2", _v(i, "gasv_pco2")),
            _par("SvO2", _v(i, "svo2")),
        ] if p]
        partes_eas = [
            f"{lbl}: {_v(i, k)}" for lbl, k in _EAS if _v(i, k)
        ]

        if not any([data, linha_main, outros, partes_gas, partes_perf, partes_eas]):
            continue

        linhas = []
        if data:
            linhas.append(f"> {data}")
        if linha_main:
            linhas.append(linha_main)
        if outros:
            linhas.append(outros)
        if partes_gas:
            prefixo = "Gas Art" if gas_tipo == "Arterial" else ("Gas Ven" if gas_tipo == "Venosa" else "Gaso")
            linhas.append(f"{prefixo} - " + " / ".join(partes_gas))
        if partes_perf:
            linhas.append("Gas Ven - " + " / ".join(partes_perf))
        if partes_eas:
            linhas.append("Urn: " + " / ".join(partes_eas))

        slots.append(linhas)

    if not slots:
        return []

    resultado = ["# Laboratoriais"]
    for slot in slots:
        resultado.extend(slot)

    return resultado


def _secao_controles() -> list[str]:
    """
    Gera a saída determinística dos Controles & Balanço Hídrico.

    Por dia:
        > {data}
        {linha vitais: campos preenchidos com ' | '}
        {Diurese x | BH x}
    """
    _PARAMS_MM = [
        ("PAS",   "pas"),   ("PAD",   "pad"),   ("PAM",   "pam"),
        ("FC",    "fc"),    ("FR",    "fr"),     ("SatO2", "sato2"),
        ("Temp",  "temp"),  ("Dextro", "glic"),
    ]

    def _linha_dia(dia):
        data    = _get(f"ctrl_{dia}_data").strip()
        vitais  = []
        for label, chave in _PARAMS_MM:
            vmin = _get(f"ctrl_{dia}_{chave}_min").strip()
            vmax = _get(f"ctrl_{dia}_{chave}_max").strip()
            if vmin and vmax:
                vitais.append(f"{label} {vmin}-{vmax}")
            elif vmin:
                vitais.append(f"{label} {vmin}")
        diurese = _get(f"ctrl_{dia}_diurese").strip()
        balanco = _get(f"ctrl_{dia}_balanco").strip()

        if not any([data, vitais, diurese, balanco]):
            return None

        linhas = []
        if data:
            linhas.append(f">{data}")
        if vitais:
            linhas.append(" | ".join(vitais))
        bh_parts = []
        if diurese:
            bh_parts.append(f"Diurese {diurese}")
        if balanco:
            bh_parts.append(f"BH {balanco}")
        if bh_parts:
            linhas.append(" | ".join(bh_parts))
        return linhas

    dias = ["hoje", "ontem", "anteontem"]  # hoje em cima, ontem embaixo, anteontem mais embaixo
    slots = [_linha_dia(d) for d in dias if _linha_dia(d)]

    if not slots:
        return []

    periodo = (_get("ctrl_periodo") or "24 horas").strip()
    resultado = ["# Controles & Balanço Hídrico"]
    if periodo == "12 horas":
        resultado.append(">> 12 horas <<")
        resultado.append("")
    for slot in slots:
        resultado.extend(slot)

    return resultado


def _secao_evolucao_clinica() -> list[str]:
    texto = _get("evolucao_notas").strip()
    if not texto:
        return []
    return ["# Evolução Clínica", texto]


def _secao_condutas() -> list[str]:
    """
    Gera a seção '# Condutas'.
    Inclui: conduta_final_lista (manual) + condutas agregadas dos campos *_conduta (diagnósticos, sistemas, etc.).
    Cada linha recebe prefixo '- '. A conduta NUNCA aparece em Diagnósticos — só aqui.
    """
    from modules.secoes import condutas as _cond_mod

    corpo = []
    for linha in _cond_mod.coletar_condutas_agregadas():
        if linha.strip():
            corpo.append(f"- {linha.strip()}" if not linha.strip().startswith("- ") else linha.strip())

    lista = _get("conduta_final_lista").strip()
    for linha in lista.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        if not linha.startswith("- "):
            linha = f"- {linha}"
        corpo.append(linha)

    if not corpo:
        return []
    return ["# Condutas"] + corpo


def _secao_prescricao() -> list[str]:
    """
    Gera a seção '# Prescrição' com o conteúdo formatado pela IA (bloco 14).
    Aparece abaixo de Condutas no prontuário completo.
    """
    texto = _get("prescricao_formatada").strip()
    if not texto:
        return []
    return ["===", "# Prescrição", "", texto]


def _secao_sistemas() -> list[str]:
    """
    Gera a saída determinística da Evolução por Sistemas.
    Regra: campo preenchido → aparece; campo vazio/None → não aparece.
    Campos Sim/Não → positivo ou negativo conforme valor.
    """
    corpo = []

    def _s(key):
        v = _get(key)
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip() or None
        return v

    def _jun(items, sep=", "):
        """Junta lista não-vazia com separador."""
        return sep.join(i for i in items if i)

    def _lista_e(items):
        """Junta com vírgulas e 'e' antes do último."""
        items = [i for i in items if i]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        return ", ".join(items[:-1]) + " e " + items[-1]

    def _turnos():
        t = []
        if st.session_state.get("sis_gastro_escape_manha", False): t.append("manhã")
        if st.session_state.get("sis_gastro_escape_tarde",  False): t.append("tarde")
        if st.session_state.get("sis_gastro_escape_noite",  False): t.append("noite")
        lista = _lista_e(t)
        return f"nos períodos da {lista}" if lista else ""

    def _limpar_barra(val):
        """Remove barras dos valores (ex: 3/ → 3, 22/00/0 → 22000)."""
        if val is None or not isinstance(val, str):
            return val
        return str(val).replace("/", "").strip() or None

    # ── NEUROLÓGICO ──────────────────────────────────────────────────────────
    neuro = []

    ecg  = st.session_state.get("sis_neuro_ecg", "") or ""
    ecgp = st.session_state.get("sis_neuro_ecg_p", "") or ""
    rass = st.session_state.get("sis_neuro_rass", "") or ""
    ao   = st.session_state.get("sis_neuro_ecg_ao", "") or ""
    rv   = st.session_state.get("sis_neuro_ecg_rv", "") or ""
    rm   = st.session_state.get("sis_neuro_ecg_rm", "") or ""

    ecg_parts = []
    if str(ecg).strip():
        ecg_str = f"ECG {ecg}"
        sub = [p for p in [
            f"AO {ao}" if str(ao).strip() else None,
            f"RV {rv}" if str(rv).strip() else None,
            f"RM {rm}" if str(rm).strip() else None,
        ] if p]
        if sub:
            ecg_str += f" ({' '.join(sub)})"
        ecg_parts.append(ecg_str)
    if str(ecgp).strip():
        ecg_parts.append(f"ECG-P {ecgp}")
    if str(rass).strip():
        ecg_parts.append(f"RASS {rass}")
    if ecg_parts:
        neuro.append(" | ".join(ecg_parts))

    cam      = _s("sis_neuro_cam_icu")
    delirium = _s("sis_neuro_delirium")
    del_tipo = _s("sis_neuro_delirium_tipo")
    if cam or delirium:
        cam_parts = []
        if cam:
            cam_parts.append(f"CAM-ICU: {cam}")
        if delirium == "Sim":
            cam_parts.append(f"delirium {del_tipo.lower()}" if del_tipo else "com delirium")
        elif delirium == "Não":
            cam_parts.append("sem delirium")
        neuro.append(", ".join(cam_parts))

    tam  = _s("sis_neuro_pupilas_tam")
    sime = _s("sis_neuro_pupilas_simetria")
    foto = _s("sis_neuro_pupilas_foto")
    if tam or sime or foto:
        pup = []
        if tam:  pup.append({"Normal": "Normais", "Miótica": "Mióticas", "Midríase": "Midríase"}.get(tam, tam))
        if sime: pup.append({"Simétricas": "simétricas", "Anisocoria": "anisocóricas"}.get(sime, sime))
        if foto: pup.append({"Fotoreagente": "fotoreagentes", "Não fotoreagente": "não fotoreagentes"}.get(foto, foto))
        neuro.append("Pupilas: " + ", ".join(pup))

    algico = _s("sis_neuro_analgesico_adequado")
    if algico == "Sim":   neuro.append("Paciente com bom controle álgico")
    elif algico == "Não": neuro.append("Sem controle álgico adequado")

    fixas, resgates = [], []
    for i in range(1, 4):
        tipo   = _s(f"sis_neuro_analgesia_{i}_tipo")
        drogas = _s(f"sis_neuro_analgesia_{i}_drogas")
        dose   = _s(f"sis_neuro_analgesia_{i}_dose")
        freq   = _s(f"sis_neuro_analgesia_{i}_freq")
        if not drogas:
            continue
        if dose and freq:
            entry = f"{drogas} {dose}, {freq}"
        elif dose:
            entry = f"{drogas} {dose}"
        elif freq:
            entry = f"{drogas}, {freq}"
        else:
            entry = drogas
        (fixas if tipo == "Fixa" else resgates).append(entry)
    if fixas:    neuro.append("Analgesia Fixa: "    + " | ".join(fixas))
    if resgates: neuro.append("Analgesia Resgate: " + " | ".join(resgates))

    sed_entries = []
    for i in range(1, 4):
        dr   = _s(f"sis_neuro_sedacao_{i}_drogas")
        dose = _s(f"sis_neuro_sedacao_{i}_dose")
        if not dr:
            continue
        sed_entries.append(f"{dr} {dose}" if dose else dr)
    if sed_entries:
        meta = _s("sis_neuro_sedacao_meta")
        linha_sed = "Sedação: " + " | ".join(sed_entries)
        if meta:
            m = str(meta).strip()
            m = m.replace("RASS", "").replace("Rass", "").strip() or m
            linha_sed += f"; Meta Rass {m}"
        neuro.append(linha_sed)

    bnm_med = _s("sis_neuro_bloqueador_med")
    bnm_dose = _s("sis_neuro_bloqueador_dose")
    if bnm_med or bnm_dose:
        neuro.append(f"Bloqueador Neuromuscular: {bnm_med} {bnm_dose}".strip())

    df = _s("sis_neuro_deficits_focais")
    df_ausente = st.session_state.get("sis_neuro_deficits_ausente") in ("Ausente", True)
    if df:
        neuro.append(f"Déficit Focal: {df}")
    elif df_ausente:
        neuro.append("Sem déficit focal")

    pocus = _s("sis_neuro_pocus")
    if pocus: neuro.append(f"Pocus Neurológico: {pocus}")
    obs = _s("sis_neuro_obs")
    if obs: neuro.append(f"Obs: {obs}")

    if neuro:
        corpo.append("- Neurológico")
        corpo.extend(neuro)

    # ── RESPIRATÓRIO ─────────────────────────────────────────────────────────
    resp = []

    exame_resp = _s("sis_resp_ausculta")
    if exame_resp: resp.append(f"Respiratório: {exame_resp}")

    modo      = _s("sis_resp_modo")
    modo_vent = _s("sis_resp_modo_vent")
    if modo:
        if modo == "Ventilação Mecânica":
            vm_params = []
            if modo_vent:
                vm_params.append(modo_vent.upper())
            pressao = _s("sis_resp_pressao"); volume = _s("sis_resp_volume")
            fio2    = _s("sis_resp_fio2");    peep   = _s("sis_resp_peep")
            freq_r  = _s("sis_resp_freq")
            if pressao:
                p = pressao if any(u in pressao.lower() for u in ["mmhg", "mmh2o", "cmh2o"]) else f"{pressao} cmH₂O"
                vm_params.append(f"Pressão {p}")
            if volume:
                v = volume if "ml" in volume.lower() else f"{volume} mL"
                vm_params.append(f"Volume {v}")
            if fio2:
                vm_params.append(f"FiO2 {fio2}" if "%" in fio2 else f"FiO2 {fio2}%")
            if peep:
                pe = peep if any(u in peep.lower() for u in ["mmhg", "mmh2o", "cmh2o"]) else f"{peep} cmH₂O"
                vm_params.append(f"PEEP {pe}")
            if freq_r:
                fr = freq_r if "ipm" in freq_r.lower() else f"{freq_r} ipm"
                vm_params.append(f"FR {fr}")
            if vm_params:
                if len(vm_params) > 1:
                    sufixo = ", ".join(vm_params[:-1]) + " e " + vm_params[-1]
                else:
                    sufixo = vm_params[0]
                resp.append(f"Ventilação Mecânica; {sufixo}")
            else:
                resp.append("Ventilação Mecânica")
        elif modo == "Oxigenoterapia":
            ox_modo = _s("sis_resp_oxigenio_modo")
            ox_fluxo = _s("sis_resp_oxigenio_fluxo")
            partes = []
            if ox_modo:
                partes.append(ox_modo)
            if ox_fluxo:
                fluxo_str = ox_fluxo if "L/min" in ox_fluxo or "l/min" in ox_fluxo.lower() else f"{ox_fluxo} L/min"
                partes.append(fluxo_str)
            resp.append("Oxigenoterapia; " + ", ".join(partes) if partes else "Oxigenoterapia")
        elif modo == "Cateter de Alto Fluxo":
            volume = _s("sis_resp_volume"); fio2 = _s("sis_resp_fio2")
            partes = ["Cateter de Alto Fluxo"]
            if volume:
                v = volume if "ml" in volume.lower() else f"{volume} mL"
                partes.append(f"Volume {v}")
            if fio2:
                partes.append(f"FiO2 {fio2}" if "%" in fio2 else f"FiO2 {fio2}%")
            resp.append(", ".join(partes))
        else:
            resp.append(modo)

    vent_prot = _s("sis_resp_vent_protetora")
    sincro    = _s("sis_resp_sincronico")
    assincr   = _s("sis_resp_assincronia")
    if vent_prot or sincro:
        vs = []
        if vent_prot == "Sim":   vs.append("Em ventilação protetora")
        elif vent_prot == "Não": vs.append("Sem ventilação protetora")
        if sincro == "Sim":
            vs.append("sincrônico")
        elif sincro == "Não":
            vs.append(f"assincrônico, apresenta {assincr}" if assincr else "assincrônico")
        resp.append(", ".join(vs))

    mec = []
    comp   = _s("sis_resp_complacencia"); resist = _s("sis_resp_resistencia")
    dp     = _s("sis_resp_dp");           plato  = _s("sis_resp_plato")
    pico   = _s("sis_resp_pico")
    if comp:   mec.append(f"Complacência {comp} mL/cmH₂O")
    if resist: mec.append(f"Resistência {resist} cmH₂O/L/s")
    if dp:     mec.append(f"Driving Pressure {dp} cmH₂O")
    if plato:  mec.append(f"Pressão de platô {plato} cmH₂O")
    if pico:   mec.append(f"Pressão de pico {pico} cmH₂O")
    if mec: resp.append("Mecânica Ventilatória: " + ", ".join(mec))

    drenos = []
    for i in range(1, 4):
        nome = _s(f"sis_resp_dreno_{i}")
        deb  = _s(f"sis_resp_dreno_{i}_debito")
        if nome:
            prefixo = "" if "dreno" in nome.lower() else "Dreno "
            if deb:
                suf = "" if any(u in deb for u in ("ml", "mL", "L", "/")) else " mL"
                drenos.append(f"{prefixo}{nome}: {deb}{suf}")
            else:
                drenos.append(f"{prefixo}{nome}")
    if drenos: resp.append(" | ".join(drenos))

    pocus = _s("sis_resp_pocus")
    if pocus: resp.append(f"Pocus Respiratório: {pocus}")
    obs = _s("sis_resp_obs")
    if obs: resp.append(f"Obs: {obs}")

    if resp:
        corpo.append("")
        corpo.append("- Respiratório")
        corpo.extend(resp)

    # ── CARDIOVASCULAR ───────────────────────────────────────────────────────
    cardio = []

    fc    = _s("sis_cardio_fc");           crd = _s("sis_cardio_cardioscopia")
    pam_c = _s("sis_cardio_pam")
    exame_cardio = _s("sis_cardio_exame_cardio")
    _fc   = f"FC {fc} bpm" if fc and "bpm" not in fc.lower() else (f"FC {fc}" if fc else None)
    _rit  = None
    if crd:
        r = crd.strip()
        if r.lower().startswith("ritmo"):
            _rit = "Ritmo " + r[5:].strip()
        else:
            _rit = f"Ritmo {r}"
    _pam  = f"PAM {pam_c} mmHg" if pam_c and "mmhg" not in pam_c.lower() else (f"PAM {pam_c}" if pam_c else None)
    hemo  = [p for p in [_fc, _rit, _pam] if p]
    if hemo: cardio.append(", ".join(hemo))
    if exame_cardio: cardio.append(f"Cardiológico: {exame_cardio}")

    perf = _s("sis_cardio_perfusao")
    tec = _s("sis_cardio_tec")
    if perf or tec:
        perf_p = []
        if perf:
            perf_p.append(f"Perfusão: {perf}")
        if tec:
            tec_s = f"{tec} seg" if tec.strip() and "seg" not in tec.lower() else tec
            perf_p.append(f"TEC: {tec_s}")
        cardio.append(", ".join(perf_p))
    fr_ = _s("sis_cardio_fluido_responsivo")
    ft_ = _s("sis_cardio_fluido_tolerante")
    if fr_ or ft_:
        l1 = "Fluidoresponsivo" if fr_ == "Sim" else ("Não fluidoresponsivo" if fr_ == "Não" else None)
        l2 = "fluidotolerante" if ft_ == "Sim" else ("não fluidotolerante" if ft_ == "Não" else None)
        partes_f = [p for p in [l1, l2] if p]
        if partes_f:
            cardio.append("; ".join(partes_f))

    dvas = []
    for i in range(1, 5):
        med  = _s(f"sis_cardio_dva_{i}_med")
        dose = _s(f"sis_cardio_dva_{i}_dose")
        if med: dvas.append(f"{med} {dose}" if dose else med)
    if dvas: cardio.append("DVA: " + " | ".join(dvas))

    pocus = _s("sis_cardio_pocus")
    if pocus: cardio.append(f"Pocus Cardiovascular: {pocus}")
    obs = _s("sis_cardio_obs")
    if obs: cardio.append(f"Obs: {obs}")

    if cardio:
        corpo.append("")
        corpo.append("- Cardiovascular")
        corpo.extend(cardio)

    # ── EXAME ABDOMINAL / NUTRICIONAL ─────────────────────────────────────────
    gastro = []

    ef = _s("sis_gastro_exame_fisico")
    icter_presente = _s("sis_gastro_ictericia_presente") == "Presente"
    icter_cruzes = _s("sis_gastro_ictericia_cruzes")
    if ef:
        if icter_presente:
            cruzes_str = str(icter_cruzes).strip() if icter_cruzes else ""
            cruzes_valido = cruzes_str in ("1", "2", "3", "4")
            suf = f", icteríco {cruzes_str}+" if cruzes_valido else ", icteríco"
        else:
            suf = ", sem icterícia"
        gastro.append(f"Abdomen: {ef}{suf}")

    oral     = _s("sis_gastro_dieta_oral")
    enteral  = _s("sis_gastro_dieta_enteral"); e_vol = _s("sis_gastro_dieta_enteral_vol")
    parent   = _s("sis_gastro_dieta_parenteral"); p_vol = _s("sis_gastro_dieta_parenteral_vol")
    meta_cal = _s("sis_gastro_meta_calorica")
    dieta_p  = []
    if oral:    dieta_p.append(f"Oral {oral}")
    if enteral:
        ev = (e_vol or "").strip()
        if ev and "kcal" not in ev.lower() and "ml" not in ev.lower():
            ev = f"{ev} kcal"
        dieta_p.append(f"Enteral {enteral} {ev}" if ev else f"Enteral {enteral}")
    if parent:
        pv = (p_vol or "").strip()
        if pv and "kcal" not in pv.lower() and "ml" not in pv.lower():
            pv = f"{pv} kcal"
        dieta_p.append(f"Parenteral {parent} {pv}" if pv else f"Parenteral {parent}")
    if dieta_p or meta_cal:
        linha_d = "Dieta: " + (", ".join(dieta_p) if dieta_p else "")
        if meta_cal:
            sep = "; " if dieta_p else ""
            mc = f"{meta_cal} kcal" if "kcal" not in meta_cal.lower() else meta_cal
            linha_d += sep + f"Meta calórica de {mc}"
        gastro.append(linha_d)

    na_meta  = _s("sis_gastro_na_meta")
    ingestao = _s("sis_gastro_ingestao_quanto")
    if na_meta == "Sim":
        ing = f"{ingestao} kcal" if ingestao and "kcal" not in ingestao.lower() else ingestao
        gastro.append("Na meta calórica" + (f" - {ing} nas últimas 24 horas" if ing else ""))
    elif na_meta == "Não":
        ing = f"{ingestao} kcal" if ingestao and "kcal" not in ingestao.lower() else ingestao
        gastro.append("Fora da meta calórica" + (f", {ing} nas últimas 24 horas" if ing else ""))

    escape = _s("sis_gastro_escape_glicemico")
    if escape == "Sim":
        vezes   = _s("sis_gastro_escape_vezes")
        turnos  = _turnos()
        i_m = _s("sis_gastro_insulino_dose_manha")
        i_t = _s("sis_gastro_insulino_dose_tarde")
        i_n = _s("sis_gastro_insulino_dose_noite")
        insulino = _s("sis_gastro_insulino")
        doses = [f"{d} UI" for d in [i_m, i_t, i_n] if d]
        insulino_str = " - ".join(doses) if doses else ""
        esc = "Escape glicêmico:"
        if vezes:
            try:
                n = int(str(vezes).strip())
                esc += f" {n} vez" if n == 1 else f" {n} vezes"
            except (ValueError, TypeError):
                esc += f" {vezes}"
        if turnos:  esc += f", {turnos}"
        if insulino == "Sim" and insulino_str: esc += f", em insulinoterapia {insulino_str}"
        gastro.append(esc)
    elif escape == "Não":
        gastro.append("Sem escape glicêmico, sem insulinoterapia")

    evac      = _s("sis_gastro_evacuacao")
    evac_data = _s("sis_gastro_evacuacao_data")
    laxativo  = _s("sis_gastro_laxativo")
    if evac == "Sim":
        gastro.append("Evacuação: Presente" + (f", última em {evac_data}" if evac_data else ""))
    elif evac == "Não":
        linha_ev = "Evacuação: Ausente"
        if evac_data: linha_ev += f", última em {evac_data}"
        if laxativo:  linha_ev += f", em uso de {laxativo}"
        gastro.append(linha_ev)

    pocus = _s("sis_gastro_pocus")
    if pocus: gastro.append(f"Pocus Exame Abdominal: {pocus}")
    obs = _s("sis_gastro_obs")
    if obs: gastro.append(f"Obs: {obs}")
    nutri_obs = _s("sis_nutri_obs")
    if nutri_obs: gastro.append(f"Nutri: {nutri_obs}")

    if gastro:
        corpo.append("")
        corpo.append("- Exame Abdominal")
        corpo.extend(gastro)

    # ── RENAL ────────────────────────────────────────────────────────────────
    renal = []

    diurese  = _s("sis_renal_diurese"); balanco = _s("sis_renal_balanco"); bal_ac = _s("sis_renal_balanco_acum")
    _ml = lambda v: f"{v} mL" if v and "ml" not in str(v).lower() else v
    bh = [p for p in [
        f"Diurese {_ml(diurese)}" if diurese else None,
        f"BH {_ml(balanco)}" if balanco else None,
        f"BH Acumulado {_ml(bal_ac)}" if bal_ac else None,
    ] if p]
    if bh: renal.append(" | ".join(bh))

    volemia = _s("sis_renal_volemia")
    if volemia: renal.append(volemia)

    cr_a = _s("sis_renal_cr_antepen"); cr_u = _s("sis_renal_cr_ult"); cr_h = _s("sis_renal_cr_hoje")
    ur_a = _s("sis_renal_ur_antepen"); ur_u = _s("sis_renal_ur_ult"); ur_h = _s("sis_renal_ur_hoje")
    fr_p = []
    if cr_a or cr_u or cr_h:
        partes = [str(_limpar_barra(p) or p) for p in [cr_a, cr_u, cr_h] if p]
        fr_p.append("Cr: " + " → ".join(partes))
    if ur_a or ur_u or ur_h:
        partes = [str(_limpar_barra(p) or p) for p in [ur_a, ur_u, ur_h] if p]
        fr_p.append("Ur: " + " → ".join(partes))
    if fr_p: renal.append(" | ".join(fr_p))

    _DHE = [
        ("sis_renal_sodio",    ["Hiponatremia", "Hipernatremia"]),
        ("sis_renal_potassio", ["Hipocalemia",  "Hipercalemia"]),
        ("sis_renal_magnesio", ["Hipomagnesemia","Hipermagnesemia"]),
        ("sis_renal_fosforo",  ["Hipofosfatemia","Hiperfosfatemia"]),
        ("sis_renal_calcio",   ["Hipocalcemia",  "Hipercalcemia"]),
    ]
    disturbs = [_s(k) for k, vals in _DHE if _s(k) in vals]
    if disturbs: renal.append("DHE: " + ", ".join(disturbs))

    trs = _s("sis_renal_trs")
    if trs == "Sim":
        trs_p = ["Em TRS"]
        via = _s("sis_renal_trs_via"); ult = _s("sis_renal_trs_ultima"); prox = _s("sis_renal_trs_proxima")
        if via:  trs_p.append(via)
        if ult:  trs_p.append(f"Última TSR em {ult}")
        if prox: trs_p.append(f"próxima programada para {prox}")
        renal.append(", ".join(trs_p))
    elif trs == "Não":
        renal.append("Sem TRS")

    pocus = _s("sis_renal_pocus")
    if pocus: renal.append(f"Pocus Renal: {pocus}")
    obs = _s("sis_renal_obs")
    if obs: renal.append(f"Obs: {obs}")
    metab_obs = _s("sis_metab_obs")
    if metab_obs: renal.append(f"Metab: {metab_obs}")

    if renal:
        corpo.append("")
        corpo.append("- Renal")
        corpo.extend(renal)

    # ── INFECCIOSO ───────────────────────────────────────────────────────────
    infec = []

    febre = _s("sis_infec_febre"); f_v = _s("sis_infec_febre_vezes"); f_u = _s("sis_infec_febre_ultima")
    if febre == "Sim":
        feb = "Febre: Presente"
        if f_v:
            try:
                n = int(str(f_v).strip())
                feb += f", {n} vez" if n == 1 else f", {n} vezes"
            except (ValueError, TypeError):
                feb += f", {f_v}"
        if f_u: feb += f"; Último pico febril: {f_u}"
        infec.append(feb)
    elif febre == "Não":
        infec.append("Febre: Ausente")

    atb       = _s("sis_infec_atb");       atb_g = _s("sis_infec_atb_guiado")
    atb_lista = _lista_e([_s("sis_infec_atb_1"), _s("sis_infec_atb_2"), _s("sis_infec_atb_3")])
    if atb == "Sim":
        guiado = {"Sim": "guiada por culturas", "Não": "empírica"}.get(atb_g or "", "")
        base = f"Antibioticoterapia{f' {guiado}' if guiado else ''}"
        infec.append(f"{base} em uso de {atb_lista}" if atb_lista else base)
    elif atb == "Não":
        infec.append("Sem antibioticoterapia")

    cult_and = _s("sis_infec_culturas_and")
    if cult_and == "Sim":
        cults = []
        for i in range(1, 5):
            s = _s(f"sis_infec_cult_{i}_sitio"); d = _s(f"sis_infec_cult_{i}_data")
            if s: cults.append(f"{s} ({d})" if d else s)
        if cults: infec.append("Culturas em andamento: " + ", ".join(cults))
    elif cult_and == "Não":
        infec.append("Sem culturas em andamento")

    pcr_a = _s("sis_infec_pcr_antepen"); pcr_u = _s("sis_infec_pcr_ult"); pcr_h = _s("sis_infec_pcr_hoje")
    leuc_a = _s("sis_infec_leuc_antepen"); leuc_u = _s("sis_infec_leuc_ult"); leuc_h = _s("sis_infec_leuc_hoje")
    marc = []
    if pcr_a or pcr_u or pcr_h:
        partes = [str(_limpar_barra(p) or p) for p in [pcr_a, pcr_u, pcr_h] if p]
        marc.append("PCR: " + " → ".join(partes))
    if leuc_a or leuc_u or leuc_h:
        partes = [str(_limpar_barra(p) or p) for p in [leuc_a, leuc_u, leuc_h] if p]
        marc.append("Leucócitos: " + " → ".join(partes))
    if marc: infec.append(" | ".join(marc))

    iso = _s("sis_infec_isolamento")
    if iso == "Sim":
        i_tipo = _s("sis_infec_isolamento_tipo")
        infec.append(f"Isolamento: {i_tipo}" if i_tipo else "Isolamento: presente")

    pat = _s("sis_infec_patogenos")
    if pat: infec.append(f"Patógenos isolados: {pat}")

    pocus = _s("sis_infec_pocus")
    if pocus: infec.append(f"Pocus Infeccioso: {pocus}")
    obs = _s("sis_infec_obs")
    if obs: infec.append(f"Obs: {obs}")

    if infec:
        corpo.append("")
        corpo.append("- Infeccioso")
        corpo.extend(infec)

    # ── HEMATOLÓGICO ─────────────────────────────────────────────────────────
    hemato = []

    anticoag = _s("sis_hemato_anticoag")
    if anticoag == "Sim":
        ac_t = _s("sis_hemato_anticoag_tipo")
        ac_m = _s("sis_hemato_anticoag_motivo")
        if ac_t == "Plena" and ac_m:
            ac_m_display = _sigla_upper(ac_m) if ac_m else ac_m  # TEP, TVP, FA em maiúsculas
            hemato.append(f"Anticoagulação: Plena, por {ac_m_display}")
        elif ac_t:
            hemato.append(f"Anticoagulação: {ac_t}")
        else:
            hemato.append("Anticoagulação: em uso")
    elif anticoag == "Não":
        hemato.append("Sem anticoagulação")

    sangr = _s("sis_hemato_sangramento")
    if sangr == "Sim":
        s_v = _s("sis_hemato_sangramento_via"); s_d = _s("sis_hemato_sangramento_data")
        linha_s = "Sangramento presente"
        if s_v: linha_s += f"; {s_v}"
        if s_d: linha_s += f", último apresentado em {s_d}"
        hemato.append(linha_s)
    elif sangr == "Não":
        hemato.append("Sem sangramentos")

    t_data = _s("sis_hemato_transf_data")
    if t_data:
        comps = []
        for i in range(1, 4):
            cn = _s(f"sis_hemato_transf_{i}_comp"); cb = _s(f"sis_hemato_transf_{i}_bolsas")
            if cn: comps.append(f"{cn} {cb}" if cb else cn)
        hemato.append(f"Transfusão em {t_data}" + ("; " + ", ".join(comps) if comps else ""))

    hb_a = _s("sis_hemato_hb_antepen"); hb_u = _s("sis_hemato_hb_ult"); hb_h = _s("sis_hemato_hb_hoje")
    pl_a = _s("sis_hemato_plaq_antepen"); pl_u = _s("sis_hemato_plaq_ult"); pl_h = _s("sis_hemato_plaq_hoje")
    hemo2 = []
    if hb_a or hb_u or hb_h:
        partes = [str(_limpar_barra(p) or p) for p in [hb_a, hb_u, hb_h] if p]
        hemo2.append("Hb: " + " → ".join(partes))
    if pl_a or pl_u or pl_h:
        partes = [str(_limpar_barra(p) or p) for p in [pl_a, pl_u, pl_h] if p]
        hemo2.append("Plaq: " + " → ".join(partes))
    if hemo2: hemato.append(" | ".join(hemo2))

    inr_a = _s("sis_hemato_inr_antepen"); inr_u = _s("sis_hemato_inr_ult"); inr_h = _s("sis_hemato_inr_hoje")
    if inr_a or inr_u or inr_h:
        partes = [str(_limpar_barra(p) or p) for p in [inr_a, inr_u, inr_h] if p]
        hemato.append("INR: " + " → ".join(partes))

    pocus = _s("sis_hemato_pocus")
    if pocus: hemato.append(f"Pocus Hematológico: {pocus}")
    obs = _s("sis_hemato_obs")
    if obs: hemato.append(f"Obs: {obs}")

    if hemato:
        corpo.append("")
        corpo.append("- Hematológico")
        corpo.extend(hemato)

    # ── PELE E MUSCULOESQUELÉTICO ─────────────────────────────────────────────
    pele = []

    edema = _s("sis_pele_edema")
    cruzes = _s("sis_pele_edema_cruzes")
    if edema == "Presente":
        cruzes_str = str(cruzes).strip() if cruzes else ""
        if cruzes_str in ("1", "2", "3", "4"):
            pele.append(f"Edema presente, {cruzes_str}+")
        else:
            pele.append("Edema presente")
    elif edema == "Ausente":
        pele.append("Sem edema")

    lpp = _s("sis_pele_lpp")
    if lpp == "Sim":
        lpp_items = []
        for i in range(1, 4):
            loc = _s(f"sis_pele_lpp_local_{i}"); grau = _s(f"sis_pele_lpp_grau_{i}")
            if loc: lpp_items.append(f"{loc} {grau}" if grau else loc)
        pele.append("LPP: " + ", ".join(lpp_items) if lpp_items else "LPP: presente")
    elif lpp == "Não":
        pele.append("Sem LPP")

    polineu = _s("sis_pele_polineuropatia")
    if polineu == "Sim":   pele.append("Polineuropatia do doente crítico")
    elif polineu == "Não": pele.append("Sem polineuropatia")

    pocus = _s("sis_pele_pocus")
    if pocus: pele.append(f"Pocus Pele e musculoesquelético: {pocus}")
    obs = _s("sis_pele_obs")
    if obs: pele.append(f"Obs: {obs}")

    if pele:
        corpo.append("")
        corpo.append("- Pele e Musculoesquelético")
        corpo.extend(pele)

    if not corpo:
        return []
    return ["# Evolução por sistemas"] + corpo


def gerar_texto_final() -> str:
    """
    Monta o texto final do prontuário concatenando todas as seções.
    Cada seção retorna uma lista de linhas; seções vazias são ignoradas.
    """
    secoes = []

    secoes.append(_secao_identificacao())
    secoes.append(_secao_diagnosticos())
    secoes.append(_secao_comorbidades())
    secoes.append(_secao_muc())
    secoes.append(_secao_dispositivos())
    secoes.append(_secao_culturas())
    secoes.append(_secao_hmpa())

    secoes.append(_secao_antibioticos())
    secoes.append(_secao_complementares())
    secoes.append(_secao_laboratoriais())
    secoes.append(_secao_controles())
    secoes.append(_secao_evolucao_clinica())
    secoes.append(_secao_sistemas())
    secoes.append(_secao_condutas())
    secoes.append(_secao_prescricao())

    blocos = []
    for s in secoes:
        if not s:
            continue
        # Garante que nenhuma seção termine com linhas em branco
        while s and s[-1] == "":
            s.pop()
        if s:
            blocos.append("\n".join(s))
    texto = "\n\n".join(blocos)
    # Normaliza ml → mL em toda a saída
    texto = texto.replace(" ml", " mL")
    return texto
