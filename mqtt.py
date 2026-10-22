import paho.mqtt.client as mqtt
import time
import csv
import json

broker = "test.mosquitto.org"
topico = "semaforo/anticolisao/sensores"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(broker, 1883, 60)

print("Iniciando telemetria IoT com dados limpos do NGSIM...")

FPS_PARA_KMH = 1.09728
PES_PARA_CM = 30.48
LIMIAR_VELOCIDADE_KMH = 60.0
POSICAO_SEMAFORO_PES = 400.0  

try:
    # Agora lemos diretamente do arquivo padronizado
    with open('ngsim_limpo.csv', 'r') as f:
        reader = csv.DictReader(f)
        carro_alvo = "12" 
        
        for linha in reader:
            if linha['Vehicle_ID'] != carro_alvo:
                continue
            
            # Leitura direta sem necessidade de .replace()
            v_vel_fps = float(linha['v_Vel'])
            local_y_pes = float(linha['Local_Y'])
            
            velocidade_kmh = round(v_vel_fps * FPS_PARA_KMH, 2)
            distancia_pes = POSICAO_SEMAFORO_PES - local_y_pes
            distancia_cm = max(0.0, round(distancia_pes * PES_PARA_CM, 2))
            
            if velocidade_kmh > LIMIAR_VELOCIDADE_KMH and distancia_cm < 5000.0 and distancia_cm > 0:
                estado = "ALL_RED_CLEARANCE"
            else:
                estado = "NORMAL"

            payload = {
                "timestamp_ms": linha['Global_Time'], 
                "veiculo_id": linha['Vehicle_ID'],
                "sensores": {
                    "ultrassonico_dist_cm": distancia_cm,
                    "radar_vel_kmh": velocidade_kmh
                },
                "decisao_borda": {
                    "status_cruzamento": estado,
                    "gatilho_ativo": True if estado == "ALL_RED_CLEARANCE" else False
                }
            }
            
            client.publish(topico, json.dumps(payload))
            print(f"[{payload['timestamp_ms']}] Distância: {distancia_cm}cm | Velocidade: {velocidade_kmh}km/h -> {estado}")
            
            time.sleep(0.1) 

except FileNotFoundError:
    print("Erro: Execute primeiro o script 'limpar_dataset.py' para gerar o 'ngsim_limpo.csv'.")