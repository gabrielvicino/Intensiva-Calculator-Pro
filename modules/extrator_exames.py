"""
Extração de exames e prescrições usando a mesma lógica multi-agente do PACER.
- extrair_exames():      6 agentes paralelos (idêntico ao PACER — aba Exames)
- extrair_prescricao():  3 agentes sequenciais (idêntico ao PACER — aba Prescrição)

Qualidade: sempre usa gemini-2.5-pro para Gemini (exames, gasometria e prescrição
exigem máxima precisão). Para OpenAI, usa gpt-4o.
"""
from google import genai as _genai_new
from google.genai import types as _genai_types
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# Modelo fixo de alta qualidade para exames e prescrição
_MODELO_GEMINI_QUALIDADE = "gemini-2.5-pro"


# ==============================================================================
# HELPER: chamada única de IA (igual ao processar_texto do PACER)
# ==============================================================================

def _chamar_ia(provider: str, api_key: str, modelo: str,
               prompt_system: str, input_text: str) -> str:
    try:
        if "gemini" in provider.lower() or "google" in provider.lower():
            client = _genai_new.Client(api_key=api_key)
            response = client.models.generate_content(
                model=_MODELO_GEMINI_QUALIDADE,  # sempre Pro para exames/prescrição
                contents=input_text,
                config=_genai_types.GenerateContentConfig(
                    system_instruction=prompt_system,
                    temperature=0.0,
                    thinking_config=_genai_types.ThinkingConfig(thinking_budget=0),
                ),
            )
            return response.text
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
5. Fórmula do Leuco (use apenas os que existirem, com barras "/" internas):
   Blast X% / Mie X% / Meta X% / Bast X% / Seg X% / Linf X% / Mon X% / Eos X% / Bas X%
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
Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Blast 0% / Mie 0% / Meta 1% / Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | Cai 1,01

# FORMATO DE RESPOSTA
- Apenas a string de dados ou VAZIO. Sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

_PROMPT_HEPATICO = """# ATUE COMO
Especialista em Gastroenterologia e Bioquímica.

# TAREFA
Extraia os dados abaixo. Se o dado não existir, PULE para o próximo.
Não deixe espaços vazios ou pipes extras.

# ORDEM DE PREFERÊNCIA
1. TGP (Alanina Aminotransferase / ALT)
2. TGO (Aspartato Aminotransferase / AST)
3. FAL (Fosfatase Alcalina)
4. GGT (Gama GT)
5. BT (Se houver direta: BT X,X (Y,Y))
6. Prot Tot
7. Alb (Albumina)
8. LDH (Lactato Desidrogenase)
9. Amil (Amilase)
10. Lipas (Lipase)

# REGRAS DE LIMPEZA
- Retorne apenas o que tiver valor.
- Exemplo: Se só tem TGP e LDH, retorne: "TGP 32 | LDH 280".

# EXEMPLO DE SAÍDA (TEMPLATE)
TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Prot Tot 6,5 | Alb 3,8 | LDH 280 | Amil 65 | Lipas 40

# FORMATO DE RESPOSTA
- Apenas a string de dados ou VAZIO. Sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

_PROMPT_COAGULACAO = """# ATUE COMO
Especialista em Marcadores Críticos e Coagulação.

# TAREFA
Extraia apenas os marcadores presentes no texto.

# LISTA ALVO
1. PCR (Proteína C Reativa — inteiro, sem casas decimais)
2. VHS (Velocidade de hemossedimentação — inteiro)
3. CPK (inteiro, sem casas decimais)
4. CK-MB (inteiro, sem casas decimais)
5. BNP ou NT-proBNP (inteiro)
6. Trop (Troponina — 2 casas decimais)
7. TP (com atividade % e RNI entre parênteses) - SEMPRE 1 casa decimal
8. TTPa (com Relação entre parênteses) - SEMPRE 1 casa decimal
9. Fibrin (Fibrinogênio — inteiro)
10. Lac sérico (Lactato SÉRICO — não gasometria; 1 casa decimal)

# REGRAS DE PRECISÃO NUMÉRICA (RIGOROSO)
- PCR, VHS, CPK, CK-MB, BNP, Fibrin: INTEIROS (Ex: 89, 150, 12)
- Trop: 2 casas decimais (Ex: 0,01)
- TP: formato "Xs (Ativ Y% / RNI Z,ZZ)". Exemplo: "TP 19,7s (Ativ 48% / RNI 1,52)"
- TTPa: formato "Xs (R: Z,ZZ)". Exemplo: "TTPa 33,1s (R: 1,18)"
- Lac sérico: apenas se for lactato de sangue venoso/arterial POR FORA da gasometria. Ex: "Lac sérico 2,1"

# REGRA DE OURO (ANTI-ALUCINAÇÃO)
- Se o texto menciona um exame mas não traz resultado numérico, NÃO inclua na saída.
- Lac sérico: NÃO extrair se o lactato vier exclusivamente dentro da gasometria (pO2, pH, etc).

# EXEMPLOS DE SAÍDA (TEMPLATES)
Exemplo 1: PCR 89 | TP 19,7s (Ativ 48% / RNI 1,52) | TTPa 33,1s (R: 1,18)
Exemplo 2: PCR 12 | VHS 45 | CPK 150 | CK-MB 12 | Trop 0,01 | Fibrin 320 | BNP 450 | TP 14,2s (Ativ 80% / RNI 1,10) | TTPa 30,0s (R: 1,00)

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
Identifique TODAS as gasometrias no texto. Extraia tipo (Arterial ou Venosa), hora e valores de cada uma.
Agrupe em até 3 ENTRADAS e retorne da mais recente para a mais antiga.

# PASSO 1 — EXTRAIR E ORDENAR
Liste todas as gasometrias encontradas com seus horários.
Se o horário não estiver disponível, trate essa gasometria como a mais antiga.

# PASSO 2 — REGRA DE AGRUPAMENTO (PAREADA vs SEPARADA)
Para cada par Arterial + Venosa no texto:
  - Diferença de horário < 2 horas → PAREADA (formam UMA entrada com prefixo "Gas Par")
  - Diferença de horário ≥ 2 horas → SEPARADAS (cada uma é uma entrada independente)

Gasometrias do mesmo tipo (ex: duas arteriais) são SEMPRE entradas independentes.

# PASSO 3 — SELECIONAR ATÉ 3 ENTRADAS
- Ordene as entradas da mais recente para a mais antiga.
- Selecione no máximo 3 entradas para a saída.
- Entrada PAREADA: o horário de referência é o da arterial.

# REGRA DE HORA
- Extraia a hora do campo "Recebimento material:", "Data da coleta" ou similar.
- Formate como "HHh" com dois dígitos: "04:18" → "04h" | "16:45" → "16h" | "4h" → "04h".
- Se hora indisponível, omita o bloco de hora (ex: "Gas Art pH 7,35 / ...").

# REGRAS DE PRECISÃO NUMÉRICA E DADOS FALTANTES (RIGOROSO)
1. INTEIROS (sem vírgula): pCO2, pO2, HCO3, SatO2, SvO2, AG, Cl, Na.
2. 1 CASA DECIMAL: BE (Ex: -2,3), Lac (Ex: 1,5), K (Ex: 4,0).
3. 2 CASAS DECIMAIS: pH (Ex: 7,35), Cai (Ex: 1,15).
4. DADOS FALTANTES: Se algum exame não constar no laudo, pule o item. Não deixe barras (/) sobrando.

# CAMPOS POR TIPO DE ENTRADA
- ARTERIAL isolada:              Gas Art (HHh) pH / pCO2 / pO2 / HCO3 / BE / SatO2 / Lac / AG / Cl / Na / K / Cai
- VENOSA isolada (≥ 2h):        Gas Ven (HHh) pH / pCO2 / HCO3 / BE / SvO2 / Lac / AG / Cl / Na / K / Cai
  → SatO2 vira SvO2. pO2 NÃO aparece.
- PAREADA (< 2h): Gas Par (HHh) arterial COMPLETA | pCO2 X / SvO2 Y%
  → Hora exibida = hora da arterial. Venosa: apenas pCO2 e SvO2, sem prefixo, separados por " | ".

# ESTRUTURA DE SAÍDA
- Cada entrada ocupa UMA linha.
- Separe valores com " / ".
- Retorne as entradas da mais recente para a mais antiga, uma por linha.

# EXEMPLOS DE SAÍDA

Exemplo 1 — 1 arterial:
Gas Art (04h) pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15

Exemplo 2 — 1 venosa isolada:
Gas Ven (16h) pH 7,31 / pCO2 48 / HCO3 24 / BE -1,5 / SvO2 70% / Lac 1,8 / AG 12 / Cl 102 / Na 137 / K 4,2 / Cai 1,10

Exemplo 3 — PAREADA (Art 04h + Ven 05h → diff 1h < 2h):
Gas Par (04h) pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15 | pCO2 48 / SvO2 70%

Exemplo 4 — Art 04h + Ven 10h (diff 6h ≥ 2h → SEPARADAS, mais recente primeiro):
Gas Ven (10h) pH 7,33 / pCO2 42 / HCO3 21 / BE -3,7 / SvO2 70% / Lac 1,5 / AG 12 / Cl 101 / Na 136 / K 4,2 / Cai 1,10
Gas Art (04h) pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15

Exemplo 5 — 3 arteriais em horários diferentes:
Gas Art (16h) pH 7,38 / pCO2 36 / pO2 88 / HCO3 22 / BE -2,0 / SatO2 97% / Lac 1,2 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15
Gas Art (10h) pH 7,32 / pCO2 38 / pO2 82 / HCO3 20 / BE -4,0 / SatO2 95% / Lac 2,1 / AG 12 / Cl 102 / Na 137 / K 4,2 / Cai 1,12
Gas Art (04h) pH 7,30 / pCO2 40 / pO2 80 / HCO3 19 / BE -5,0 / SatO2 94% / Lac 2,8 / AG 14 / Cl 104 / Na 136 / K 4,4 / Cai 1,10

Exemplo 6 — 2 pareadas + 1 arterial isolada (Art 04h+Ven 05h | Art 10h | Art 16h+Ven 17h):
Gas Par (16h) pH 7,38 / pCO2 36 / pO2 88 / HCO3 22 / BE -2,0 / SatO2 97% / Lac 1,2 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15 | pCO2 44 / SvO2 72%
Gas Art (10h) pH 7,32 / pCO2 38 / pO2 82 / HCO3 20 / BE -4,0 / SatO2 95% / Lac 2,1 / AG 12 / Cl 102 / Na 137 / K 4,2 / Cai 1,12
Gas Par (04h) pH 7,30 / pCO2 40 / pO2 80 / HCO3 19 / BE -5,0 / SatO2 94% / Lac 2,8 / AG 14 / Cl 104 / Na 136 / K 4,4 / Cai 1,10 | pCO2 48 / SvO2 68%

Exemplo 7 — 3 pareadas (Art 04h+Ven 04h | Art 10h+Ven 10h | Art 16h+Ven 17h):
Gas Par (16h) pH 7,38 / pCO2 36 / pO2 88 / HCO3 22 / BE -2,0 / SatO2 97% / Lac 1,2 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15 | pCO2 44 / SvO2 72%
Gas Par (10h) pH 7,32 / pCO2 38 / pO2 82 / HCO3 20 / BE -4,0 / SatO2 95% / Lac 2,1 / AG 12 / Cl 102 / Na 137 / K 4,2 / Cai 1,12 | pCO2 46 / SvO2 69%
Gas Par (04h) pH 7,30 / pCO2 40 / pO2 80 / HCO3 19 / BE -5,0 / SatO2 94% / Lac 2,8 / AG 14 / Cl 104 / Na 136 / K 4,4 / Cai 1,10 | pCO2 50 / SvO2 65%

Exemplo 8 — Sem hora no laudo:
Gas Art pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Na 138 / K 4,0 / Cai 1,15

# FORMATO DE RESPOSTA
- Retorne ABSOLUTAMENTE APENAS as linhas formatadas conforme os exemplos acima.
- NUNCA use formatação markdown (como ```).
- Cada entrada em sua própria linha, da mais recente para a mais antiga.
- Se não houver dados de gasometria, retorne VAZIO.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""

_PROMPT_NAO_TRANSCRITOS = """# ATUE COMO
Especialista em auditoria de laudos laboratoriais.

# TAREFA
Leia o texto e identifique o nome de TODOS os exames/testes laboratoriais mencionados.
Em seguida, liste APENAS os exames que NÃO pertencem a nenhuma das categorias abaixo (já cobertas por outros agentes).

# CATEGORIAS JÁ COBERTAS (IGNORE COMPLETAMENTE)
- Hemograma / Hemato: Hb, Ht, VCM, HCM, RDW, Leucócitos (e diferencial: Seg, Bast, Linf, Mon, Eos, Bas), Plaquetas
- Renal / Eletrólitos: Creatinina, Ureia, Sódio, Potássio, Magnésio, Fósforo, Cálcio Total, Cálcio Iônico, CaT, CaI, CaI, Pi, Mg, Na, K, Cr, Ur
- Hepático / Pancreático: TGP, TGO, ALT, AST, FAL, GGT, Bilirrubinas (BT, BD, BI), Proteínas Totais, Albumina, Amilase, Lipase
- Cardio / Coag / Inflamação: CPK, CK-MB, BNP, NT-proBNP, Troponina, PCR, VHS, TP, TAP, RNI, TTPa, TTPA
- Urina (EAS): Urina Tipo I, EAS, Elementos Anormais, Urocultura (apenas a parte do sumário/EAS)
- Gasometria: Gasometria Arterial, Gasometria Venosa, Gasometria Pareada (e todos os seus componentes: pH, pCO2, pO2, HCO3, BE, SatO2, SvO2, Lactato, Anion Gap, Cloreto)

# REGRAS
1. Liste APENAS exames que NÃO estão nas categorias acima.
2. Cada nome deve ser conciso (sem resultados, sem datas, apenas o nome do exame).
3. Separe por " | ".
4. Se não houver nenhum exame fora das categorias acima, retorne exatamente: VAZIO

# EXEMPLOS DE SAÍDA
Exemplo 1 (com exames extras): TSH | T4 Livre | Ferritina | Ferro Sérico | Vancomicina Nível
Exemplo 2 (sem exames extras): VAZIO

# FORMATO DE RESPOSTA
- Apenas a string com os nomes separados por " | " ou "VAZIO". Sem markdown.

# INPUT PARA PROCESSAR:
{{TEXTO_INPUT}}"""


# Ordem fixa dos agentes de exames (mesma do PACER)
_AGENTES_EXAMES_ORDEM = [
    "hematologia_renal",
    "hepatico",
    "coagulacao",
    "urina",
    "gasometria",
    "nao_transcritos",
]
_AGENTES_EXAMES_PROMPTS = {
    "hematologia_renal": _PROMPT_HEMATOLOGIA_RENAL,
    "hepatico":          _PROMPT_HEPATICO,
    "coagulacao":        _PROMPT_COAGULACAO,
    "urina":             _PROMPT_URINA,
    "gasometria":        _PROMPT_GASOMETRIA,
    "nao_transcritos":   _PROMPT_NAO_TRANSCRITOS,
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
# EXPORTS PÚBLICOS — pacer.py importa daqui (fonte única de verdade)
# Devem ficar APÓS todos os _PROMPT_* estarem definidos
# ==============================================================================
PROMPT_AGENTE_IDENTIFICACAO              = _PROMPT_ID_EXAMES
PROMPT_AGENTE_HEMATOLOGIA_RENAL          = _PROMPT_HEMATOLOGIA_RENAL
PROMPT_AGENTE_HEPATICO                   = _PROMPT_HEPATICO
PROMPT_AGENTE_COAGULACAO                 = _PROMPT_COAGULACAO
PROMPT_AGENTE_URINA                      = _PROMPT_URINA
PROMPT_AGENTE_GASOMETRIA                 = _PROMPT_GASOMETRIA
PROMPT_AGENTE_NAO_TRANSCRITOS            = _PROMPT_NAO_TRANSCRITOS
PROMPT_AGENTE_IDENTIFICACAO_PRESCRICAO   = _PROMPT_ID_PRESCRICAO
PROMPT_AGENTE_DIETA                      = _PROMPT_DIETA
PROMPT_AGENTE_MEDICACOES                 = _PROMPT_MEDICACOES


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

    # Passo 2: 6 agentes especializados em paralelo (5 de exames + nao_transcritos)
    resultados_dict: dict[str, str] = {}

    def _worker(agente_id: str):
        prompt = _AGENTES_EXAMES_PROMPTS[agente_id]
        r = _chamar_ia(provider, api_key, modelo, prompt, texto)
        if r and "❌" not in r and "⚠️" not in r:
            r_limpo = r.strip().rstrip(".,:;!? ")
            if r_limpo and r_limpo.upper() != "VAZIO":
                return agente_id, r_limpo
        return agente_id, None

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(_worker, aid): aid for aid in _AGENTES_EXAMES_ORDEM}
        for future in as_completed(futures):
            aid, resultado = future.result(timeout=60)
            if resultado:
                resultados_dict[aid] = resultado

    # Passo 3: montar resultado na ordem fixa do PACER
    # Agrupamento igual ao pacer.py:
    #   Linha data:      hematologia_renal
    #   Linha bioquím:   hepatico + coagulacao (joinados com " | ")
    #   Linha própria:   urina
    #   Linha própria:   gasometria
    #   Linha própria:   Não Transcritos (agente novo)
    _INLINE    = ["hematologia_renal"]
    _BIOQUIM   = ["hepatico", "coagulacao"]
    _SEPARADOS = ["gasometria", "urina"]

    def _ok(v):
        return v and v.strip().rstrip('.,:;!? ').upper() != "VAZIO"

    if not resultados_dict:
        return f"{nome_hc}\n{data_linha} (Nenhum dado laboratorial encontrado)"

    linhas_saida = [nome_hc]

    inline_partes = [resultados_dict[aid] for aid in _INLINE if aid in resultados_dict and _ok(resultados_dict[aid])]
    linhas_saida.append(f"{data_linha} " + " | ".join(inline_partes) if inline_partes else data_linha)

    bioquim_partes = [resultados_dict[aid] for aid in _BIOQUIM if aid in resultados_dict and _ok(resultados_dict[aid])]
    if bioquim_partes:
        linhas_saida.append(" | ".join(bioquim_partes))

    for aid in _SEPARADOS:
        if aid in resultados_dict and _ok(resultados_dict[aid]):
            linhas_saida.append(resultados_dict[aid])

    # Linha de exames não transcritos (sempre por último)
    nao_trans = resultados_dict.get("nao_transcritos", "")
    if _ok(nao_trans):
        linhas_saida.append(f"Não Transcritos: {nao_trans}")

    return "\n".join(linhas_saida)


# ==============================================================================
# rodar_agentes_exame() — expõe os agentes especializados como dict
# Para uso pelo tab_laboratoriais (preenchimento de campos)
# ==============================================================================

def rodar_agentes_exame(texto: str, api_key: str, provider: str, modelo: str) -> dict[str, str]:
    """
    Roda os 6 agentes especializados em paralelo e retorna dict {agente_id: texto}.
    Inclui: hematologia_renal, hepatico, coagulacao, urina, gasometria, nao_transcritos.
    Usado por tab_laboratoriais para preenchimento campo a campo via parse_agentes_para_slot.
    """
    if not texto or not api_key:
        return {}

    resultados: dict[str, str] = {}

    def _worker(agente_id: str):
        prompt = _AGENTES_EXAMES_PROMPTS[agente_id]
        r = _chamar_ia(provider, api_key, modelo, prompt, texto)
        if r and "❌" not in r and "⚠️" not in r:
            r_limpo = r.strip().rstrip(".,:;!? ")
            if r_limpo and r_limpo.upper() != "VAZIO":
                return agente_id, r_limpo
        return agente_id, None

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(_worker, aid): aid for aid in _AGENTES_EXAMES_ORDEM}
        for future in as_completed(futures):
            aid, resultado = future.result(timeout=60)
            if resultado:
                resultados[aid] = resultado

    return resultados


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
