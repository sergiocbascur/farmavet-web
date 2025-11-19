#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la configuración SMTP
Ejecutar en el VPS: python3 diagnosticar_smtp.py
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_env_vars():
    """Verifica que las variables de entorno estén configuradas"""
    print_section("1. Verificando Variables de Entorno")
    
    required_vars = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD']
    optional_vars = ['SMTP_FROM']
    
    all_present = True
    for var in required_vars:
        value = os.environ.get(var, '')
        if value:
            # Ocultar contraseña
            if 'PASSWORD' in var:
                display_value = '*' * min(len(value), 16) + ('...' if len(value) > 16 else '')
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: NO CONFIGURADA")
            all_present = False
    
    for var in optional_vars:
        value = os.environ.get(var, '')
        if value:
            print(f"  ✅ {var}: {value}")
        else:
            print(f"  ⚠️  {var}: No configurada (usará SMTP_USER)")
    
    return all_present

def test_smtp_connection():
    """Prueba la conexión SMTP"""
    print_section("2. Probando Conexión SMTP")
    
    smtp_host = os.environ.get('SMTP_HOST', '')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    
    if not smtp_host or not smtp_user or not smtp_password:
        print("  ❌ No se puede probar: faltan variables de entorno")
        return False
    
    try:
        print(f"  Conectando a {smtp_host}:{smtp_port}...")
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        print("  ✅ Conexión establecida")
        
        print("  Iniciando TLS...")
        server.starttls()
        print("  ✅ TLS iniciado")
        
        print(f"  Autenticando con usuario: {smtp_user}...")
        server.login(smtp_user, smtp_password)
        print("  ✅ Autenticación exitosa")
        
        server.quit()
        print("\n  ✅✅✅ CONEXIÓN SMTP EXITOSA ✅✅✅")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"  ❌ ERROR DE AUTENTICACIÓN: {str(e)}")
        print("\n  💡 Posibles causas:")
        print("     - Usuario o contraseña incorrectos")
        print("     - Para Gmail: ¿Estás usando App Password? (no la contraseña normal)")
        print("     - App Password puede haber expirado o sido revocada")
        print("     - Verifica que la verificación en 2 pasos esté activada")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"  ❌ ERROR DE CONEXIÓN: {str(e)}")
        print("\n  💡 Posibles causas:")
        print("     - Host o puerto incorrectos")
        print("     - Firewall bloqueando la conexión")
        print("     - Servidor SMTP no disponible")
        return False
        
    except smtplib.SMTPException as e:
        print(f"  ❌ ERROR SMTP: {str(e)}")
        return False
        
    except Exception as e:
        print(f"  ❌ ERROR INESPERADO: {str(e)}")
        return False

def test_email_send():
    """Prueba el envío de un correo de prueba"""
    print_section("3. Probando Envío de Correo")
    
    smtp_host = os.environ.get('SMTP_HOST', '')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    smtp_from = os.environ.get('SMTP_FROM', smtp_user)
    
    # Preguntar email de destino
    test_email = input("\n  Ingresa un email de destino para la prueba (o Enter para omitir): ").strip()
    
    if not test_email:
        print("  ⚠️  Prueba de envío omitida")
        return
    
    if '@' not in test_email:
        print("  ❌ Email inválido")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_from
        msg['To'] = test_email
        msg['Subject'] = 'Prueba SMTP - FARMAVET'
        
        body = """
Este es un correo de prueba desde el sistema FARMAVET.

Si recibes este correo, la configuración SMTP está funcionando correctamente.

---
Enviado automáticamente desde el script de diagnóstico.
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        print(f"  Enviando correo de prueba a {test_email}...")
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"  ✅ Correo enviado exitosamente a {test_email}")
        print("  📧 Revisa tu bandeja de entrada (y spam) en unos minutos")
        
    except Exception as e:
        print(f"  ❌ Error al enviar correo: {str(e)}")

def show_recommendations():
    """Muestra recomendaciones según el problema"""
    print_section("4. Recomendaciones")
    
    smtp_host = os.environ.get('SMTP_HOST', '')
    
    if 'gmail' in smtp_host.lower():
        print("  📧 Configuración para Gmail:")
        print("     1. Activa la verificación en 2 pasos en tu cuenta Google")
        print("     2. Ve a: https://myaccount.google.com/apppasswords")
        print("     3. Genera una 'App Password' para 'Mail'")
        print("     4. Usa esa contraseña (16 caracteres) como SMTP_PASSWORD")
        print("     5. NO uses tu contraseña normal de Gmail")
        
    elif 'uchile' in smtp_host.lower():
        print("  📧 Configuración para correo institucional:")
        print("     1. Verifica con TI de la Universidad las credenciales correctas")
        print("     2. Asegúrate de usar el puerto correcto (587 o 465)")
        print("     3. Verifica que no haya restricciones de firewall")
        
    print("\n  🔧 Para actualizar la configuración:")
    print("     1. Edita: sudo nano /etc/systemd/system/farmavet-web.service")
    print("     2. Agrega/modifica las líneas Environment=\"SMTP_...\"")
    print("     3. Ejecuta: sudo systemctl daemon-reload")
    print("     4. Reinicia: sudo systemctl restart farmavet-web")
    print("     5. O usa el script: sudo ./configurar_correo.sh")

def main():
    print("\n" + "="*60)
    print("  DIAGNÓSTICO DE CONFIGURACIÓN SMTP - FARMAVET")
    print("="*60)
    
    # Verificar variables de entorno
    env_ok = check_env_vars()
    
    if not env_ok:
        print("\n  ❌ Faltan variables de entorno. Configúralas primero.")
        show_recommendations()
        return
    
    # Probar conexión
    connection_ok = test_smtp_connection()
    
    if connection_ok:
        # Si la conexión funciona, probar envío
        test_email_send()
    else:
        show_recommendations()
    
    print("\n" + "="*60)
    print("  DIAGNÓSTICO COMPLETADO")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()

