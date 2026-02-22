"""
12 agentes de IA para preencher os campos estruturados de cada seção
a partir do texto já fatiado pelo ia_extrator.
"""
import json
import re
import streamlit as st
from openai import OpenAI
import google.generativeai as genai


def _extrair_json(texto: str) -> dict | None:
    """Extrai JSON de texto que pode conter markdown ou explicações."""
    if not texto or not texto.strip():
        return None
    txt = texto.strip()
    txt = re.sub(r"^```(?:json)?\s*", "", txt)
    txt = re.sub(r"\s*```\s*$", "", txt)
    txt = txt.strip()
    match = re.search(r"\{[\s\S]*\}", txt)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return None


def _chamar_ia(prompt_system: str, texto: str, api_key: str, provider: str, modelo: str) -> dict:
    """Helper: envia texto para a IA e retorna JSON parseado."""
    try:
        if "OpenAI" in provider or "GPT" in provider:
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=modelo if modelo.startswith("gpt") else "gpt-4o",
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user",   "content": f"TEXTO DA SEÇÃO:\n\n{texto}"}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=modelo if modelo.startswith("gemini") else "gemini-2.5-flash",
                system_instruction=prompt_system
            )
            resp = model.generate_content(f"TEXTO DA SEÇÃO:\n\n{texto}")
            txt = (resp.text or "").replace("```json", "").replace("```", "").strip()
            parsed = _extrair_json(txt)
            if parsed is not None:
                return parsed
            return json.loads(txt)
    except json.JSONDecodeError as e:
        return {"_erro": f"JSON inválido: {e}"}
    except Exception as e:
        return {"_erro": str(e)}


# ==============================================================================
# AGENTE 1: IDENTIFICAÇÃO
# ==============================================================================
_PROMPT_IDENTIFICACAO = """Você é um extrator de dados médicos. Leia o texto clínico e preencha os campos de identificação do paciente.
REGRAS:
- Extraia APENAS o que está explicitamente no texto. Dados ausentes = string vazia "".
- sexo: EXATAMENTE "Masculino" ou "Feminino"
- idade: número inteiro (ex: 65), não string
- sofa_adm, sofa_atual: números inteiros
- saps3: string numérica (ex: "55")
- paliativo: true ou false
image.png- Datas: manter formato original do texto (DD/MM/AAAA, MM/AAAA ou MM/AA). Se ausente, ""
- Retorne APENAS JSON válido.

CAMPO ESPECIAL — departamento:
  O texto pode começar com um cabeçalho que indica onde a evolução está sendo escrita.
  Exemplos: "### Sala Vermelha", "### Evolução UTI", "# UTI Adulto", "# Enfermaria",
            "# Pela Clínica Médica", "# Pela Cirurgia", "## PA", "- evolução"
  Se existir, extraia o texto limpo do cabeçalho (sem #, *, - ou espaços extras).
  Exemplo: "### Sala Vermelha ###" → departamento: "Sala Vermelha"
  Se não existir, deixe "".

{
  "departamento": "nome do setor/departamento onde a evolução foi escrita",
  "nome": "Nome completo do paciente",
  "idade": 0,
  "sexo": "Masculino",
  "prontuario": "número do prontuário/HC",
  "leito": "número ou nome do leito",
  "origem": "procedência (PS, UPA, Enfermaria, Transferência, etc.)",
  "equipe": "equipe médica responsável",
  "di_hosp": "data internação hospitalar DD/MM/AAAA",
  "di_uti": "data entrada UTI DD/MM/AAAA",
  "di_enf": "data entrada enfermaria DD/MM/AAAA",
  "saps3": "valor SAPS3",
  "sofa_adm": 0,
  "sofa_atual": 0,
  "mrs": "valor mRS",
  "pps": "valor PPS",
  "cfs": "valor CFS",
  "paliativo": false
}"""

def preencher_identificacao(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_IDENTIFICACAO, texto, api_key, provider, modelo)
    r.pop("_erro", None)
    for k in ["sofa_adm", "sofa_atual"]:
        if k in r:
            try: r[k] = int(r[k]) if r[k] != "" else 0
            except: r[k] = 0
    if "idade" in r:
        try: r["idade"] = int(r["idade"]) if r["idade"] != "" else 0
        except: r["idade"] = 0
    if "paliativo" in r and isinstance(r["paliativo"], str):
        r["paliativo"] = r["paliativo"].lower() in ("true", "sim", "yes", "1")
    return r


# ==============================================================================
# AGENTE 2: HD - DIAGNÓSTICOS ATUAIS E PRÉVIOS
# ==============================================================================
_PROMPT_HD = """Você é um extrator estruturado de dados médicos para prontuário hospitalar.

OBJETIVO
Extrair hipóteses diagnósticas do texto e classificá-las em:
- Diagnósticos Atuais (ativos/em andamento)
- Diagnósticos Resolvidos (encerrados/histórico)

REGRAS GERAIS
- Máximo 4 diagnósticos atuais e 4 resolvidos.
- Ordenação obrigatória:
  - Diagnósticos Atuais: do mais recente para o mais antigo (pela data de início).
  - Diagnósticos Resolvidos: do mais recente para o mais antigo (pela data de resolução; se ausente, usar data de início).
- Se houver mais de 4, priorizar por relevância clínica.
- Dados ausentes = "".
- NÃO inferir informações não explicitamente descritas.
- NÃO criar diagnósticos.
- NÃO preencher campos de conduta.
- Datas: aceitar e manter o formato original do texto (DD/MM/AAAA, MM/AAAA ou MM/AA). Não converter nem completar. Se ausente ou ambígua, "".
- Retornar APENAS JSON válido. Não usar null. Não incluir texto fora do JSON.

PADRONIZAÇÃO OBRIGATÓRIA DO NOME
- Expandir siglas: "IAM" → "Infarto Agudo do Miocardio", "IRA" → "Insuficiencia Renal Aguda"
- Title Case: "INFARTO AGUDO DO MIOCARDIO" → "Infarto Agudo do Miocardio"
- No campo "class" são permitidas siglas formais de estadiamento: "KDIGO 3", "Killip II", "NYHA III"

DEFINIÇÕES
- Diagnóstico Atual: condição ativa, em tratamento, investigação ou evolução clínica.
- Diagnóstico Resolvido: condição descrita como resolvida, tratada, encerrada ou evento passado.

REGRAS DE PREENCHIMENTO
- nome: nome clínico objetivo, sem siglas, sem data, sem classificação, Title Case.
- class: apenas estadiamento ou gravidade formal. Se não houver, "".
- data_inicio: data explícita de início. Manter formato original (DD/MM/AAAA, MM/AAAA ou MM/AA). Se ausente, "".
- data_fim: apenas para resolvidos. Data explícita de resolução. Manter formato original. Se ausente, "".
- observacoes: resumo objetivo da evolução clínica. Não incluir condutas. Texto curto e clínico.

SAÍDA FINAL — somente JSON válido.
Mapeamento: atuais → slots 1-4 (status Atual); resolvidos → slots 5-8 (status Resolvida).
data_fim dos resolvidos → campo Resolvido no formulário.
{
  "diagnosticos_atuais": [
    {"nome": "", "class": "", "data_inicio": "", "observacoes": ""}
  ],
  "diagnosticos_resolvidos": [
    {"nome": "", "class": "", "data_inicio": "", "data_fim": "", "observacoes": ""}
  ]
}"""


def preencher_hd(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_HD, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    resultado = {}

    # Converte array de atuais → hd_1..hd_4 com status Atual
    for i, item in enumerate(r.get("diagnosticos_atuais", [])[:4], 1):
        resultado[f"hd_{i}_nome"] = item.get("nome", "")
        resultado[f"hd_{i}_class"] = item.get("class", "")
        resultado[f"hd_{i}_data_inicio"] = item.get("data_inicio", "")
        resultado[f"hd_{i}_data_resolvido"] = ""
        resultado[f"hd_{i}_status"] = "Atual"
        resultado[f"hd_{i}_obs"] = item.get("observacoes", "")

    # Converte array de resolvidos → hd_5..hd_8 com status Resolvida
    for i, item in enumerate(r.get("diagnosticos_resolvidos", [])[:4], 5):
        resultado[f"hd_{i}_nome"] = item.get("nome", "")
        resultado[f"hd_{i}_class"] = item.get("class", "")
        resultado[f"hd_{i}_data_inicio"] = item.get("data_inicio", "")
        resultado[f"hd_{i}_data_resolvido"] = item.get("data_fim", "")
        resultado[f"hd_{i}_status"] = "Resolvida"
        resultado[f"hd_{i}_obs"] = item.get("observacoes", "")

    return resultado


# ==============================================================================
# AGENTE 3: COMORBIDADES
# ==============================================================================
_PROMPT_COMORBIDADES = """Você é um extrator estruturado de dados médicos para prontuário hospitalar.

OBJETIVO
Extrair exclusivamente comorbidades (doenças pré-existentes ao evento/internação atual) a partir do texto clínico.

DEFINIÇÃO OPERACIONAL
Comorbidade = condição crônica ou antecedente médico prévio já existente antes do quadro atual.
Exemplos válidos: Hipertensão Arterial Sistêmica, Diabetes Mellitus tipo 2, Insuficiência Cardíaca, Doença Pulmonar Obstrutiva Crônica, Neoplasia prévia, Doença Renal Crônica.

NÃO INCLUIR:
- Diagnósticos da internação atual
- Complicações agudas do evento atual
- Sintomas isolados
- Procedimentos
- Condutas
- Fatores de risco isolados sem diagnóstico formal

REGRAS GERAIS
- Máximo 10 comorbidades.
- Ordenar da mais relevante clinicamente para a menos relevante.
- Se houver mais de 10, priorizar por impacto prognóstico.
- Dados ausentes = "".
- NÃO inferir informações não explicitamente descritas.
- NÃO criar comorbidades.
- NÃO preencher campos de conduta.
- NÃO utilizar null.
- Retornar APENAS JSON válido. Não incluir texto fora do JSON.

PADRONIZAÇÃO OBRIGATÓRIA DO CAMPO "nome"
- Expandir todas as siglas: "HAS" → "Hipertensão Arterial Sistêmica", "DM2" → "Diabetes Mellitus tipo 2", "DPOC" → "Doença Pulmonar Obstrutiva Crônica", "IRC" → "Doença Renal Crônica"
- NÃO permitir siglas no campo "nome".
- NÃO incluir classificação no campo "nome".
- NÃO incluir datas.
- Title Case obrigatório: "HIPERTENSÃO ARTERIAL SISTÊMICA" → "Hipertensão Arterial Sistêmica"

PADRONIZAÇÃO DO CAMPO "class"
- Pode conter estadiamento, gravidade ou controle (NYHA III, Child-Pugh B, CKD G4, GOLD 3).
- Se não houver classificação explícita no texto, preencher "".
- Não repetir o nome da doença nesse campo.

REGRAS DE EXCLUSÃO
- Se houver dúvida entre diagnóstico atual e comorbidade, considerar como comorbidade apenas se explicitamente descrito como antecedente ou condição prévia.
- Não considerar "história familiar" como comorbidade.
- Não considerar tabagismo isolado como comorbidade (a menos que descrito como doença associada, ex: DPOC).

VALIDAÇÕES INTERNAS — confirmar antes de retornar:
- Sem siglas no campo "nome".
- Sem campos adicionais.
- No máximo 10 itens.
- Sem texto fora do JSON.

SAÍDA FINAL — somente JSON válido:
{
  "comorbidades": [
    {"nome": "", "class": ""}
  ]
}"""


def preencher_comorbidades(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_COMORBIDADES, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    resultado = {}
    for i, item in enumerate(r.get("comorbidades", [])[:10], 1):
        resultado[f"cmd_{i}_nome"]  = item.get("nome", "")
        resultado[f"cmd_{i}_class"] = item.get("class", "")
    return resultado


# ==============================================================================
# AGENTE 4: MUC - MEDICAÇÕES DE USO CONTÍNUO
# ==============================================================================
_PROMPT_MUC = """Você é um extrator estruturado de dados médicos para prontuário hospitalar.

OBJETIVO
Extrair exclusivamente medicações de uso contínuo domiciliar (em uso antes da internação atual).

DEFINIÇÃO OPERACIONAL
Medicação de uso contínuo = medicamento utilizado cronicamente pelo paciente antes do evento/internação atual.

NÃO INCLUIR:
- Medicamentos iniciados durante a internação atual
- Antibióticos hospitalares
- Drogas vasoativas
- Sedativos hospitalares
- Profilaxias da internação
- Condutas

LIMITE
- Máximo 20 medicações. Se houver mais de 20, priorizar por relevância clínica.

ORDENAÇÃO
- Da mais relevante clinicamente para a menos relevante.

────────────────────────
DETERMINAÇÃO OBRIGATÓRIA DE ADESÃO (ETAPA 1 — ANTES DA EXTRAÇÃO FINAL)

Analisar todo o texto e classificar adesão global pela regra hierárquica:

Se QUALQUER medicamento for descrito como uso irregular, esquecimento, baixa adesão, uso intermitente ou abandono parcial:
  adesao_global = "Uso Irregular"

Se NÃO houver qualquer irregularidade e houver descrição explícita de uso correto/regular:
  adesao_global = "Uso Regular"

Se houver incerteza explícita no texto:
  adesao_global = "Desconhecido"

Se não houver qualquer menção sobre adesão:
  adesao_global = ""

Importante: se UMA medicação for irregular, TODAS = "Uso Irregular".

────────────────────────
REGRAS GERAIS DE EXTRAÇÃO
- Não inferir medicamentos não descritos.
- Não duplicar fármacos.
- Não separar o mesmo medicamento em duas entradas, salvo esquemas distintos explicitamente descritos.
- Dados ausentes = "". Não utilizar null. Não retornar texto fora do JSON.

CAMPO "nome": nome genérico (DCI), Title Case, sem siglas, sem dose, sem frequência.
  Exemplo: "AAS" → "Acido Acetilsalicilico"

CAMPO "dose": apenas valor + unidade. Exemplos: "20mg", "850mg", "10UI". Se ausente, "".

CAMPO "freq": formato padronizado. Se o texto usar notação 1-0-0 (manhã-tarde-noite), converter:
  - 1-0-0, 0-1-0 ou 0-0-1 (um "1") → "1x ao dia"
  - 0-1-1, 1-0-1 ou 1-1-0 (dois "1"s) → "a cada 12 horas" ou "12/12h"
  - 1-1-1 (três "1"s) → "a cada 8 horas" ou "8/8h"
  Outros formatos: "1x/dia", "2x/dia", "ao deitar", "pela manha". Se ausente, "". Não inferir.

────────────────────────
VALIDAÇÕES FINAIS (CHECAR ANTES DE RETORNAR)
- Máximo 20 medicamentos.
- Nenhum medicamento da internação incluído.
- Nome não contém dose ou frequência.
- Sem null, sem campos extras, sem texto fora do JSON.

────────────────────────
SAÍDA FINAL — somente JSON válido:
{
  "adesao_global": "",
  "medicacoes": [
    {"nome": "", "dose": "", "freq": ""}
  ]
}"""


def preencher_muc(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_MUC, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    resultado = {}

    adesao = r.get("adesao_global", "")
    if adesao in ("Uso Regular", "Uso Irregular", "Desconhecido"):
        resultado["muc_adesao_global"] = adesao

    for i, item in enumerate(r.get("medicacoes", [])[:20], 1):
        resultado[f"muc_{i}_nome"] = item.get("nome", "")
        resultado[f"muc_{i}_dose"] = item.get("dose", "")
        resultado[f"muc_{i}_freq"] = item.get("freq", "")

    return resultado


# ==============================================================================
# AGENTE 5: HMPA — reescreve a HMA/HMP mantendo fidelidade absoluta
# ==============================================================================
_PROMPT_HMPA = """Você é um Especialista em Redação Médica e Comunicação Clínica de Alta Complexidade.

Sua tarefa é reescrever a História da Moléstia Atual (HMA) e História Patológica Pregressa (HMP) fornecidas, otimizando clareza, organização lógica e precisão técnica para leitura por outro médico intensivista.

════════════════════════════
REGRAS ABSOLUTAS (INVIOLÁVEIS)

FIDELIDADE INTEGRAL
- É terminantemente proibido adicionar, inferir, interpretar ou omitir qualquer dado factual.
- Não completar lacunas.
- Não reorganizar eventos de forma que altere significado clínico.
- Se o texto estiver ambíguo, manter a ambiguidade.

PROIBIÇÃO DE ALUCINAÇÃO
- Não introduzir hipóteses diagnósticas.
- Não introduzir exames ou condutas não descritas.
- Não melhorar o raciocínio clínico, apenas a redação.

INTEGRIDADE DO CONTEÚDO
- Todos os dados presentes devem permanecer na versão final.
- Nenhuma informação pode ser removida.

════════════════════════════
OBJETIVOS DA REESCRITA

ORGANIZAÇÃO CRONOLÓGICA
Sempre que possível, organizar na seguinte sequência lógica:
1. Antecedentes relevantes
2. Início dos sintomas
3. Evolução temporal
4. Atendimentos prévios
5. Admissão atual
6. Evolução até o momento descrito

Se a cronologia não estiver clara, reorganizar apenas com base nas informações explicitamente fornecidas.

MELHORIA DE CLAREZA
- Corrigir erros gramaticais e ortográficos.
- Corrigir concordância verbal e nominal.
- Transformar frases telegráficas em períodos médicos claros e objetivos.
- Eliminar repetições desnecessárias mantendo todo o conteúdo factual.

DENSIDADE INFORMATIVA
- Agrupar informações correlatas no mesmo parágrafo.
- Evitar fragmentação excessiva.
- Manter linguagem técnica adequada ao ambiente de terapia intensiva.

════════════════════════════
PADRONIZAÇÃO LINGUÍSTICA
- Utilizar português formal técnico.
- Manter terminologia médica adequada para comunicação médico-médico.
- Evitar siglas médicas incomuns ou regionais.
- Manter siglas amplamente reconhecidas (ex: UTI, IAM, AVC, PCR, DPOC, HAS).
- Corrigir erros grosseiros: "PACIEWNTE COMPARECEU A UPA." → "Paciente compareceu à UPA."

════════════════════════════
FORMATO DE SAÍDA
- Retornar apenas o texto reescrito.
- Não incluir comentários, explicações ou títulos adicionais.
- Texto contínuo, pronto para colar no prontuário."""

def preencher_hmpa(texto, api_key, provider, modelo):
    if not texto or not texto.strip():
        return {}

    try:
        if "OpenAI" in provider or "GPT" in provider:
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=modelo if modelo.startswith("gpt") else "gpt-4o",
                messages=[
                    {"role": "system", "content": _PROMPT_HMPA},
                    {"role": "user",   "content": f"Texto Original:\n\n{texto}"}
                ]
            )
            reescrito = resp.choices[0].message.content.strip()
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=modelo if modelo.startswith("gemini") else "gemini-2.5-flash",
                system_instruction=_PROMPT_HMPA
            )
            resp = model.generate_content(f"Texto Original:\n\n{texto}")
            reescrito = resp.text.strip()

        return {"hmpa_reescrito": reescrito}

    except Exception as e:
        return {"_erro": str(e)}


# ==============================================================================
# AGENTE 6: DISPOSITIVOS INVASIVOS
# ==============================================================================
_PROMPT_DISPOSITIVOS = """Você é um extrator estruturado de dados médicos para prontuário hospitalar.

OBJETIVO
Extrair dispositivos invasivos mencionados no texto clínico.

DEFINIÇÃO OPERACIONAL
Dispositivo invasivo = qualquer dispositivo inserido no paciente com permanência para monitorização, terapia ou suporte.
Exemplos válidos: CVC, PICC, TOT, TQT, SVD, SNE, SNG, PAM, PIC, Cateter Arterial, Cateter de Hemodiálise, Dreno Torácico.

NÃO INCLUIR:
- Oxigênio por cateter nasal, Máscara de Venturi, VNI
- Dispositivos externos ou procedimentos sem permanência
- Condutas

REGRAS GERAIS
- Máximo 8 dispositivos. Se houver mais, priorizar ativos.
- Não duplicar. Não criar dispositivos não mencionados.
- Dados ausentes = "". Não utilizar null.
- NÃO preencher conduta.
- Retornar APENAS JSON válido. Sem texto fora do JSON.

CAMPOS DE CADA DISPOSITIVO
- nome: sigla padronizada (CVC, TOT, SVD). Sem local, calibre ou data.
- local: local anatômico (ex: "Jugular Direita", "Vesical"). Se não mencionado, "".
- data_insercao: manter formato original (DD/MM/AAAA, MM/AAAA ou MM/AA). Se ausente, "".
- data_retirada: apenas se houver retirada explícita. Manter formato original. Se ainda presente, "".
- status: EXATAMENTE "Ativo" (presente/em uso) ou "Removido" (retirado explicitamente). Nunca vazio.

ORDENAÇÃO
- Slots 1-8: primeiro "Ativo" (do mais recente ao mais antigo), depois "Removido".

SAÍDA FINAL — somente JSON válido:
{
  "dispositivos": [
    {"nome": "", "local": "", "data_insercao": "", "data_retirada": "", "status": "Ativo"}
  ]
}"""


def preencher_dispositivos(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_DISPOSITIVOS, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    resultado = {}
    for i, item in enumerate(r.get("dispositivos", [])[:8], 1):
        resultado[f"disp_{i}_nome"]           = item.get("nome", "")
        resultado[f"disp_{i}_local"]          = item.get("local", "")
        resultado[f"disp_{i}_data_insercao"]  = item.get("data_insercao", "")
        resultado[f"disp_{i}_data_retirada"]  = item.get("data_retirada", "")
        resultado[f"disp_{i}_status"]         = item.get("status", "Ativo")
    return resultado


# ==============================================================================
# AGENTE 7: CULTURAS
# ==============================================================================
_PROMPT_CULTURAS = """Você é um extrator estruturado de dados médicos para prontuário hospitalar.

OBJETIVO
Extrair culturas microbiológicas mencionadas no texto clínico e preencher exatamente os campos definidos abaixo.

DEFINIÇÃO OPERACIONAL
Cultura microbiológica = qualquer exame microbiológico coletado para identificação de micro-organismos.
Exemplos válidos: Hemocultura, Urocultura, Aspirado Traqueal, Swab Retal, Lavado Broncoalveolar, Cultura de Ponta de Cateter, Dreno, Líquor.

NÃO INCLUIR:
- PCR viral isolada, sorologias, exames moleculares isolados sem cultura, condutas.

REGRAS GERAIS
- Máximo 8 culturas. Se houver mais de 8, priorizar culturas positivas.
- Dados ausentes = "". Não utilizar null.
- NÃO preencher conduta. Não retornar campo check.
- Retornar APENAS JSON válido. Sem texto fora do JSON.

STATUS — EXATAMENTE UMA DAS OPÇÕES:
- "Positivo com Antibiograma" → crescimento + perfil de sensibilidade disponível
- "Positivo aguarda isolamento" → crescimento identificado, antibiograma pendente
- "Pendente negativo" → resultado parcial, pendente ou parcialmente negativo
- "Negativo" → resultado final negativo confirmado
Nunca usar variações.

PREENCHIMENTO DOS CAMPOS
- cult_{i}_sitio: nome do sítio em Title Case. Sem datas.
- cult_{i}_data_coleta: manter formato original (DD/MM/AAAA, MM/AAAA ou MM/AA). Se ausente, "".
- cult_{i}_data_resultado: apenas se explicitamente descrito. Manter formato original. Se ausente, "".
- cult_{i}_status: EXATAMENTE uma das 4 opções.
- cult_{i}_micro: micro-organismo isolado. Se negativo ou pendente, "". Não incluir sensibilidade.
- cult_{i}_sensib: perfil de sensibilidade (ex: "Sensível a Polimixina B"). Se aguarda ou negativo, "".
- cult_{i}_conduta: sempre "". Nunca preencher.

ORDENAÇÃO (slots 1 a 8):
1. Positivo com Antibiograma (mais recente primeiro pela data_resultado)
2. Positivo aguarda isolamento (mais recente primeiro)
3. Pendente negativo (mais recente primeiro pela data_coleta)
4. Negativo (mais recente primeiro pela data_resultado)
Se datas ausentes, manter ordem de aparecimento no texto.

CAMPO AUXILIAR
culturas_notas: resumo objetivo do contexto microbiológico. Sem interpretação clínica. Sem conduta.
cult_ordem: lista numérica correspondente à ordem final preenchida (ex: [1,2,3,4]).

VALIDAÇÕES INTERNAS (CHECAR ANTES DE RETORNAR):
- Máximo 8 culturas. Status apenas uma das 4 opções. Sem null. Sem campos extras. Sem texto fora do JSON.

SAÍDA FINAL — somente JSON válido:
{
  "culturas": [
    {
      "cult_1_sitio": "", "cult_1_data_coleta": "", "cult_1_data_resultado": "",
      "cult_1_status": "", "cult_1_micro": "", "cult_1_sensib": "", "cult_1_conduta": ""
    }
  ],
  "culturas_notas": "",
  "cult_ordem": []
}"""


_STATUS_CULTURAS = {
    "Positivo com Antibiograma",
    "Positivo aguarda isolamento",
    "Pendente negativo",
    "Negativo",
}


def preencher_culturas(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_CULTURAS, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    resultado = {}
    for i, item in enumerate(r.get("culturas", [])[:8], 1):
        def _v(campo, _i=i, _item=item):
            return _item.get(f"cult_{_i}_{campo}") or _item.get(campo) or ""

        status = _v("status")
        resultado[f"cult_{i}_sitio"]          = _v("sitio")
        resultado[f"cult_{i}_data_coleta"]    = _v("data_coleta")
        resultado[f"cult_{i}_data_resultado"] = _v("data_resultado")
        resultado[f"cult_{i}_status"]         = status if status in _STATUS_CULTURAS else None
        resultado[f"cult_{i}_micro"]          = _v("micro")
        resultado[f"cult_{i}_sensib"]         = _v("sensib")

    return resultado


# ==============================================================================
# AGENTE 8: ANTIBIÓTICOS
# ==============================================================================
_PROMPT_ANTIBIOTICOS = """Você é um extrator estruturado de dados médicos para prontuário hospitalar.

OBJETIVO
Extrair antibióticos/antimicrobianos mencionados no texto clínico e preencher exatamente os campos definidos abaixo.

════════════════════════════
DEFINIÇÃO OPERACIONAL

Antibiótico = qualquer agente antimicrobiano prescrito para tratamento de infecção ativa.

Inclui:
- Antibacterianos
- Antifúngicos sistêmicos
- Antivirais terapêuticos
- Antiparasitários de uso hospitalar

NÃO INCLUIR:
- Profilaxia isolada (ex: dose única pré-operatória)
- Antissépticos
- Vitaminas ou suplementos
- Condutas
- Ajustes de dose isolados

════════════════════════════
CLASSIFICAÇÃO OBRIGATÓRIA

Antibióticos Atuais → array "atb_atuais"
→ Em uso no momento descrito no texto
→ Sem data de término real documentada
Se descrito como "mantido", "em uso", "segue" → Atual

Antibióticos Prévios → array "atb_previos"
→ Já suspensos
→ Com data de término real ou suspensão explícita
Se descrito como "suspenso", "finalizado", "encerrado" → Prévio

════════════════════════════
REGRAS GERAIS

- Máximo 5 atuais + 5 prévios.
- Dados ausentes → "". Não utilizar null.
- NÃO preencher conduta. Nunca.
- Retornar APENAS JSON válido. Sem texto fora do JSON.
- Datas: manter exatamente o formato descrito no texto (DD/MM/AAAA, MM/AAAA ou MM/AA).

════════════════════════════
CAMPO "tipo" — EXATAMENTE uma das opções ou "":

"Empírico" → iniciado sem cultura positiva ou antes do resultado microbiológico.
"Guiado por Cultura" → iniciado ou ajustado com base em cultura, antibiograma ou agente identificado.
Se não houver informação explícita → "".
Nunca usar variações.

════════════════════════════
PADRONIZAÇÃO DO NOME

- Utilizar DCI (Denominação Comum Internacional).
- Converter nome comercial para genérico.
- Title Case obrigatório.
- Não incluir dose nem frequência.
- Manter hífen quando fizer parte do nome oficial (ex: Piperacilina-Tazobactam).

════════════════════════════
PREENCHIMENTO DOS CAMPOS

ATUAIS
atb_curr_{i}_nome: DCI, Title Case, sem dose/frequência.
atb_curr_{i}_foco: foco infeccioso alvo, Title Case. Ex: "PAV", "ITU", "Bacteremia", "Abdome". Se ausente → "".
atb_curr_{i}_tipo: "Empírico", "Guiado por Cultura" ou "".
atb_curr_{i}_data_ini: data de início, manter formato original. Se ausente → "".
atb_curr_{i}_data_fim: término previsto, apenas se explicitamente descrito. Se ausente → "".
atb_curr_{i}_conduta: sempre "". Nunca preencher.

PRÉVIOS
atb_prev_{i}_nome: DCI, Title Case, sem dose/frequência.
atb_prev_{i}_foco: foco infeccioso, Title Case. Se ausente → "".
atb_prev_{i}_tipo: "Empírico", "Guiado por Cultura" ou "".
atb_prev_{i}_data_ini: manter formato original. Se ausente → "".
atb_prev_{i}_data_fim: data real de término, manter formato original. Se suspensão sem data → "".
atb_prev_{i}_obs: motivo da suspensão ou resposta ao tratamento. Frase objetiva e curta. Sem conduta. Se ausente → "".
atb_prev_{i}_conduta: sempre "". Nunca preencher.

════════════════════════════
ORDENAÇÃO

Atuais (slots 1→5): mais recente primeiro pela data_ini. Se ausente, manter ordem do texto.
Prévios (slots 1→5): mais recente primeiro pela data_fim. Se ausente, manter ordem do texto.

atb_curr_ordem: lista numérica da ordem final dos atuais. Ex: [1,2,3]
atb_prev_ordem: lista numérica da ordem final dos prévios. Ex: [1,2,3]

════════════════════════════
CAMPO AUXILIAR

antibioticos_notas: resumo objetivo do contexto antimicrobiano. Sem conduta. Sem opinião clínica.

════════════════════════════
VALIDAÇÕES INTERNAS (CHECAR ANTES DE RETORNAR)

- Máximo 5 atuais e 5 prévios.
- tipo apenas "Empírico", "Guiado por Cultura" ou "".
- conduta sempre "".
- Nenhum null. Nenhum campo extra. Nenhum texto fora do JSON.
- Nome não contém dose ou frequência.

════════════════════════════
ESTRUTURA DE SAÍDA (IMUTÁVEL)

{
  "atb_atuais": [
    {
      "atb_curr_1_nome": "", "atb_curr_1_foco": "", "atb_curr_1_tipo": "",
      "atb_curr_1_data_ini": "", "atb_curr_1_data_fim": "", "atb_curr_1_conduta": ""
    }
  ],
  "atb_previos": [
    {
      "atb_prev_1_nome": "", "atb_prev_1_foco": "", "atb_prev_1_tipo": "",
      "atb_prev_1_data_ini": "", "atb_prev_1_data_fim": "",
      "atb_prev_1_obs": "", "atb_prev_1_conduta": ""
    }
  ],
  "antibioticos_notas": "",
  "atb_curr_ordem": [],
  "atb_prev_ordem": []
}

════════════════════════════
SAÍDA FINAL
Somente JSON válido conforme estrutura acima."""


_TIPO_ATB = {"Empírico", "Guiado por Cultura"}


def preencher_antibioticos(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_ANTIBIOTICOS, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    resultado = {}

    for i, item in enumerate(r.get("atb_atuais", [])[:5], 1):
        def _vc(campo, _i=i, _item=item):
            return _item.get(f"atb_curr_{_i}_{campo}") or _item.get(campo) or ""
        tipo = _vc("tipo")
        resultado[f"atb_curr_{i}_nome"]     = _vc("nome")
        resultado[f"atb_curr_{i}_foco"]     = _vc("foco")
        resultado[f"atb_curr_{i}_tipo"]     = tipo if tipo in _TIPO_ATB else None
        resultado[f"atb_curr_{i}_data_ini"] = _vc("data_ini")
        resultado[f"atb_curr_{i}_data_fim"] = _vc("data_fim")

    for i, item in enumerate(r.get("atb_previos", [])[:5], 1):
        def _vp(campo, _i=i, _item=item):
            return _item.get(f"atb_prev_{_i}_{campo}") or _item.get(campo) or ""
        tipo = _vp("tipo")
        resultado[f"atb_prev_{i}_nome"]     = _vp("nome")
        resultado[f"atb_prev_{i}_foco"]     = _vp("foco")
        resultado[f"atb_prev_{i}_tipo"]     = tipo if tipo in _TIPO_ATB else None
        resultado[f"atb_prev_{i}_data_ini"] = _vp("data_ini")
        resultado[f"atb_prev_{i}_data_fim"] = _vp("data_fim")
        resultado[f"atb_prev_{i}_obs"]      = _vp("obs")

    return resultado


# ==============================================================================
# AGENTE 9: COMPLEMENTARES
# ==============================================================================
_PROMPT_COMPLEMENTARES = """Você é um extrator estruturado de dados médicos para prontuário hospitalar.

OBJETIVO
Extrair laudos de exames complementares mencionados no texto clínico e preencher exatamente os campos definidos abaixo.

════════════════════════════
DEFINIÇÃO OPERACIONAL

Exame complementar = exame não laboratorial que possua laudo interpretativo formal.

Inclui:
- Imagem: TC, RX, RNM, USG, PET-CT
- Cardiológicos: Ecocardiograma, ECG, Holter, MAPA
- Funcionais: Espirometria, Polissonografia
- Anatomopatológicos: Biópsia, Citologia
- Pareceres formais de especialidades com conclusão técnica

NÃO INCLUIR:
- Exames laboratoriais (hemograma, PCR, eletrólitos, gasometria etc.)
- Culturas microbiológicas (seção própria)
- Procedimentos sem laudo interpretativo
- Resultados mencionados sem descrição de achados
- Condutas

════════════════════════════
REGRAS GERAIS

- Máximo 8 exames. Se houver mais de 8, priorizar os mais recentes.
- Priorizar exames com laudo completo.
- Dados ausentes → "". Não utilizar null.
- NÃO preencher conduta.
- Retornar APENAS JSON válido. Sem texto fora do JSON.

════════════════════════════
CAMPOS POR EXAME (comp_1 a comp_8)

comp_{i}_exame → Nome completo do exame, nomenclatura técnica, Title Case.
  Exemplos: "Tomografia Computadorizada de Crânio Sem Contraste", "Ecocardiograma Transtorácico", "RX de Tórax", "Ultrassom de Rins e Vias Urinárias"

comp_{i}_data → Data do exame no formato DD/MM/AAAA. Manter exatamente como no texto. "" se ausente.

comp_{i}_laudo → Achados do laudo. Transcrever de forma objetiva. Manter apenas os achados descritos no texto.
  Não resumir excessivamente. Não interpretar. Não acrescentar conclusão própria. Não incluir conduta.

comp_{i}_conduta: sempre "". Nunca preencher. Nunca inferir.

════════════════════════════
ORDENAÇÃO

- Mais recente primeiro pela data do exame.
- Se datas ausentes, manter ordem de aparecimento no texto.

comp_ordem: lista numérica da ordem final. Ex: [1,2,3,4]

════════════════════════════
CAMPO AUXILIAR

complementares_notas: resumo objetivo dos principais achados descritos. Sem interpretação clínica. Sem conduta.

════════════════════════════
VALIDAÇÕES INTERNAS (CHECAR ANTES DE RETORNAR)

- Máximo 8 exames.
- Nenhum exame laboratorial incluído.
- conduta sempre "".
- Nenhum null. Nenhum campo extra. Nenhum texto fora do JSON.
- Cada exame com comp_{i}_exame, comp_{i}_data e comp_{i}_laudo separados. Sem duplicações.

════════════════════════════
ESTRUTURA DE SAÍDA (IMUTÁVEL)

{
  "complementares": [
    { "comp_1_exame": "", "comp_1_data": "", "comp_1_laudo": "", "comp_1_conduta": "" }
  ],
  "complementares_notas": "",
  "comp_ordem": []
}

════════════════════════════
SAÍDA FINAL
Somente JSON válido conforme estrutura acima."""


def preencher_complementares(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_COMPLEMENTARES, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r

    resultado = {}
    for i, item in enumerate(r.get("complementares", [])[:8], 1):
        def _v(campo, _i=i, _item=item):
            return _item.get(f"comp_{_i}_{campo}") or _item.get(campo) or ""
        resultado[f"comp_{i}_exame"] = _v("exame")
        resultado[f"comp_{i}_data"] = _v("data")
        resultado[f"comp_{i}_laudo"] = _v("laudo")

    return resultado


# ==============================================================================
# AGENTE 10: LABORATORIAIS
# ==============================================================================
_PROMPT_LABORATORIAIS = """Você é um extrator estruturado de dados médicos para prontuário hospitalar.

OBJETIVO
Extrair valores laboratoriais do texto clínico e preencher exclusivamente:
- lab_1 → conjunto mais recente
- lab_2 → conjunto imediatamente anterior (se disponível)
Não preencher lab_3 a lab_10.

════════════════════════════
REGRAS GERAIS

- lab_1 = exames mais recentes pela data. lab_2 = imediatamente anteriores.
- Se apenas um conjunto disponível → preencher apenas lab_1.
- Todos os valores como strings. Dados ausentes → "". Não utilizar null.
- NÃO preencher conduta.
- Retornar APENAS JSON válido. Sem texto fora do JSON.
- Manter formato original das datas (DD/MM/AAAA ou DD/MM).
- Não interpretar valores. Não calcular médias. Não inferir unidades.
- Não reorganizar valores entre datas.

════════════════════════════
DETERMINAÇÃO DE CONJUNTO

Um conjunto laboratorial é definido por:
- Uma data explícita, OU
- Um bloco claramente separado no texto

Se múltiplos blocos na mesma data → considerar um único conjunto.

════════════════════════════
REGRAS DE MAPEAMENTO E NORMALIZAÇÃO

HEMOGRAMA
Hb → lab_{i}_hb | Ht → lab_{i}_ht | VCM → lab_{i}_vcm | HCM → lab_{i}_hcm | RDW → lab_{i}_rdw
Leuco → lab_{i}_leuco (incluir diferencial completo se presente. Ex: "12500 (Seg 75% / Linf 15% / Mon 8% / Eos 2%)")
Plaq → lab_{i}_plaq

RENAL / ELETRÓLITOS
Cr → lab_{i}_cr | Ur → lab_{i}_ur | Na → lab_{i}_na | K → lab_{i}_k
Mg → lab_{i}_mg | Pi → lab_{i}_pi
CaT (cálcio total) → lab_{i}_cat | CaI (cálcio iônico sérico) → lab_{i}_cai
⚠ Não confundir CaT com CaI. São campos distintos.

HEPÁTICO / PANCREÁTICO
TGO → lab_{i}_tgo | TGP → lab_{i}_tgp | FAL → lab_{i}_fal | GGT → lab_{i}_ggt
BT → lab_{i}_bt | Alb → lab_{i}_alb | Amil → lab_{i}_amil | Lipas → lab_{i}_lipas

CARDIO / COAG / INFLAMAÇÃO
CPK → lab_{i}_cpk | CPK-MB → lab_{i}_cpk_mb | BNP/NT-proBNP → lab_{i}_bnp
Trop → lab_{i}_trop | PCR → lab_{i}_pcr | VHS → lab_{i}_vhs
TP → lab_{i}_tp (incluir atividade, RNI e tempo integralmente como string. Ex: "Ativ 60% (RNI 1,5 / T 17,0s)")
TTPa → lab_{i}_ttpa (incluir relação se disponível. Ex: "42,0s (rel 1,3)")

GASOMETRIA
Se descrito como "Gas Art" → lab_{i}_gas_tipo = "Arterial"
Se descrito como "Gas Ven" isolada → lab_{i}_gas_tipo = "Venosa"

⚠ Se houver gasometria ARTERIAL e VENOSA na mesma data:
  - lab_{i}_gas_tipo = "Arterial"
  - Preencher todos os campos arteriais normalmente
  - pCO2 venosa → lab_{i}_gasv_pco2
  - SvO2 → lab_{i}_svo2
  - NÃO duplicar lactato: preencher apenas lab_{i}_gas_lac (da arterial)

Mapeamento:
pH → gas_ph | pCO2 → gas_pco2 | pO2 → gas_po2
Bic/HCO3 → gas_hco3 | BE → gas_be | SatO2 → gas_sat
Lac → gas_lac | AG → gas_ag | Cl → gas_cl
Na (da gaso) → gas_na | K (da gaso) → gas_k | CaI (da gaso) → gas_cai

PERFUSÃO
pCO2 venosa → lab_{i}_gasv_pco2
SvO2 → lab_{i}_svo2

URINA (EAS)
Den → ur_dens | Leu Est → ur_le | Nit → ur_nit
Leuco → ur_leu | Hm → ur_hm | Prot → ur_prot | Cet → ur_cet | Glic → ur_glic

OUTROS
Qualquer valor não contemplado nos campos acima → concatenar em lab_{i}_outros
Formato: "Nome Valor | Nome Valor"
Ex: "PTH 100 | TSH 4,0 | T4L 1,0"
Não repetir exames já mapeados em campos próprios.

CONDUTA
lab_{i}_conduta: sempre "". Nunca preencher.

════════════════════════════
VALIDAÇÕES INTERNAS (OBRIGATÓRIO CHECAR)

- gas_tipo apenas "Arterial", "Venosa" ou "".
- conduta sempre "". Nenhum null. Nenhum campo extra.
- Valores numéricos como strings.
- Não misturar valores entre datas.
- CaT ≠ CaI: verificar se foram mapeados nos campos corretos.
- Lactato: não duplicar entre gas_lac e outros.
- Diferencial leucocitário: incluir no campo leuco, não em outros.

════════════════════════════
ESTRUTURA DE SAÍDA (IMUTÁVEL)

{
  "lab_1_data": "",
  "lab_1_hb": "", "lab_1_ht": "", "lab_1_vcm": "", "lab_1_hcm": "", "lab_1_rdw": "", "lab_1_leuco": "", "lab_1_plaq": "",
  "lab_1_cr": "", "lab_1_ur": "", "lab_1_na": "", "lab_1_k": "", "lab_1_mg": "", "lab_1_pi": "", "lab_1_cat": "", "lab_1_cai": "",
  "lab_1_tgp": "", "lab_1_tgo": "", "lab_1_fal": "", "lab_1_ggt": "", "lab_1_bt": "", "lab_1_alb": "", "lab_1_amil": "", "lab_1_lipas": "",
  "lab_1_cpk": "", "lab_1_cpk_mb": "", "lab_1_bnp": "", "lab_1_trop": "", "lab_1_pcr": "", "lab_1_vhs": "", "lab_1_tp": "", "lab_1_ttpa": "",
  "lab_1_gas_tipo": "", "lab_1_gas_ph": "", "lab_1_gas_pco2": "", "lab_1_gas_po2": "", "lab_1_gas_hco3": "",
  "lab_1_gas_be": "", "lab_1_gas_sat": "", "lab_1_gas_lac": "", "lab_1_gas_ag": "",
  "lab_1_gas_cl": "", "lab_1_gas_na": "", "lab_1_gas_k": "", "lab_1_gas_cai": "",
  "lab_1_gasv_pco2": "", "lab_1_svo2": "",
  "lab_1_ur_dens": "", "lab_1_ur_le": "", "lab_1_ur_nit": "", "lab_1_ur_leu": "",
  "lab_1_ur_hm": "", "lab_1_ur_prot": "", "lab_1_ur_cet": "", "lab_1_ur_glic": "",
  "lab_1_outros": "",
  "lab_2_data": "", "lab_2_hb": "", "lab_2_ht": "", "lab_2_vcm": "", "lab_2_hcm": "", "lab_2_rdw": "", "lab_2_leuco": "", "lab_2_plaq": "",
  "lab_2_cr": "", "lab_2_ur": "", "lab_2_na": "", "lab_2_k": "", "lab_2_mg": "", "lab_2_pi": "", "lab_2_cat": "", "lab_2_cai": "",
  "lab_2_tgp": "", "lab_2_tgo": "", "lab_2_fal": "", "lab_2_ggt": "", "lab_2_bt": "", "lab_2_alb": "", "lab_2_amil": "", "lab_2_lipas": "",
  "lab_2_cpk": "", "lab_2_cpk_mb": "", "lab_2_bnp": "", "lab_2_trop": "", "lab_2_pcr": "", "lab_2_vhs": "", "lab_2_tp": "", "lab_2_ttpa": "",
  "lab_2_gas_tipo": "", "lab_2_gas_ph": "", "lab_2_gas_pco2": "", "lab_2_gas_po2": "", "lab_2_gas_hco3": "",
  "lab_2_gas_be": "", "lab_2_gas_sat": "", "lab_2_gas_lac": "", "lab_2_gas_ag": "",
  "lab_2_gas_cl": "", "lab_2_gas_na": "", "lab_2_gas_k": "", "lab_2_gas_cai": "",
  "lab_2_gasv_pco2": "", "lab_2_svo2": "",
  "lab_2_ur_dens": "", "lab_2_ur_le": "", "lab_2_ur_nit": "", "lab_2_ur_leu": "",
  "lab_2_ur_hm": "", "lab_2_ur_prot": "", "lab_2_ur_cet": "", "lab_2_ur_glic": "",
  "lab_2_outros": ""
}

════════════════════════════
SAÍDA FINAL
Retorne APENAS o objeto JSON. Nenhum texto antes ou depois. Nenhuma explicação. Nenhum markdown."""


def preencher_laboratoriais(texto, api_key, provider, modelo):
    if not texto or not str(texto).strip():
        return {"_erro": "Nenhum texto de exames fornecido. Cole os exames no campo de notas do Bloco 10."}
    r = _chamar_ia(_PROMPT_LABORATORIAIS, texto, api_key, provider, modelo)
    if "_erro" in r:
        return r
    r.pop("_erro", None)
    for i in (1, 2):
        k = f"lab_{i}_gas_tipo"
        if k in r and r[k] in ("", None):
            r[k] = None
    return r


# ==============================================================================
# AGENTE 11: EVOLUÇÃO CLÍNICA (texto livre — passa direto)
# ==============================================================================
def preencher_evolucao(texto, api_key, provider, modelo):
    return {"evolucao_notas": texto.strip()} if texto and texto.strip() else {}


# ==============================================================================
# AGENTE 12: SISTEMAS
# ==============================================================================
_PROMPT_SISTEMAS = """Você é um extrator estruturado de dados médicos de terapia intensiva.
Seu objetivo é preencher campos estruturados a partir de texto de evolução clínica por sistemas.

════════════════════════════
1. CONTEXTO DO TEXTO DE ENTRADA

O texto pode conter:
- Evolução médica completa ou parcial
- Exame físico isolado por sistemas
- Narrativa fragmentada ou incompleta
- Apenas 2-3 sistemas descritos — isso é NORMAL

Campos incompletos são esperados. Extrair apenas o que estiver explicitamente descrito.
Nunca inferir, completar ou inventar informação.

════════════════════════════
2. PRINCÍPIO FUNDAMENTAL — AUSÊNCIA ≠ NEGAÇÃO  (REGRA PRIORITÁRIA)

Três estados possíveis para qualquer informação:

  PRESENTE  → o texto afirma explicitamente
              → preencher com o valor descrito ("Sim", número, texto)

  NEGADO    → o texto afirma EXPLICITAMENTE que algo NÃO existe
              → preencher campo Sim/Não com "Não"
              Exemplos: "sem febre" → "Não" | "sem LPP" → "Não" | "sem TRS" → "Não"

  AUSENTE   → o texto simplesmente NÃO menciona o assunto
              → preencher com ""
              → NUNCA preencher "Não" por inferência ou ausência de menção
              Exemplo: febre não mencionada → sis_infec_febre = ""

════════════════════════════
3. REGRAS GERAIS DE PREENCHIMENTO

- Todos os campos devem existir no JSON de saída
- Campos de texto ausentes → ""
- Campos Sim/Não ausentes → "" | negados → "Não" | confirmados → "Sim"
- Campos inteiros ausentes → null (ECG, RASS, sub-escores GCS)
- Campos booleanos ausentes → false (escape_manha/tarde/noite)
- Não utilizar null em campos de texto
- Não criar campos extras além dos definidos
- Não reorganizar informações entre sistemas
- Não resumir, interpretar ou inferir clinicamente
- Manter valores numéricos como strings (ex: "1800mL", "0.08 mcg/kg/min")
- Retornar APENAS JSON válido. Sem texto adicional. Sem comentários. Sem markdown.

════════════════════════════
4. REGRAS POR SISTEMA

────────────────────────────
NEUROLÓGICO

sis_neuro_ecg      → GCS total. Inteiro 3-15 se explícito; null se não mencionado.
sis_neuro_ecg_ao   → Abertura Ocular (1-4). Inteiro se explícito (ex: "AO 3"); null se ausente.
sis_neuro_ecg_rv   → Resposta Verbal (1-5). Inteiro se explícito (ex: "RV 4"); null se ausente.
sis_neuro_ecg_rm   → Resposta Motora (1-6). Inteiro se explícito (ex: "RM 5"); null se ausente.
sis_neuro_ecg_p    → GCS pré-sedação (ECG-P). Inteiro 1-15; null se ausente.
sis_neuro_rass     → RASS. Inteiro -5 a +5; null se ausente.

sis_neuro_delirium      → "Sim" se delirium/confusão/agitação/desorientação descrita.
                           "Não" se "sem delirium", "sem confusão", "orientado" explícito.
                           "" se não mencionado.
sis_neuro_delirium_tipo → "Hiperativo" (agitação/combatividade) | "Hipoativo" (letargia/hiporesponsividade).
                           Preencher SOMENTE se delirium = "Sim". "" caso contrário.
sis_neuro_cam_icu       → "Positivo" | "Negativo" se explícito. "" se não mencionado.

sis_neuro_pupilas_tam      → "Miótica" | "Normal" | "Midríase". "" se não mencionado.
sis_neuro_pupilas_simetria → "Simétricas" (isocóricas) | "Anisocoria". "" se não mencionado.
sis_neuro_pupilas_foto     → "Fotoreagente" | "Não fotoreagente". "" se não mencionado.

sis_neuro_analgesico_adequado → "Sim" se bom controle álgico / EVA baixo / analgesia eficaz.
                                  "Não" se dor presente / controle inadequado / EVA elevado.
                                  "" se não mencionado.
sis_neuro_deficits_focais → Texto literal do déficit (ex: "Hemiparesia Direita", "hemiparesia D grau 2"). "" se não mencionado.
                              NÃO preencher com "ausente" ou "sem déficits".
sis_neuro_deficits_ausente → "Ausente" se texto disser "sem déficit focal", "ausente", "sem déficits focais".
                              null ou "" caso contrário. Preencher SOMENTE quando deficits_focais estiver vazio.

Analgesia — separar drogas, dose e frequência. Preencher slots 1→2→3 em ordem:
sis_neuro_analgesia_{1,2,3}_tipo   → "Fixa" (horária/contínua/programada) | "Se necessário" (SN/ACM/resgate)
sis_neuro_analgesia_{1,2,3}_drogas → Nome do medicamento
sis_neuro_analgesia_{1,2,3}_dose   → Dose com unidade (ex: "4mg IV")
sis_neuro_analgesia_{1,2,3}_freq   → Frequência (ex: "4/4h", "BIC Contínua", "ACM")
Se sem analgesia descrita → todos ""

Sedação — drogas e doses separados. Preencher slots 1→2→3 em ordem:
sis_neuro_sedacao_meta           → Meta RASS única (ex: "RASS -2"). "" se não mencionado.
sis_neuro_sedacao_{1,2,3}_drogas → Droga de sedação (ex: "Propofol")
sis_neuro_sedacao_{1,2,3}_dose   → Dose (ex: "20mg/h")
Se sem sedação → todos ""

sis_neuro_bloqueador_med  → Nome do medicamento BNM (ex: "Rocurônio", "Cisatracúrio"). "" se ausente.
sis_neuro_bloqueador_dose → Dose com unidade (ex: "15 ml/h", "0.1 mg/kg/h"). "" se ausente.
sis_neuro_obs             → Texto livre de observações neurológicas. "" se ausente.

────────────────────────────
RESPIRATÓRIO

sis_resp_ausculta  → Texto literal da ausculta pulmonar. "" se não mencionado.
sis_resp_modo      → "Ar Ambiente" | "Oxigenoterapia" | "VNI" | "Cateter de Alto Fluxo" | "Ventilação Mecânica"
                     "" se não mencionado.
sis_resp_modo_vent → "VCV" | "PCV" | "PSV". Preencher SOMENTE se modo = "Ventilação Mecânica". "" caso contrário.
sis_resp_oxigenio_modo  → Modo de O2 (ex: "Cateter Nasal", "Máscara de Venturi"). Preencher SOMENTE se modo = "Oxigenoterapia". "" caso contrário.
sis_resp_oxigenio_fluxo → Fluxo em L/min (ex: "2", "4"). Preencher SOMENTE se modo = "Oxigenoterapia". "" caso contrário.

Parâmetros ventilatórios (somente valores, sem unidade duplicada):
sis_resp_pressao → pressão (ex: "18")
sis_resp_volume  → volume corrente (ex: "480")
sis_resp_fio2    → FiO2 em % (ex: "45")
sis_resp_peep    → PEEP (ex: "8")
sis_resp_freq    → frequência respiratória (ex: "16")

sis_resp_vent_protetora → "Sim" se "ventilação protetora" ou volume ≤6mL/kg.
                           "Não" se negado explicitamente. "" se não mencionado.
sis_resp_sincronico     → "Sim" se "sincrônico" / boa sincronia.
                           "Não" se "assincrônico" / há assincronia.
                           "" se não mencionado.
sis_resp_assincronia    → Tipo da assincronia (ex: "Double trigger", "auto-PEEP"). "" se sincrônico ou ausente.

Mecânica ventilatória (separar cada campo):
sis_resp_complacencia → valor da complacência
sis_resp_resistencia  → valor da resistência
sis_resp_dp           → drive pressure
sis_resp_plato        → pressão de platô
sis_resp_pico         → pressão de pico

Drenos — nome e débito separados. Preencher slots 1→2→3 em ordem:
sis_resp_dreno_{1,2,3}        → nome/localização (ex: "Pleural D", "Mediastinal")
sis_resp_dreno_{1,2,3}_debito → débito com unidade (ex: "180mL/dia")
sis_resp_obs → Texto livre de observações respiratórias. "" se ausente.

────────────────────────────
CARDIOVASCULAR

sis_cardio_fc           → FC em bpm. "" se não mencionado.
sis_cardio_cardioscopia → Ritmo (ex: "Sinusal", "Fibrilação Atrial", "BAVT"). "" se não mencionado.
sis_cardio_pam          → PAM em mmHg. "" se não mencionado.

sis_cardio_perfusao         → "Normal" | "Lentificada" | "Flush". "" se ausente.
sis_cardio_tec              → Tempo de enchimento capilar em segundos (ex: "3 seg.", "4 seg."). "" se ausente.
sis_cardio_fluido_responsivo → "Sim" | "Não" se explícito. "" se não mencionado.
sis_cardio_fluido_tolerante  → "Sim" | "Não" se explícito. "" se não mencionado.

DVA — medicamento e dose separados. Preencher slots 1→2→3→4 em ordem:
sis_cardio_dva_{1,2,3,4}_med  → nome da droga vasoativa
sis_cardio_dva_{1,2,3,4}_dose → dose com unidade (ex: "0.12 mcg/kg/min")
Se sem DVA → todos ""

sis_cardio_obs → Texto livre de observações cardiovasculares. "" se ausente.

────────────────────────────
RENAL

sis_renal_diurese      → volume de diurese com unidade (ex: "1800mL"). "" se ausente.
sis_renal_balanco      → BH com sinal (ex: "+350mL", "-200mL"). "" se ausente.
sis_renal_balanco_acum → BH acumulado (ex: "+2300mL"). "" se ausente.
sis_renal_volemia      → "Hipovolêmico" | "Euvolêmico" | "Hipervolêmico". "" se ausente.
                          Sinônimos: hipovolêmico=desidratado/seco; hipervolêmico=congesto/edemaciado/sobrecarga.

Função renal — separar hoje do anterior (quando tendência descrita, ex: "Cr 2.1 → 1.8"):
sis_renal_cr_antepen → creatinina anteontem. "" se ausente.
sis_renal_cr_ult    → creatinina ontem. "" se ausente.
sis_renal_cr_hoje   → creatinina hoje. "" se ausente.
sis_renal_ur_antepen → ureia anteontem. "" se ausente.
sis_renal_ur_ult    → ureia ontem. "" se ausente.
sis_renal_ur_hoje   → ureia hoje. "" se ausente.

Distúrbios hidroeletrolíticos — preencher SOMENTE se explicitamente mencionado:
sis_renal_sodio    → "Normal" | "Hiponatremia" | "Hipernatremia". "" se sódio não mencionado.
sis_renal_potassio → "Normal" | "Hipocalemia"  | "Hipercalemia".  "" se potássio não mencionado.
sis_renal_magnesio → "Normal" | "Hipomagnesemia" | "Hipermagnesemia". "" se magnésio não mencionado.
sis_renal_fosforo  → "Normal" | "Hipofosfatemia" | "Hiperfosfatemia". "" se fósforo não mencionado.
sis_renal_calcio   → "Normal" | "Hipocalcemia"  | "Hipercalcemia".   "" se cálcio não mencionado.
ATENÇÃO: "" ≠ "Normal". Só preencher "Normal" se o texto disser explicitamente que está normal.

sis_renal_trs         → "Sim" se em TRS/diálise/hemodiálise/CRRT/CVVHDF.
                         "Não" se "sem TRS", "sem diálise", "TRS suspensa" explícito.
                         "" se não mencionado.
sis_renal_trs_via     → via de acesso (ex: "Cateter femoral D"). "" se ausente.
sis_renal_trs_ultima  → data da última sessão. "" se ausente.
sis_renal_trs_proxima → data programada da próxima. "" se ausente.
sis_renal_obs → Texto livre de observações renais. "" se ausente.
sis_metab_obs → Texto livre de observações metabólicas (glicemia, eletrólitos, ácido-base). "" se ausente.
sis_nutri_obs → Texto livre de observações nutricionais. "" se ausente.

────────────────────────────
INFECCIOSO

sis_infec_febre        → "Sim" se febril/picos febris/temperatura elevada mencionados.
                          "Não" se "afebril", "sem febre", "apirético" explícito.
                          "" se temperatura não mencionada.
sis_infec_febre_vezes  → número de picos nas últimas 24h (texto, ex: "2"). "" se ausente.
sis_infec_febre_ultima → data/hora do último pico. "" se ausente.

sis_infec_atb        → "Sim" se em uso de ATB. "Não" se "sem ATB" explícito. "" se ausente.
sis_infec_atb_guiado → "Sim" se guiado por cultura/antibiograma. "Não" se empírico. "" se ausente.
sis_infec_atb_{1,2,3} → nomes dos ATBs em uso, um por slot. "" se ausente.

sis_infec_culturas_and → "Sim" se culturas pendentes/em andamento. "Não" se sem pendentes explícito. "" se ausente.
sis_infec_cult_{1,2,3,4}_sitio → sítio da cultura em andamento (ex: "Hemocultura central"). "" se ausente.
sis_infec_cult_{1,2,3,4}_data  → data da coleta. "" se ausente.

sis_infec_pcr_hoje    → PCR mais recente (número como texto). "" se ausente.
sis_infec_pcr_ult     → PCR anterior. "" se ausente.
sis_infec_pcr_antepen → PCR antepenúltimo. "" se ausente.
sis_infec_leuc_antepen → leucócitos anteontem. "" se ausente.
sis_infec_leuc_ult    → leucócitos ontem. "" se ausente.
sis_infec_leuc_hoje   → leucócitos hoje. "" se ausente.

sis_infec_isolamento        → "Sim" | "Não" se explícito. "" se não mencionado.
sis_infec_isolamento_tipo   → "Contato" | "Aerossol" | "Gotícula" | "Reverso". "" se ausente.
sis_infec_isolamento_motivo → agente/motivo (ex: "K. pneumoniae KPC+"). "" se ausente.
sis_infec_patogenos         → patógenos identificados — texto literal. "" se ausente.
sis_infec_obs → Texto livre de observações infecciosas. "" se ausente.

────────────────────────────
GASTROINTESTINAL / NUTRICIONAL

sis_gastro_exame_fisico       → texto literal do EF abdominal. "" se ausente.
sis_gastro_dieta_oral         → tipo de dieta oral (ex: "Pastosa", "Completa"). "" se ausente.
sis_gastro_dieta_enteral      → fórmula enteral (ex: "Peptamen", "Fresubin"). "" se ausente.
sis_gastro_dieta_enteral_vol  → Kcal Enteral (ex: "300", "1200 kcal"). "" se ausente.
sis_gastro_dieta_parenteral   → tipo NPP (ex: "NPT", "hidrolisada"). "" se ausente.
sis_gastro_dieta_parenteral_vol → Kcal NPP (ex: "1100", "500 kcal"). "" se ausente.
sis_gastro_meta_calorica      → meta calórica em kcal — somente número (ex: "1800"). "" se ausente.

sis_gastro_na_meta        → "Sim" se atingindo meta. "Não" se fora da meta. "" se ausente.
sis_gastro_ingestao_quanto → ingestão real descrita (ex: "800 kcal"). "" se ausente.

sis_gastro_escape_glicemico → "Sim" se escape/hiperglicemia. "Não" se "sem escape" / glicemia controlada. "" se ausente.
sis_gastro_escape_vezes     → número de episódios. "" se ausente.
sis_gastro_escape_manha     → true se manhã mencionada como turno. false caso contrário.
sis_gastro_escape_tarde     → true se tarde mencionada. false caso contrário.
sis_gastro_escape_noite     → true se noite mencionada. false caso contrário.
sis_gastro_insulino         → "Sim" | "Não" se explícito. "" se ausente.
sis_gastro_insulino_dose_manha → dose manhã (ex: "10", "10 Un"). "" se ausente.
sis_gastro_insulino_dose_tarde → dose tarde. "" se ausente.
sis_gastro_insulino_dose_noite → dose noite. "" se ausente.
Saída: "Insulinoterapia, 10 - 10 - 10" (manhã - tarde - noite).

sis_gastro_evacuacao      → "Sim" se evacuou. "Não" se "sem evacuação", "constipado", "obstipado". "" se ausente.
sis_gastro_evacuacao_data → data da última evacuação. "" se ausente.
sis_gastro_laxativo       → laxativo em uso (ex: "Lactulose 10mL 8/8h"). "" se ausente.
sis_gastro_obs → Texto livre de observações gastrointestinais. "" se ausente.

────────────────────────────
HEMATOLÓGICO

sis_hemato_anticoag        → "Sim" se em anticoagulação. "Não" se "sem anticoag" / suspensa. "" se ausente.
sis_hemato_anticoag_tipo   → "Profilática" (dose baixa/profilática) | "Plena" (terapêutica). "" se ausente.
sis_hemato_anticoag_motivo → indicação (ex: "TVP", "FA", "TEP", "imobilização"). "" se ausente.

sis_hemato_sangramento      → "Sim" se sangramento ativo/recente. "Não" se "sem sangramento" explícito. "" se ausente.
sis_hemato_sangramento_via  → via (ex: "Digestiva alta", "Urinária"). "" se ausente.
sis_hemato_sangramento_data → data do último episódio. "" se ausente.

Transfusão — componentes e bolsas separados. Preencher slots 1→2→3 em ordem:
sis_hemato_transf_data           → data da transfusão. "" se ausente.
sis_hemato_transf_{1,2,3}_comp   → componente (ex: "Concentrado de hemácias", "Plaquetas", "PFC")
sis_hemato_transf_{1,2,3}_bolsas → número de bolsas (ex: "2 bolsas")

sis_hemato_hb_antepen → Hb anteontem. "" se ausente.
sis_hemato_hb_ult    → Hb ontem. "" se ausente.
sis_hemato_hb_hoje   → Hb hoje. "" se ausente.
sis_hemato_plaq_antepen → Plaq anteontem. "" se ausente.
sis_hemato_plaq_ult  → Plaq ontem. "" se ausente.
sis_hemato_plaq_hoje → Plaq hoje. "" se ausente.
sis_hemato_inr_antepen → INR anteontem. "" se ausente.
sis_hemato_inr_ult   → INR ontem. "" se ausente.
sis_hemato_inr_hoje  → INR hoje. "" se ausente.
sis_hemato_obs → Texto livre de observações hematológicas. "" se ausente.

────────────────────────────
PELE E MUSCULOESQUELÉTICO

Edema (saída: "Edema presente, cacifo X cruzes" ou "Sem edema"):
sis_pele_edema → "Presente" se edema descrito. "Ausente" se negado ("sem edema"). "" se ausente.
sis_pele_edema_cruzes → Número de cruzes do cacifo quando edema presente (ex: "1", "2", "3"). "" se ausente ou edema ausente.

LPP:
sis_pele_lpp → "Sim" se LPP/úlcera/escara descrita. "Não" se "sem LPP" / "pele íntegra". "" se ausente.
sis_pele_lpp_local_{1,2,3} → localização (ex: "Sacro", "Calcâneo D", "Trocânter E")
sis_pele_lpp_grau_{1,2,3}  → grau/estágio (ex: "Grau II"). Preencher slots 1→2→3 em ordem.

Polineuropatia (saída: "Polineuropatia do doente crítico" ou "Sem polineuropatia"):
sis_pele_polineuropatia → "Sim" se polineuropatia do doente crítico/PICS descrita. "Não" se negado. "" se ausente.

sis_pele_obs → Texto livre de observações. "" se ausente.

════════════════════════════
5. VALIDAÇÕES FINAIS (CHECAR ANTES DE RETORNAR)

- Todos os campos do JSON estão presentes
- Nenhum campo com valor null (exceto inteiros ECG/RASS/sub-escores quando ausentes)
- Nenhum campo extra além dos definidos
- Regra AUSÊNCIA ≠ NEGAÇÃO respeitada em todos os campos Sim/Não
- Nenhuma inferência clínica realizada
- Nenhuma informação explícita omitida
- JSON válido e sem texto externo

════════════════════════════
ESTRUTURA DE SAÍDA OBRIGATÓRIA

Retorne EXATAMENTE este JSON com todos os campos listados.
Campos ausentes = "". Inteiros ausentes = null. Booleanos ausentes = false.

{
  "sis_neuro_ecg": null,
  "sis_neuro_ecg_ao": null, "sis_neuro_ecg_rv": null, "sis_neuro_ecg_rm": null,
  "sis_neuro_ecg_p": null, "sis_neuro_rass": null,
  "sis_neuro_delirium": "", "sis_neuro_delirium_tipo": "",
  "sis_neuro_cam_icu": "",
  "sis_neuro_pupilas_tam": "", "sis_neuro_pupilas_simetria": "", "sis_neuro_pupilas_foto": "",
  "sis_neuro_analgesico_adequado": "", "sis_neuro_deficits_focais": "", "sis_neuro_deficits_ausente": "",
  "sis_neuro_analgesia_1_tipo": "", "sis_neuro_analgesia_1_drogas": "", "sis_neuro_analgesia_1_dose": "", "sis_neuro_analgesia_1_freq": "",
  "sis_neuro_analgesia_2_tipo": "", "sis_neuro_analgesia_2_drogas": "", "sis_neuro_analgesia_2_dose": "", "sis_neuro_analgesia_2_freq": "",
  "sis_neuro_analgesia_3_tipo": "", "sis_neuro_analgesia_3_drogas": "", "sis_neuro_analgesia_3_dose": "", "sis_neuro_analgesia_3_freq": "",
  "sis_neuro_sedacao_meta": "",
  "sis_neuro_sedacao_1_drogas": "", "sis_neuro_sedacao_1_dose": "",
  "sis_neuro_sedacao_2_drogas": "", "sis_neuro_sedacao_2_dose": "",
  "sis_neuro_sedacao_3_drogas": "", "sis_neuro_sedacao_3_dose": "",
  "sis_neuro_bloqueador_med": "", "sis_neuro_bloqueador_dose": "", "sis_neuro_obs": "",

  "sis_resp_ausculta": "",
  "sis_resp_modo": "", "sis_resp_modo_vent": "",
  "sis_resp_oxigenio_modo": "", "sis_resp_oxigenio_fluxo": "",
  "sis_resp_pressao": "", "sis_resp_volume": "", "sis_resp_fio2": "", "sis_resp_peep": "", "sis_resp_freq": "",
  "sis_resp_vent_protetora": "", "sis_resp_sincronico": "", "sis_resp_assincronia": "",
  "sis_resp_complacencia": "", "sis_resp_resistencia": "", "sis_resp_dp": "", "sis_resp_plato": "", "sis_resp_pico": "",
  "sis_resp_dreno_1": "", "sis_resp_dreno_1_debito": "",
  "sis_resp_dreno_2": "", "sis_resp_dreno_2_debito": "",
  "sis_resp_dreno_3": "", "sis_resp_dreno_3_debito": "",
  "sis_resp_obs": "",

  "sis_cardio_fc": "", "sis_cardio_cardioscopia": "", "sis_cardio_pam": "",
  "sis_cardio_perfusao": "", "sis_cardio_tec": "", "sis_cardio_fluido_responsivo": "", "sis_cardio_fluido_tolerante": "",
  "sis_cardio_dva_1_med": "", "sis_cardio_dva_1_dose": "",
  "sis_cardio_dva_2_med": "", "sis_cardio_dva_2_dose": "",
  "sis_cardio_dva_3_med": "", "sis_cardio_dva_3_dose": "",
  "sis_cardio_dva_4_med": "", "sis_cardio_dva_4_dose": "",
  "sis_cardio_obs": "",

  "sis_renal_diurese": "", "sis_renal_balanco": "", "sis_renal_balanco_acum": "",
  "sis_renal_volemia": "",
  "sis_renal_cr_antepen": "", "sis_renal_cr_ult": "", "sis_renal_cr_hoje": "",
  "sis_renal_ur_antepen": "", "sis_renal_ur_ult": "", "sis_renal_ur_hoje": "",
  "sis_renal_sodio": "", "sis_renal_potassio": "", "sis_renal_magnesio": "", "sis_renal_fosforo": "", "sis_renal_calcio": "",
  "sis_renal_trs": "", "sis_renal_trs_via": "", "sis_renal_trs_ultima": "", "sis_renal_trs_proxima": "",
  "sis_renal_obs": "", "sis_metab_obs": "", "sis_nutri_obs": "",

  "sis_infec_febre": "", "sis_infec_febre_vezes": "", "sis_infec_febre_ultima": "",
  "sis_infec_atb": "", "sis_infec_atb_guiado": "",
  "sis_infec_atb_1": "", "sis_infec_atb_2": "", "sis_infec_atb_3": "",
  "sis_infec_culturas_and": "",
  "sis_infec_cult_1_sitio": "", "sis_infec_cult_1_data": "",
  "sis_infec_cult_2_sitio": "", "sis_infec_cult_2_data": "",
  "sis_infec_cult_3_sitio": "", "sis_infec_cult_3_data": "",
  "sis_infec_cult_4_sitio": "", "sis_infec_cult_4_data": "",
  "sis_infec_pcr_hoje": "", "sis_infec_pcr_ult": "", "sis_infec_pcr_antepen": "",
  "sis_infec_leuc_antepen": "", "sis_infec_leuc_ult": "", "sis_infec_leuc_hoje": "",
  "sis_infec_isolamento": "", "sis_infec_isolamento_tipo": "", "sis_infec_isolamento_motivo": "",
  "sis_infec_patogenos": "", "sis_infec_obs": "",

  "sis_gastro_exame_fisico": "",
  "sis_gastro_dieta_oral": "", "sis_gastro_dieta_enteral": "", "sis_gastro_dieta_enteral_vol": "",
  "sis_gastro_dieta_parenteral": "", "sis_gastro_dieta_parenteral_vol": "", "sis_gastro_meta_calorica": "",
  "sis_gastro_na_meta": "", "sis_gastro_ingestao_quanto": "",
  "sis_gastro_escape_glicemico": "", "sis_gastro_escape_vezes": "",
  "sis_gastro_escape_manha": false, "sis_gastro_escape_tarde": false, "sis_gastro_escape_noite": false,
  "sis_gastro_insulino": "",
  "sis_gastro_insulino_dose_manha": "", "sis_gastro_insulino_dose_tarde": "", "sis_gastro_insulino_dose_noite": "",
  "sis_gastro_evacuacao": "", "sis_gastro_evacuacao_data": "", "sis_gastro_laxativo": "",
  "sis_gastro_obs": "",

  "sis_hemato_anticoag": "", "sis_hemato_anticoag_tipo": "", "sis_hemato_anticoag_motivo": "",
  "sis_hemato_sangramento": "", "sis_hemato_sangramento_via": "", "sis_hemato_sangramento_data": "",
  "sis_hemato_transf_data": "",
  "sis_hemato_transf_1_comp": "", "sis_hemato_transf_1_bolsas": "",
  "sis_hemato_transf_2_comp": "", "sis_hemato_transf_2_bolsas": "",
  "sis_hemato_transf_3_comp": "", "sis_hemato_transf_3_bolsas": "",
  "sis_hemato_hb_antepen": "", "sis_hemato_hb_ult": "", "sis_hemato_hb_hoje": "",
  "sis_hemato_plaq_antepen": "", "sis_hemato_plaq_ult": "", "sis_hemato_plaq_hoje": "",
  "sis_hemato_inr_antepen": "", "sis_hemato_inr_ult": "", "sis_hemato_inr_hoje": "",
  "sis_hemato_obs": "",

  "sis_pele_edema": "", "sis_pele_edema_cruzes": "",
  "sis_pele_lpp": "",
  "sis_pele_lpp_local_1": "", "sis_pele_lpp_grau_1": "",
  "sis_pele_lpp_local_2": "", "sis_pele_lpp_grau_2": "",
  "sis_pele_lpp_local_3": "", "sis_pele_lpp_grau_3": "",
  "sis_pele_polineuropatia": "", "sis_pele_obs": ""
}"""

def preencher_sistemas(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_SISTEMAS, texto, api_key, provider, modelo)
    r.pop("_erro", None)

    # Campos neurológicos numéricos: inteiros → string para text_input (como FC, PAM)
    for k, default in [("sis_neuro_ecg", 15), ("sis_neuro_ecg_p", 15)]:
        if k in r:
            try: v = int(r[k]) if r[k] not in ("", None) else default
            except: v = default
            r[k] = str(v) if v is not None else ""

    if "sis_neuro_rass" in r:
        try: v = int(r["sis_neuro_rass"]) if r["sis_neuro_rass"] not in ("", None) else 0
        except: v = 0
        r["sis_neuro_rass"] = str(v)

    for k in ["sis_neuro_ecg_ao", "sis_neuro_ecg_rv", "sis_neuro_ecg_rm"]:
        if k in r:
            try: v = int(r[k]) if r[k] not in ("", None) else None
            except: v = None
            r[k] = str(v) if v is not None else ""

    # Booleanos do escape glicêmico
    for k in ["sis_gastro_escape_manha", "sis_gastro_escape_tarde", "sis_gastro_escape_noite"]:
        if k in r and isinstance(r[k], str):
            r[k] = r[k].lower() in ("true", "sim", "yes", "1")

    # Edema: normaliza Sim/Não → Presente/Ausente (compatível com pills)
    if "sis_pele_edema" in r:
        v = r["sis_pele_edema"]
        if isinstance(v, str) and v.strip():
            if v.strip().lower() in ("sim", "yes", "1", "presente"):
                r["sis_pele_edema"] = "Presente"
            elif v.strip().lower() in ("não", "nao", "no", "0", "ausente"):
                r["sis_pele_edema"] = "Ausente"
        else:
            r["sis_pele_edema"] = ""

    # Déficit focal ausente: converte para "Ausente" ou None (compatível com pills)
    if "sis_neuro_deficits_ausente" in r:
        v = r["sis_neuro_deficits_ausente"]
        if v == "Ausente" or v is True or (isinstance(v, str) and v.strip().lower() in ("true", "sim", "yes", "1", "ausente")):
            r["sis_neuro_deficits_ausente"] = "Ausente"
        else:
            r["sis_neuro_deficits_ausente"] = None

    return r


# ==============================================================================
# AGENTE 13: CONTROLES & BALANÇO HÍDRICO
# ==============================================================================
_PROMPT_CONTROLES = """Você é um extrator estruturado de dados médicos para prontuário hospitalar.

OBJETIVO
Extrair controles vitais, glicemia, diurese e balanço hídrico para até 3 dias distintos, preenchendo exclusivamente:
- ctrl_hoje → dia mais recente
- ctrl_ontem → dia imediatamente anterior
- ctrl_anteontem → dia anterior a ontem

════════════════════════════
DETERMINAÇÃO DOS DIAS

- Identificar blocos de dados com data explícita e ordenar cronologicamente.
- ctrl_hoje = data mais recente | ctrl_ontem = anterior | ctrl_anteontem = anterior a ontem
- Se 1 dia → preencher somente ctrl_hoje.
- Se 2 dias → preencher ctrl_hoje e ctrl_ontem.
- Se mais de 3 dias → usar apenas os 3 mais recentes.
- Sem datas explícitas → primeiro bloco = hoje, segundo = ontem, terceiro = anteontem.
- Se mesma data repetida → consolidar em um único dia, não duplicar.
- Nunca misturar valores entre datas.

════════════════════════════
REGRAS GERAIS

- Todos os valores como strings. Dados ausentes → "". Não utilizar null.
- NÃO preencher conduta.
- Retornar APENAS JSON válido. Sem texto fora do JSON.
- Datas: manter formato original (DD/MM/AAAA ou DD/MM).
- Não calcular médias. Não estimar valores ausentes. Não reorganizar parâmetros entre dias.

════════════════════════════
PARÂMETROS COM MÍNIMO E MÁXIMO

→ Se intervalo descrito (ex: "110-135", "110 a 135", "110 – 135") → _min = "110", _max = "135"
→ Se apenas um valor → preencher somente _min, _max = ""
→ Se múltiplos valores isolados no mesmo dia → _min = menor, _max = maior
→ Se _min e _max invertidos no texto → corrigir posição (não alterar valores)

PAS → ctrl_{dia}_pas_min / _max
PAD → ctrl_{dia}_pad_min / _max
PAM → ctrl_{dia}_pam_min / _max
FC  → ctrl_{dia}_fc_min  / _max
FR  → ctrl_{dia}_fr_min  / _max
SatO2 → ctrl_{dia}_sato2_min / _max
Temperatura → ctrl_{dia}_temp_min / _max
Dextro / Glic / Glicemia → ctrl_{dia}_glic_min / _max

════════════════════════════
PARÂMETROS DE VALOR ÚNICO

ctrl_{dia}_diurese: volume total diário. Manter unidade se descrita (ex: "1800ml").
ctrl_{dia}_balanco: balanço hídrico. Manter sinal + ou - e unidade se descritos.
→ Não converter unidades. Não calcular balanço se não estiver explícito.

ctrl_periodo: "24 horas" | "12 horas"
→ "12 horas" se o texto mencionar controles em 12h, turnos de 12h, controles 12/12h, etc.
→ "24 horas" se controles em 24h, diário, ou ausente (padrão).

════════════════════════════
VALIDAÇÕES INTERNAS (CHECAR ANTES DE RETORNAR)

- Não misturar valores entre dias.
- _min ≤ _max quando ambos preenchidos.
- Nenhum null. Nenhum campo extra. Sem texto fora do JSON.
- Se todos os campos de um dia estiverem vazios → manter dia vazio (renderização posterior ocultará).

════════════════════════════
ESTRUTURA DE SAÍDA (IMUTÁVEL)

{
  "ctrl_periodo": "24 horas",

  "ctrl_hoje_data": "",
  "ctrl_hoje_pas_min": "", "ctrl_hoje_pas_max": "",
  "ctrl_hoje_pad_min": "", "ctrl_hoje_pad_max": "",
  "ctrl_hoje_pam_min": "", "ctrl_hoje_pam_max": "",
  "ctrl_hoje_fc_min":  "", "ctrl_hoje_fc_max": "",
  "ctrl_hoje_fr_min":  "", "ctrl_hoje_fr_max": "",
  "ctrl_hoje_sato2_min": "", "ctrl_hoje_sato2_max": "",
  "ctrl_hoje_temp_min": "", "ctrl_hoje_temp_max": "",
  "ctrl_hoje_glic_min": "", "ctrl_hoje_glic_max": "",
  "ctrl_hoje_diurese": "", "ctrl_hoje_balanco": "",

  "ctrl_ontem_data": "",
  "ctrl_ontem_pas_min": "", "ctrl_ontem_pas_max": "",
  "ctrl_ontem_pad_min": "", "ctrl_ontem_pad_max": "",
  "ctrl_ontem_pam_min": "", "ctrl_ontem_pam_max": "",
  "ctrl_ontem_fc_min":  "", "ctrl_ontem_fc_max": "",
  "ctrl_ontem_fr_min":  "", "ctrl_ontem_fr_max": "",
  "ctrl_ontem_sato2_min": "", "ctrl_ontem_sato2_max": "",
  "ctrl_ontem_temp_min": "", "ctrl_ontem_temp_max": "",
  "ctrl_ontem_glic_min": "", "ctrl_ontem_glic_max": "",
  "ctrl_ontem_diurese": "", "ctrl_ontem_balanco": "",

  "ctrl_anteontem_data": "",
  "ctrl_anteontem_pas_min": "", "ctrl_anteontem_pas_max": "",
  "ctrl_anteontem_pad_min": "", "ctrl_anteontem_pad_max": "",
  "ctrl_anteontem_pam_min": "", "ctrl_anteontem_pam_max": "",
  "ctrl_anteontem_fc_min":  "", "ctrl_anteontem_fc_max": "",
  "ctrl_anteontem_fr_min":  "", "ctrl_anteontem_fr_max": "",
  "ctrl_anteontem_sato2_min": "", "ctrl_anteontem_sato2_max": "",
  "ctrl_anteontem_temp_min": "", "ctrl_anteontem_temp_max": "",
  "ctrl_anteontem_glic_min": "", "ctrl_anteontem_glic_max": "",
  "ctrl_anteontem_diurese": "", "ctrl_anteontem_balanco": ""
}

════════════════════════════
SAÍDA FINAL
Somente JSON válido conforme estrutura acima."""

def preencher_controles(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_CONTROLES, texto, api_key, provider, modelo)
    r.pop("_erro", None)
    return r


# ==============================================================================
# MAPEAMENTO: seção → função agente e campo _notas
# ==============================================================================
_AGENTES = {
    "identificacao":  preencher_identificacao,
    "hd":             preencher_hd,
    "comorbidades":   preencher_comorbidades,
    "muc":            preencher_muc,
    "hmpa":           preencher_hmpa,
    "dispositivos":   preencher_dispositivos,
    "culturas":       preencher_culturas,
    "antibioticos":   preencher_antibioticos,
    "complementares": preencher_complementares,
    "laboratoriais":  preencher_laboratoriais,
    "controles":      preencher_controles,
    "evolucao":       preencher_evolucao,
    "sistemas":       preencher_sistemas,
}

_NOTAS_MAP = {
    "identificacao":  "identificacao_notas",
    "hd":             "hd_notas",
    "comorbidades":   "comorbidades_notas",
    "muc":            "muc_notas",
    "hmpa":           "hmpa_texto",
    "dispositivos":   "dispositivos_notas",
    "culturas":       "culturas_notas",
    "antibioticos":   "antibioticos_notas",
    "complementares": "complementares_notas",
    "laboratoriais":  "laboratoriais_notas",
    "controles":      "controles_notas",
    "evolucao":       "evolucao_notas",
    "sistemas":       "sistemas_notas",
}

NOMES_SECOES = {
    "identificacao":  "1. Identificação",
    "hd":             "2. Diagnósticos",
    "comorbidades":   "3. Comorbidades",
    "muc":            "4. MUC",
    "hmpa":           "5. HMPA",
    "dispositivos":   "6. Dispositivos",
    "culturas":       "7. Culturas",
    "antibioticos":   "8. Antibióticos",
    "complementares": "9. Complementares",
    "laboratoriais":  "10. Exames Laboratoriais",
    "controles":      "11. Controles & Balanço",
    "evolucao":       "12. Evolução Clínica",
    "sistemas":       "13. Sistemas",
}


def preencher_todas_secoes(api_key: str, provider: str, modelo: str):
    """
    Lê os campos _notas já preenchidos pelo ia_extrator,
    roda cada um dos 12 agentes e retorna (resultado_dict, lista_erros).
    """
    resultado = {}
    erros = []

    for secao, fn_agente in _AGENTES.items():
        chave_notas = _NOTAS_MAP[secao]
        texto = st.session_state.get(chave_notas, "").strip()

        if not texto:
            continue

        dados = fn_agente(texto, api_key, provider, modelo)

        if "_erro" in dados:
            erros.append(f"{NOMES_SECOES[secao]}: {dados['_erro']}")
        else:
            resultado.update(dados)

    return resultado, erros
