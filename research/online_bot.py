"""
Bot Rocket League pour Matchs Privés - Recherche Universitaire
===============================================================

AVERTISSEMENT IMPORTANT:
Ce code est destiné UNIQUEMENT à la recherche universitaire avec des
participants consentants dans des matchs privés.

L'utilisation dans des matchs en ligne publics:
- Viole les conditions d'utilisation de Rocket League
- Peut entraîner un ban permanent
- Est considéré comme de la triche

UTILISATION ACCEPTÉE:
✓ Matchs privés avec joueurs consentants
✓ Recherche universitaire documentée
✓ Environnements contrôlés

Ce bot combine:
1. Memory reading pour obtenir les données du jeu
2. L'IA entraînée de Zenitobot
3. Simulation d'inputs via manette virtuelle
"""

import sys
import os
import time
import threading
import numpy as np
from pathlib import Path

# Ajoute le dossier parent au path pour les imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "Zenitobot"))

from memory_reader import RocketLeagueMemoryReader, GameData
from input_simulator import VirtualController, ControllerState

# Import de l'agent Zenitobot
try:
    from agent import Agent
    from Zenitobot_obs import ZenitobotObsBuilder, BOOST_LOCATIONS
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"⚠ Agent Zenitobot non disponible: {e}")
    AGENT_AVAILABLE = False


class OnlineZenitobot:
    """
    Version de Zenitobot pour matchs privés en ligne

    Cette classe adapte Zenitobot pour:
    1. Lire les données via memory reading au lieu de l'API RLBot
    2. Envoyer les commandes via un contrôleur virtuel
    """

    def __init__(self, team: int = 0, player_index: int = 0, tick_skip: int = 8):
        """
        Args:
            team: 0 pour bleu, 1 pour orange
            player_index: Index du joueur contrôlé par le bot (0-7)
            tick_skip: Nombre de ticks entre chaque décision (8 = 15Hz)
        """
        print("=" * 60)
        print("ZENITOBOT - MODE RECHERCHE ONLINE")
        print("=" * 60)
        print()

        self.team = team
        self.player_index = player_index
        self.tick_skip = tick_skip
        self.ticks = 0

        # Initialise le memory reader
        print("Initialisation du memory reader...")
        self.memory_reader = RocketLeagueMemoryReader()
        if not self.memory_reader.find_process():
            raise RuntimeError("Impossible de trouver le processus Rocket League")

        # Initialise le contrôleur virtuel
        print("Initialisation du contrôleur virtuel...")
        try:
            self.controller = VirtualController()
        except Exception as e:
            self.memory_reader.close()
            raise RuntimeError(f"Impossible d'initialiser le contrôleur virtuel: {e}")

        # Initialise l'agent IA
        if not AGENT_AVAILABLE:
            raise RuntimeError(
                "Agent Zenitobot non disponible. "
                "Assure-toi que Zenitobot-model.pt existe."
            )

        print("Chargement du modèle Zenitobot...")
        self.agent = Agent()
        self.obs_builder = None  # Sera initialisé au premier update
        self.action = np.zeros(8)
        self.update_action = True

        # État du jeu
        self.game_state = None
        self.prev_time = 0

        # Thread de contrôle
        self.running = False
        self.thread = None

        print("\n✓ Initialisation terminée!")
        print(f"  Team: {'Blue' if team == 0 else 'Orange'}")
        print(f"  Player index: {player_index}")
        print(f"  Tick skip: {tick_skip} (≈{120/tick_skip:.1f} Hz)")

    def convert_memory_to_obs(self, game_data: GameData):
        """
        Convertit les données mémoire en observations pour l'agent

        Cette fonction adapte les données du memory reader au format
        attendu par ZenitobotObsBuilder
        """
        # TODO: Cette fonction doit être adaptée selon le format exact
        # de ZenitobotObsBuilder. Pour l'instant c'est un placeholder.

        # L'idée est de créer un objet similaire à GameState de rlgym
        # à partir des données memory

        if self.obs_builder is None:
            # Initialise le obs builder (nécessite field_info)
            # Pour l'instant, on utilise des valeurs par défaut
            # Dans un vrai cas, il faudrait aussi lire le terrain de la mémoire
            from rlgym_compat import GameState
            # Placeholder - à adapter
            self.obs_builder = ZenitobotObsBuilder(field_info=None)

        # Convertit les données mémoire en format compatible
        # C'est ici qu'il faut faire le mapping entre:
        # - game_data.ball -> game_state.ball
        # - game_data.cars -> game_state.players
        # etc.

        # Pour l'instant, retourne un placeholder
        # Cette partie nécessite une analyse plus détaillée du format
        # exact de ZenitobotObsBuilder
        raise NotImplementedError(
            "La conversion memory -> obs n'est pas encore implémentée.\n"
            "Il faut mapper les structures de memory_reader vers le format\n"
            "attendu par ZenitobotObsBuilder."
        )

    def update(self):
        """
        Met à jour le bot (lecture données + décision + envoi commandes)
        """
        # Lit l'état du jeu depuis la mémoire
        game_data = self.memory_reader.read_game_state()

        if game_data is None:
            # Pas de données valides
            return False

        # Incrémente le compteur de ticks
        self.ticks += 1

        # Vérifie si on doit prendre une nouvelle décision
        if self.ticks >= self.tick_skip:
            self.ticks = 0
            self.update_action = True

        if self.update_action:
            self.update_action = False

            # Vérifie qu'on a assez de voitures
            if len(game_data.cars) <= self.player_index:
                print(f"⚠ Player index {self.player_index} non disponible")
                return False

            # Convertit les données en observations
            try:
                obs = self.convert_memory_to_obs(game_data)
            except NotImplementedError:
                # Pour l'instant, utilise des actions aléatoires
                # comme placeholder
                self.action = np.random.randn(8)
                self.action = np.clip(self.action, -1, 1)
                self.action[5:] = (self.action[5:] > 0).astype(float)
            else:
                # Demande une action à l'agent
                self.action, _ = self.agent.act(obs, beta=1.0)

        # Envoie l'action au contrôleur virtuel
        self.controller.update_from_array(self.action)
        return True

    def run_loop(self, fps: float = 120.0):
        """
        Boucle principale du bot

        Args:
            fps: Fréquence de la boucle (devrait matcher le jeu)
        """
        print("\n" + "=" * 60)
        print("BOT DÉMARRÉ")
        print("=" * 60)
        print("\nPour arrêter le bot, appuie sur Ctrl+C\n")

        frame_time = 1.0 / fps
        self.running = True

        try:
            while self.running:
                start_time = time.perf_counter()

                # Met à jour le bot
                success = self.update()

                if not success:
                    time.sleep(0.1)  # Attends un peu avant de réessayer
                    continue

                # Maintient le framerate
                elapsed = time.perf_counter() - start_time
                sleep_time = frame_time - elapsed

                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif sleep_time < -frame_time:
                    # On est vraiment en retard
                    print(f"⚠ Warning: Running slow ({elapsed*1000:.1f}ms)")

        except KeyboardInterrupt:
            print("\n\n✓ Arrêt demandé (Ctrl+C)")

        finally:
            self.stop()

    def start(self, fps: float = 120.0):
        """
        Démarre le bot dans un thread séparé
        """
        if self.running:
            print("⚠ Bot déjà en cours d'exécution")
            return

        self.thread = threading.Thread(target=self.run_loop, args=(fps,))
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """
        Arrête le bot proprement
        """
        print("\nArrêt du bot...")
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        # Remet le contrôleur à zéro
        self.controller.reset()
        self.controller.release()

        # Ferme le memory reader
        self.memory_reader.close()

        print("✓ Bot arrêté proprement")

    def __del__(self):
        if self.running:
            self.stop()


def main():
    """
    Point d'entrée principal
    """
    print("\n" + "=" * 60)
    print("ZENITOBOT - RECHERCHE UNIVERSITAIRE")
    print("Matchs Privés avec Participants Consentants")
    print("=" * 60)
    print()
    print("AVERTISSEMENT:")
    print("- Ce code est destiné UNIQUEMENT à la recherche")
    print("- À utiliser dans des matchs privés avec joueurs consentants")
    print("- L'utilisation en matchmaking public peut entraîner un ban")
    print()
    print("PRÉREQUIS:")
    print("✓ Rocket League lancé et dans un match privé")
    print("✓ ViGEmBus installé (pour le contrôleur virtuel)")
    print("✓ Offsets mémoire configurés (memory_reader.py)")
    print("✓ Droits administrateur (pour memory reading)")
    print()

    input("Appuie sur ENTRÉE pour continuer ou Ctrl+C pour annuler...")

    try:
        # Configuration
        print("\nConfiguration:")
        team = int(input("Team (0=Blue, 1=Orange): "))
        player_index = int(input("Player index (généralement 0 pour toi): "))

        # Crée et lance le bot
        bot = OnlineZenitobot(team=team, player_index=player_index)
        bot.run_loop(fps=120.0)

    except KeyboardInterrupt:
        print("\n\n✓ Annulation")
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
