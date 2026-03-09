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
        ("HCM",   "hcm"),   ("RDW",   "rdw"),   ("Leuco","__leuco_dif__"),
        ("Plaq",  "plaq"),  ("Cr",    "cr"),     ("Ur",   "ur"),
        ("Na",    "na"),    ("K",     "k"),      ("Mg",   "mg"),
        ("Pi",    "pi"),    ("CaT",   "cat"),    ("CaI",  "cai"),
        ("TGO",   "tgo"),   ("TGP",   "tgp"),   ("FAL",  "fal"),
        ("GGT",   "ggt"),   ("BT",    "__bt_bd__"), ("Prot Tot", "prot_tot"),
        ("Amil",  "amil"),  ("Lipas", "lipas"),  ("Alb",  "alb"),   ("LDH",  "ldh"),
        ("CPK",   "cpk"),   ("CPK-MB","cpk_mb"), ("BNP",  "bnp"),
        ("Trop",  "trop"),  ("PCR",   "pcr"),    ("VHS",  "vhs"),    ("Lac sérico","lac"),
        ("TP",    "tp"),    ("TTPa",  "ttpa"),   ("Fibrin","fbrn"),
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

    def _slot_tem_dados(i):
        return any([_v(i, "data"), _v(i, "hb"), _v(i, "cr"), _v(i, "na"),
                    _v(i, "plaq"), _v(i, "gas_ph"), _v(i, "outros")])

    def _sort_key(i):
        data = _v(i, "data")
        hora = _v(i, "hora") if _v(i, "hora") else ""
        try:
            p = data.split("/")
            data_iso = f"{p[2]}-{p[1]}-{p[0]}" if len(p) == 3 else ""
        except (IndexError, ValueError):
            data_iso = ""
        try:
            hora_int = int(hora.split(":")[0]) if ":" in hora else 0
        except (ValueError, IndexError):
            hora_int = 0
        return (data_iso, hora_int)

    active_slots = sorted(
        [i for i in range(1, 31) if _slot_tem_dados(i)],
        key=_sort_key,
    )

    slots = []
    for i in active_slots:
        data   = _v(i, "data")
        hora   = _v(i, "hora")
        outros = _v(i, "outros")

        _DIF_CAMPOS = [
            ("Blastos","leuco_bla"), ("Mielos","leuco_mie"), ("Metas","leuco_meta"),
            ("Bast","leuco_bast"),   ("Seg","leuco_seg"),    ("Linf","leuco_linf"),
            ("Mon","leuco_mon"),     ("Eos","leuco_eos"),    ("Bas","leuco_bas"),
        ]

        main_parts = []
        for _lbl, _k in _MAIN:
            if _k == "__leuco_dif__":
                leuco_v = _v(i, "leuco")
                if not leuco_v:
                    continue
                if "(" in leuco_v:
                    main_parts.append(f"Leuco {leuco_v}")
                else:
                    dif_parts = [f"{dl} {_v(i, ds)}" for dl, ds in _DIF_CAMPOS if _v(i, ds)]
                    if dif_parts:
                        main_parts.append(f"Leuco {leuco_v} ({' / '.join(dif_parts)})")
                    else:
                        main_parts.append(f"Leuco {leuco_v}")
            elif _k == "__bt_bd__":
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
        header = f"> {data}"
        if hora:
            try:
                hc = int(hora.split(":")[0])
                header += f" ({hc:02d}h)"
            except (ValueError, IndexError):
                pass
        if data:
            linhas.append(header)
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
