# Specifications fonctionnelles / Functional Specifications

## FR - Spécifications fonctionnelles

### À quoi sert la solution ?
Le module "VTherm Heating Optimizer" permet d’optimiser automatiquement le choix de la source de chauffage (poêle à pellets, climatisation réversible, radiateurs électriques) en fonction du coût instantané de l’énergie, de la météo, de la production solaire et du niveau de batterie. Il vise à réduire la facture énergétique tout en maintenant le confort.

### Problématiques adressées
- Réduire le coût de chauffage dans un contexte multi-énergie (électricité, solaire, batteries, granulés)
- Éviter les conflits entre systèmes (poêle/clim/radiateurs)
- Adapter dynamiquement la stratégie selon la météo, la disponibilité solaire et le prix horaire de l'électricité
- Limiter l’usure des équipements (anti-cycles, priorisation)

### Public cible
- Utilisateurs Home Assistant équipés de Versatile Thermostat
- Propriétaires de maisons avec plusieurs sources de chauffage
- Utilisateurs avancés cherchant à automatiser l’optimisation énergétique

## EN - Functional Specifications

### Purpose
The "VTherm Heating Optimizer" module automatically optimizes the choice of heating source (pellet stove, reversible AC, electric radiators) based on real-time energy cost, weather, solar production, and battery level. Its goal is to reduce energy bills while maintaining comfort.

### Addressed Issues
- Reduce heating costs in a multi-energy context (electricity, solar, batteries, pellets)
- Prevent conflicts between systems (stove/AC/radiators)
- Dynamically adapt strategy to weather, solar availability, and hourly electricity price
- Limit equipment wear (anti-cycling, prioritization)

### Target Audience
- Home Assistant users with Versatile Thermostat
- Homeowners with multiple heating sources
- Advanced users seeking automated energy optimization

---

## FR - Configuration détaillée des capteurs et paramètres

### Capteurs d'entrée (`apps.yaml`)

| Clé YAML | Unité | Signe / convention | Description |
|---|---|---|---|
| `electricity_price_entity` | €/kWh | toujours **positif** | Prix horaire de l'électricité. Compatible avec `sensor.tempo_price` de l'intégration Tempo EDF. Si absent ou invalide, la valeur de `default_electricity_price_eur_kwh` est utilisée comme repli. |
| `battery_power_entity` | W | **positif** = batterie en décharge (fournit de l'énergie au foyer) / **négatif** = batterie en charge | Puissance instantanée de la batterie. La climatisation est favorisée si cette valeur ≥ `battery_support_threshold_w`. |
| `net_consumption_entity` | W | **négatif** = surplus solaire disponible (le foyer exporte) / **positif** = tirage réseau (le foyer consomme) | Consommation nette du foyer = production PV − consommation instantanée. La clim est favorisée si cette valeur ≤ −`solar_support_threshold_w`. |
| `indoor_temp_entity` | °C | positif | **Optionnel.** Température intérieure de référence. Si absent, l'attribut `current_temperature` du climate actif est utilisé (même logique de repli que pour la consigne). |

### Paramètres de comportement et de calcul (`apps.yaml`)

| Clé YAML | Unité | Défaut | Description |
|---|---|---|---|
| `cycle_seconds` | s | 60 | Intervalle entre deux cycles de décision. |
| `hysteresis_on_delta_c` | °C | 0,4 | Écart sous la consigne pour démarrer le chauffage (T < consigne − 0,4°C). |
| `hysteresis_off_delta_c` | °C | 0,1 | Écart sous la consigne pour arrêter le chauffage (arrêt si T ≥ consigne − 0,1°C). |
| `min_on_seconds` | s | 600 | Durée minimale d'activation avant bascule vers une autre source (anti-cycles). |
| `min_off_seconds` | s | 600 | Durée minimale d'arrêt avant réactivation (anti-cycles). |
| `ac_cop` | sans unité | 3,0 | COP de la climatisation réversible. Coût clim = prix élec / COP. |
| `pellet_kwh_per_kg` | kWh/kg | 4,8 | Pouvoir calorifique des granulés. |
| `pellet_efficiency` | 0–1 | 0,85 | Rendement du poêle (0,85 = 85 %). |
| `pellet_bag_price_eur` | € | 6,0 | Prix d'un sac de pellets. Paramètre statique, pas de sensor nécessaire. |
| `pellet_bag_weight_kg` | kg | 15,0 | Poids d'un sac de pellets. Paramètre statique, pas de sensor nécessaire. |
| `default_electricity_price_eur_kwh` | €/kWh | 0,20 | Prix de repli si le capteur `electricity_price_entity` est absent ou invalide. |
| `battery_support_threshold_w` | W | 500 | Puissance de décharge minimale de la batterie pour considérer qu'elle peut soutenir le chauffage électrique. |
| `solar_support_threshold_w` | W | 500 | Seuil de surplus solaire : la clim est favorisée si `net_consumption` ≤ −`solar_support_threshold_w`. |

### Notifications

- A chaque changement de source de chauffage selectionnee, le service Home Assistant `persistent_notification.create` est appele.
- Le message contient l'equipement concerne, l'action (allume ou eteint) et la raison de la decision.

---

## EN - Detailed Sensor and Parameter Configuration

### Input sensors (`apps.yaml`)

| YAML key | Unit | Sign / convention | Description |
|---|---|---|---|
| `electricity_price_entity` | €/kWh | always **positive** | Hourly electricity price. Compatible with `sensor.tempo_price` from the EDF Tempo integration. Falls back to `default_electricity_price_eur_kwh` if absent or invalid. |
| `battery_power_entity` | W | **positive** = discharging (supplying energy) / **negative** = charging | Instantaneous battery power. AC is favored when this value ≥ `battery_support_threshold_w`. |
| `net_consumption_entity` | W | **negative** = solar surplus available (home is exporting) / **positive** = drawing from grid (home is consuming) | Net household consumption = PV production − instantaneous load. AC is favored when this value ≤ −`solar_support_threshold_w`. |
| `indoor_temp_entity` | °C | positive | **Optional.** Reference indoor temperature sensor. If absent, the `current_temperature` attribute of the active climate entity is used (same fallback logic as the setpoint). |

### Behavior and calculation parameters (`apps.yaml`)

| YAML key | Unit | Default | Description |
|---|---|---|---|
| `cycle_seconds` | s | 60 | Interval between two decision cycles. |
| `hysteresis_on_delta_c` | °C | 0.4 | Gap below setpoint to start heating (T < setpoint − 0.4°C). |
| `hysteresis_off_delta_c` | °C | 0.1 | Gap below setpoint to stop heating (stops when T ≥ setpoint − 0.1°C). |
| `min_on_seconds` | s | 600 | Minimum active time before switching to another source (anti-cycling). |
| `min_off_seconds` | s | 600 | Minimum off time before reactivation (anti-cycling). |
| `ac_cop` | dimensionless | 3.0 | AC coefficient of performance. AC cost = electricity price / COP. |
| `pellet_kwh_per_kg` | kWh/kg | 4.8 | Pellet calorific value. |
| `pellet_efficiency` | 0–1 | 0.85 | Stove efficiency (0.85 = 85%). |
| `pellet_bag_price_eur` | € | 6.0 | Price of one pellet bag. Static parameter, no sensor needed. |
| `pellet_bag_weight_kg` | kg | 15.0 | Weight of one pellet bag. Static parameter, no sensor needed. |
| `default_electricity_price_eur_kwh` | €/kWh | 0.20 | Fallback price when `electricity_price_entity` is absent or invalid. |
| `battery_support_threshold_w` | W | 500 | Minimum battery discharge power to consider it can support electric heating. |
| `solar_support_threshold_w` | W | 500 | Solar surplus threshold: AC is favored when `net_consumption` ≤ −`solar_support_threshold_w`. |

### Notifications

- On each selected heating source change, the Home Assistant service `persistent_notification.create` is called.
- The message includes the impacted equipment, the action (on or off), and the decision reason.
