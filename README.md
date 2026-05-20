# VTherm Heating Optimizer

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

## FR - Prototype AppDaemon (Step 1)

### Fichiers
- Script AppDaemon : `appdaemon/apps/vtherm_heating_optimizer.py`
- Exemple de configuration : `appdaemon/apps/apps.yaml.example`
- Tests unitaires : `tests/test_heating_decision_engine.py`

### Comportement implante
- Calcul du cout utile poele, clim et radiateurs a chaque cycle
- Bascule selon priorites et couts
- Hysteresis de temperature (declenchement et arret)
- Anti-cycles ON/OFF (durees minimales)
- Notification persistante Home Assistant a chaque changement d'equipement (allumage/extinction)
- Mode `dry_run` pour valider la logique sans commander les equipements

### Configuration des capteurs

| Clé YAML | Unité | Signe / convention | Description |
|---|---|---|---|
| `electricity_price_entity` | €/kWh | toujours **positif** | Prix horaire de l'électricité. Compatible avec `sensor.tempo_price` (intégration Tempo EDF). Repli sur `default_electricity_price_eur_kwh` si absent. |
| `battery_power_entity` | W | **positif** = décharge / **négatif** = charge | Puissance instantanée de la batterie. Clim favorisée si ≥ `battery_support_threshold_w`. |
| `net_consumption_entity` | W | **négatif** = surplus solaire disponible (export réseau) / **positif** = tirage réseau | Consommation nette foyer (production PV − charge). Clim favorisée si ≤ −`solar_support_threshold_w`. |
| `indoor_temp_entity` | °C | positif | **Optionnel.** Capteur de température intérieure. Si absent, `current_temperature` du climate actif est utilisé. |

Pour le détail de tous les paramètres (`ac_cop`, seuils, hystérésis…), voir [tech-docs/specifications.md](tech-docs/specifications.md).

### Lancer les tests
```bash
pytest
```

## EN - AppDaemon Prototype (Step 1)

### Files
- AppDaemon script: `appdaemon/apps/vtherm_heating_optimizer.py`
- Configuration example: `appdaemon/apps/apps.yaml.example`
- Unit tests: `tests/test_heating_decision_engine.py`

### Implemented behavior
- Compute effective cost for stove, AC and radiators at each cycle
- Switch based on priorities and costs
- Temperature hysteresis (start and stop thresholds)
- ON/OFF anti-cycling (minimum durations)
- Home Assistant persistent notification on each equipment change (on/off)
- `dry_run` mode to validate logic without controlling equipment

### Sensor configuration

| YAML key | Unit | Sign / convention | Description |
|---|---|---|---|
| `electricity_price_entity` | €/kWh | always **positive** | Hourly electricity price. Compatible with `sensor.tempo_price` (EDF Tempo integration). Falls back to `default_electricity_price_eur_kwh` if absent. |
| `battery_power_entity` | W | **positive** = discharging / **negative** = charging | Instantaneous battery power. AC is favored when ≥ `battery_support_threshold_w`. |
| `net_consumption_entity` | W | **negative** = solar surplus available (exporting) / **positive** = drawing from grid | Net household consumption (PV production − load). AC is favored when ≤ −`solar_support_threshold_w`. |
| `indoor_temp_entity` | °C | positive | **Optional.** Indoor temperature sensor. If absent, `current_temperature` from the active climate is used. |

For all calculation parameters (`ac_cop`, thresholds, hysteresis…), see [tech-docs/specifications.md](tech-docs/specifications.md).

### Run tests
```bash
pytest
```
