from ._base import *
import streamlit as st

def _secao_laboratoriais() -> list[str]:
    """
    Gera a saída determinística dos laboratoriais.

    Por slot:
        > {data}
        {linha principal: campos preenchidos separados por ' | '}
        {outros}  ← linha livre, se preenchida
        Gas Art/Ven/Par - ...  ← gasometrias
        Urn: ...              ← EAS, se preenchido
    """
    def _v(i, campo):
        v = _get(f"lab_{i}_{campo}")
        return str(v).strip() if v else ""

    def _par(label, val):
        return f"{label} {val}" if val else None

    _MAIN = [
        ("Hb",    "hb"),    ("Ht",    "ht"),    ("VCM",  "vcm"),
        ("HCM",   "hcm"),   ("RDW",   "rdw"),   ("Leuco","leuco"),
        ("Plaq",  "plaq"),  ("Cr",    "cr"),     ("Ur",   "ur"),
        ("Na",    "na"),    ("K",     "k"),      ("Mg",   "mg"),
        ("Pi",    "pi"),    ("CaT",   "cat"),    ("CaI",  "cai"),
        ("TGO",   "tgo"),   ("TGP",   "tgp"),   ("FAL",  "fal"),
        ("GGT",   "ggt"),   ("BT",    "__bt_bd__"), ("Prot Tot", "prot_tot"),
        ("Amil",  "amil"),  ("Lipas", "lipas"),  ("Alb",  "alb"),
        ("CPK",   "cpk"),   ("CPK-MB","cpk_mb"), ("BNP",  "bnp"),
        ("Trop",  "trop"),  ("PCR",   "pcr"),    ("VHS",  "vhs"),
        ("TP",    "tp"),    ("TTPa",  "ttpa"),
    ]
    _GAS_CAMPOS = [
        ("pH",    "ph"),  ("pCO2", "pco2"), ("Bic",  "hco3"),
        ("BE",    "be"),  ("Cl",   "cl"),   ("AG",   "ag"),
        ("pO2",   "po2"), ("SatO2","sat"),  ("Na",   "na"),
        ("K",     "k"),   ("CaI",  "cai"),  ("Lac",  "lac"),
    ]
    _EAS = [
        ("Den",      "ur_dens"), ("Leu Est", "ur_le"),  ("Nit",  "ur_nit"),
        ("Leuco",    "ur_leu"),  ("Hm",      "ur_hm"),  ("Prot", "ur_prot"),
        ("Cet",      "ur_cet"),  ("Glic",    "ur_glic"),
    ]

    import re as _re

    def _normalizar_outros(texto: str) -> str:
        """
        Normaliza capitalização do campo 'Não Transcritos':
        - Palavra all-caps com > 4 letras → Title Case  (GLICOSE → Glicose)
        - Sigla all-caps com ≤ 4 letras  → mantém      (TSH, PCR, PTH → intacto)
        - Resto (já misto)               → mantém
        """
        def _fix(m):
            w = m.group(0)
            if w.isupper() and len(w) > 4:
                return w.capitalize()
            return w
        return _re.sub(r"[A-Za-zÀ-ÿ]{2,}", _fix, texto)

    def _linha_gas(i, gn):
        p  = "gas" if gn == 1 else f"gas{gn}"
        kv = "gasv_pco2" if gn == 1 else f"{p}v_pco2"
        ks = "svo2"      if gn == 1 else f"{p}_svo2"

        tipo      = _v(i, f"{p}_tipo")
        gasv_pco2 = _v(i, kv)
        svo2_val  = _v(i, ks)
        partes    = [f"{lbl} {_v(i, f'{p}_{c}')}" for lbl, c in _GAS_CAMPOS if _v(i, f'{p}_{c}')]

        if not partes and not gasv_pco2:
            return []

        resultado = []
        if partes:
            hora_raw = _v(i, f"{p}_hora")
            if hora_raw:
                _m = _re.match(r"(\d+)", hora_raw.strip())
                hora_fmt = f"({int(_m.group(1)):02d}h)" if _m else ""
            else:
                hora_fmt = ""

            if tipo == "Pareada" or (tipo not in ("Arterial", "Venosa") and gasv_pco2):
                perf = [x for x in [_par("pCO2", gasv_pco2), _par("SvO2", svo2_val)] if x]
                linha = f"Gas Par {hora_fmt}".strip() + " " + " / ".join(partes)
                if perf:
                    linha += " | " + " / ".join(perf)
                resultado.append(linha)
            else:
                if tipo == "Arterial":
                    prefixo = "Gas Art"
                elif tipo == "Venosa":
                    prefixo = "Gas Ven"
                else:
                    if _v(i, f"{p}_po2"):
                        prefixo = "Gas Art"
                    else:
                        sat_raw = _v(i, f"{p}_sat")
                        try:
                            prefixo = "Gas Art" if float(str(sat_raw).replace("%","").strip()) > 82 else "Gas Ven"
                        except (ValueError, TypeError):
                            prefixo = "Gas Art"

                prefixo_hora = f"{prefixo} {hora_fmt}" if hora_fmt else prefixo
                if prefixo == "Gas Ven" and svo2_val and not gasv_pco2:
                    partes.append(f"SvO2 {svo2_val}")
                resultado.append(prefixo_hora + " " + " / ".join(partes))

        return resultado

    slots = []
    for i in range(1, 11):
        data   = _v(i, "data")
        outros = _v(i, "outros")

        main_parts = []
        for _lbl, _k in _MAIN:
            if _k == "__bt_bd__":
                bt_v = _v(i, "bt")
                bd_v = _v(i, "bd")
                if bt_v:
                    main_parts.append(f"BT {bt_v} (BD {bd_v})" if bd_v else f"BT {bt_v}")
            else:
                val = _v(i, _k)
                if val:
                    main_parts.append(f"{_lbl} {val}")
        linha_main = " | ".join(main_parts)

        linhas_gas = _linha_gas(i, 1) + _linha_gas(i, 2) + _linha_gas(i, 3)
        partes_eas = [f"{lbl}: {_v(i, k)}" for lbl, k in _EAS if _v(i, k)]

        if not any([data, linha_main, outros, linhas_gas, partes_eas]):
            continue

        linhas = []
        if i == 4:
            # Slot 4 (Admissão/Externo): prefixo "Adm –" inline, sem header ">"
            adm_prefix = f"> Adm ({data}) –" if data else "> Adm –"
            if linha_main:
                linhas.append(f"{adm_prefix} {linha_main}")
            elif data:
                linhas.append(adm_prefix)
        else:
            if data:
                linhas.append(f"> {data}")
            if linha_main:
                linhas.append(linha_main)
        if outros:
            linhas.append(_normalizar_outros(outros))
        linhas.extend(linhas_gas)
        if partes_eas:
            linhas.append("Urn: " + " / ".join(partes_eas))

        slots.append(linhas)

    if not slots:
        return []

    resultado = ["# Laboratoriais"]
    for slot in slots:
        resultado.extend(slot)
    return resultado
