"""
Memory Reader pour Rocket League - Projet de Recherche Universitaire
=====================================================================

AVERTISSEMENT: Ce module est destiné uniquement à la recherche universitaire
avec des participants consentants dans des environnements contrôlés.

L'utilisation de ce code dans des matchs en ligne publics viole les
conditions d'utilisation de Rocket League et peut entraîner un ban permanent.

Ce code lit directement la mémoire du processus Rocket League pour obtenir
les données de jeu (positions, vitesses, etc.) en temps réel.
"""

import ctypes
import struct
from dataclasses import dataclass
from typing import List, Optional
import numpy as np

# Windows API
kernel32 = ctypes.windll.kernel32
OpenProcess = kernel32.OpenProcess
ReadProcessMemory = kernel32.ReadProcessMemory
CloseHandle = kernel32.CloseHandle

# Process access rights
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400


@dataclass
class Vector3:
    x: float
    y: float
    z: float

    def to_array(self):
        return np.array([self.x, self.y, self.z])


@dataclass
class Rotator:
    pitch: float
    yaw: float
    roll: float

    def to_array(self):
        return np.array([self.pitch, self.yaw, self.roll])


@dataclass
class CarData:
    position: Vector3
    rotation: Rotator
    velocity: Vector3
    angular_velocity: Vector3
    boost_amount: float
    is_demolished: bool
    has_wheel_contact: bool
    is_supersonic: bool
    team: int


@dataclass
class BallData:
    position: Vector3
    rotation: Rotator
    velocity: Vector3
    angular_velocity: Vector3


@dataclass
class GameData:
    ball: BallData
    cars: List[CarData]
    game_time: float
    is_kickoff: bool
    blue_score: int
    orange_score: int


class RocketLeagueMemoryReader:
    """
    Lecteur mémoire pour Rocket League

    REMARQUES IMPORTANTES:
    - Les offsets mémoire changent à chaque mise à jour du jeu
    - Ces offsets sont des EXEMPLES et doivent être mis à jour
    - Utilise Cheat Engine ou similar pour trouver les vrais offsets
    - Nécessite les droits administrateur pour accéder à la mémoire
    """

    def __init__(self):
        self.process_handle = None
        self.process_id = None
        self.base_address = None

        # OFFSETS EXEMPLE - À METTRE À JOUR SELON LA VERSION DU JEU
        # Ces offsets sont génériques et ne fonctionneront probablement pas
        # Utilise des outils comme Cheat Engine pour trouver les vrais
        self.offsets = {
            # Base du GameState
            'game_state_base': 0x01AB2340,  # EXEMPLE - À METTRE À JOUR

            # Ball offsets (relatifs au game state)
            'ball_position': 0x2A8,
            'ball_rotation': 0x2B4,
            'ball_velocity': 0x2D8,
            'ball_angular_velocity': 0x2E4,

            # Car array
            'cars_array': 0x150,
            'car_count': 0x158,

            # Car offsets (relatifs à chaque voiture)
            'car_position': 0x30,
            'car_rotation': 0x3C,
            'car_velocity': 0x60,
            'car_angular_velocity': 0x6C,
            'car_boost': 0xA0,
            'car_demolished': 0xB8,
            'car_wheel_contact': 0xC0,
            'car_supersonic': 0xC4,
            'car_team': 0xD0,

            # Game info
            'game_time': 0x190,
            'is_kickoff': 0x1A0,
            'blue_score': 0x1B0,
            'orange_score': 0x1B4,
        }

    def find_process(self) -> bool:
        """
        Trouve le processus Rocket League
        Retourne True si trouvé, False sinon
        """
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if 'RocketLeague' in proc.info['name']:
                    self.process_id = proc.info['pid']
                    self.process_handle = OpenProcess(
                        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
                        False,
                        self.process_id
                    )
                    if self.process_handle:
                        print(f"✓ Processus Rocket League trouvé (PID: {self.process_id})")
                        return True
            print("✗ Processus Rocket League non trouvé")
            return False
        except ImportError:
            print("✗ Module psutil requis: pip install psutil")
            return False
        except Exception as e:
            print(f"✗ Erreur lors de la recherche du processus: {e}")
            return False

    def read_memory(self, address: int, size: int) -> Optional[bytes]:
        """
        Lit la mémoire à l'adresse donnée
        """
        if not self.process_handle:
            return None

        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)

        success = ReadProcessMemory(
            self.process_handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(bytes_read)
        )

        if success and bytes_read.value == size:
            return buffer.raw
        return None

    def read_float(self, address: int) -> Optional[float]:
        """Lit un float (4 bytes)"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('f', data)[0]
        return None

    def read_int(self, address: int) -> Optional[int]:
        """Lit un int (4 bytes)"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('i', data)[0]
        return None

    def read_bool(self, address: int) -> Optional[bool]:
        """Lit un bool (1 byte)"""
        data = self.read_memory(address, 1)
        if data:
            return struct.unpack('?', data)[0]
        return None

    def read_vector3(self, base_address: int, offset: int) -> Optional[Vector3]:
        """Lit un Vector3 (3 floats)"""
        addr = base_address + offset
        x = self.read_float(addr)
        y = self.read_float(addr + 4)
        z = self.read_float(addr + 8)

        if x is not None and y is not None and z is not None:
            return Vector3(x, y, z)
        return None

    def read_rotator(self, base_address: int, offset: int) -> Optional[Rotator]:
        """Lit un Rotator (3 floats en degrés)"""
        addr = base_address + offset
        pitch = self.read_float(addr)
        yaw = self.read_float(addr + 4)
        roll = self.read_float(addr + 8)

        if pitch is not None and yaw is not None and roll is not None:
            # Convertit en radians pour compatibilité avec RLBot
            return Rotator(
                np.radians(pitch),
                np.radians(yaw),
                np.radians(roll)
            )
        return None

    def read_ball_data(self, game_state_addr: int) -> Optional[BallData]:
        """Lit les données de la balle"""
        position = self.read_vector3(game_state_addr, self.offsets['ball_position'])
        rotation = self.read_rotator(game_state_addr, self.offsets['ball_rotation'])
        velocity = self.read_vector3(game_state_addr, self.offsets['ball_velocity'])
        angular_velocity = self.read_vector3(game_state_addr, self.offsets['ball_angular_velocity'])

        if all([position, rotation, velocity, angular_velocity]):
            return BallData(position, rotation, velocity, angular_velocity)
        return None

    def read_car_data(self, car_addr: int) -> Optional[CarData]:
        """Lit les données d'une voiture"""
        position = self.read_vector3(car_addr, self.offsets['car_position'])
        rotation = self.read_rotator(car_addr, self.offsets['car_rotation'])
        velocity = self.read_vector3(car_addr, self.offsets['car_velocity'])
        angular_velocity = self.read_vector3(car_addr, self.offsets['car_angular_velocity'])

        boost = self.read_float(car_addr + self.offsets['car_boost'])
        demolished = self.read_bool(car_addr + self.offsets['car_demolished'])
        wheel_contact = self.read_bool(car_addr + self.offsets['car_wheel_contact'])
        supersonic = self.read_bool(car_addr + self.offsets['car_supersonic'])
        team = self.read_int(car_addr + self.offsets['car_team'])

        if all([position, rotation, velocity, angular_velocity]) and boost is not None:
            return CarData(
                position, rotation, velocity, angular_velocity,
                boost, demolished or False, wheel_contact or False,
                supersonic or False, team or 0
            )
        return None

    def read_game_state(self) -> Optional[GameData]:
        """
        Lit l'état complet du jeu

        IMPORTANT: Cette méthode retournera None tant que les offsets
        ne sont pas correctement configurés pour votre version du jeu.
        """
        if not self.process_handle:
            return None

        # Lit l'adresse de base du game state
        # NOTE: Dans un vrai cas, il faut souvent faire un "pointer scan"
        # car l'adresse change à chaque lancement du jeu
        game_state_addr = self.base_address or self.offsets['game_state_base']

        # Lit les données de la balle
        ball = self.read_ball_data(game_state_addr)
        if not ball:
            return None

        # Lit le nombre de voitures
        car_count_addr = game_state_addr + self.offsets['car_count']
        car_count = self.read_int(car_count_addr)
        if car_count is None or car_count < 0 or car_count > 8:
            car_count = 0

        # Lit les données des voitures
        cars = []
        cars_array_addr = game_state_addr + self.offsets['cars_array']
        for i in range(car_count):
            # Calcule l'adresse de chaque voiture dans le tableau
            car_addr = cars_array_addr + (i * 0x200)  # EXEMPLE - taille d'un struct Car
            car_data = self.read_car_data(car_addr)
            if car_data:
                cars.append(car_data)

        # Lit les infos de la partie
        game_time = self.read_float(game_state_addr + self.offsets['game_time']) or 0.0
        is_kickoff = self.read_bool(game_state_addr + self.offsets['is_kickoff']) or False
        blue_score = self.read_int(game_state_addr + self.offsets['blue_score']) or 0
        orange_score = self.read_int(game_state_addr + self.offsets['orange_score']) or 0

        return GameData(
            ball=ball,
            cars=cars,
            game_time=game_time,
            is_kickoff=is_kickoff,
            blue_score=blue_score,
            orange_score=orange_score
        )

    def close(self):
        """Ferme le handle du processus"""
        if self.process_handle:
            CloseHandle(self.process_handle)
            self.process_handle = None
            print("✓ Memory reader fermé")

    def __del__(self):
        self.close()


def main():
    """
    Test du memory reader
    """
    print("=" * 60)
    print("ROCKET LEAGUE MEMORY READER - RECHERCHE UNIVERSITAIRE")
    print("=" * 60)
    print()
    print("AVERTISSEMENT:")
    print("- Les offsets doivent être mis à jour pour votre version du jeu")
    print("- Nécessite des droits administrateur")
    print("- À utiliser uniquement pour la recherche")
    print()

    reader = RocketLeagueMemoryReader()

    if not reader.find_process():
        print("\n✗ Impossible de continuer sans le processus Rocket League")
        return

    print("\nTentative de lecture des données du jeu...")
    print("(Ceci échouera probablement car les offsets doivent être configurés)\n")

    try:
        game_data = reader.read_game_state()

        if game_data:
            print("✓ Données lues avec succès!")
            print(f"  Balle: {game_data.ball.position.to_array()}")
            print(f"  Voitures: {len(game_data.cars)}")
            print(f"  Score: {game_data.blue_score} - {game_data.orange_score}")
        else:
            print("✗ Échec de lecture (offsets non configurés)")
            print("\nÉTAPES POUR CONFIGURER LES OFFSETS:")
            print("1. Télécharge Cheat Engine: https://www.cheatengine.org/")
            print("2. Attache-le au processus RocketLeague.exe")
            print("3. Cherche les valeurs (position X de la balle, score, etc.)")
            print("4. Trouve les offsets et mets à jour memory_reader.py")
            print("5. Documentation: https://wiki.cheatengine.org/")

    except Exception as e:
        print(f"✗ Erreur: {e}")

    finally:
        reader.close()


if __name__ == "__main__":
    main()
