import paho.mqtt.client as mqtt
import time
import json
import random

# Configurações MQTT
broker = "test.mosquitto.org"
topico = "semaforo/anticolisao/sensores"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(broker, 1883, 60)

print("=== SIMULADOR DE TRÂNSITO EM TEMPO REAL INICIADO ===")
print("Gerando fluxo dinâmico de veículos no cruzamento...\n")

class Veiculo:
    def __init__(self, id_veiculo, perfil):
        self.id = id_veiculo
        self.perfil = perfil  # 'PRUDENTE', 'INFRATOR', 'PEDESTRE'
        
        if perfil == 'PRUDENTE':
            self.distancia_cm = 10000.0  # 100 metros
            self.velocidade_kmh = random.uniform(45.0, 55.0)
            self.desaceleracao = random.uniform(3.5, 5.0)
        elif perfil == 'INFRATOR':
            self.distancia_cm = 12000.0  # 120 metros
            self.velocidade_kmh = random.uniform(80.0, 95.0)
            self.desaceleracao = 0.0     # Não freia
        elif perfil == 'PEDESTRE':
            self.distancia_cm = 600.0    # 6 metros (próximo à faixa)
            self.velocidade_kmh = random.uniform(3.0, 5.0)
            self.desaceleracao = 0.0

    def atualizar_posicao(self, dt=0.2):
        """ Atualiza a física do veículo a cada passo de tempo (0.2s) """
        # Adiciona ruído gaussiano para emular a variação analógica dos sensores
        ruido_vel = random.gauss(0, 1.0)
        ruido_dist = random.gauss(0, 15.0)

        # Atualiza a velocidade
        self.velocidade_kmh = max(0.0, self.velocidade_kmh - (self.desaceleracao * dt) + ruido_vel)
        
        # Converte km/h para cm/s e atualiza distância
        velocidade_cms = (self.velocidade_kmh / 3.6) * 100
        self.distancia_cm = max(0.0, self.distancia_cm - (velocidade_cms * dt) + ruido_dist)

    def esta_no_cruzamento(self):
        return self.distancia_cm <= 0 and self.velocidade_kmh <= 0

# Loop Principal de Simulação
contador_veiculos = 1

while True:
    # Sorteia o perfil do novo veículo que entrou na via
    sorteio = random.random()
    if sorteio < 0.70:
        perfil = 'PRUDENTE'
    elif sorteio < 0.90:
        perfil = 'INFRATOR'
    else:
        perfil = 'PEDESTRE'

    veiculo_atual = Veiculo(f"VEIC_{contador_veiculos:03d}", perfil)
    print(f"\n--- [NOVO ALVO DETECTADO: {veiculo_atual.id}] | Perfil: {perfil} ---")

    # Acompanha o trajeto do veículo até ele cruzar/parar
    passo = 0
    while not veiculo_atual.esta_no_cruzamento() and passo < 80:
        veiculo_atual.atualizar_posicao(dt=0.2)
        
        # Leitura simulada dos dois sensores (Radar Doppler + Ultrassônico)
        vel_sensor = round(veiculo_atual.velocidade_kmh, 2)
        dist_sensor = round(veiculo_atual.distancia_cm, 2)

        # Processamento na Borda (ESP32 Logic):
        # Dispara All-Red se distância < 50m (5000cm) e velocidade > 60km/h
        if vel_sensor > 60.0 and 0 < dist_sensor < 5000.0:
            decisao_borda = "ALL_RED_CLEARANCE"
        else:
            decisao_borda = "NORMAL"

        # Formatação da Telemetria IoT
        payload = {
            "timestamp": time.time(),
            "veiculo_id": veiculo_atual.id,
            "perfil_simulado": perfil,
            "sensores": {
                "radar_doppler_kmh": vel_sensor,
                "ultrassonico_dist_cm": dist_sensor
            },
            "decisao_esp32": {
                "status": decisao_borda,
                "bloqueio_ativo": True if decisao_borda == "ALL_RED_CLEARANCE" else False
            }
        }

        # Publica no MQTT
        client.publish(topico, json.dumps(payload))
        
        # Exibe status no terminal com destaque visual para emergência
        alerta_str = "🚨 [ALL-RED ATIVADO]" if decisao_borda == "ALL_RED_CLEARANCE" else "🟢 [NORMAL]"
        print(f"[{veiculo_atual.id}] Dist: {dist_sensor:7.1f}cm | Vel: {vel_sensor:5.1f}km/h | {alerta_str}")

        time.sleep(0.2)  # Frequência de atualização de 5 Hz (200ms)
        passo += 1

    contador_veiculos += 1
    # Intervalo aleatório de 2 a 5 segundos antes do próximo veículo surgir na via
    intervalo_novo_carro = random.uniform(2.0, 5.0)
    time.sleep(intervalo_novo_carro)