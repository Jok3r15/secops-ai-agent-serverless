import json
import boto3
import re
import os

# Patrón RegEx para parsear el formato estándar de nuestro laboratorio
LOG_PATTERN = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) '
    r'IP (?P<ip>[\d\.]+) '
    r'HTTP (?P<status>\d{3}) '
    r'(?P<path>\/\S*)'
)

def lambda_handler(event, context):
    print("🤖 [SecOps Agent] Inicializando análisis de trazas...")
    
    s3_client = boto3.client('s3')
    sns_client = boto3.client('sns')
    
    # Leer el ARN de SNS desde las variables de entorno inyectadas por Terraform
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    
    # Extraer información del evento de S3
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    print(f"📁 Destino detectado -> Bucket: {bucket} | Archivo: {key}")
    
    try:
        # Descargar el archivo desde S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        log_content = response['Body'].read().decode('ascii')
        
        lineas_procesadas = 0
        alertas_detectadas = []
        
        print("🕵️‍♂️ [Análisis] Escaneando líneas en busca de patrones maliciosos...")
        
        for line in log_content.strip().split('\n'):
            if not line.strip():
                continue
                
            lineas_procesadas += 1
            match = LOG_PATTERN.match(line.strip())
            
            if match:
                data = match.groupdict()
                status = data['status']
                path = data['path']
                ip = data['ip']
                
                # Regla 1: Escaneo de directorios
                if "admin" in path or "config" in path or "phpmyadmin" in path:
                    print(f"⚠️ [ALERTA] Intento de escaneo de directorios por IP {ip} en ruta: {path}")
                    alertas_detectadas.append({
                        "tipo": "Directory Scanning / Unauthorized Access",
                        "ip": ip,
                        "ruta": path,
                        "status": status
                    })
                
                # Regla 2: Accesos denegados anómalos
                elif status == "403":
                    print(f"⚠️ [ALERTA] Acceso denegado detectado para IP {ip} en ruta: {path}")
                    alertas_detectadas.append({
                        "tipo": "Anomalous 403 Forbidden",
                        "ip": ip,
                        "ruta": path,
                        "status": status
                    })
        
        # --- VEREDICTO FINAL Y PLAN DE ALERTA ---
        print("\n=== 📊 REPORTE DE EVALUACIÓN DE SECOPS ===")
        print(f"Total líneas analizadas: {lineas_procesadas}")
        print(f"Total amenazas identificadas: {len(alertas_detectadas)}")
        
        if len(alertas_detectadas) > 0:
            print("🚨 ESTADO DEL SISTEMA: COMPROMETIDO / REQUIERE ATENCIÓN INMEDIATA")
            
            # Formatear el mensaje de alerta para el equipo humano de DevOps
            mensaje_alerta = (
                f"🚨 [SecOps AI Agent Alerta Crítica]\n\n"
                f"Se han detectado {len(alertas_detectadas)} incidentes de seguridad en el archivo: {key}\n"
                f"Bucket de Origen: {bucket}\n\n"
                f"Detalle de los vectores de ataque:\n"
                f"{json.dumps(alertas_detectadas, indent=2)}\n\n"
                f"Acción recomendada: Revisar las reglas de firewall o bloquear las IPs atacantes inmediatamente."
            )
            
            # Enviar la notificación de forma asíncrona mediante SNS si el ARN existe
            if sns_topic_arn:
                print("📤 [SNS] Publicando alerta de seguridad en el canal de ingeniería...")
                sns_client.publish(
                    TopicArn=sns_topic_arn,
                    Subject="🚨 SecOps Agent: Alerta de Sistema Comprometido",
                    Message=mensaje_alerta
                )
            else:
                print("⚠️ [SNS] No se detectó variable de entorno SNS_TOPIC_ARN configurada.")
                
        else:
            print("🟢 ESTADO DEL SISTEMA: SEGURO / SIN ANOMALÍAS DETECTADAS")
        print("===========================================\n")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Análisis e hilo de alertas de SecOps ejecutados con éxito.')
        }
        
    except Exception as e:
        print(f"❌ Fallo catastrófico en la ejecución: {str(e)}")
        raise e