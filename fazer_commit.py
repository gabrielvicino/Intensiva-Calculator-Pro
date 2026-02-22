#!/usr/bin/env python3
"""
Script para fazer commit e push - contorna o erro do exclude no OneDrive.
Execute: python fazer_commit.py
"""
import os
import subprocess
import sys

# Diretório do script = pasta do projeto
PASTA = os.path.dirname(os.path.abspath(__file__))
GIT = r"C:\Program Files\Git\bin\git.exe"

def run(cmd, cwd=PASTA):
    """Executa comando e retorna (sucesso, saida)"""
    args = [GIT] + (cmd if isinstance(cmd, list) else cmd.split())
    try:
        r = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, encoding="utf-8"
        )
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode == 0, out.strip()
    except Exception as e:
        return False, str(e)

def main():
    os.chdir(PASTA)
    print(f"Pasta: {PASTA}\n")

    # 1. Corrigir exclude
    exclude_path = os.path.join(PASTA, ".git", "info", "exclude")
    try:
        with open(exclude_path, "w", encoding="ascii") as f:
            f.write("#\n")
        print("[OK] Arquivo exclude corrigido")
    except Exception as e:
        print(f"[ERRO] Nao foi possivel corrigir exclude: {e}")
        input("Pressione Enter para sair...")
        sys.exit(1)

    # 2. Git add
    ok, out = run("add -A")
    if not ok and "exclude" in out.lower():
        print("[ERRO] O erro do exclude persiste. Tente mover o projeto para C:\\Projetos")
        print("       (arraste a pasta para fora do OneDrive)")
        input("Pressione Enter para sair...")
        sys.exit(1)
    elif not ok:
        print(f"[AVISO] git add: {out}")
    else:
        print("[OK] git add")

    # 3. Git status
    ok, out = run("status")
    print(out)

    # 4. Verificar se tem algo para commitar
    ok, out = run("diff --cached --name-only")
    if not out.strip():
        print("\nNenhum arquivo para commitar. Nada a fazer.")
        input("Pressione Enter para sair...")
        return

    # 5. Configurar user se necessario
    ok, _ = run("config user.email")
    if not ok or not _.strip():
        email = input("Digite seu email do GitHub: ").strip()
        if email:
            run(["config", "user.email", email])
    ok, _ = run("config user.name")
    if not ok or not _.strip():
        nome = input("Digite seu nome: ").strip()
        if nome:
            run(["config", "user.name", nome])

    # 6. Commit
    ok, out = run(["commit", "-m", "Atualizacoes: remover PCT, adicionar UI na insulinoterapia"])
    if not ok:
        print(f"[ERRO] git commit: {out}")
        input("Pressione Enter para sair...")
        sys.exit(1)
    print("[OK] git commit")

    # 7. Branch main
    run("branch -M main")

    # 8. Push
    ok, out = run("push -u origin main")
    if not ok:
        print(f"[ERRO] git push: {out}")
        print("\nSe for autenticacao, configure token ou SSH no GitHub.")
    else:
        print("[OK] git push - enviado ao GitHub!")

    print()
    input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()
