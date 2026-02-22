import google.generativeai as genai
from openai import OpenAI
import json
import streamlit as st

def run_agent(prompt, provider, key, model_name=None):
    try:
        if "Google" in provider:
            # Se não especificou modelo, extrai do provider ou usa padrão
            if not model_name:
                # Verificar se o provider contém o nome do modelo (ex: "Google Gemini gemini-2.5-flash")
                if "gemini-" in provider:
                    # Extrair o nome do modelo do provider
                    parts = provider.split()
                    for part in parts:
                        if part.startswith("gemini-"):
                            model_name = part
                            break
                # Se ainda não tem modelo, tenta detectar pela nomenclatura antiga
                elif "2.5 Flash" in provider and "thinking" not in provider.lower():
                    model_name = 'gemini-2.5-flash'
                elif "2.5 Pro" in provider:
                    model_name = 'gemini-2.5-pro'
                elif "1.5 Pro" in provider:
                    model_name = 'gemini-1.5-pro-002'
                elif "Thinking" in provider or "thinking" in provider.lower():
                    model_name = 'gemini-2.5-flash-thinking'
                else:
                    model_name = 'gemini-2.5-flash'  # Padrão: Gemini 2.5 Flash
            
            try: 
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
            except Exception as e:
                return None
            
            txt = resp.text.replace("```json", "").replace("```", "").strip()
            return json.loads(txt)

        elif "OpenAI" in provider or "GPT" in provider:
            # Extrair o nome do modelo se vier no provider (ex: "OpenAI GPT gpt-4o-mini")
            openai_model = "gpt-4o"  # Padrão
            if "gpt-" in provider.lower():
                parts = provider.split()
                for part in parts:
                    if part.lower().startswith("gpt-"):
                        openai_model = part.lower()
                        break
            elif model_name:
                openai_model = model_name
            
            client = OpenAI(api_key=key)
            resp = client.chat.completions.create(
                model=openai_model,
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
