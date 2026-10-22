import matplotlib
import sys

# Força o backend gráfico interativo
try:
    matplotlib.use('TkAgg')
except Exception:
    pass

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import paho.mqtt.client as mqtt
import json

broker = "test.mosquitto.org"
topico = "semaforo/anticolisao/sensores"

tempos, distancias, velocidades = [], [], []
contador = 0

def on_message(client, userdata, msg):
    global contador
    try:
        data = json.loads(msg.payload.decode())
        
        # Leitura flexível dos sensores
        sensores = data.get("sensores", {})
        vel = sensores.get("radar_doppler_kmh") or sensores.get("radar_vel_kmh") or data.get("velocidade_kmh", 0)
        dist = sensores.get("ultrassonico_dist_cm") or sensores.get("ultrassonico_dist_cm") or data.get("distancia_cm", 0)
        
        tempos.append(contador)
        velocidades.append(vel)
        distancias.append(dist)
        contador += 1

        if len(tempos) > 40:
            tempos.pop(0)
            velocidades.pop(0)
            distancias.pop(0)
    except Exception as e:
        pass

# Configura Cliente MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(broker, 1883, 60)
client.subscribe(topico)
client.loop_start()

# Configura Subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7))

def update(frame):
    if not tempos:
        return
    
    # Gráfico Radar
    ax1.clear()
    ax1.plot(tempos, velocidades, 'r-o', linewidth=2, label="Radar Doppler (km/h)")
    ax1.axhline(60, color='gray', linestyle='--', alpha=0.7, label="Limiar (>60 km/h)")
    ax1.set_title("Aferição Cinemática - Radar Doppler")
    ax1.set_ylabel("Velocidade (km/h)")
    ax1.grid(True)
    ax1.legend(loc="upper right")

    # Gráfico Ultrassônico
    ax2.clear()
    ax2.plot(tempos, distancias, 'b-s', linewidth=2, label="Ultrassônico (cm)")
    ax2.axhline(5000, color='orange', linestyle='--', alpha=0.7, label="Zona Crítica (<50m)")
    ax2.set_title("Aproximação Física - Sensor Ultrassônico")
    ax2.set_ylabel("Distância (cm)")
    ax2.set_xlabel("Amostras de Telemetria")
    ax2.grid(True)
    ax2.legend(loc="upper right")

# cache_frame_data=False elimina o Warning de cache
ani = FuncAnimation(fig, update, interval=200, cache_frame_data=False)

plt.tight_layout()
plt.show()