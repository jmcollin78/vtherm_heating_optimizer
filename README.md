# VTherm Heating Optimizer

## FR - Spécifications fonctionnelles

### À quoi sert la solution ?
Le module "VTherm Heating Optimizer" permet d’optimiser automatiquement le choix de la source de chauffage (poêle à pellets, climatisation réversible, radiateurs électriques) en fonction du coût instantané de l’énergie, de la météo, de la production solaire et du niveau de batterie. Il vise à réduire la facture énergétique tout en maintenant le confort.

### Problématiques adressées
- Réduire le coût de chauffage dans un contexte multi-énergie (Tempo, solaire, batteries, granulés)
- Éviter les conflits entre systèmes (poêle/clim/radiateurs)
- Adapter dynamiquement la stratégie selon la météo, la disponibilité solaire, le tarif Tempo
- Limiter l’usure des équipements (anti-cycles, priorisation)

### Public cible
- Utilisateurs Home Assistant équipés de Versatile Thermostat
- Propriétaires de maisons avec plusieurs sources de chauffage
- Utilisateurs avancés cherchant à automatiser l’optimisation énergétique

## EN - Functional Specifications

### Purpose
The "VTherm Heating Optimizer" module automatically optimizes the choice of heating source (pellet stove, reversible AC, electric radiators) based on real-time energy cost, weather, solar production, and battery level. Its goal is to reduce energy bills while maintaining comfort.

### Addressed Issues
- Reduce heating costs in a multi-energy context (Tempo, solar, batteries, pellets)
- Prevent conflicts between systems (stove/AC/radiators)
- Dynamically adapt strategy to weather, solar availability, Tempo tariff
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
- Blocage des sources electriques en Tempo rouge HP, avec fallback secours
- Mode `dry_run` pour valider la logique sans commander les equipements

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
- Electric sources disabled during red Tempo peak, with emergency fallback
- `dry_run` mode to validate logic without controlling equipment

### Run tests
```bash
pytest
```
