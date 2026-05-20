# Architecture technique AppDaemon / AppDaemon Technical Architecture

## FR - Architecture technique

- **Technologie** : AppDaemon (Python 3)
- **Déploiement** : Copie d’un fichier Python dans le dossier `apps/` d’AppDaemon
- **Configuration** : Fichier YAML associé (apps.yaml)
- **Accès Home Assistant** : API native AppDaemon (écoute d’événements, lecture/écriture d’états)
- **Logique** :
    - Calcul du coût instantané de chaque source (poêle, clim, radiateurs)
    - Prise de décision selon règles (hystérésis, anti-cycles, priorités)
    - Commande des thermostats (VTherm, clim, radiateurs)
    - Logs détaillés pour debug
    - Extensibilité : Ajout facile de nouvelles règles ou capteurs

### Paramètres / Entités nécessaires

- `sensor.tempo_color` : Couleur du jour Tempo (bleu/blanc/rouge)
- `sensor.tempo_period` : Plage horaire Tempo (HP/HC) ou `sensor.tempo_price` (€/kWh)
- `sensor.pv_power` : Puissance photovoltaïque instantanée
- `sensor.battery_soc` : État de charge batterie (%)
- `sensor.battery_power` : Puissance batterie (charge/décharge)
- `sensor.surplus_solar` : Surplus solaire (optionnel)
- `sensor.temp_salon` : Température intérieure de référence
- `sensor.temp_exterieure` : Température extérieure
- `input_number.pellet_bag_price_eur` : Prix d'un sac de pellets (€)
- `input_number.pellet_bag_weight_kg` : Poids d'un sac de pellets (kg)
- `climate.vtherm_poele` : Thermostat poêle à pellets
- `climate.clim_salon` : Thermostat climatisation
- `climate.thermostat_sam1` : Thermostat radiateurs électriques

### Règles de bascule entre modes de chauffage

- Priorité 1 : Poêle à pellets (base load)
- Priorité 2 : Climatisation réversible (appoint si coût clim < coût poêle OU surplus solaire/batterie)
- Priorité 3 : Radiateurs électriques (secours uniquement)

**Critères de bascule :**
- Calculer le coût utile de chaque source à chaque cycle :
    - Poêle : coût granulés (€/kWh utile), calculé à partir du prix et du poids du sac
    - Clim : coût élec / COP (€/kWh chaleur)
    - Radiateurs : coût élec direct (€/kWh)
- Si surplus solaire ou batterie > seuil : favoriser la clim
- Si tarif Tempo élevé (rouge HP) : éviter radiateurs et clim
- Hystérésis sur la température pour éviter les oscillations :
    - Déclenchement appoint si T < consigne - 0,4°C
    - Arrêt appoint si T > consigne - 0,1°C
- Respecter les durées minimales ON/OFF de chaque source (anti-bagots)
- Ne jamais activer deux sources en même temps (hors secours)

## EN - Technical Architecture

- **Technology**: AppDaemon (Python 3)
- **Deployment**: Copy a Python file into the AppDaemon `apps/` folder
- **Configuration**: Associated YAML file (apps.yaml)
- **Home Assistant Access**: Native AppDaemon API (event listening, state read/write)
- **Logic**:
    - Compute real-time cost for each source (stove, AC, radiators)
    - Decision-making based on rules (hysteresis, anti-cycling, priorities)
    - Control thermostats (VTherm, AC, radiators)
    - Detailed logs for debugging
    - Extensibility: Easy to add new rules or sensors

### Required Parameters / Entities

- `sensor.tempo_color`: Tempo day color (blue/white/red)
- `sensor.tempo_period`: Tempo period (peak/off-peak) or `sensor.tempo_price` (€/kWh)
- `sensor.pv_power`: Instantaneous PV power
- `sensor.battery_soc`: Battery state of charge (%)
- `sensor.battery_power`: Battery power (charge/discharge)
- `sensor.surplus_solar`: Solar surplus (optional)
- `sensor.temp_salon`: Reference indoor temperature
- `sensor.temp_exterieure`: Outdoor temperature
- `input_number.pellet_bag_price_eur`: Pellet bag price (EUR)
- `input_number.pellet_bag_weight_kg`: Pellet bag weight (kg)
- `climate.vtherm_poele`: Pellet stove thermostat
- `climate.clim_salon`: AC thermostat
- `climate.thermostat_sam1`: Electric radiators thermostat

### Heating Mode Switching Rules

- Priority 1: Pellet stove (base load)
- Priority 2: Reversible AC (supplement if AC cost < stove cost OR solar/battery surplus)
- Priority 3: Electric radiators (emergency only)

**Switching criteria:**
- Compute the effective cost of each source at each cycle:
    - Stove: pellet cost (€/kWh useful), computed from bag price and bag weight
    - AC: electricity cost / COP (€/kWh heat)
    - Radiators: direct electricity cost (€/kWh)
- If solar surplus or battery > threshold: favor AC
- If Tempo tariff is high (red peak): avoid radiators and AC
- Hysteresis on temperature to avoid oscillations:
    - Trigger supplement if T < setpoint - 0.4°C
    - Stop supplement if T > setpoint - 0.1°C
- Respect minimum ON/OFF durations for each source (anti-cycling)
- Never activate two sources at the same time (except emergency)

