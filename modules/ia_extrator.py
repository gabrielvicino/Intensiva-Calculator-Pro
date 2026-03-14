import json
import re
import time
from datetime import date
from openai import OpenAI
from google import genai as _genai_new
from google.genai import types as _genai_types

SYSTEM_PROMPT = """Você é um Auditor Médico de Terapia Intensiva focado em EXTRAÇÃO DE DADOS.
Sua missão é receber um texto clínico despadronizado e "fatiá-lo" cirurgicamente em 14 campos JSON.

════════════════════════════
DIRETRIZES DE "CORTE E COLAGEM" (ZERO ALUCINAÇÃO)

1. FIDELIDADE ABSOLUTA: Não resuma. Não reescreva. Apenas copie o trecho original e cole no campo.
2. DETECÇÃO DE CABEÇALHOS: O texto pode usar #, *, CAIXA ALTA ou apenas dois pontos (:) para seções.
   Exemplos: "# ID", "IDENTIFICAÇÃO:", "Paciente:" → campo `identificacao`
3. LIMITE DE SEÇÃO: O conteúdo vai do cabeçalho até o próximo cabeçalho reconhecido.
4. EFEITO ÍMÂ (exames complementares): Vários cabeçalhos de exames seguidos (AngioTC, EcoTT, CATE...)
   → junte TODOS dentro de `complementares`.
5. TEXTO INCOMPLETO É NORMAL: Prontuários reais são frequentemente parciais. Se um sistema
   (ex: renal, hematológico) não estiver descrito no texto, o campo correspondente fica "".
   NÃO invente nem complete com dados ausentes.

════════════════════════════
REGRA GLOBAL DE DATAS

- Ano padrão: se o ano não estiver explícito no texto, use o ano informado no campo "Data de hoje" da mensagem do usuário.
- Formato de saída: DD/MM/AAAA (4 dígitos no ano). Nunca use 2 dígitos no ano.
- Se outro ano estiver explícito no texto (ex: 2024, 2025), use o ano mencionado.

════════════════════════════
REGRAS DE OURO CLÍNICAS

- Antibióticos vs. História:
  • Prescrição atual ("Ceftriaxona D3", "Em uso de Tazocin") → campo `antibioticos`
  • Narrativa histórica ("Usou 7 dias de Merope na UPA") → campo `hmpa`

- Conduta Fragmentada:
  • Se conduta dividida por sistemas ("CONDUTA: #Neuro: ... #Resp: ...") → campo único `conduta`

- Evolução — o campo `evolucao` captura todo texto narrativo e subjetivo (impressão clínica,
    intercorrências, resumo do dia, exame físico, achados por sistemas).
    NÃO existe campo separado para "sistemas" — tudo vai em `evolucao`.

════════════════════════════
MAPEAMENTO DE CAMPOS

1.  identificacao
    Gatilhos: #ID, Nome, Paciente, Registro, HC, Leito, Idade, Data de nascimento
    IMPORTANTE — Cabeçalho de departamento: o prontuário frequentemente começa com uma linha de
    cabeçalho que indica onde a evolução está sendo escrita. Exemplos reais:
      "### Sala Vermelha", "### Evolução UTI", "# UTI Adulto", "# Enfermaria",
      "# Pela Clínica Médica", "# Pela Cirurgia", "- evolução", "## PA"
    Se esse cabeçalho existir, INCLUA-O no campo `identificacao` (mesmo que venha antes de qualquer
    dado do paciente). Ele será usado para identificar o setor de origem da evolução.

2.  hd
    Gatilhos: #HD, Diagnóstico(s), Hipóteses Diagnósticas, Problemas, Impressão diagnóstica,
              Listas numeradas no início do prontuário

3.  comorbidades
    Gatilhos: #CMD, #AP, Antecedentes, Comorbidades, HPP, Hábitos, ICSAP, Ex-tabagista,
              Histórico médico prévio

4.  muc
    Gatilhos: #MUC, #MED, Medicações Prévias, Uso Domiciliar, Receita de casa,
              Medicações em uso crônico

5.  hmpa
    Gatilhos: #HPMA, #HDA, #HMA, História, Resumo da internação, Admissão, Motivo da internação,
              Histórico da doença atual

6.  dispositivos
    Gatilhos: #DISP, Invasões, Acessos vasculares, Sondas, Cateteres, TOT, TQT,
              Dispositivos invasivos, CVC, SVD, SNE, PAI

7.  culturas
    Gatilhos: #CULT, Culturas, Microbiologia, Bacteriologia, Germes, Antibiograma,
              Swab, Urocultura, Hemocultura, Aspirado traqueal

8.  antibioticos
    Gatilhos: #ATB, Antimicrobianos, Antibióticos em uso, Esquema antibiótico atual
    ATENÇÃO: só ATBs da prescrição atual, não históricos

9.  complementares
    Gatilhos (junte todos): #EXAMES, Imagem, TC, RX, Raio-X, USG, ECO, Ecocardiograma,
              CATE, Ressonância, Cintilografia, Pareceres, Laudos, Endoscopia, Broncoscopia

10. evolucao
    Gatilhos: #EVO, Evolução (narrativa), Subjetivo, Intercorrências, Resumo do dia,
              Impressão clínica, Exame Físico, Evolução por Sistemas, Achados por sistema
    INCLUA tudo: narrativa subjetiva E achados objetivos por sistema.

11. conduta
    Gatilhos: #CD, #CONDUTA, Plano, Planejamento, Condutas, Prescrições do dia
    Inclua todas as subseções de conduta, mesmo divididas por sistemas.
    FORMATO DE SAÍDA: cada item de conduta em uma linha separada, prefixado com "- ".
    Exemplo: "- Manter Piperacilina-Tazobactam por mais 3 dias\n- Solicitar ecocardiograma TT\n- Repetir hemograma amanhã"
    Se o texto original já usa "- " ou numeração, mantenha um item por linha.

════════════════════════════
SAÍDA OBRIGATÓRIA

Retorne APENAS um objeto JSON válido, sem markdown, sem explicações antes ou depois.
Se um campo não tiver correspondência, retorne "".
ATENÇÃO JSON: Dentro dos valores, nunca use aspas duplas literais — substitua por aspas simples se necessário.

{
    "identificacao": "...",
    "hd": "...",
    "comorbidades": "...",
    "muc": "...",
    "hmpa": "...",
    "dispositivos": "...",
    "culturas": "...",
    "antibioticos": "...",
    "complementares": "...",
    "evolucao": "...",
    "conduta": "..."
}"""


def _extrair_json_robusto(texto: str) -> dict:
    """
    Extrai JSON de resposta que pode conter markdown, prefixos ou sufixos de texto.
    Mais robusto que json.loads direto — tenta múltiplas estratégias antes de falhar.
    """
    if not texto or not texto.strip():
        raise ValueError("Resposta vazia da IA")
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
    return json.loads(txt)


def extrair_dados_prontuario(texto_bruto: str, api_key: str, provider: str = "OpenAI GPT", modelo: str = "gpt-4o") -> dict:
    """
    Envia o prontuário bruto para a IA e retorna um dicionário com os 14 campos extraídos.
    Suporta OpenAI (padrão) e Google Gemini.
    """
    data_hoje = date.today().strftime("%d/%m/%Y")
    msg_usuario = (
        f"Data de hoje: {data_hoje}\n\n"
        f"Extraia os dados do seguinte prontuário médico:\n\n{texto_bruto}"
    )

    for attempt in range(3):
        try:
            if "OpenAI" in provider or "GPT" in provider:
                modelo_openai = modelo if modelo.startswith("gpt") else "gpt-4o"
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=modelo_openai,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": msg_usuario},
                    ],
                    response_format={"type": "json_object"},
                )
                return json.loads(response.choices[0].message.content)

            else:
                # Google Gemini — fallback
                # gemini-2.5-pro não aceita thinking_budget=0; gemini-2.5-flash aceita
                _modelo = modelo if modelo.startswith("gemini") else "gemini-2.0-flash"
                client = _genai_new.Client(api_key=api_key)
                cfg_kwargs: dict = {
                    "system_instruction": SYSTEM_PROMPT,
                    "temperature": 0.0,
                }
                if "2.5-flash" in _modelo:
                    cfg_kwargs["thinking_config"] = _genai_types.ThinkingConfig(thinking_budget=0)
                response = client.models.generate_content(
                    model=_modelo,
                    contents=msg_usuario,
                    config=_genai_types.GenerateContentConfig(**cfg_kwargs),
                )
                return _extrair_json_robusto(response.text or "")

        except json.JSONDecodeError as e:
            if attempt < 2:
                time.sleep(5)
                continue
            return {"_erro": f"JSON inválido retornado pela IA: {e}"}
        except Exception as e:
            err_str = str(e)
            is_rate_limit = "429" in err_str or "rate_limit" in err_str.lower()
            if (is_rate_limit or "500" in err_str) and attempt < 2:
                time.sleep(20 * (attempt + 1))
                continue
            return {"_erro": err_str}

    return {"_erro": "Máximo de tentativas atingido"}
