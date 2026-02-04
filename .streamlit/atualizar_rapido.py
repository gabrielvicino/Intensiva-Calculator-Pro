#!/usr/bin/env python3
"""
🚀 ATUALIZAÇÃO RÁPIDA DO GITHUB
Upload otimizado em 3 comandos
"""
import os
import subprocess
from datetime import datetime

def run_fast(cmd):
    """Executa comando e retorna True se sucesso"""
    return subprocess.run(cmd, shell=True, capture_output=True).returncode == 0

def atualizar_rapido():
    print("🚀 Upload Rápido - GitHub")
    print("=" * 40)
    
    # Mensagem
    msg = input("📝 Mudança (Enter = auto): ").strip()
    if not msg:
        msg = f"Update {datetime.now().strftime('%d/%m %H:%M')}"
    
    # 3 comandos em sequência rápida
    print("\n⚡ Processando...")
    
    if not run_fast("git add ."):
        print("❌ Erro no add")
        return
    
    if not run_fast(f'git commit -m "{msg}"'):
        print("⚠️  Nada para commitar")
        return
    
    if not run_fast("git push origin main"):
        print("❌ Erro no push - Veja detalhes acima")
        return
    
    print("\n✅ DONE! GitHub atualizado.")
    print("=" * 40)

if __name__ == "__main__":
    atualizar_rapido()
