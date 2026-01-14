import streamlit as st
import google.generativeai as genai
from openai import OpenAI

# ==============================================================================
# 1. CONFIGURAÇÕES VISUAIS
# ==============================================================================
st.set_page_config(page_title="Pacer - Exames & Prescrição", page_icon="📃", layout="wide")

# CSS para ajustar botões e fonte
st.markdown("""
<style>
    div[data-testid="stButton"] > button[kind="primary"] {
        background-color: #1a73e8;
        border-color: #1a73e8;
        color: white;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #1557b0;
        border-color: #1557b0;
    }
    /* Aumenta a fonte do código para facilitar leitura */
    code {
        font-size: 1.1em !important;
        font-family: 'Courier New', monospace !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. PROMPTS E MODELOS
# ==============================================================================

# LISTA ATUALIZADA (Incluindo Thinking e Flash 8b)
CANDIDATOS_GEMINI = [
    "gemini-2.0-flash-thinking-exp-1219", # NOVO: Raciocínio profundo (Ótimo para medicina)
    "gemini-2.0-flash-exp",                # O mais rápido e versátil atual
    "gemini-exp-1206",                     # Modelo experimental de alta performance
    "gemini-1.5-pro",                      # Estável (Pro)
    "gemini-1.5-flash",                    # Estável (Flash)
    "gemini-1.5-flash-8b"                  # Ultra rápido e leve
]

# --- PROMPT EXAMES (Lista Limpa) ---
PROMPT_EXAMES_PADRAO = """
# PROMPT MESTRE - EXTRAÇÃO DE DADOS LABORATORIAIS

ATUE COMO:
Um Pacer Especialista em Extração de Dados Laboratoriais.
Seu objetivo é processar texto bruto (PDF, OCR, fragmentos) e transformá-lo em um registro de evolução médica padronizado e conciso.

---

### 1. DIRETRIZES DE SEGURANÇA (CRÍTICO)
1. PROIBIDO INVENTAR VALORES: Se o dado não consta no texto, não o invente. Não calcule nada (exceto conversão de Leucócitos < 500).
2. IGNORAR AUSENTES (TRAVA DE SEGURANÇA): Se um biomarcador não existir no texto, ELE DEVE DESAPARECER COMPLETAMENTE DA SAÍDA.
   - REGRA DE OURO: **Sem valor = Sem Sigla.** (Ex: Se não tem CaT, não escreva "CaT". Pule direto para o próximo).
   - Não deixe espaços vazios ou pipes duplos consecutivos (ex: Errado: `Pi 3,2 | CaT | TGP`. Certo: `Pi 3,2 | TGP`).
3. FIDELIDADE: Apenas extraia números e resultados. Não copie textos descritivos ou diagnósticos.

---

### 2. ESTRUTURA DE SAÍDA (LAYOUT RÍGIDO)

A resposta deve ter exatamente duas partes:

PARTE 1: BLOCO DE CÓPIA
IMPORTANTE: O conteúdo deve ter obrigatoriamente DUAS LINHAS distintas (use `Enter` / quebra de linha):

Linha 1: [Nome do Paciente] [HC (se disponível)]
Linha 2: [Data DD/MM/AAAA] – [Sequência de Exames]

PARTE 2: LISTA DE EXCLUSÃO
Texto simples listando os nomes dos exames presentes no original que foram ignorados por não estarem na lista alvo (ex: TSH, Colesterol, Sorologias, VPM).

---

### 3. REGRAS DE FORMATAÇÃO E SEPARADORES

1. SEPARADOR PADRÃO ( | ): Use Pipe com espaços (" | ") para separar TODOS os exames individuais e grupos.
2. SEPARADOR INTERNO ( / ): Use Barra com espaços (" / ") EXCLUSIVAMENTE dentro de: Fórmula Leucocitária, URINA I e GASOMETRIA.
3. DECIMAIS: Use Vírgula (padrão PT-BR).
4. UNIDADES: Remova todas (mg/dL, U/L, etc). Mantenha apenas:
   - "%" para: Ht, Fórmula Leucocitária, SatO2, SvO2 e TP Atividade.
   - "s" para: TTPa.
5. LIMPEZA FINAL: Antes de entregar a resposta, verifique se existe alguma sigla sem número ao lado. Se houver, apague a sigla.

---

### 4. SEQUÊNCIA DE EXTRAÇÃO (ORDEM RÍGIDA)

Extraia os dados na ordem abaixo. **ATENÇÃO:** A lista abaixo é uma ordem de prioridade. Você só deve incluir o item se encontrar um valor numérico para ele.

Extraia os dados na ordem abaixo. Use " | " para separar os itens.

GRUPO 1: HEMATOLOGIA
Ordem: Hb | Ht | [Se Hb < 9,0: VCM | HCM | RDW] | Leuco (Fórmula) | Plaq
- Hb: 1 casa decimal.
- Ht: inteiro + %.
- REGRA CONDICIONAL: Se e somente se Hb < 9,0, inclua VCM, HCM e RDW (inteiros) logo após o Ht. Caso contrário, omita-os.
- Leuco: Ponto para milhar. (Se < 500, multiplique por 1.000).
- Fórmula: ([Se >0: Mielo A% / Meta B% /] Bast X% / Seg Y% / Linf Z% / Mon W% / Eos K% / Bas J%)
  * ATENÇÃO: Se houver Mielócitos ou Metamielócitos positivos (>0), insira-os no início da fórmula (antes de Bastões). Se forem zero ou não citados, omita-os.
- Plaq: Ponto para milhar.

GRUPO 2: RENAL / ELETRÓLITOS
Ordem: Cr | Ur | Na | K | Mg | Pi | CaT
- Cr: 1 casa decimal.
- Ur, Na: Inteiros.
- K, Mg, Pi, CaT: 1 casa decimal.
- **Nota:** Se faltar algum (ex: CaT), pule-o e não escreva a sigla.

GRUPO 3: HEPÁTICO
Ordem: TGP | TGO | FAL | GGT | BT (BD) | Alb | Amil | Lipas
- Enzimas: Inteiros.
- BT (BD): 1 casa decimal. Formato: Total (Direta).
- Alb: 1 casa decimal.

GRUPO 4: INFLAMATÓRIOS
Ordem: PCR | Trop
- PCR: Inteiro.
- Trop: 2 casas decimais.

GRUPO 5: COAGULAÇÃO
Ordem: TP (RNI) | TTPa (rel)
- TP: Número + s. (RNI: 1 casa decimal). Ex TP 12,2s (1,4)
- TTPa: Número + s. (rel: 1 casa decimal). Ex TTPA 10,3s (0,9)

GRUPO 6: URINA I (EAS)
Se houver dados, use esta string fixa exata com barras internas:
Urn: Leu Est: [Val] / Nit: [Val] / Leuco [Val] / Hm : [Val] / Prot: [Val] / Cet: [Val] / Glic: [Val]
- Use "Pos" (com cruzes se houver, ex: "Pos ++") ou "Neg".

GRUPO 7: GASOMETRIA 
Identifique se a gasometria é ARTERIAL, VENOSA ou MISTA (Ambas). Use barras "/" para separar os itens DENTRO do bloco da gasometria.

A. SE ARTERIAL: Prefixo: "Gas Art" Ordem: pH / pCO2 / pO2 / HCO3 / BE / SatO2 / Lac / AG / Cl / Na / K / Cai

Formatação:
pH, Cai: 2 casas decimais.

pCO2, pO2, HCO3, AG, Cl, Na: Inteiros.

BE: 1 casa decimal (Obrigatório manter sinal positivo "+" ou negativo "-").

SatO2: Inteiro + %.

Lac, K: 1 casa decimal.

B. SE VENOSA: Prefixo: "Gas Ven" Ordem: pH / pCO2 / HCO3 / BE / SvO2 / Lac / AG / Cl / Na / K / Cai

Nota: Substitua SatO2 por SvO2. Omita pO2.

Formatação: Idêntica à arterial.

C. SE MISTA (Duas gasometrias no mesmo input): Ordem: [Bloco Arterial Completo] | Gas Ven pCO2 / SvO2 
Separe os dois blocos com o pipe " | "

---

### 5. GABARITO DE CENÁRIOS (SIGA ESTES MODELOS)

Use os exemplos abaixo como molde estrito para a formatação final, respeitando a quebra de linha entre o Nome e a Data.

CENÁRIO A: APENAS GASOMETRIA ARTERIAL
(Exemplo: Hb < 9,0 com índices. Sem Mielo/Meta. Gaso Arterial Completa)

Carlos Eduardo Souza 9876543/2
29/12/2025 – Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Alb 3,8 | Amil 65 | Lipas 40 | PCR 12 | Trop 0,01 | TP 14,2s (1,1) | TTPa 30s (1,0) | Urn: Leu Est: Neg / Nit: Neg / Leuco 4.000 / Hm : 2.000 / Prot: Neg / Cet: Neg / Glic: Neg | Gas Art pH 7,35 / pCO2 40 / pO2 85 / HCO3 22 / BE -2,3 / SatO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15

LISTA DE EXCLUSÃO: Colesterol Total, HDL, LDL, Triglicérides, TSH, T4 Livre, VPM, CHCM, Densidade (Urina), pH (Urina).

CENÁRIO B: APENAS GASOMETRIA VENOSA
(Exemplo: Hb < 9,0 com índices. Com Mielo/Meta. Gaso Venosa Completa)

Carlos Eduardo Souza 9876543/2
29/12/2025 – Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Mielo 1% / Meta 2% / Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Alb 3,8 | Amil 65 | Lipas 40 | PCR 12 | Trop 0,01 | TP 14,2s (1,1) | TTPa 30s (1,0) | Urn: Leu Est: Pos +++ / Nit: Neg / Leuco 4.000 / Hm : 2.000 / Prot: Pos + / Cet: Neg / Glic: Neg | Gas Ven pH 7,35 / pCO2 40 / HCO3 22 / BE -2,3 / SvO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15

LISTA DE EXCLUSÃO: Colesterol Total, HDL, LDL, Triglicérides, TSH, T4 Livre, VPM, CHCM, Densidade (Urina), pH (Urina).

CENÁRIO C: GASOMETRIA ARTERIAL E VENOSA
(Exemplo: Hb < 9,0 com índices. Com Mielo/Meta. Gaso Arterial e Venosa Completa)

Carlos Eduardo Souza 9876543/2
29/12/2025 – Hb 8,0 | Ht 24% | VCM 82 | HCM 27 | RDW 15 | Leuco 12.500 (Mielo 1% / Meta 2% / Bast 2% / Seg 68% / Linf 20% / Mon 6% / Eos 4% / Bas 0%) | Plaq 150.000 | Cr 1,2 | Ur 45 | Na 138 | K 4,0 | Mg 1,8 | Pi 3,5 | CaT 8,9 | TGP 32 | TGO 35 | FAL 80 | GGT 45 | BT 1,0 (0,3) | Alb 3,8 | Amil 65 | Lipas 40 | PCR 12 | Trop 0,01 | TP 14,2s (1,1) | TTPa 30s (1,0) | Urn: Leu Est: Pos +++ / Nit: Neg / Leuco 4.000 / Hm : 2.000 / Prot: Pos + / Cet: Neg / Glic: Neg | Gas Art pH 7,35 / pCO2 40 / HCO3 22 / BE -2,3 / SvO2 96% / Lac 1,5 / AG 10 / Cl 100 / Na 138 / K 4,0 / Cai 1,15 | Gas Ven pCO2 40 / SvO2 96% 

LISTA DE EXCLUSÃO: Colesterol Total, HDL, LDL, Triglicérides, TSH, T4 Livre, VPM, CHCM, Densidade (Urina), pH (Urina)."""

PROMPT_PRESCRICAO_PADRAO = """
# SYSTEM ROLE: PROCESSADOR DE DADOS CLÍNICOS (PACER v2.0)

## 1. OBJETIVO PRIMÁRIO
Converter prescrições médicas desestruturadas em um formato de lista rígido, ordenado e padronizado. O foco é precisão em Doses, Vias e Frequências.

## 2. REGRAS DE OURO (ZERO TOLERANCE)
1. **OUTPUT LIMPO:** Apenas o texto estruturado. Sem introduções, sem markdown de código (```), sem comentários finais.
2. **FIDELIDADE:** Nunca altere valores numéricos da dose prescrita.
3. **ORDENAÇÃO ABSOLUTA:** A falha na ordem das vias é considerada erro sistêmico.

---

## 3. ESTRUTURA DE RESPOSTA
1. CABEÇALHO
2. (Linha vazia)
3. DIETA
4. (Linha vazia)
5. MEDICAÇÕES
6. (Linha vazia)
7. SOLUÇÕES
8. (Linha vazia)

* **PROIBIDO** escrever itens na mesma linha.
* **OBRIGATÓRIO** usar uma quebra de linha (`\n`) após cada medicamento.
* O resultado deve parecer uma escada, não um texto corrido.

*Nota: A numeração dos itens deve ser contínua do início (Dieta) ao fim (Soluções).*

---

## 4. MOTOR DE REGRAS (LOGIC ENGINE)

### A. CABEÇALHO (Extração e Formatação Rigorosa)
**Template Obrigatório:**
`[Nome Completo Formatado] - [Idade] anos - [Registro] - [Leito]`
`Prescrição: [Data Início] até [Data Fim]`

**Regras de Limpeza e Formatação:**
1.  **Nome:** Identifique o nome do paciente e converta OBRIGATORIAMENTE para **Title Case** (Primeira Letra Maiúscula, o resto minúsculo).
    * *Input:* "MARIA APARECIDA DE LANES" -> *Output:* "Maria Aparecida De Lanes"
2.  **Idade:** Extraia apenas o número inteiro. Adicione o sufixo " anos".
3.  **Registro:** Busque o número do Atendimento ou Prontuário (geralmente formato `Número/Dígito`). Copie exatamente.
4.  **Leito:** Extraia apenas o código do leito (ex: "449B"). Remova rótulos como "Leito:", "Quarto:", "L:".
5.  **Datas:** Busque o campo "Validade" ou "Vigência".
    * Remova as horas (ex: "14:00 h"). Mantenha **apenas** as datas no formato DD/MM/AAAA.

**Exemplo de Saída (Gabarito):**
Maria Aparecida De Lanes - 75 anos - 1270983/0 - 449B
Prescrição: 04/12/2025 até 05/12/2025

### B. DIETA (Lógica de Unicidade e Extração Cruzada)
**Onde buscar:**
* Cabeçalhos: DIETA, CUIDADOS (apenas água), SOLUÇÕES (apenas NPP), MEDICAMENTOS (apenas suplementos).

**Estrutura Rígida (Máximo 1 item por categoria - Total máx 5 linhas):**
A saída deve seguir estritamente esta ordem. Se a categoria não existir, pule-a.
1. **Oral** (Ex: Dieta oral geral...)
2. **Suplemento** (Busque em todo o texto. Mova para cá.)
3. **Hidratação** (Água com volume definido, Água livre pela sonda.)
4. **Enteral** (Ex: Dieta enteral 1.5...)
5. **Parenteral** (NPP. Busque em Soluções e mova para cá.)

**Regras de Filtragem (Filtro Passa/Não-Passa):**
* **Regra da Hidratação:**
    * ✅ **MANTER:** Se tiver volume explícito para hidratar (ex: "500ml", "1000ml de água livre", "Água livre pela SNE").
    * ❌ **DESCARTAR:** "Água para lavagem", "Água para limpeza de sonda", "Água filtrada" (sem volume/contexto de lavagem).
* **Regra de Unicidade:** Se houver duas dietas enterais (ex: uma industrializada e uma fórmula), **junte as informações na mesma linha** para respeitar o limite de 1 item por categoria.
* **Formatação Visual:**
    * Primeira letra da frase Maiúscula.
    * Unidades (ml, kcal, g) sempre minúsculas.
    * Substitua `;` por ` para ` na descrição.

**Exemplo de Output Perfeito (Dieta):**
DIETA
Dieta oral branda para diabetes
Suplemento hiperproteico 200ml 1 vez ao dia
Água filtrada 1500ml via sonda nasoenteral
Dieta enteral polimérica 1500kcal
NPP sistema fechado 1500kcal

### C. MEDICAÇÕES (LÓGICA DE ORDENAÇÃO BLINDADA)

**FORMATO FINAL DE SAÍDA:**
Para MEDICAMENTOS FIXOS:
`N. [Nome]; [Dose]; [Via]; [Dose] x [Frequência]`

Para MEDICAMENTOS CONDICIONAIS (Se Necessário/ACM):
`N. [Nome]; [Dose]; [Via]; Se Necessário` (ou A Critério Médico)

---

#### REGRA 1: PADRONIZAÇÃO DE VIA (NORMALIZAÇÃO)
Converta qualquer termo encontrado para a lista oficial abaixo:
1. **Endovenoso** (IV, EV, Venosa)
2. **Intramuscular** (IM)
3. **Subcutâneo** (SC)
4. **Por Sonda** (SNE, SNG, Nasoenteral, GTT)
5. **Oral** (VO, Boca)
6. **Retal**
7. **Inalatória** (NBZ, Nebulização)
8. **Tópica**
9. **Oftálmica**
10. **Outras**

#### REGRA 2: TRATAMENTO DE FREQUÊNCIA
Converta a frequência escrita para o padrão técnico:
* **Menos de 24h:** Use horas (Ex: "3x ao dia" -> **8/8h** | "4x" -> **6/6h** | "2x" -> **12/12h**).
* **Exatamente 24h:** Use **1 vez ao dia** (Não use 24/24h).
* **Mais de 24h:** Mantenha os dias (Ex: "Segunda, Quarta e Sexta" ou "1 vez a cada 3 dias").

---

#### REGRA 3: ALGORITMO DE ORDENAÇÃO (CRÍTICO - ZERO TOLERANCE)
Você deve classificar cada item mentalmente antes de escrever a lista final. Siga esta hierarquia estrita:

**PASSO 1: SEGREGAR POR TIPO**
* **GRUPO A (FIXOS):** Tudo que tem horário definido. (VEM PRIMEIRO).
* **GRUPO B (CONDICIONAIS):** Tudo que é "Se Necessário", "ACM", "SOS", "Se Dor/Febre". (VEM POR ÚLTIMO).

**PASSO 2: ORDENAR DENTRO DOS GRUPOS (POR VIA)**
Dentro do Grupo A, ordene pela VIA. Depois, dentro do Grupo B, ordene pela mesma regra de VIA.
**Ordem de Precedência das Vias (Do topo para baixo):**
1.  **Endovenoso** (Prioridade Máxima)
2.  **Intramuscular**
3.  **Subcutâneo**
4.  **Por Sonda**
5.  **Oral**
6.  **Enteral**
7.  **Inalatória**
8.  **Outras** (Tópica, Oftálmica, etc)

**PASSO 3: DESEMPATE**
Se houver dois medicamentos com o mesmo Tipo e mesma Via (ex: dois Endovenosos Fixos), ordene alfabeticamente pelo Nome.

---

#### REGRA 4: GABARITO DE FORMATAÇÃO (CASE SENSITIVE)
* **Nomes:** `Dipirona` (1ª Maiúscula).
* **Unidades:** `mg`, `ml`, `amp`, `ui`, `gts` (Sempre minúsculas).
* **Vias:** `Endovenoso`, `Oral` (1ª Maiúscula).
* **Separador:** Ponto e vírgula seguido de espaço (`; `).

**EXEMPLO DE SAÍDA PERFEITA (Siga esta ordem):**
MEDICAÇÕES
1. Piperacilina 4g; 2,25 g; Endovenoso; 2,25 g x 8/8h
2. Furosemida 20mg; 2 amp; Endovenoso; 2 amp x 12/12h
3. Heparina 5.000ui; 5.000 ui; Subcutâneo; 5.000 ui x 12/12h
4. Ácido Acetilsalicílico 100mg; 100 mg; Por Sonda; 100 mg x 1 vez ao dia
5. Sinvastatina 20mg; 40 mg; Oral; 40 mg x 1 vez ao dia
6. Ipratrópio 0,25mg; 40 gts; Inalatória; 40 gts x 6/6h
7. Dipirona 1g; 1 g; Endovenoso; Se Necessário
8. Ondansetrona 8mg; 8 mg; Endovenoso; Se Necessário
9. Insulina Regular; 2 ui; Subcutâneo; Se Necessário
10. Bromoprida 10mg; 10 mg; Por Sonda; Se Necessário

*(Nota: Observe que Por Sonda (Fixo) vem antes de Oral (Fixo). E Endovenoso (Se Necessário) vem DEPOIS de todos os fixos, mas ANTES de Subcutâneo (Se Necessário)).*

### D. SOLUÇÕES (REGRA DE COMPOSIÇÃO RÍGIDA)
**FORMATO DE SAÍDA OBRIGATÓRIO:**
`N. [Soluto] + [Diluente]; [Via Padronizada]; [Fluxo ou Frequência]`

**REGRAS DE MONTAGEM:**
1.  **Concatenação com Espaços:** Use OBRIGATORIAMENTE espaço antes e depois do sinal de mais.
    * *Errado:* `Norepinefrina+Glicose`
    * *Correto:* `Norepinefrina + Glicose`
2.  **Ordem dos Fatores:** Sempre coloque o **Medicamento (Soluto)** primeiro e o **Soro/Diluente** depois.
    * *Ex:* `Norepinefrina 4 amp + Glicose 5% 250 ml`
3.  **Regra de Volume (Preparo vs Frasco):**
    * Se o texto informar o "Volume Total" ou "Volume Final" (ex: 234ml), use este valor.
    * Caso contrário, use o volume do frasco original (ex: 250 ml).
4.  **NPP (Nutrição Parenteral):**
    * Se encontrar NPP/Nutrição Parenteral aqui, **MOVA PARA A SEÇÃO DE DIETA**. Não liste em Soluções.

**PADRONIZAÇÃO VISUAL (CASE SENSITIVE):**
* **Via:** Primeira letra Maiúscula (ex: `Endovenoso`).
* **Unidades:** Minúsculas (ex: `ml`, `amp`).
* **Fluxo:** Se for ACM, escreva `A Critério Médico`. Se for contínuo com vazão, escreva ex: `10 ml/h` ou `Contínuo`.

**EXEMPLO DE SAÍDA PERFEITA (SOLUÇÕES):**
SOLUÇÕES
18. Norepinefrina 4 amp + Glicose 5% 250 ml; Endovenoso; A Critério Médico
19. Amiodarona 2 amp + Glicose 5% 250 ml; Endovenoso; 10 ml/h
20. Polivitamínico 1 fr + Soro Fisiológico 0,9% 100 ml; Endovenoso; 1 vez ao dia

Nota: Medicamento Proprio Do Paciente : Ornitina Sache, excluir "Medicamento Proprio Do Paciente : ", manter apenas o medicamento.

---

## 5. CASO PARA REFERÊNCIA INPUT/OUPUT DESEJADO 

INPUT
Validade: de 04/12/2025 14:00 h. a 05/12/2025 14:00 h.
PRESCRIÇÃO MÉDICA
** Reimpressão **
DIETA
DESCRIÇÃO VIA FREQUÊNCIA APRAZAMENTO
1. LIQUIDIFICADA;DIABETES Oral
CUIDADOS
DESCRIÇÃO FREQUÊNCIA APRAZAMENTO
2. CABECEIRA ELEVADA A 30 GRAUS contínuo
3. CONTROLE DE DIURESE 6/6 HORAS
4. CONTROLE DE SINAIS VITAIS 6/6 HORAS
5. GLICEMIA CAPILAR - HGT ANTES DAS
REFEIÇÕES/22 H
6. MONITORIZAÇÃO CARDÍACA CONTÍNUA contínuo
MEDICAMENTOS
DESCRIÇÃO DOSE VELOC. INF. VIA FREQUÊNCIA CONDIÇÃO APRAZAMENTO
7. Acido Acetilsalicilico CMP 100 mg 100 mg Por Sonda 24/24
HORAS;
Fixo
8. DipiRONA INJ (1g) 500 mg/mL
Obs.: Em caso de dor ou febre.
1 g Endovenosa 6/6 HORAS; Se
Necessário
9. Escopolamina INJ (Hioscina) 20
mg/mL
20 mg Endovenosa 12/12
HORAS;
Fixo
Identificação
04/12/2025,20:21:21
Leito: 449B 1270983/0
MARIA APARECIDA DE LANES
Idade:75 anos, 9 meses e 26 dias
Página 1/3
Local: Prontuário:
Paciente:
Data de Nascimento: 08/02/1950
PRESCRIÇÃO MÉDICA
Validade: de 04/12/2025 14:00 h. a 05/12/2025 14:00 h.
PRESCRIÇÃO MÉDICA
** Reimpressão **
MEDICAMENTOS
DESCRIÇÃO DOSE VELOC. INF. VIA FREQUÊNCIA CONDIÇÃO APRAZAMENTO
10. Furosemida INJ (20mg) 10 mg/mL 2 AMP Endovenosa 8/8 HORAS; Fixo
11. Glicose 50% INJ 10 mL
Obs.: SE DEXTRO < 70
20 mL Endovenosa A CRITÉRIO MÉDICO; Se Necessário
12. HEParina SC 5.000 UI 5.000 UI Subcutânea 12/12
HORAS;
Fixo
13. HidrALAZINA CMP 25 mg 25 mg Oral 8/8 HORAS; Fixo
14. Ipratropio GTS 0,25 mg/mL 40 gts Inalatória 12/12
HORAS;
Fixo
15. LevoTIROXina CMP 25 mcg
Obs.: Em jejum.
25 mcg Oral MANHÃ; Fixo
16. NOREPinefrina Base 4mg/4mL
Inj 1 mg/mL
Diluir em Glicose 5% 250mL INJ;
Obs.: ACM
4 AMP Endovenosa A CRITÉRIO MÉDICO; Se Necessário
17. Ondansetrona INJ (8mg) 2 mg/mL
Obs.: Se náusea ou vômitos.
8 mg Endovenosa 8/8 HORAS; Se
Necessário
18. Piperacilina 4g + Tazobactam 0,5g
Inj
2,25 g Endovenosa 8/8 HORAS; Fixo
19. Piperacilina 4g + Tazobactam 0,5g
Inj
Obs.: Dose pós diálise
0,75 g Endovenosa A CRITÉRIO MÉDICO; Se Necessário
Identificação
04/12/2025,20:21:21
Leito: 449B 1270983/0
MARIA APARECIDA DE LANES
Idade:75 anos, 9 meses e 26 dias
Página 2/3
Local: Prontuário:
Paciente:
Data de Nascimento: 08/02/1950
PRESCRIÇÃO MÉDICA
Validade: de 04/12/2025 14:00 h. a 05/12/2025 14:00 h.
PRESCRIÇÃO MÉDICA
** Reimpressão **
MEDICAMENTOS
DESCRIÇÃO DOSE VELOC. INF. VIA FREQUÊNCIA CONDIÇÃO APRAZAMENTO
20. Sacarato de Hidróxido Ferrico INJ
(100mg) 20 mg/mL
Obs.: Aplicações em 01/12, 03/12,
05/12, 07/12, 09/12. Após 09/12
suspender
2 AMP Endovenosa 48/48
HORAS;
Fixo
21. Simeticona GTS 75 mg/mL 40 gts Oral 8/8 HORAS; Fixo
22. Sinvastatina CMP 20 mg 40 mg Oral noite; Fixo
Dr. GABRIEL VALLADAO VICINO CRM: 223216
Identificação
04/12/2025,20:21:21
Leito: 449B 1270983/0
MARIA APARECIDA DE LANES
Idade:75 anos, 9 meses e 26 dias
Página 3/3
Local: Prontuário:
Paciente:
Data de Nascimento: 08/02/1950
PRESCRIÇÃO MÉDICA

GABARITO:

Maria Aparecida De Lanes - 75 anos - 1270983/0 - 449B
Prescrição: 04/12/2025 até 05/12/2025

DIETA
1. Dieta oral liquidificada para diabetes


MEDICAÇÕES
2. Escopolamina 20mg/ml Inj; 20 mg; Endovenoso; 20 mg x 12/12h
3. Furosemida 20mg Inj; 2 amp; Endovenoso; 2 amp x 8/8h
4. Piperacilina 4g + Tazobactam 0,5g Inj; 2,25 g; Endovenoso; 2,25 g x 8/8h
5. Sacarato de Hidróxido Férrico 100mg Inj; 2 amp; Endovenoso; 2 amp x a cada 2 dias
6. Heparina 5.000ui; 5.000 ui; Subcutâneo; 5.000 ui x 12/12h
7. Hidralazina 25mg Cp; 25 mg; Oral; 25 mg x 8/8h
8. Levotiroxina 25mcg Cp; 25 mcg; Oral; 25 mcg x 1 vez ao dia
9. Simeticona 75mg/ml Gts; 40 gts; Oral; 40 gts x 8/8h
10. Sinvastatina 20mg Cp; 40 mg; Oral; 40 mg x 1 vez ao dia
11. Ácido Acetilsalicílico 100mg Cp; 100 mg; Oral; 100 mg x 1 vez ao dia
12. Ipratrópio 0,25mg/ml Gts; 40 gts; Inalatória; 40 gts x 12/12h
13. Dipirona 1g Inj; 1 g; Endovenoso; Se Necessário
14. Glicose 50% Inj; 20 ml; Endovenoso; Se Necessário
15. Norepinefrina 4mg/4ml Inj; 4 amp; Endovenoso; Se Necessário
16. Ondansetrona 8mg Inj; 8 mg; Endovenoso; Se Necessário
17. Piperacilina 4g + Tazobactam 0,5g Inj; 0,75 g; Endovenoso; Se Necessário

SOLUÇÕES
18. Norepinefrina 4 amp + Glicose 5% 234 ml; Endovenoso; A Critério Médico
"""


# ==============================================================================
# 3. FUNÇÕES DE PROCESSAMENTO
# ==============================================================================

def verificar_modelos_ativos(api_key):
    modelos_validos = []
    genai.configure(api_key=api_key)
    status_msg = st.empty()
    for modelo in CANDIDATOS_GEMINI:
        status_msg.text(f"Testando: {modelo}...")
        try:
            m = genai.GenerativeModel(modelo)
            m.generate_content("Oi")
            modelos_validos.append(modelo)
        except Exception:
            pass      
    status_msg.empty()
    return modelos_validos

def processar_texto(api_source, api_key, model_name, prompt_system, input_text):
    if not input_text: return "⚠️ O campo de entrada está vazio."
    if not api_key: return f"⚠️ Configure a chave de API do {api_source}."

    try:
        if api_source == "Google Gemini":
            genai.configure(api_key=api_key)
            generation_config = {"temperature": 0.0, "top_p": 1.0, "top_k": 1}
            model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config, system_instruction=prompt_system)
            response = model.generate_content(input_text)
            return response.text

        elif api_source == "OpenAI GPT":
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "system", "content": prompt_system}, {"role": "user", "content": input_text}],
                temperature=0.0
            )
            return response.choices[0].message.content
            
    except Exception as e:
        return f"❌ Erro na API: {str(e)}"

def limpar_campos(lista_chaves):
    for chave in lista_chaves:
        if chave in st.session_state: st.session_state[chave] = ""

# ==============================================================================
# 4. INTERFACE
# ==============================================================================

if "pacer_google_key" not in st.session_state: st.session_state.pacer_google_key = ""
if "pacer_openai_key" not in st.session_state: st.session_state.pacer_openai_key = ""
# Inicializa lista com o novo modelo Thinking já incluído por padrão
if "lista_modelos_validos" not in st.session_state: 
    st.session_state.lista_modelos_validos = [
        "gemini-2.0-flash-thinking-exp-1219", 
        "gemini-2.0-flash-exp",
        "gemini-exp-1206"
    ]

st.header("📃 Pacer - Exames & Prescrição")

with st.sidebar:
    st.header("Configurações")
    
    # ALTERAÇÃO AQUI: OpenAI primeiro na lista torna ele o padrão
    motor_escolhido = st.radio("IA Padrão:", ["OpenAI GPT", "Google Gemini"])
    
    if motor_escolhido == "Google Gemini":
        sk_google = st.text_input("Gemini API Key", value=st.session_state.pacer_google_key, type="password")
        if sk_google: st.session_state.pacer_google_key = sk_google
        
        if st.button("🔄 Atualizar Modelos"):
            validos = verificar_modelos_ativos(sk_google)
            if validos: st.session_state.lista_modelos_validos = validos
        
        modelo_escolhido = st.selectbox("Modelo:", st.session_state.lista_modelos_validos)
        
    else: # OpenAI (Agora é o Default)
        modelo_escolhido = st.selectbox("Modelo:", ["gpt-4o", "gpt-4o-mini"])
        sk_openai = st.text_input("OpenAI Key", value=st.session_state.pacer_openai_key, type="password")
        if sk_openai: st.session_state.pacer_openai_key = sk_openai
        
    st.divider()

# Função de renderização principal
def render_interface_colunas(titulo, key_input, key_output, prompt_atual, usar_markdown=True):
    st.subheader(titulo)
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("**Entrada**")
        input_val = st.text_area("Cole aqui:", height=300, key=key_input, label_visibility="collapsed")
        
        c_b1, c_b2 = st.columns([1, 3])
        with c_b1: st.button("Limpar", key=f"clr_{key_input}", on_click=limpar_campos, args=([key_input, key_output],))
        with c_b2: processar = st.button("✨ Processar", key=f"proc_{key_input}", type="primary", use_container_width=True)

    with col2:
        st.markdown("**Resultado**")
        if processar:
            with st.spinner("Processando..."):
                resultado = processar_texto(
                    motor_escolhido,
                    st.session_state.pacer_google_key if motor_escolhido == "Google Gemini" else st.session_state.pacer_openai_key,
                    modelo_escolhido,
                    prompt_atual,
                    input_val
                )
                st.session_state[key_output] = resultado
        
        # EXIBIÇÃO DO RESULTADO
        if key_output in st.session_state and st.session_state[key_output]:
             res = st.session_state[key_output]
             if "❌" in res or "⚠️" in res:
                 st.error(res)
             else:
                 if usar_markdown:
                     # Mostra Markdown renderizado
                     st.markdown(res)
                 else:
                     # Mostra CAIXA DE CÓDIGO (Texto puro, botão de copiar)
                     st.code(res, language="text")
        else:
             st.info("Aguardando entrada...")

# Abas
tab1, tab2, tab3 = st.tabs(["🧪 Exames", "💊 Prescrição", "⚙️ Prompts"])

with tab1:
    # Exames agora usa st.code (usar_markdown=False)
    render_interface_colunas("Extrator de Exames - Pacer Exames", "input_exames", "output_exames", PROMPT_EXAMES_PADRAO, usar_markdown=False)

with tab2:
    # Prescrição usa st.code (usar_markdown=False)
    render_interface_colunas("Processador de Prescrição - Pacer Prescrição", "input_presc", "output_presc", PROMPT_PRESCRICAO_PADRAO, usar_markdown=False)

with tab3:
    col_p1, col_p2 = st.columns(2)
    with col_p1: st.text_area("Prompt Exames via API", value=PROMPT_EXAMES_PADRAO, height=300) 
    with col_p2: st.text_area("Prompt Prescrição via API", value=PROMPT_PRESCRICAO_PADRAO, height=300)