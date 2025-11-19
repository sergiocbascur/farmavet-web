#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para forzar la compilación de traducciones"""
import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from babel.messages.pofile import read_po
    from babel.messages.mofile import write_mo
    print("Usando babel.messages...")
except ImportError:
    print("Error: babel no está instalado. Instala con: pip install Babel")
    sys.exit(1)

def compile_translations():
    """Compila los archivos .po a .mo"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    translations_dir = os.path.join(base_dir, 'translations')
    
    if not os.path.exists(translations_dir):
        print(f"Error: No se encuentra el directorio {translations_dir}")
        return False
    
    compiled = 0
    for lang in ['en', 'es']:
        po_file = os.path.join(translations_dir, lang, 'LC_MESSAGES', 'messages.po')
        mo_file = os.path.join(translations_dir, lang, 'LC_MESSAGES', 'messages.mo')
        
        if not os.path.exists(po_file):
            print(f"Advertencia: No se encuentra {po_file}")
            continue
        
        try:
            # Leer el archivo .po
            with open(po_file, 'rb') as f:
                catalog_obj = read_po(f, locale=lang)
            
            # Escribir el archivo .mo
            with open(mo_file, 'wb') as f:
                write_mo(f, catalog_obj)
            
            print(f"[OK] Compilado: {lang}/LC_MESSAGES/messages.mo")
            compiled += 1
        except Exception as e:
            print(f"Error compilando {lang}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print(f"\n[OK] {compiled} archivo(s) compilado(s) exitosamente")
    return True

if __name__ == '__main__':
    success = compile_translations()
    sys.exit(0 if success else 1)

