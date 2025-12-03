"""
Input Simulator pour Rocket League - Projet de Recherche Universitaire
========================================================================

AVERTISSEMENT: Ce module est destiné uniquement à la recherche universitaire
avec des participants consentants dans des environnements contrôlés.

L'utilisation de ce code dans des matchs en ligne publics viole les
conditions d'utilisation de Rocket League et peut entraîner un ban permanent.

Ce code simule des inputs de manette virtuelle pour contrôler Rocket League.
"""

import ctypes
import time
from dataclasses import dataclass
import numpy as np

# vgamepad pour simulation de manette Xbox
try:
    import vgamepad as vg
    VGAMEPAD_AVAILABLE = True
except ImportError:
    VGAMEPAD_AVAILABLE = False
    print("Module vgamepad non disponible. Installation: pip install vgamepad")


@dataclass
class ControllerState:
    """
    État d'une manette compatible Rocket League
    Toutes les valeurs entre -1 et 1 sauf jump/boost/handbrake (0 ou 1)
    """
    throttle: float = 0.0  # -1 (reverse) à 1 (forward)
    steer: float = 0.0  # -1 (left) à 1 (right)
    pitch: float = 0.0  # -1 (backward) à 1 (forward)
    yaw: float = 0.0  # -1 (left) à 1 (right)
    roll: float = 0.0  # -1 (left) à 1 (right)
    jump: bool = False  # A button
    boost: bool = False  # B button
    handbrake: bool = False  # X button

    def to_array(self):
        """Convertit en array numpy (format RLBot)"""
        return np.array([
            self.throttle,
            self.steer,
            self.pitch,
            self.yaw,
            self.roll,
            1.0 if self.jump else 0.0,
            1.0 if self.boost else 0.0,
            1.0 if self.handbrake else 0.0
        ])

    @classmethod
    def from_array(cls, arr):
        """Crée un ControllerState depuis un array numpy"""
        return cls(
            throttle=float(arr[0]),
            steer=float(arr[1]),
            pitch=float(arr[2]),
            yaw=float(arr[3]),
            roll=float(arr[4]),
            jump=arr[5] > 0.5,
            boost=arr[6] > 0.5,
            handbrake=arr[7] > 0.5
        )


class VirtualController:
    """
    Contrôleur virtuel pour Rocket League utilisant vgamepad

    Cette classe simule une manette Xbox 360 virtuelle que Rocket League
    peut détecter et utiliser comme une vraie manette.

    PRÉREQUIS:
    - Windows uniquement
    - Driver ViGEm installé: https://github.com/ViGEm/ViGEmBus/releases
    - Module Python vgamepad: pip install vgamepad
    """

    def __init__(self):
        if not VGAMEPAD_AVAILABLE:
            raise ImportError(
                "Module vgamepad non disponible.\n"
                "Installation:\n"
                "1. Télécharge et installe ViGEmBus: "
                "https://github.com/ViGEm/ViGEmBus/releases\n"
                "2. pip install vgamepad"
            )

        try:
            self.gamepad = vg.VX360Gamepad()
            print("✓ Manette virtuelle Xbox 360 créée")
        except Exception as e:
            raise RuntimeError(
                f"Impossible de créer la manette virtuelle.\n"
                f"Erreur: {e}\n"
                f"As-tu installé ViGEmBus? "
                f"https://github.com/ViGEm/ViGEmBus/releases"
            )

        self.current_state = ControllerState()

    def _clamp(self, value: float, min_val: float = -1.0, max_val: float = 1.0) -> float:
        """Limite une valeur entre min et max"""
        return max(min_val, min(max_val, value))

    def _normalize_to_byte(self, value: float) -> int:
        """
        Convertit une valeur entre -1 et 1 en un byte (0-255)
        0 = -1, 128 = 0, 255 = 1
        """
        normalized = (value + 1.0) / 2.0  # Convertit -1..1 en 0..1
        return int(self._clamp(normalized, 0.0, 1.0) * 255)

    def update(self, controller_state: ControllerState):
        """
        Met à jour la manette virtuelle avec le nouvel état

        Args:
            controller_state: État du contrôleur à appliquer
        """
        # Triggers (throttle)
        if controller_state.throttle > 0:
            # Right trigger = forward
            self.gamepad.right_trigger(value=int(controller_state.throttle * 255))
            self.gamepad.left_trigger(value=0)
        else:
            # Left trigger = reverse
            self.gamepad.left_trigger(value=int(abs(controller_state.throttle) * 255))
            self.gamepad.right_trigger(value=0)

        # Left stick (steer/yaw)
        # Dans Rocket League: stick gauche = steer (au sol) et yaw (en l'air)
        left_x = self._clamp(controller_state.steer)
        self.gamepad.left_joystick_float(x_value_float=left_x, y_value_float=0.0)

        # Right stick (pitch/roll)
        # Dans Rocket League: stick droit = pitch (Y) et roll (X)
        right_x = self._clamp(controller_state.roll)
        right_y = self._clamp(controller_state.pitch)
        self.gamepad.right_joystick_float(x_value_float=right_x, y_value_float=right_y)

        # Boutons
        if controller_state.jump:
            self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        else:
            self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

        if controller_state.boost:
            self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
        else:
            self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)

        if controller_state.handbrake:
            self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
        else:
            self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)

        # Envoie les updates au système
        self.gamepad.update()

        self.current_state = controller_state

    def update_from_array(self, action_array):
        """
        Met à jour depuis un array numpy (format RLBot)

        Args:
            action_array: Array de 8 floats [throttle, steer, pitch, yaw, roll, jump, boost, handbrake]
        """
        controller_state = ControllerState.from_array(action_array)
        self.update(controller_state)

    def reset(self):
        """Remet tous les inputs à zéro"""
        self.update(ControllerState())

    def release(self):
        """Libère la manette virtuelle"""
        try:
            self.reset()
            # Petit délai pour s'assurer que le reset est envoyé
            time.sleep(0.05)
            print("✓ Manette virtuelle libérée")
        except Exception as e:
            print(f"⚠ Erreur lors de la libération de la manette: {e}")

    def __del__(self):
        self.release()


class KeyboardInputSimulator:
    """
    Alternative utilisant des inputs clavier (moins recommandé pour RL)

    REMARQUE: Rocket League préfère les manettes. Cette classe est fournie
    comme alternative si vgamepad ne fonctionne pas, mais la précision sera
    moins bonne (inputs digitaux vs analogiques).
    """

    def __init__(self):
        print("⚠ Simulateur clavier - Précision limitée (digital, pas analog)")
        print("  Recommandation: Utilise VirtualController avec vgamepad")

        # Virtual key codes Windows
        self.VK_W = 0x57  # Forward
        self.VK_S = 0x53  # Reverse
        self.VK_A = 0x41  # Left
        self.VK_D = 0x44  # Right
        self.VK_SPACE = 0x20  # Jump
        self.VK_SHIFT = 0x10  # Boost
        self.VK_CONTROL = 0x11  # Handbrake

        # État actuel
        self.pressed_keys = set()

    def _press_key(self, vk_code):
        """Simule l'appui d'une touche"""
        if vk_code not in self.pressed_keys:
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            self.pressed_keys.add(vk_code)

    def _release_key(self, vk_code):
        """Simule le relâchement d'une touche"""
        if vk_code in self.pressed_keys:
            ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
            self.pressed_keys.discard(vk_code)

    def update_from_array(self, action_array):
        """
        Met à jour depuis un array numpy
        Convertit les valeurs analogiques en inputs digitaux
        """
        controller_state = ControllerState.from_array(action_array)

        # Throttle (digital approximation)
        if controller_state.throttle > 0.3:
            self._press_key(self.VK_W)
        else:
            self._release_key(self.VK_W)

        if controller_state.throttle < -0.3:
            self._press_key(self.VK_S)
        else:
            self._release_key(self.VK_S)

        # Steer (digital approximation)
        if controller_state.steer < -0.3:
            self._press_key(self.VK_A)
        else:
            self._release_key(self.VK_A)

        if controller_state.steer > 0.3:
            self._press_key(self.VK_D)
        else:
            self._release_key(self.VK_D)

        # Buttons
        if controller_state.jump:
            self._press_key(self.VK_SPACE)
        else:
            self._release_key(self.VK_SPACE)

        if controller_state.boost:
            self._press_key(self.VK_SHIFT)
        else:
            self._release_key(self.VK_SHIFT)

        if controller_state.handbrake:
            self._press_key(self.VK_CONTROL)
        else:
            self._release_key(self.VK_CONTROL)

    def reset(self):
        """Relâche toutes les touches"""
        for vk_code in list(self.pressed_keys):
            self._release_key(vk_code)

    def release(self):
        """Libère toutes les touches"""
        self.reset()

    def __del__(self):
        self.release()


def test_virtual_controller():
    """Test interactif du contrôleur virtuel"""
    print("=" * 60)
    print("TEST DU CONTRÔLEUR VIRTUEL")
    print("=" * 60)
    print()

    try:
        controller = VirtualController()
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return

    print("\n✓ Contrôleur virtuel créé avec succès!")
    print("\nLance Rocket League et va dans:")
    print("  Settings > Controls > Change Bindings")
    print("\nTu devrais voir une manette Xbox 360 détectée.")
    print("\nTest de mouvements en cours...\n")

    try:
        # Test séquence
        print("1. Forward + Boost pendant 2 secondes...")
        state = ControllerState(throttle=1.0, boost=True)
        for _ in range(20):
            controller.update(state)
            time.sleep(0.1)

        print("2. Steer gauche pendant 1 seconde...")
        state = ControllerState(throttle=1.0, steer=-1.0)
        for _ in range(10):
            controller.update(state)
            time.sleep(0.1)

        print("3. Jump!")
        state = ControllerState(throttle=1.0, jump=True)
        for _ in range(3):
            controller.update(state)
            time.sleep(0.1)

        print("4. Pitch up en l'air...")
        state = ControllerState(pitch=1.0, boost=True)
        for _ in range(10):
            controller.update(state)
            time.sleep(0.1)

        print("\n✓ Test terminé!")

    finally:
        controller.release()
        print("\n✓ Contrôleur libéré")


if __name__ == "__main__":
    test_virtual_controller()
