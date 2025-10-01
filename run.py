#!/usr/bin/env python3
"""
Script para executar o Monitor de Processos Químicos
"""

import os
import sys
import webbrowser
import time
from threading import Timer

def open_browser():
    """Abre o navegador após 2 segundos"""
    webbrowser.open('http://127.0.0.1:5000')

def main():
    """Função principal"""
    print("=" * 60)
    print("🧪 MONITOR DE PROCESSOS QUÍMICOS")
    print("=" * 60)
    print("")
    print("Iniciando aplicação Dash...")
    print("Servidor: http://127.0.0.1:5000")
    print("")
    print("Funcionalidades disponíveis:")
    print("• Dashboard em tempo real")
    print("• Entrada de dados manual e upload CSV")
    print("• Análise histórica avançada")
    print("• Sistema de alertas configurável") 
    print("• Exportação de dados e relatórios")
    print("• Simulação de dados de processo")
    print("")
    print("Para parar o servidor, pressione Ctrl+C")
    print("=" * 60)
    print("")
    
    # Programar abertura do navegador
    Timer(2.0, open_browser).start()
    
    # Importar e executar o app
    try:
        import app
        app.app.run(debug=True, host='127.0.0.1', port=5000)
    except KeyboardInterrupt:
        print("\n\n🛑 Aplicação interrompida pelo usuário")
        print("Obrigado por usar o Monitor de Processos Químicos!")
    except Exception as e:
        print(f"\n❌ Erro ao executar a aplicação: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
