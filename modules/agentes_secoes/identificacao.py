from ._base import (
    _chamar_ia, _REGRA_DATA, _extrair_json,
    OpenAI, _genai_new, _genai_types,
)

# ==============================================================================
# AGENTE 1: IDENTIFICAÇÃO
# ==============================================================================
_PROMPT_IDENTIFICACAO = """# CONTEXTO
Você é uma ferramenta usada para análise e extração de dados estruturados de textos clínicos hospitalares.

# OBJETIVO
Ler o texto fornecido pelo usuário e extrair as respostas exatas para as informações solicitadas na tag <VARIAVEIS>.

# REGRAS DE EXTRAÇÃO E FORMATAÇÃO
1. Responda de forma direta, concisa e objetiva.
2. Se a informação não constar explicitamente no texto, retorne estritamente o valor `null` no JSON. Não use variações como "Não encontrado", "Vazio" ou "".
3. Para perguntas de Sim ou Não, utilize valores booleanos padronizados: `true` para Sim e `false` para Não. Caso não encontre, retorne `null`.
4. Não faça presunções ou deduções além do que está escrito no texto.
5. A saída final deve ser EXCLUSIVAMENTE um objeto JSON válido, sem textos introdutórios, explicações ou blocos de código markdown ao redor.

# ENTRADAS
<TEXTO_ALVO>
[O texto clínico será fornecido na mensagem do usuário]
</TEXTO_ALVO>

<VARIAVEIS>
Extraia exatamente as seguintes chaves JSON:

- nome (string): Nome completo do paciente conforme escrito no texto.
- idade (number): Idade do paciente em anos. Retornar apenas o valor numérico inteiro (ex: 65). Ignorar meses ou dias — retornar somente os anos completos. Não incluir a palavra "anos" ou qualquer texto adicional.
- sexo (string): Sexo do paciente. Retornar EXATAMENTE "Masculino" ou "Feminino", mapeando automaticamente abreviações textuais (ex: "M", "Masc", "masc." → "Masculino"; "F", "Fem", "fem." → "Feminino"). Se não encontrado, null.
- prontuario (string): Número do prontuário ou número de registro hospitalar (HC). Retornar apenas o número como string.
- leito (string): Número ou identificação do leito do paciente (ex: "206A", "UTI-05", "Leito 3").
- origem (string): Procedência ou origem do paciente antes da internação atual (ex: "PS", "UPA", "Enfermaria", "Transferência hospitalar", "CC"). Texto literal do documento.
- equipe (string): Equipe médica responsável pelo paciente (ex: "Clínica Médica", "Cirurgia Geral", "Intensivismo"). Texto literal do documento.
- departamento (string): Setor/unidade onde o paciente está internado (ex: "UTI Adulto", "Sala Vermelha", "Enfermaria"). Texto literal do documento. Se ausente, null.
- interconsultora (string): Especialidade ou serviço em interconsulta (ex: "Cardiologia", "Nefrologia"). Texto literal do documento. Se ausente, null.
- di_hosp (string): Data de internação hospitalar. Manter o formato original do texto (DD/MM/AAAA, MM/AAAA ou MM/AA). Se ausente, null.
- di_uti (string): Data de entrada na UTI. Manter o formato original do texto. Se ausente, null.
- di_enf (string): Data de entrada na enfermaria. Manter o formato original do texto. Se ausente, null.
- saps3 (number): Valor do escore SAPS 3. Retornar apenas o valor numérico inteiro (ex: 55). Se ausente, null.
- sofa_adm (number): Valor do escore SOFA na admissão. Retornar apenas o valor numérico inteiro (ex: 8). Se ausente, null.
- sofa_atual (number): Valor do escore SOFA atual ou mais recente. Retornar apenas o valor numérico inteiro. Se ausente, null.
- mrs (string): Valor da Escala de Rankin Modificada (mRS). Retornar apenas o número como string (ex: "2"). Se ausente, null.
- pps (string): Valor do Palliative Performance Scale (PPS). Retornar o valor como string (ex: "80%", "80"). Se ausente, null.
- cfs (string): Valor da Clinical Frailty Scale (Escala de Fragilidade Clínica). Retornar o valor como string (ex: "3", "5 - Levemente frágil"). Se ausente, null.
- paliativo (boolean): O paciente está em cuidados paliativos, conforto ou sem medidas de ressuscitação? true se mencionado explicitamente, false se explicitamente negado, null se não mencionado.

# EXEMPLO DE SAÍDA PERFEITA
{
  "nome": "Maria Aparecida da Silva",
  "idade": 68,
  "sexo": "Feminino",
  "prontuario": "12345678",
  "leito": "206A",
  "origem": "PS",
  "equipe": "Clínica Médica - Intensivismo",
  "departamento": "UTI Adulto",
  "interconsultora": "Nefrologia",
  "di_hosp": "20/02/2026",
  "di_uti": "21/02/2026",
  "di_enf": null,
  "saps3": 72,
  "sofa_adm": 10,
  "sofa_atual": 6,
  "mrs": "2",
  "pps": "60%",
  "cfs": "4 - Vulnerável",
  "paliativo": true
}
</VARIAVEIS>"""

def preencher_identificacao(texto, api_key, provider, modelo):
    r = _chamar_ia(_PROMPT_IDENTIFICACAO, texto, api_key, provider, modelo)
    r.pop("_erro", None)
    # Campos numéricos inteiros: null/None → 0, converte string → int
    for k in ["sofa_adm", "sofa_atual"]:
        if k in r:
            try: r[k] = int(r[k]) if r[k] not in (None, "", "null") else 0
            except: r[k] = 0
    if "idade" in r:
        try: r["idade"] = int(r["idade"]) if r["idade"] not in (None, "", "null") else 0
        except: r["idade"] = 0
    # saps3: a IA retorna number, mas o widget é text_input → converte para string
    if "saps3" in r:
        r["saps3"] = str(int(r["saps3"])) if r["saps3"] not in (None, "", "null") else ""
    # Campos string: null/None → "" (campos de texto do formulário esperam string)
    for k in ["nome", "sexo", "prontuario", "leito", "origem", "equipe", "departamento", "interconsultora",
              "di_hosp", "di_uti", "di_enf", "mrs", "pps", "cfs"]:
        if r.get(k) is None:
            r[k] = ""
    # Booleano paliativo: null/None → False
    if "paliativo" in r:
        if r["paliativo"] is None:
            r["paliativo"] = False
        elif isinstance(r["paliativo"], str):
            r["paliativo"] = r["paliativo"].lower() in ("true", "sim", "yes", "1")
    return r
