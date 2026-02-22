"""
Extração de exames e prescrições usando a mesma lógica multi-agente do PACER.
- extrair_exames():      6 agentes paralelos (idêntico ao PACER — aba Exames)
- extrair_prescricao():  3 agentes sequenciais (idêntico ao PACER — aba Prescrição)
"""
import google.generativeai as genai
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed


# ==============================================================================
# HELPER: chamada única de IA (igual ao processar_texto do PACER)
# ==============================================================================

def _chamar_ia(provider: str, api_key: str, modelo: str,
               prompt_system: str, input_text: str) -> str:
    try:
        if "gemini" in provider.lower() or "google" in provider.lower():
            genai.configure(api_key=api_key)
            cfg = {"temperature": 0.0, "top_p": 1.0, "top_k": 1}
            m = genai.GenerativeModel(
                model_name=modelo,
                generation_config=cfg,
                system_instruction=prompt_system,
            )
            return m.generate_content(input_text).text
        else:
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user",   "content": input_text},
                ],
                temperature=0.0,
                top_p=0.1,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                max_tokens=2000,
                seed=42,
            )
            return resp.choices[0].message.content
    except Exception as e:
        return f"❌ Erro na API: {e}"


# ==============================================================================
# PROMPTS — EXAMES (cópia fiel dos agentes do PACER)
# ==============================================================================

_PROMPT_ID_EXAMES = """# ATUE COMO
Um formatador de identificação hospitalar.

# TAREFA
Extraia Nome, Registro (HC) e Data do texto.

# REGRAS DE FORMATAÇÃO (RIGOROSAS)
1. NOME: Converta OBRIGATORIAMENTE para Title Case (Apenas primeiras letras maiúsculas).
   - Entrada: "MARCOS PAULO DE GODOY" -> Saída: "Marcos Paulo de Godoy"
2. DATA: Se não houver data no texto, use a data de hoje.
3. SAÍDA: Exatamente duas linhas. Mantenha o travessão final.

# FORMATO DE RESPOSTA
Linha 1: [Nome Title Case] [HC]
Linha 2: [Data DD/MM/AAAA] –

# EXEMPLO DE SAÍDA (TEMPLATE)
João da Silva 1234567
01/02/2026 –

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

_PROMPT_HEMATOLOGIA_RENAL = """# ATUE COMO
Especialista em Hematologia e Nefrologia.

# TAREFA
Varra o texto buscando os dados abaixo.
Retorne APENAS os itens que possuem valor numérico, separados por " | ".

# REGRAS DE LIMPEZA (CRÍTICO)
- Se um item não tiver valor, IGNORE-O completamente.
- NÃO deixe pipes duplos "||".
- NÃO escreva o nome do exame se não houver número (Ex: Proibido retornar "Ur |").

# ORDEM DE BUSCA
1. Hb (1 casa decimal)
2. Ht (Inteiro + %)
3. [CONDICIONAL]: Se Hb < 9,0 inclua: VCM | HCM | RDW. (Se Hb >= 9,0, ignore estes 3).
4. Leuco (Se <500, converta ex: 0,4->400)
5. Fórmula (Bast X% / Seg Y% / Linf Z% / Mon W% / Eos K% / Bas H%). Use barras "/" internas.
6. Plaq
7. Cr (1 casa decimal)
8. Ur (Inteiro)
9. Na (Inteiro)
10. K (1 casa decimal)
11. Mg (1 casa decimal)
12. Pi (1 casa decimal)
13. CaT (1 casa decimal)
14. Cai (2 casas decimais)

# EXEMPLO DE SAÍDA (TEMPLATE)
Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | Cai 1,01

# FORMATO DE RESPOSTA
- Apenas a string de dados ou VAZIO. Sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

_PROMPT_HEPATICO = """# ATUE COMO
Especialista em Gastroenterologia.

# TAREFA
Extraia os dados abaixo. Se o dado não existir, PULE para o próximo.
Não deixe espaços vazios ou pipes extras.

# ORDEM DE PREFERÊNCIA
1. TGP
2. TGO
3. FAL
4. GGT
5. BT (Se houver direta: BT X,X (Y,Y))
6. Prot Tot
7. Alb
8. Amil
9. Lipas

# REGRAS DE LIMPEZA
- Retorne apenas o que tiver valor.
- Exemplo: Se só tem TGP e Amilase, retorne: "TGP 32 | Amil 65".

# EXEMPLO DE SAÍDA (TEMPLATE)
TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Prot Tot 6,5 | Alb 3,8 | Amil 65 | Lipas 40

# FORMATO DE RESPOSTA
- Apenas a string de dados ou VAZIO. Sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

_PROMPT_COAGULACAO = """# ATUE COMO
Especialista em Marcadores Críticos.

# TAREFA
Extraia apenas os marcadores presentes no texto.

# LISTA ALVO
1. PCR (inteiro, sem casas decimais)
2. CPK (inteiro, sem casas decimais)
3. CK-MB (inteiro, sem casas decimais)
4. Trop (2 casas decimais)
5. TP (com RNI entre parênteses) - SEMPRE 1 casa decimal
6. TTPa (com Relação entre parênteses) - SEMPRE 1 casa decimal

# REGRAS DE PRECISÃO NUMÉRICA (RIGOROSO)
- PCR, CPK, CK-MB: INTEIROS (Ex: 89, 150, 12)
- Trop: 2 casas decimais (Ex: 0,01)
- TP: SEMPRE 1 casa decimal (Ex: 14,2s) - Sigla: "TP" (NÃO "TP Ativ")
- TTPa: SEMPRE 1 casa decimal (Ex: 69,1s)
- RNI/Relação: 2 casas decimais entre parênteses (Ex: (1,22))

# REGRA DE OURO (ANTI-ALUCINAÇÃO)
- Se o texto menciona "CPK" mas não traz o resultado numérico, NÃO inclua "CPK" na saída.
- Proibido saídas como: "CPK | CK-MB".
- Correto: "PCR 12 | Trop 0,01".

# EXEMPLOS DE SAÍDA (TEMPLATES)
Exemplo 1: PCR 89 | TP 14,2s (1,22) | TTPa 69,1s (2,49)
Exemplo 2: PCR 12 | CPK 150 | CK-MB 12 | Trop 0,01 | TP 14,2s (1,10) | TTPa 30,0s (1,00)

# FORMATO DE RESPOSTA
- Apenas a string de dados ou VAZIO. Sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

_PROMPT_URINA = """# ATUE COMO
Especialista em Urinálise.

# TAREFA
Verifique se há exame de URINA TIPO I (EAS).
- SE SIM: Monte a string completa.
- SE NÃO: Retorne string vazia.

# ESTRUTURA
Urn: Den: [Val] / Leu Est: [Val] / Nit: [Val] / Leuco [Val] / Hm : [Val] / Prot: [Val] / Cet: [Val] / Glic: [Val]

# REGRAS
- Den (Densidade): Ex 1.020.
- Qualitativos: Use "Pos" ou "Neg".
- Quantitativos: Use números.

# EXEMPLO DE SAÍDA (TEMPLATE)
Urn: Den: 1.020 / Leu Est: Neg / Nit: Neg / Leuco 4.000 / Hm : 2.000 / Prot: Neg / Cet: Neg / Glic: Neg

# FORMATO DE RESPOSTA
- Apenas a string formatada ou VAZIO. Sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

_PROMPT_GASOMETRIA = """# ATUE COMO
Especialista em Gasometria.

# TAREFA
Identifique Gasometria (Arterial, Venosa ou Ambas).
REGRA DE DATA: Se houver múltiplas coletas, extraia APENAS a que tiver horário mais recente.

# REGRAS DE PRECISÃO NUMÉRICA (RIGOROSO)
Aplique estas regras de arredondamento/formatação para cada item:
1. INTEIROS (Sem vírgula): pCO2, pO2, HCO3, SatO2, SvO2, AG, Cl, Na.
2. 1 CASA DECIMAL: BE (Ex: -2,3), Lac (Ex: 1,5), K (Ex: 4,0).
3. 2 CASAS DECIMAIS: pH (Ex: 7,35), Cai (Ex: 1,15).

# ESTRUTURA
- Use " / " entre valores.
- Use " | " entre blocos (apenas se for mista).

# CENÁRIOS
A. ARTERIAL: pH / pCO2 / pO2 / HCO3 / BE / SatO2 / Lac / AG / Cl / Na / K / Cai
B. VENOSA: pH / pCO2 / HCO3 / BE / SvO2 / Lac / AG / Cl / Na / K / Cai

# EXEMPLOS DE SAÍDA (TEMPLATES)
Exemplo 1 (Só Arterial):
Gas Art pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15

Exemplo 2 (Só Venosa):
Gas Ven pH 7,31 / pCO2 48 / HCO3 24 / BE -1,5 / SvO2 70% / Lac 1,8 / AG 12 / Cl 102 / Na 137 / K 4,2 / Cai 1,10

Exemplo 3 (Mista - Arterial Completa + Venosa Resumida):
Gas Art pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15 | Gas Ven pCO2 48 / SvO2 70%

# FORMATO DE RESPOSTA
- Escolha UM cenário. Retorne APENAS a string formatada conforme as regras de precisão.
- Se não houver dados, retorne VAZIO.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

# Ordem fixa dos agentes de exames (mesma do PACER)
_AGENTES_EXAMES_ORDEM = [
    "hematologia_renal",
    "hepatico",
    "coagulacao",
    "urina",
    "gasometria",
]
_AGENTES_EXAMES_PROMPTS = {
    "hematologia_renal": _PROMPT_HEMATOLOGIA_RENAL,
    "hepatico":          _PROMPT_HEPATICO,
    "coagulacao":        _PROMPT_COAGULACAO,
    "urina":             _PROMPT_URINA,
    "gasometria":        _PROMPT_GASOMETRIA,
}


# ==============================================================================
# PROMPTS — PRESCRIÇÃO (cópia fiel dos agentes do PACER)
# ==============================================================================

_PROMPT_ID_PRESCRICAO = """# ROLE
Você é um Especialista em Admissão e Registro Hospitalar.

# TAREFA
Sua única função é extrair os dados de identificação do paciente e o período da prescrição a partir do texto bruto.

# REGRAS DE EXTRAÇÃO
1. NOME: Converta OBRIGATORIAMENTE para Title Case (Apenas primeiras letras maiúsculas).
2. IDADE: Extraia apenas o número.
3. DATAS: Formato DD/MM/AAAA.
4. REGISTRO/LEITO: Se não encontrar, deixe em branco, mas mantenha a estrutura.

# ESTRUTURA DE SAÍDA (FORMATO RÍGIDO)
Retorne APENAS duas linhas de texto bruto (Plaintext). Nada mais.

Linha 1: [Nome Completo], [Idade] anos - [Registro] - [Leito]
Linha 2: Prescrição: [Data Início] até [Data Fim]

# EXEMPLO DE SAÍDA
João da Silva - 74 anos - 1570869/3 - 643A
Prescrição: 09/01/2026 até 10/01/2026

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

_PROMPT_DIETA = """# ROLE
Você é um Auditor de Nutrição Clínica.

# TAREFA
Extraia e organize os itens de nutrição.
Sua prioridade máxima é a CONSISTÊNCIA: Você deve gerar no máximo 1 linha para cada categoria nutricional.

# AS 6 CATEGORIAS PERMITIDAS (HIERARQUIA RÍGIDA)
1. Dieta Oral
2. Suplemento Oral
3. Hidratação (Água livre/Flush)
4. Dieta Enteral
5. Suplemento Enteral
6. Nutrição Parenteral (NPP)

# REGRAS DE PROCESSAMENTO (CRÍTICO)
1. REGRA DE FUSÃO (UNICIDADE): É estritamente PROIBIDO ter duas linhas da mesma categoria.
   - Cenário: O texto diz "Dieta branda" e depois "Dieta para diabetes".
   - Ação: Funda as características em uma única linha.
   - Resultado: "1. Dieta oral branda para diabetes".

2. O QUE INCLUIR:
   - Dietas, Suplementos (mesmo se estiverem em medicamentos) e NPP (mesmo se estiver em soluções).
   - Cuidados EXCLUSIVOS de hidratação.

3. LIMPEZA:
   - Troque ";" por " e ".
   - Padronize para Title Case na primeira letra.

# FORMATO DE SAÍDA
- Título: DIETA
- Lista numerada sequencial (iniciando em 1).
- Se uma categoria não existir, pule-a (não deixe linha vazia).

# EXEMPLO DE SAÍDA (CENÁRIO COMPLETO)
DIETA
1. Dieta oral liquidificada para diabetes e hepatopata
2. Suplemento oral hiperproteico 900 kcal
3. Hidratação via sonda 500ml a cada 8 horas
4. Dieta enteral oligomérica padrão 1000 kcal
5. Suplemento enteral hiperproteico 200 kcal
6. NPP individualizada oligomérica 1500 kcal

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

_PROMPT_MEDICACOES = """# ROLE
Você é um Farmacêutico Clínico Especialista em Segurança do Paciente.

# TAREFA
Extraia, Padronize e ORDENE as Medicações e Soluções.

# REGRAS DE PADRONIZAÇÃO
1. NOME: Fármaco + Concentração (Ex: Dipirona 1g).
2. DOSE: A quantidade final prescrita (Ex: 2 amp, 40mg). Não confunda com a concentração do frasco.
3. VIAS: Padronize para: Endovenoso, Intramuscular, Subcutâneo, Oral, Por Sonda, Inalatória, Retal.
4. FREQUÊNCIA:
   - "24/24h" -> converta para "1 vez ao dia".
   - Fixos: use separador " x " (Ex: 40 mg x 1 vez ao dia).
   - Se Necessário (ACM/SOS): use separador " ; " (Ex: Se Necessário).

# REGRAS DE SOLUÇÕES (SOROS/DILUENTES)
- Se houver dois volumes (ex: "Soro 250ml INJ 234ml"), escolha SEMPRE o volume de preparo (234ml) e ignore o nominal (250ml).
- Remova termos: "Base", "INJ", "Solução".

# O QUE IGNORAR (CRÍTICO)
- NÃO inclua Nutrição Parenteral (NPP) aqui. Isso pertence à Dieta.
- NÃO inclua Suplementos Nutricionais.

# ALGORITMO DE ORDENAÇÃO (OBRIGATÓRIO)
Processe tudo na memória e imprima nesta ordem estrita:

GRUPO 1: MEDICAMENTOS FIXOS (Horário agendado)
   Ordem: Endovenoso > Intramuscular > Subcutâneo > Oral > Sonda > Outros.

GRUPO 2: MEDICAMENTOS "SE NECESSÁRIO" (SOS/ACM)
   Ordem: Endovenoso > Intramuscular > Subcutâneo > Oral > Sonda > Outros.

GRUPO 3: SOLUÇÕES (Soros e Infusões Contínuas)
   Siga a mesma lógica (Fixos > SN).

# ESTRUTURA DE SAÍDA
Separe em dois blocos: MEDICAÇÕES e SOLUÇÕES.
Inicie a numeração em 1 para cada bloco.
Use quebra de linha dupla entre os blocos.

# FORMATO DE CADA LINHA
[Número]. [Nome]; [Dose]; [Via]; [Dose x Frequência ou Se Necessário]

# EXEMPLO DE SAÍDA
MEDICAÇÕES
1. Amicacina 500mg; 1 amp; Endovenoso; 1 amp x 1 vez ao dia
2. Sinvastatina 20mg; 40 mg; Oral; 40 mg x 1 vez ao dia
3. Dipirona 1g; 1 g; Endovenoso; Se Necessário

SOLUÇÕES
1. Norepinefrina 4 amp + Cloreto de Sodio 0,9% 234 ml; Endovenoso; A Critério Médico

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""


# ==============================================================================
# extrair_exames() — 6 agentes paralelos (idêntico ao PACER)
# ==============================================================================

def extrair_exames(texto: str, api_key: str, provider: str, modelo: str) -> str:
    """
    Processa texto bruto de exames com múltiplos agentes em paralelo.
    Retorna string formatada no padrão PACER (Nome HC / Data – Exames).
    """
    if not texto or not api_key:
        return ""

    # Passo 1: identificação (sequencial)
    resultado_id = _chamar_ia(provider, api_key, modelo, _PROMPT_ID_EXAMES, texto)
    if resultado_id.startswith("❌") or resultado_id.startswith("⚠️"):
        return resultado_id

    linhas = resultado_id.strip().split("\n")
    if len(linhas) < 2:
        return "❌ Erro ao extrair identificação dos exames."
    nome_hc   = linhas[0].strip()
    data_linha = linhas[1].strip()

    # Passo 2: 5 agentes especializados em paralelo
    resultados_dict: dict[str, str] = {}

    def _worker(agente_id: str):
        prompt = _AGENTES_EXAMES_PROMPTS[agente_id]
        r = _chamar_ia(provider, api_key, modelo, prompt, texto)
        if r and "❌" not in r and "⚠️" not in r:
            r_limpo = r.strip().rstrip(".,:;!? ")
            if r_limpo and r_limpo.upper() != "VAZIO":
                return agente_id, r_limpo
        return agente_id, None

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_worker, aid): aid for aid in _AGENTES_EXAMES_ORDEM}
        for future in as_completed(futures):
            aid, resultado = future.result(timeout=60)
            if resultado:
                resultados_dict[aid] = resultado

    # Passo 3: montar resultado na ordem fixa do PACER
    partes = [r for aid in _AGENTES_EXAMES_ORDEM if (r := resultados_dict.get(aid))]

    if partes:
        return f"{nome_hc}\n{data_linha} " + " | ".join(partes)
    return f"{nome_hc}\n{data_linha} (Nenhum dado laboratorial encontrado)"


# ==============================================================================
# extrair_prescricao() — 3 agentes sequenciais (idêntico ao PACER)
# ==============================================================================

def extrair_prescricao(texto: str, api_key: str, provider: str, modelo: str) -> str:
    """
    Processa texto bruto de prescrição com 3 agentes especializados.
    Retorna string completa: Identificação / DIETA / MEDICAÇÕES / SOLUÇÕES.
    """
    if not texto or not api_key:
        return ""

    # Agente 1: Identificação
    resultado_id = _chamar_ia(provider, api_key, modelo, _PROMPT_ID_PRESCRICAO, texto)
    if resultado_id.startswith("❌") or resultado_id.startswith("⚠️"):
        return resultado_id
    identificacao = resultado_id.strip()

    # Agente 2: Dieta
    resultado_dieta = ""
    try:
        r = _chamar_ia(provider, api_key, modelo, _PROMPT_DIETA, texto)
        if r and "❌" not in r and "⚠️" not in r:
            r_limpo = r.strip()
            if r_limpo and r_limpo.upper() != "VAZIO":
                resultado_dieta = r_limpo
    except Exception:
        pass

    # Agente 3: Medicações e Soluções
    resultado_med = ""
    try:
        r = _chamar_ia(provider, api_key, modelo, _PROMPT_MEDICACOES, texto)
        if r and "❌" not in r and "⚠️" not in r:
            r_limpo = r.strip()
            if r_limpo and r_limpo.upper() != "VAZIO":
                resultado_med = r_limpo
    except Exception:
        pass

    # Montar resultado final
    partes = [identificacao]
    if resultado_dieta:
        partes.append("\n" + resultado_dieta)
    if resultado_med:
        partes.append("\n" + resultado_med)
    if not resultado_dieta and not resultado_med:
        partes.append("\n(Nenhum dado de prescrição encontrado)")

    return "\n".join(partes)
