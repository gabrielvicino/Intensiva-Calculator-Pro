import google.generativeai as genai
from openai import OpenAI
import json
import streamlit as st

def run_agent(prompt, provider, key):
    try:
        if "Google" in provider:
            model_name = 'gemini-1.5-flash' 
            try: 
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
            except Exception as e:
                return None
            
            txt = resp.text.replace("```json", "").replace("```", "").strip()
            return json.loads(txt)

        elif "OpenAI" in provider:
            client = OpenAI(api_key=key)
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"Erro na IA: {e}")
        return {}

def agente_admissao(texto_prontuario, provider, key, escopos=None):
    if not escopos:
        escopos = ["identidade", "hd", "comorbidades", "laboratoriais", "condutas"]

    prompt_base = f"""
    Você é um assistente médico especialista em Terapia Intensiva.
    Analise o texto de evolução clínica abaixo e extraia estruturadamente APENAS os dados solicitados.
    
    TEXTO ORIGINAL:
    \"\"\"
    {texto_prontuario}
    \"\"\"
    
    INSTRUÇÕES:
    1. Responda ESTRITAMENTE em formato JSON.
    2. Se um dado não for encontrado, mantenha null ou string vazia.
    3. Normalizar datas para DD/MM/AAAA.
    
    --- FILTROS DE EXTRAÇÃO ATIVOS ---
    Extraia APENAS: {', '.join([e.upper() for e in escopos])}
    
    --- ESQUEMA JSON ALVO ---
    {{
    """
    
    prompt_json_parts = []
    
    if "identidade" in escopos:
        prompt_json_parts.append("""
        "identidade": {
            "nome": "string", "idade": int, "sexo": "Masculino/Feminino",
            "leito": "string", "origem": "string", "prontuario": "string",
            "datas": {"hospital": "DD/MM/AAAA", "uti": "DD/MM/AAAA"}
        }""")
        
    if "hd" in escopos:
        prompt_json_parts.append("""
        "hd": { "principal": "Resumo do diagnóstico", "status": "Estável/Melhora/Piora" }""")

    if "comorbidades" in escopos:
        prompt_json_parts.append('"comorbidades": "lista de comorbidades"')
        
    if "muc" in escopos:
        prompt_json_parts.append('"muc": "alergias ou mucosas"')

    if "hmpa" in escopos:
        prompt_json_parts.append('"hmpa": "HMPA resumido"')

    if "dispositivos" in escopos:
        prompt_json_parts.append("""
        "dispositivos": { "vm_modo": "string", "vm_parametros": "string", "sonda": "string", "acesso": "string" }""")

    if "culturas" in escopos:
        prompt_json_parts.append('"culturas": "resultados de culturas"')

    if "antibioticos" in escopos:
        prompt_json_parts.append('"antibioticos": "lista de ATB com dia"')
        
    if "laboratoriais" in escopos:
        prompt_json_parts.append('"laboratoriais": "resumo dos exames"')

    if "evolucao_clinica" in escopos:
        prompt_json_parts.append('"evolucao_clinica": "resumo sucinto"')
    
    if "condutas" in escopos:
        prompt_json_parts.append('"condutas": "plano terapêutico"')
        
    if "sistemas" in escopos:
        prompt_json_parts.append('"sistemas": "alterações no exame físico"')

    if "identidade" in escopos: 
        prompt_json_parts.append(""" "scores": { "saps3": int, "sofa_adm": int, "sofa_atual": int } """)

    prompt_final = prompt_base + ",\n".join(prompt_json_parts) + "\n}"

    return run_agent(prompt_final, provider, key)
