# Zenitobot - Mode Recherche pour Matchs Privés

## ⚠️ AVERTISSEMENT IMPORTANT

Ce code est destiné **UNIQUEMENT** à la recherche universitaire avec des participants **consentants** dans des matchs **privés**.

### Utilisation Interdite
❌ Matchmaking public
❌ Ranked games
❌ Casual games
❌ Toute partie non consentante

### Utilisation Autorisée
✅ Matchs privés avec participants consentants
✅ Recherche universitaire documentée
✅ Environnements contrôlés
✅ Tests avec accord explicite

### Risques
- ⚠️ **Violation des ToS de Rocket League**
- ⚠️ **Ban permanent possible** (même en matchs privés)
- ⚠️ Ce projet accepte ces risques dans le cadre de la recherche

---

## 📋 Vue d'Ensemble

Ce projet adapte Zenitobot pour fonctionner dans des matchs privés en ligne en:
1. **Lisant les données du jeu** via memory reading
2. **Utilisant l'IA entraînée** de Zenitobot
3. **Simulant des inputs** via manette virtuelle

### Architecture

```
Rocket League Process
        ↓ (memory reading)
    Memory Reader
        ↓ (game data)
   Zenitobot Agent (IA)
        ↓ (actions)
  Virtual Controller
        ↓ (inputs simulés)
Rocket League Input
```

---

## 🔧 Installation

### Prérequis

- **Windows 10/11** (obligatoire)
- **Python 3.8+**
- **Droits administrateur** (pour memory reading)
- **Rocket League** installé
- **RLBot** déjà configuré avec Zenitobot

### Étape 1: Driver ViGEmBus

Le contrôleur virtuel nécessite le driver ViGEmBus:

1. Télécharge: https://github.com/ViGEm/ViGEmBus/releases
2. Installe `ViGEmBusSetup_x64.msi`
3. Redémarre si demandé

### Étape 2: Dépendances Python

```bash
cd research
pip install -r requirements.txt
```

Dépendances installées:
- `psutil` - Trouve le processus Rocket League
- `vgamepad` - Simule une manette Xbox 360

### Étape 3: Test de Configuration

Lance le script de test:

```bash
TEST_SETUP.bat
```

Ce script vérifie:
- ✓ Python installé
- ✓ Dépendances disponibles
- ✓ Memory reader fonctionne
- ✓ Contrôleur virtuel fonctionne

---

## ⚙️ Configuration des Offsets Mémoire

**C'est l'étape la plus importante et complexe.**

Les offsets mémoire changent **à chaque mise à jour** de Rocket League. Tu dois les trouver toi-même.

### Outils Nécessaires

#### Option 1: Cheat Engine (Recommandé pour débutants)
1. Télécharge: https://www.cheatengine.org/
2. Lance Rocket League
3. Lance Cheat Engine **en administrateur**
4. Attache-le au processus `RocketLeague.exe`

#### Option 2: ReClass.NET (Plus avancé)
1. Télécharge: https://github.com/ReClassNET/ReClass.NET/releases
2. Meilleur pour analyser les structures de données

### Trouver les Offsets

#### Exemple: Position X de la Balle

1. **Lance un match** (Freeplay ou Exhibition)
2. **Dans Cheat Engine:**
   - Cherche "Float" (type)
   - Valeur initiale: position X de la balle (visible dans le jeu)
   - La balle bouge → "Next Scan" avec nouvelle valeur
   - Répète jusqu'à trouver 1-2 adresses
3. **Trouve l'offset:**
   - Adresse trouvée: `0x7FF6AB2A8120`
   - Adresse de base: `0x7FF6A9AB0000` (module base)
   - **Offset = `0x017F8120`**
4. **Met à jour dans `memory_reader.py`:**
   ```python
   'ball_position': 0x017F8120,
   ```

#### Valeurs à Chercher

| Donnée | Type | Comment la trouver |
|--------|------|-------------------|
| Ball X | Float | Position visible en jeu |
| Ball Y | Float | Position visible en jeu |
| Ball Z | Float | Position visible en jeu (hauteur) |
| Ball Speed | Float | Vitesse affichée (km/h ÷ 3.6 = m/s) |
| Car Boost | Float | Ton boost (0.0 - 1.0 ou 0-100) |
| Blue Score | Int | Score affiché |
| Orange Score | Int | Score affiché |

### Pointer Scans (Avancé)

Les offsets simples ne suffisent pas toujours car les adresses changent à chaque lancement.

**Solution: Pointer scans**
1. Cheat Engine → Pointer Scan
2. Trouve les "pointeurs statiques" vers les données
3. Ces pointeurs restent valides entre les lancements

**Tutoriels:**
- https://wiki.cheatengine.org/index.php?title=Tutorials
- https://www.youtube.com/results?search_query=cheat+engine+pointer+scan

### Ressources Communautaires

Certains projets open-source ont déjà trouvé des offsets:
- **BakkesMod** (SDK pour modding RL)
- **RLTracker plugins**
- **Discord communautaire RLBot**

⚠️ Vérifie que les offsets correspondent à **ta version du jeu**.

---

## 🚀 Utilisation

### Étape 1: Préparer Rocket League

1. **Lance Rocket League**
2. **Crée un match privé:**
   - Play → Private Match
   - Configure les paramètres
   - **Ne commence PAS le match encore**
3. **Configure ta manette:**
   - Settings → Controls
   - Note quel slot de manette tu utilises (généralement 0)

### Étape 2: Lancer le Bot

```bash
cd research
python online_bot.py
```

**Configuration interactive:**
```
Team (0=Blue, 1=Orange): 0
Player index (généralement 0 pour toi): 0
```

### Étape 3: Démarrer le Match

1. **Le bot est maintenant actif**
2. **Commence le match dans RL**
3. **Le bot devrait contrôler ta voiture**

### Arrêter le Bot

Appuie sur **Ctrl+C** dans le terminal.

Le bot:
- ✓ Relâche tous les inputs
- ✓ Ferme la manette virtuelle
- ✓ Libère la mémoire

---

## 🧪 Tests Recommandés

### Test 1: Contrôleur Virtuel Seul

```bash
python input_simulator.py
```

**Vérifications:**
- Va dans RL → Settings → Controls
- Tu devrais voir "Xbox 360 Controller" détecté
- Le test fait bouger la manette pendant 5 secondes

### Test 2: Memory Reader Seul

```bash
python memory_reader.py
```

**Vérifications:**
- Lance RL en Freeplay
- Le script affiche position balle, score, etc.
- Si erreur → offsets non configurés

### Test 3: Bot Complet en Freeplay

1. Lance RL en **Freeplay**
2. Lance `python online_bot.py`
3. Observe le comportement du bot

**Problèmes courants:**
- Bot ne bouge pas → Vérifier contrôleur virtuel
- Bot fait n'importe quoi → Vérifier offsets mémoire
- Crash → Vérifier logs d'erreur

---

## 📊 Configuration Avancée

### Ajuster la Fréquence de Décision

Dans `online_bot.py`:
```python
bot = OnlineZenitobot(
    team=0,
    player_index=0,
    tick_skip=8  # Plus bas = plus réactif, plus de CPU
)
```

| tick_skip | Fréquence | Usage |
|-----------|-----------|-------|
| 4 | 30 Hz | Très réactif, intensive |
| 8 | 15 Hz | Défaut, bon équilibre |
| 12 | 10 Hz | Économise CPU |

### Utiliser le Clavier (si vgamepad ne marche pas)

Dans `online_bot.py`, remplace:
```python
from input_simulator import VirtualController
self.controller = VirtualController()
```

Par:
```python
from input_simulator import KeyboardInputSimulator
self.controller = KeyboardInputSimulator()
```

⚠️ **Moins précis** (inputs digitaux vs analogiques)

---

## 🔍 Dépannage

### Erreur: "Processus Rocket League non trouvé"

**Solutions:**
1. Lance Rocket League d'abord
2. Vérifie que le processus s'appelle bien `RocketLeague.exe`
3. Sur Epic Games, le nom peut différer

### Erreur: "Impossible de créer la manette virtuelle"

**Solutions:**
1. ViGEmBus installé? → https://github.com/ViGEm/ViGEmBus/releases
2. Redémarre après installation
3. Vérifie Device Manager → "Nefarius Virtual Gamepad Emulation Bus"

### Erreur: "Access Denied" lors du memory reading

**Solutions:**
1. Lance Python **en administrateur**
2. Sur certains systèmes: désactive anti-virus temporairement
3. Vérifie que tu as les droits admin

### Bot ne répond pas aux données du jeu

**Solutions:**
1. Offsets incorrects → Refais les pointer scans
2. Version du jeu différente → Mets à jour les offsets
3. Lance en mode debug et affiche les valeurs lues

### Bot fait des mouvements erratiques

**Causes possibles:**
1. **Offsets partiellement corrects** → Double-check tous les offsets
2. **Mauvais player_index** → Essaie 0, 1, 2...
3. **Interférences manette** → Débranche ta vraie manette

### Performance lente / Lag

**Optimisations:**
1. Augmente `tick_skip` à 12 ou 16
2. Ferme programmes inutiles
3. Vérifie CPU usage (Task Manager)

---

## 📝 Structure des Fichiers

```
research/
│
├── memory_reader.py          # Lit la mémoire de RL
├── input_simulator.py        # Simule manette/clavier
├── online_bot.py            # Bot principal
│
├── requirements.txt         # Dépendances Python
├── TEST_SETUP.bat          # Script de test
└── README_RESEARCH.md      # Ce fichier
```

---

## 🎓 Contexte Recherche

### Objectif Scientifique

Cette implémentation permet d'étudier:
- Performance d'une IA entraînée hors-ligne dans un contexte en ligne
- Comparaison API vs Memory Reading
- Latence et timing dans un environnement réseau
- Comportement de l'IA face à des joueurs humains réels

### Protocole Expérimental Suggéré

1. **Participants:**
   - Recrutement de joueurs volontaires
   - Consentement éclairé explicite
   - Diversité de niveaux (Gold → GC)

2. **Environnement:**
   - Matchs privés 2v2
   - 1 Bot + 1 Humain vs 2 Humains
   - Sessions enregistrées

3. **Métriques:**
   - Winrate du bot
   - Détection par les joueurs (questionnaire post-match)
   - Latence moyenne de décision
   - Qualité des mécaniques exécutées

4. **Éthique:**
   - Transparence totale avec participants
   - Données anonymisées
   - Droit de retrait à tout moment

### Publication

Si tu publies des résultats:
- ✓ Mentionne le cadre de recherche
- ✓ Explique les mesures éthiques prises
- ✓ Documente les limitations techniques
- ✓ Crédite RLBot et la communauté

---

## 🤝 Contribution & Support

### Problèmes Connus

- [ ] Conversion `GameData` → `ZenitobotObs` non implémentée
- [ ] Offsets génériques non fonctionnels
- [ ] Pas de support macOS/Linux
- [ ] Détection de lag réseau limitée

### Améliorations Futures

- [ ] Auto-détection des offsets via pattern scanning
- [ ] Support multi-agent (plusieurs bots)
- [ ] Enregistrement des parties pour analyse
- [ ] Interface GUI de configuration
- [ ] Système de logs détaillés

### Contact

Pour questions spécifiques à la recherche:
- Discord RLBot communautaire
- GitHub Issues (si projet public)

---

## 📚 Ressources Additionnelles

### Memory Hacking
- **GameHacking.org** - Forums et tutoriels
- **GuidedHacking** - Cours complets
- **Cheat Engine Tutorials** - Guides pas-à-pas

### Rocket League Modding
- **BakkesMod** - SDK de modding RL
- **RocketLeagueMods subreddit**
- **RL Mod Central Discord**

### IA et Bots
- **RLBot Discord** - Communauté active
- **RLGym** - Environnement d'entraînement
- **RL AI Research Papers** - Littérature scientifique

---

## ⚖️ Considérations Légales

### Terms of Service

Extrait pertinent des ToS de Rocket League:
> "You may not use cheats, automation software, hacks, mods or any unauthorized third-party software designed to modify or interfere with the Game."

**Notre position:**
- Ce projet viole techniquement les ToS
- Utilisé **uniquement** pour recherche universitaire
- Participants consentants dans matchs privés
- Acceptation du risque de ban
- But pédagogique et scientifique, pas de gain compétitif

### Droit à la Recherche

Dans un contexte académique:
- ✓ Reverse engineering à des fins éducatives (Fair Use)
- ✓ Analyse de systèmes pour publication scientifique
- ✓ Tests en environnement contrôlé

**Recommandations:**
- Documente ton cadre institutionnel
- Obtiens aval de ton superviseur
- Garde preuves du consentement des participants
- Ne partage pas publiquement sans réflexion éthique

---

## 📄 License

Ce code est fourni "AS IS" pour la recherche universitaire uniquement.

**Disclaimer:**
L'auteur n'est pas responsable de:
- Bans de compte Rocket League
- Violations des ToS
- Utilisation malveillante du code
- Dommages directs ou indirects

**Utilise ce code à tes risques et périls.**

---

## ✅ Checklist de Démarrage

Avant de lancer ton premier test:

- [ ] ViGEmBus installé et redémarré
- [ ] Python 3.8+ avec dépendances
- [ ] TEST_SETUP.bat réussi
- [ ] Offsets mémoire configurés (au moins balle + voiture)
- [ ] Rocket League fonctionne normalement
- [ ] Participants informés et consentants
- [ ] Match privé créé (pas matchmaking)
- [ ] Documentation recherche préparée

**Bon courage pour ta recherche! 🚀**

---

*Dernière mise à jour: 2025*
*Version: 1.0.0*
