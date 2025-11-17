#!/usr/bin/env python
"""
Script para compilar traducciones de Flask-Babel
Ejecutar después de actualizar los archivos .po
"""
import os
import sys

# Cambiar al directorio del script
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

try:
    from babel.messages.pofile import read_po
    from babel.messages.mofile import write_mo
except ImportError:
    print("Error: Flask-Babel no esta instalado.")
    print("   Ejecuta: pip install Flask-Babel Babel")
    sys.exit(1)

def compile_translations():
    """Compila los archivos .po a .mo"""
    translations_dir = 'translations'
    
    if not os.path.exists(translations_dir):
        print(f"Error: No existe el directorio {translations_dir}")
        return False
    
    success = True
    for lang in ['es', 'en']:
        po_file = os.path.join(translations_dir, lang, 'LC_MESSAGES', 'messages.po')
        mo_file = os.path.join(translations_dir, lang, 'LC_MESSAGES', 'messages.mo')
        
        if not os.path.exists(po_file):
            print(f"Advertencia: No existe {po_file}")
            continue
        
        try:
            # Leer archivo .po
            with open(po_file, 'rb') as f:
                cat = read_po(f, locale=lang)
            
            # Escribir archivo .mo
            with open(mo_file, 'wb') as f:
                write_mo(f, cat)
            
            print(f"Compilado: {lang}/LC_MESSAGES/messages.mo")
        except Exception as e:
            print(f"Error al compilar {lang}: {e}")
            import traceback
            traceback.print_exc()
            success = False
    
    return success

if __name__ == '__main__':
    print("Compilando traducciones...")
    success = compile_translations()
    if success:
        print("\nProceso completado. Reinicia el servidor Flask para aplicar los cambios.")
    else:
        print("\nHubo errores durante la compilacion.")
        sys.exit(1)
