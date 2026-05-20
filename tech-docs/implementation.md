# Implementation Notes / Notes d'implementation

## FR - Comment le code est execute

### Pourquoi il n'y a pas de "point d'entree" classique
Ce projet est une application AppDaemon. Le controle d'execution est delegue au framework AppDaemon (inversion de controle).

Il n'y a donc pas de bloc Python `if __name__ == "__main__":`.
Le demarrage se fait via la configuration AppDaemon, pas via une execution directe du fichier Python.

### Point d'entree declaratif
Le point d'entree est defini dans `appdaemon/apps/apps.yaml.example` :
- `module: vtherm_heating_optimizer`
- `class: VThermHeatingOptimizer`

AppDaemon lit cette configuration, charge le module Python, instancie la classe, puis appelle automatiquement sa methode de cycle de vie `initialize()`.

### Sequence d'execution au demarrage
1. AppDaemon charge le module `vtherm_heating_optimizer`.
2. AppDaemon instancie `VThermHeatingOptimizer`.
3. AppDaemon appelle `initialize()`.
4. `initialize()` :
   - lit les parametres (`self.args`) pour construire `OptimizerConfig`,
   - cree `HeatingDecisionEngine`,
   - mappe les entites Home Assistant,
   - enregistre la boucle periodique avec `run_every(self._run_cycle, "now", cycle_seconds)`.

### Quand le code s'execute ensuite
Apres l'initialisation, AppDaemon declenche `_run_cycle()` toutes les `cycle_seconds` secondes.

Chaque cycle effectue :
1. Lecture des capteurs et consignes Home Assistant (`_read_inputs`).
2. Calcul de la meilleure source (`engine.decide`).
3. Application de la source choisie sur les entites climate (`_apply_source`).
4. Mise a jour de l'etat interne anti-cycling (`engine.commit`).

### Logique de decision (resume)
Le moteur pur `HeatingDecisionEngine` applique :
- hysteresis de temperature (demarrage/arret),
- contraintes anti-cycling (temps minimum ON/OFF),
- estimation de couts (electricite, pellets, AC via COP),
- arbitrage final de source.

### Effet du mode dry_run
Si `dry_run: true`, les commandes `climate/set_hvac_mode` ne sont pas envoyees a Home Assistant.
Le comportement est trace dans les logs AppDaemon pour valider la logique sans actionner les equipements.

### Execution hors AppDaemon
Le fichier Python inclut un fallback d'import (`hass.Hass`) pour les tests locaux, mais ce fallback ne lance aucune boucle d'execution.
L'ordonnancement periodique existe uniquement quand la classe est executee par AppDaemon.

---

## EN - How the code is executed

### Why there is no traditional "entry point"
This project is an AppDaemon application. Execution control is delegated to the AppDaemon framework (inversion of control).

So there is no Python `if __name__ == "__main__":` block.
Startup is driven by AppDaemon configuration, not by running the Python file directly.

### Declarative entry point
The entry point is declared in `appdaemon/apps/apps.yaml.example`:
- `module: vtherm_heating_optimizer`
- `class: VThermHeatingOptimizer`

AppDaemon reads this configuration, loads the Python module, instantiates the class, then automatically calls its lifecycle method `initialize()`.

### Startup execution sequence
1. AppDaemon loads module `vtherm_heating_optimizer`.
2. AppDaemon instantiates `VThermHeatingOptimizer`.
3. AppDaemon calls `initialize()`.
4. `initialize()`:
   - reads parameters (`self.args`) to build `OptimizerConfig`,
   - creates `HeatingDecisionEngine`,
   - maps Home Assistant entities,
   - registers the periodic loop with `run_every(self._run_cycle, "now", cycle_seconds)`.

### When code runs after startup
After initialization, AppDaemon triggers `_run_cycle()` every `cycle_seconds` seconds.

Each cycle performs:
1. Read Home Assistant sensors and setpoint (`_read_inputs`).
2. Compute the best source (`engine.decide`).
3. Apply the selected source on climate entities (`_apply_source`).
4. Update internal anti-cycling state (`engine.commit`).

### Decision logic (summary)
The pure `HeatingDecisionEngine` applies:
- temperature hysteresis (start/stop),
- anti-cycling constraints (minimum ON/OFF times),
- cost estimation (electricity, pellets, AC through COP),
- final source arbitration.

### Effect of dry_run mode
If `dry_run: true`, `climate/set_hvac_mode` service calls are not sent to Home Assistant.
Behavior is logged in AppDaemon logs to validate logic without actuating devices.

### Execution outside AppDaemon
The Python file includes an import fallback (`hass.Hass`) for local tests, but this fallback does not start any execution loop.
Periodic scheduling exists only when the class is run by AppDaemon.
