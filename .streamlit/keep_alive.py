"""
🔄 Keep Alive - Mantém Streamlit Ativo
Adiciona funcionalidade de heartbeat para prevenir timeout de sessão.
"""
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

def inject_keep_alive():
    """
    Injeta JavaScript para manter a sessão ativa com pings periódicos.
    
    Características:
    - Ping automático a cada 30 segundos
    - Invisível para o usuário
    - Não afeta performance
    """
    
    components.html(
        """
        <script>
        // Keep-Alive: Mantém sessão Streamlit ativa
        console.log('🔄 Keep-Alive: Iniciado');
        
        let pingCount = 0;
        const PING_INTERVAL = 30000; // 30 segundos
        
        function sendPing() {
            fetch(window.location.href, {
                method: 'HEAD',
                cache: 'no-cache'
            })
            .then(() => {
                pingCount++;
                console.log(`✅ Keep-Alive Ping #${pingCount} - ${new Date().toLocaleTimeString()}`);
            })
            .catch((error) => {
                console.warn('⚠️ Keep-Alive Ping falhou:', error);
            });
        }
        
        // Primeiro ping após 5 segundos
        setTimeout(sendPing, 5000);
        
        // Pings periódicos
        setInterval(sendPing, PING_INTERVAL);
        
        // Log de inicialização
        console.log(`⏰ Keep-Alive: Configurado para ping a cada ${PING_INTERVAL/1000}s`);
        </script>
        """,
        height=0,
        width=0
    )

def session_heartbeat():
    """
    Mantém variável de sessão atualizada para prevenir expiração.
    Chame esta função periodicamente em seus callbacks.
    """
    if 'last_heartbeat' not in st.session_state:
        st.session_state.last_heartbeat = datetime.now()
    else:
        st.session_state.last_heartbeat = datetime.now()
    
    # Log opcional (apenas para debug)
    # print(f"💓 Heartbeat: {st.session_state.last_heartbeat.strftime('%H:%M:%S')}")

def show_connection_status():
    """
    Mostra status de conexão discreto na sidebar (opcional).
    Use apenas para debug ou monitoramento.
    """
    if 'last_heartbeat' in st.session_state:
        elapsed = (datetime.now() - st.session_state.last_heartbeat).seconds
        
        if elapsed < 60:
            status = "🟢 Ativo"
        elif elapsed < 300:
            status = "🟡 Inativo"
        else:
            status = "🔴 Dormindo"
        
        with st.sidebar:
            st.caption(f"Conexão: {status}")

# Função principal para usar no app.py
def enable_keep_alive(show_status=False):
    """
    Habilita keep-alive completo.
    
    Args:
        show_status: Se True, mostra status de conexão na sidebar
    
    Uso:
        # No início do app.py
        from .streamlit.keep_alive import enable_keep_alive
        enable_keep_alive()
    """
    inject_keep_alive()
    session_heartbeat()
    
    if show_status:
        show_connection_status()
