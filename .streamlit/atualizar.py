import os
import time
from datetime import datetime

def atualizar_site():
    print("=========================================")
    print("🚀 INICIANDO ATUALIZAÇÃO DO SITE")
    print("=========================================")

    # 1. Adicionar todos os arquivos modificados
    print("\n📦 1. Preparando arquivos (git add)...")
    os.system("git add .")

    # 2. Perguntar mensagem ou usar data automática
    agora = datetime.now().strftime("%d/%m/%Y às %H:%M")
    mensagem = input(f"📝 Descreva a mudança (ou dê Enter para usar a data): ")
    
    if not mensagem:
        mensagem = f"Atualização automática em {agora}"
    
    print(f"\n📸 2. Salvando versão: '{mensagem}'...")
    os.system(f'git commit -m "{mensagem}"')

    # 3. Enviar para a nuvem
    print("\n☁️  3. Enviando para o GitHub (git push)...")
    
    # O comando abaixo tenta enviar. Se o OneDrive reclamar, ele ignora e segue.
    resultado = os.system("git push")

    print("\n=========================================")
    if resultado == 0:
        print("✅ SUCESSO! O site será atualizado em 2 minutos.")
    else:
        print("⚠️  AVISO: O OneDrive pode ter reclamado, mas verifique o GitHub.")
        print("Se aparecer 'Writing objects: 100%', deu tudo certo.")
    print("=========================================")

if __name__ == "__main__":
    atualizar_site()
    # Espera 10 segundos antes de fechar para você ler o resultado
    time.sleep(10)