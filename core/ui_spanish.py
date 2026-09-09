"""Spanish presentation for known system notices; user text is preserved."""
PHRASES = {
    "Interrupted — listening...": "Interrumpido — escuchando...",
    "Shutdown requested.": "Se solicitó cerrar el asistente.",
    "Briefing phase 1 (greeting) sent.": "Saludo inicial enviado.",
    "Briefing phase 2 (news) sent.": "Resumen de noticias enviado.",
    "Briefing phase 2 failed:": "Falló el resumen de noticias:",
    "News fetch timed out/failed:": "No se pudieron obtener las noticias:",
    "News unavailable — backend returned:": "Noticias no disponibles — respuesta del servicio:",
    "Monitor alert sent.": "Alerta del monitor enviada.",
    "Proactive check-in.": "Aviso proactivo.",
    "Phone connected via Remote Dashboard.": "Celular conectado mediante el panel remoto.",
    "Reconnected — conversation restored.": "Reconectado — conversación restaurada.",
    "JARVIS online.": "JARVIS en línea.",
    "Could not restore the conversation — starting fresh.": "No se pudo restaurar la conversación — iniciando una nueva.",
    "Advanced audio features unavailable — reconnecting without them.": "Funciones avanzadas de audio no disponibles — reconectando con audio básico.",
    "API key invalid — please re-enter your key.": "Clave API no válida — vuelve a ingresarla.",
    "Dashboard unavailable.": "Panel remoto no disponible.",
    "Run: pip install": "Instala las dependencias: pip install",
    "Applying ": "Aplicando ", " — reconnecting": " — reconectando",
    " (starting a fresh conversation)": " (iniciando una conversación nueva)",
    "Microphone '": "Micrófono '", "Speaker '": "Altavoz '",
    " unavailable — using system default.": " no disponible — usando el predeterminado del sistema.",
}

def translate_log(text):
    if text.startswith("You:"):
        return "Tú:" + text[4:]
    prefixes = {"SYS:": "SISTEMA:", "ERR:": "ERROR:", "NET:": "RED:", "FILE:": "ARCHIVO:"}
    for prefix, spanish in prefixes.items():
        if text.startswith(prefix):
            body = text[len(prefix):]
            for source, target in PHRASES.items():
                body = body.replace(source, target)
            return spanish + body
    return text
