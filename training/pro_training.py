"""
ZENITOBOT PRO TRAINING - SSL+++ MECHANICS MASTERY
==================================================
Training ultra-avancé pour apprendre TOUTES les mécaniques de niveau professionnel
Optimisé pour 2v2 avec système de checkpoints automatique

Mécaniques couvertes:
- Powershots (wall, upside down, air roll, ground, aerial)
- Backboard clears/shots
- Dribbling avancé (tous types de flicks, wavedash, etc.)
- Aerials pro (flip reset, musty, air roll, heli resets)
- Fast aerial & half flips
- Redirects
- Recoveries avancées (wavedash, chain dash, bunny jump)
- Bounce/ground/wall to air dribbles
- Ceiling shots, double taps, pinches
- Shadow defense, squishy save, flip cancel
- Turtle, stall, ceiling shuffle, hel jump
"""

from typing import List, Dict, Any
import numpy as np
import os
from pathlib import Path

# Fix Windows encoding issues
os.environ['PYTHONIOENCODING'] = 'utf-8'

from rlgym.api import RewardFunction, AgentID, StateMutator
from rlgym.rocket_league.api import GameState
from rlgym.rocket_league import common_values


# ============================================================================
# SYSTÈME DE CHECKPOINTS AVANCÉ
# ============================================================================

def find_best_checkpoint():
    """Find the best checkpoint directory (highest timesteps)"""
    base_dir = Path("data/checkpoints")

    if not base_dir.exists():
        print("[CHECKPOINT] No checkpoints found, starting from scratch")
        return None

    checkpoint_dirs = []
    for run_dir in base_dir.iterdir():
        if run_dir.is_dir():
            for ts_dir in run_dir.iterdir():
                if ts_dir.is_dir() and (ts_dir / "PPO_POLICY.pt").exists():
                    try:
                        timesteps = int(ts_dir.name)
                        checkpoint_dirs.append((ts_dir, timesteps))
                    except ValueError:
                        pass

    if not checkpoint_dirs:
        print("[CHECKPOINT] No valid checkpoints found, starting from scratch")
        return None

    checkpoint_dirs.sort(key=lambda x: x[1], reverse=True)
    best = checkpoint_dirs[0]
    print(f"[CHECKPOINT] Found best checkpoint: {best[0].parent.name}/{best[0].name}")
    print(f"[CHECKPOINT] Resuming from: {best[1]:,} timesteps")
    return str(best[0])


# ============================================================================
# REWARD FUNCTIONS - POWERSHOTS
# ============================================================================

class PowershotReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les powershots - tirs puissants depuis différentes positions"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.last_touches = {agent: 0 for agent in agents}
        self.last_ball_vel = np.linalg.norm(initial_state.ball.linear_velocity)

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        ball_vel = np.linalg.norm(state.ball.linear_velocity)

        for agent in agents:
            car = state.cars[agent]
            current_touches = car.ball_touches

            if current_touches > self.last_touches[agent]:
                vel_increase = ball_vel - self.last_ball_vel
                car_pos = car.physics.position
                car_height = car_pos[2]

                # Détection du type de powershot
                is_on_wall = abs(car_pos[0]) > 3500 or abs(car_pos[1]) > 4500
                is_upside_down = car.physics.up[2] < -0.5  # Toit vers le bas
                is_aerial = car_height > 300
                is_air_rolling = np.linalg.norm(car.physics.angular_velocity) > 3.0

                # Powershot = contact puissant (augmentation vitesse significative)
                if vel_increase > 800:  # Powershot détecté
                    base_reward = 5.0

                    # BONUS selon le type de powershot
                    if is_on_wall:
                        base_reward += 3.0  # Wall powershot
                    if is_upside_down:
                        base_reward += 4.0  # Upside down powershot (très difficile)
                    if is_air_rolling:
                        base_reward += 3.5  # Air roll powershot
                    if is_aerial and not is_on_wall:
                        base_reward += 4.0  # Aerial powershot
                    if not is_aerial and not is_on_wall and car_height < 50:
                        base_reward += 2.0  # Ground powershot

                    # MEGA BONUS si combinaison de techniques
                    if (is_upside_down and is_air_rolling) or (is_aerial and is_air_rolling and vel_increase > 1200):
                        base_reward += 5.0  # Powershot combiné ultra-avancé

                    rewards[agent] = base_reward
                else:
                    rewards[agent] = 0.0

                self.last_touches[agent] = current_touches
            else:
                rewards[agent] = 0.0

        self.last_ball_vel = ball_vel
        return rewards


class BackboardReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les backboard clears et shots"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.last_touches = {agent: 0 for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        ball_pos = state.ball.position
        ball_height = ball_pos[2]

        for agent in agents:
            car = state.cars[agent]
            current_touches = car.ball_touches

            # Backboard = balle haute et proche du mur arrière
            is_on_backboard = ball_height > 500 and (abs(ball_pos[1]) > 4000)

            if current_touches > self.last_touches[agent] and is_on_backboard:
                car_pos = car.physics.position

                # Déterminer si c'est un clear (défense) ou un shot (attaque)
                if car.is_orange:
                    own_goal_y = common_values.BACK_NET_Y
                    opp_goal_y = -common_values.BACK_NET_Y
                else:
                    own_goal_y = -common_values.BACK_NET_Y
                    opp_goal_y = common_values.BACK_NET_Y

                # Clear = balle proche de notre but, on l'éloigne
                is_defensive = abs(ball_pos[1] - own_goal_y) < abs(ball_pos[1] - opp_goal_y)

                ball_vel_toward_opp = state.ball.linear_velocity[1] * (1 if opp_goal_y > 0 else -1)

                if is_defensive:
                    # Backboard clear (défensif)
                    if ball_vel_toward_opp > 500:  # On éloigne la balle
                        rewards[agent] = 8.0  # Gros reward pour clear depuis backboard
                    else:
                        rewards[agent] = 3.0
                else:
                    # Backboard shot (offensif)
                    if ball_vel_toward_opp > 800:  # Tir puissant vers le but
                        rewards[agent] = 10.0  # Énorme reward pour backboard shot
                    else:
                        rewards[agent] = 4.0

                self.last_touches[agent] = current_touches
            else:
                rewards[agent] = 0.0

        return rewards


# ============================================================================
# REWARD FUNCTIONS - DRIBBLING AVANCÉ
# ============================================================================

class AdvancedDribblingReward(RewardFunction[AgentID, GameState, float]):
    """Récompense le dribbling avancé avec détection des différents types de flicks"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.ball_on_car = {agent: False for agent in agents}
        self.dribble_time = {agent: 0 for agent in agents}
        self.last_car_pitch = {agent: 0.0 for agent in agents}
        self.last_ball_vel = np.linalg.norm(initial_state.ball.linear_velocity)
        self.last_touches = {agent: 0 for agent in agents}
        self.powerslide_dribble = {agent: False for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        ball_vel = np.linalg.norm(state.ball.linear_velocity)
        ball_pos = state.ball.position

        for agent in agents:
            car = state.cars[agent]
            car_pos = car.physics.position
            car_pitch = car.physics.euler_angles[0]  # pitch
            current_touches = car.ball_touches

            # Balle sur le toit de la voiture
            above_car = ball_pos[2] - car_pos[2]
            horizontal_dist = np.linalg.norm(ball_pos[:2] - car_pos[:2])

            # Dribble standard (balle sur le toit)
            if 80 < above_car < 250 and horizontal_dist < 120:
                self.ball_on_car[agent] = True
                self.dribble_time[agent] += 1

                # Powerslide dribble detection
                if car.handbrake:
                    self.powerslide_dribble[agent] = True
                    rewards[agent] = 1.5  # Bonus powerslide dribble
                else:
                    rewards[agent] = 0.8  # Bonus dribble normal

            elif self.ball_on_car[agent]:
                # Vient de quitter le toit - FLICK détecté !
                vel_increase = ball_vel - self.last_ball_vel
                pitch_change = abs(car_pitch - self.last_car_pitch[agent])

                if vel_increase > 600:  # Flick réussi
                    base_reward = 6.0

                    # Détection du type de flick selon angle et vitesse
                    if pitch_change > 0.8 and vel_increase > 1500:
                        # Musty flick (flip backwards)
                        base_reward = 15.0
                    elif pitch_change > 0.6 and vel_increase > 1200:
                        # 180° flick
                        base_reward = 12.0
                    elif pitch_change > 0.4 and vel_increase > 1000:
                        # 90° flick
                        base_reward = 10.0
                    elif pitch_change > 0.2 and vel_increase > 800:
                        # 45° flick
                        base_reward = 8.0
                    elif self.dribble_time[agent] > 60:
                        # Delayed flick (attendre avant de flick)
                        base_reward = 11.0
                    elif self.powerslide_dribble[agent]:
                        # Flick depuis powerslide
                        base_reward = 9.0

                    # Wavedash flick (détection approximative)
                    if car.physics.position[2] < 30 and vel_increase > 1100:
                        base_reward = 13.0  # Wavedash flick

                    # Breezy/Mawkzy flick (très complexe, détection par air roll + flick)
                    if np.linalg.norm(car.physics.angular_velocity) > 4.0 and vel_increase > 1300:
                        base_reward = 16.0  # Breezy/Mawkzy flick

                    rewards[agent] = base_reward
                else:
                    rewards[agent] = 0.0

                self.ball_on_car[agent] = False
                self.dribble_time[agent] = 0
                self.powerslide_dribble[agent] = False
            else:
                rewards[agent] = 0.0

            self.last_car_pitch[agent] = car_pitch
            self.last_touches[agent] = current_touches

        self.last_ball_vel = ball_vel
        return rewards


class BounceDribbleReward(RewardFunction[AgentID, GameState, float]):
    """Récompense le bounce dribbling - contrôle de balle en rebond"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.last_ball_height = initial_state.ball.position[2]
        self.bounce_count = {agent: 0 for agent in agents}
        self.controlling = {agent: False for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        ball_height = state.ball.position[2]
        ball_vel_z = state.ball.linear_velocity[2]

        for agent in agents:
            car = state.cars[agent]
            dist_to_ball = np.linalg.norm(state.ball.position - car.physics.position)

            # Proche de la balle = contrôle
            if dist_to_ball < 400:
                # Détection de rebond (balle monte après avoir touché le sol)
                if ball_height < 200 and ball_vel_z > 0 and self.last_ball_height < ball_height:
                    self.bounce_count[agent] += 1
                    self.controlling[agent] = True

                if self.controlling[agent]:
                    # Récompense proportionnelle au nombre de rebonds contrôlés
                    rewards[agent] = min(self.bounce_count[agent] * 0.5, 5.0)
                else:
                    rewards[agent] = 0.0
            else:
                # Perd le contrôle
                self.bounce_count[agent] = 0
                self.controlling[agent] = False
                rewards[agent] = 0.0

        self.last_ball_height = ball_height
        return rewards


class AirDribbleReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les air dribbles (ground to air et wall to air)"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.air_dribble_active = {agent: False for agent in agents}
        self.air_touches = {agent: 0 for agent in agents}
        self.last_touches = {agent: 0 for agent in agents}
        self.started_from_wall = {agent: False for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        ball_height = state.ball.position[2]
        ball_pos = state.ball.position

        for agent in agents:
            car = state.cars[agent]
            car_height = car.physics.position[2]
            current_touches = car.ball_touches
            dist_to_ball = np.linalg.norm(ball_pos - car.physics.position)

            # Détection wall to air dribble
            is_near_wall = abs(car.physics.position[0]) > 3000 or abs(car.physics.position[1]) > 4000

            # Air dribble = balle en l'air, voiture en l'air, proche de la balle, plusieurs touches
            if ball_height > 200 and car_height > 150 and dist_to_ball < 300:
                if current_touches > self.last_touches[agent]:
                    self.air_touches[agent] += 1
                    self.air_dribble_active[agent] = True

                    if is_near_wall and not self.started_from_wall[agent]:
                        self.started_from_wall[agent] = True

                if self.air_dribble_active[agent]:
                    base_reward = min(self.air_touches[agent] * 1.5, 10.0)

                    # MEGA BONUS pour wall to air dribble
                    if self.started_from_wall[agent]:
                        base_reward *= 1.8  # Wall to air dribble est plus difficile

                    rewards[agent] = base_reward
                else:
                    rewards[agent] = 0.0
            else:
                # Fin de l'air dribble
                if self.air_dribble_active[agent] and self.air_touches[agent] >= 2:
                    # Bonus final pour air dribble réussi
                    final_bonus = 5.0 if self.started_from_wall[agent] else 3.0
                    rewards[agent] = final_bonus
                else:
                    rewards[agent] = 0.0

                self.air_dribble_active[agent] = False
                self.air_touches[agent] = 0
                self.started_from_wall[agent] = False

            self.last_touches[agent] = current_touches

        return rewards


# ============================================================================
# REWARD FUNCTIONS - AERIALS AVANCÉS
# ============================================================================

class FastAerialReward(RewardFunction[AgentID, GameState, float]):
    """Récompense le fast aerial (jump + boost + flip)"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.jumped = {agent: False for agent in agents}
        self.jump_time = {agent: 0 for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        for agent in agents:
            car = state.cars[agent]
            car_height = car.physics.position[2]
            ball_height = state.ball.position[2]

            # Détection de saut
            if not car.on_ground and car_height > 100:
                if not self.jumped[agent]:
                    self.jumped[agent] = True
                    self.jump_time[agent] = 0

                self.jump_time[agent] += 1

                # Fast aerial = montée rapide avec boost
                vertical_velocity = car.physics.linear_velocity[2]
                is_boosting = car.is_boosting

                # Fast aerial réussi si montée rapide (> 1000 uu/s vertical)
                if vertical_velocity > 1000 and is_boosting and self.jump_time[agent] < 30:
                    rewards[agent] = 2.0  # Bonus fast aerial

                    # Bonus supplémentaire si balle haute
                    if ball_height > 600 and np.linalg.norm(state.ball.position - car.physics.position) < 500:
                        rewards[agent] = 4.0  # Fast aerial vers balle haute
                else:
                    rewards[agent] = 0.0
            else:
                self.jumped[agent] = False
                rewards[agent] = 0.0

        return rewards


class FlipResetReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les flip resets"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.had_flip = {agent: True for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        for agent in agents:
            car = state.cars[agent]
            car_height = car.physics.position[2]
            has_flip = car.has_flip
            dist_to_ball = np.linalg.norm(state.ball.position - car.physics.position)

            # Flip reset = retrouve le flip en l'air en touchant la balle avec les 4 roues
            if not self.had_flip[agent] and has_flip and car_height > 200:
                # Flip reset détecté !
                if dist_to_ball < 250:  # Proche de la balle = probablement flip reset
                    rewards[agent] = 20.0  # ÉNORME reward pour flip reset
                else:
                    rewards[agent] = 0.0
            else:
                rewards[agent] = 0.0

            self.had_flip[agent] = has_flip

        return rewards


class MustyAerialReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les musty aerials (backflip aerial hit)"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.last_touches = {agent: 0 for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        for agent in agents:
            car = state.cars[agent]
            car_height = car.physics.position[2]
            current_touches = car.ball_touches

            if current_touches > self.last_touches[agent]:
                # Musty = en l'air + pitch négatif important (backflip) + contact
                car_pitch = car.physics.euler_angles[0]

                if car_height > 200 and car_pitch < -0.5:  # Backflip en l'air
                    rewards[agent] = 18.0  # Énorme reward pour musty aerial
                else:
                    rewards[agent] = 0.0

                self.last_touches[agent] = current_touches
            else:
                rewards[agent] = 0.0

        return rewards


class HeliResetReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les heli resets (spin rapide pour reset)"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.had_flip = {agent: True for agent in agents}
        self.high_spin = {agent: False for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        for agent in agents:
            car = state.cars[agent]
            has_flip = car.has_flip
            car_height = car.physics.position[2]
            ang_vel = np.linalg.norm(car.physics.angular_velocity)

            # Détection spin rapide en l'air
            if car_height > 200 and ang_vel > 5.0:
                self.high_spin[agent] = True

            # Heli reset = flip reset avec spin très rapide
            if not self.had_flip[agent] and has_flip and self.high_spin[agent]:
                rewards[agent] = 25.0  # MEGA reward pour heli reset
                self.high_spin[agent] = False
            else:
                rewards[agent] = 0.0

            self.had_flip[agent] = has_flip

        return rewards


# ============================================================================
# REWARD FUNCTIONS - CEILING & DOUBLE TAP
# ============================================================================

class CeilingShotReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les ceiling shots"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.was_on_ceiling = {agent: False for agent in agents}
        self.last_touches = {agent: 0 for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        ball_pos = state.ball.position

        for agent in agents:
            car = state.cars[agent]
            car_height = car.physics.position[2]
            current_touches = car.ball_touches

            # Sur le plafond
            if car_height > 1900:
                self.was_on_ceiling[agent] = True

            # Ceiling shot = vient du plafond et touche la balle en l'air
            if self.was_on_ceiling[agent] and current_touches > self.last_touches[agent]:
                if car_height > 500 and ball_pos[2] > 400:
                    # Bonus selon si c'est dirigé vers le but
                    if car.is_orange:
                        opp_goal_y = -common_values.BACK_NET_Y
                    else:
                        opp_goal_y = common_values.BACK_NET_Y

                    ball_vel_toward_goal = state.ball.linear_velocity[1] * (1 if opp_goal_y > 0 else -1)

                    if ball_vel_toward_goal > 500:
                        rewards[agent] = 15.0  # Ceiling shot vers le but
                    else:
                        rewards[agent] = 8.0  # Ceiling shot basique

                    self.was_on_ceiling[agent] = False
                else:
                    rewards[agent] = 0.0

                self.last_touches[agent] = current_touches
            else:
                rewards[agent] = 0.0

            # Reset si retombe au sol
            if car.on_ground:
                self.was_on_ceiling[agent] = False

        return rewards


class DoubleTapReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les double taps (2 touches aériennes consécutives)"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.first_aerial_touch = {agent: False for agent in agents}
        self.last_touches = {agent: 0 for agent in agents}
        self.aerial_touches = {agent: 0 for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        ball_height = state.ball.position[2]

        for agent in agents:
            car = state.cars[agent]
            car_height = car.physics.position[2]
            current_touches = car.ball_touches

            # Touche aérienne (balle et voiture en l'air)
            if current_touches > self.last_touches[agent] and ball_height > 300 and car_height > 200:
                self.aerial_touches[agent] += 1

                if self.aerial_touches[agent] == 1:
                    self.first_aerial_touch[agent] = True
                    rewards[agent] = 0.0
                elif self.aerial_touches[agent] == 2:
                    # DOUBLE TAP !
                    rewards[agent] = 18.0  # Énorme reward pour double tap
                    self.first_aerial_touch[agent] = False
                    self.aerial_touches[agent] = 0
                else:
                    rewards[agent] = 0.0

                self.last_touches[agent] = current_touches
            else:
                rewards[agent] = 0.0

            # Reset si touche le sol
            if car.on_ground:
                self.first_aerial_touch[agent] = False
                self.aerial_touches[agent] = 0

        return rewards


# ============================================================================
# REWARD FUNCTIONS - RECOVERIES AVANCÉES
# ============================================================================

class WavedashReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les wavedashes"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.was_airborne = {agent: False for agent in agents}
        self.jump_time = {agent: 0 for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        for agent in agents:
            car = state.cars[agent]
            car_height = car.physics.position[2]
            horizontal_speed = np.linalg.norm(car.physics.linear_velocity[:2])

            if car_height > 20 and not car.on_ground:
                self.was_airborne[agent] = True
                self.jump_time[agent] += 1

            # Wavedash = atterrissage rapide avec boost de vitesse
            if self.was_airborne[agent] and car.on_ground:
                # Wavedash réussi si temps en l'air court et vitesse élevée
                if self.jump_time[agent] < 20 and horizontal_speed > 1800:
                    rewards[agent] = 5.0  # Reward pour wavedash
                else:
                    rewards[agent] = 0.0

                self.was_airborne[agent] = False
                self.jump_time[agent] = 0
            else:
                rewards[agent] = 0.0

        return rewards


class ChainDashReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les chain dashes (wavedashes multiples)"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.consecutive_wavedashes = {agent: 0 for agent in agents}
        self.last_wavedash_time = {agent: 0 for agent in agents}
        self.frame_count = 0

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        self.frame_count += 1

        for agent in agents:
            car = state.cars[agent]
            horizontal_speed = np.linalg.norm(car.physics.linear_velocity[:2])

            # Détection wavedash (vitesse élevée au sol)
            if car.on_ground and horizontal_speed > 1800:
                # Chain dash = wavedash dans les 60 frames du précédent
                if self.frame_count - self.last_wavedash_time[agent] < 60:
                    self.consecutive_wavedashes[agent] += 1
                    # Reward croissant pour chain
                    rewards[agent] = min(self.consecutive_wavedashes[agent] * 2.0, 12.0)
                else:
                    self.consecutive_wavedashes[agent] = 1
                    rewards[agent] = 0.0

                self.last_wavedash_time[agent] = self.frame_count
            else:
                rewards[agent] = 0.0

        return rewards


class HalfFlipReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les half flips"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.backflip_started = {agent: False for agent in agents}
        self.initial_direction = {agent: np.array([1.0, 0.0, 0.0]) for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        for agent in agents:
            car = state.cars[agent]
            car_pitch = car.physics.euler_angles[0]

            # Détection backflip (pitch négatif)
            if not car.on_ground and car_pitch < -0.8:
                if not self.backflip_started[agent]:
                    self.backflip_started[agent] = True
                    # Sauvegarder direction initiale
                    yaw = car.physics.euler_angles[1]
                    self.initial_direction[agent] = np.array([np.cos(yaw), np.sin(yaw), 0.0])

            # Half flip = atterrit orienté vers l'avant après backflip
            if self.backflip_started[agent] and car.on_ground:
                yaw = car.physics.euler_angles[1]
                current_direction = np.array([np.cos(yaw), np.sin(yaw), 0.0])

                # Calculer différence d'angle (devrait être ~180° pour half flip)
                dot = np.dot(self.initial_direction[agent], current_direction)
                if dot < -0.7:  # ~180° retournement
                    rewards[agent] = 8.0  # Reward pour half flip réussi
                else:
                    rewards[agent] = 0.0

                self.backflip_started[agent] = False
            else:
                rewards[agent] = 0.0

        return rewards


# ============================================================================
# REWARD FUNCTIONS - AUTRES MÉCANIQUES AVANCÉES
# ============================================================================

class RedirectReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les redirects (changement de direction de balle en l'air)"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.last_ball_direction = initial_state.ball.linear_velocity / (np.linalg.norm(initial_state.ball.linear_velocity) + 1e-6)
        self.last_touches = {agent: 0 for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        ball_vel = state.ball.linear_velocity
        ball_speed = np.linalg.norm(ball_vel)

        if ball_speed > 10:
            current_ball_direction = ball_vel / ball_speed
        else:
            current_ball_direction = self.last_ball_direction

        ball_height = state.ball.position[2]

        for agent in agents:
            car = state.cars[agent]
            car_height = car.physics.position[2]
            current_touches = car.ball_touches

            # Redirect = touche aérienne qui change la direction de la balle
            if current_touches > self.last_touches[agent] and ball_height > 300 and car_height > 200:
                # Calculer le changement de direction
                direction_change = 1.0 - np.dot(self.last_ball_direction, current_ball_direction)

                # Redirect significatif
                if direction_change > 0.4:  # ~45° minimum
                    base_reward = 10.0 * direction_change  # Jusqu'à 20 pour redirect à 180°

                    # Bonus si dirigé vers le but adverse
                    if car.is_orange:
                        opp_goal_y = -common_values.BACK_NET_Y
                    else:
                        opp_goal_y = common_values.BACK_NET_Y

                    to_goal = np.array([0, opp_goal_y, 100]) - state.ball.position
                    to_goal_dir = to_goal / (np.linalg.norm(to_goal) + 1e-6)
                    goal_alignment = max(0, np.dot(current_ball_direction, to_goal_dir))

                    rewards[agent] = base_reward * (1 + goal_alignment)
                else:
                    rewards[agent] = 0.0

                self.last_touches[agent] = current_touches
            else:
                rewards[agent] = 0.0

        self.last_ball_direction = current_ball_direction
        return rewards


class PinchReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les pinches (wall, ground, ceiling, goal post)"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.last_ball_vel = np.linalg.norm(initial_state.ball.linear_velocity)
        self.last_touches = {agent: 0 for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        ball_vel = np.linalg.norm(state.ball.linear_velocity)
        ball_pos = state.ball.position

        for agent in agents:
            car = state.cars[agent]
            current_touches = car.ball_touches

            if current_touches > self.last_touches[agent]:
                vel_increase = ball_vel - self.last_ball_vel

                # Pinch = augmentation MASSIVE de vitesse
                if vel_increase > 1500:
                    # Détection du type de pinch
                    is_near_wall = abs(ball_pos[0]) > 3800 or abs(ball_pos[1]) > 4800
                    is_near_ceiling = ball_pos[2] > 1800
                    is_near_ground = ball_pos[2] < 200
                    is_near_goal_post = (abs(ball_pos[1]) > 4800 and abs(ball_pos[0]) < 1000)

                    base_reward = 12.0

                    if is_near_goal_post:
                        base_reward = 25.0  # Goal post pinch = ultra rare
                    elif is_near_ceiling:
                        base_reward = 18.0  # Ceiling pinch
                    elif is_near_wall:
                        base_reward = 15.0  # Wall pinch
                    elif is_near_ground:
                        base_reward = 14.0  # Ground pinch

                    rewards[agent] = base_reward
                else:
                    rewards[agent] = 0.0

                self.last_touches[agent] = current_touches
            else:
                rewards[agent] = 0.0

        self.last_ball_vel = ball_vel
        return rewards


class ShadowDefenseReward(RewardFunction[AgentID, GameState, float]):
    """Récompense le shadow defense - suivre l'attaquant en défense"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        pass

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        for agent in agents:
            car = state.cars[agent]
            ball_pos = state.ball.position

            # Position du but à défendre
            if car.is_orange:
                own_goal = np.array([0, common_values.BACK_NET_Y, 100])
            else:
                own_goal = np.array([0, -common_values.BACK_NET_Y, 100])

            # Shadow defense = être entre la balle et le but, en reculant
            to_goal = own_goal - ball_pos
            to_car = car.physics.position - ball_pos
            car_to_goal = own_goal - car.physics.position

            dist_ball_goal = np.linalg.norm(to_goal)
            dist_ball_car = np.linalg.norm(to_car)
            dist_car_goal = np.linalg.norm(car_to_goal)

            # Bon positionnement défensif
            if dist_ball_goal > 1e-6 and dist_ball_car > 1e-6:
                alignment = np.dot(to_goal / dist_ball_goal, to_car / dist_ball_car)

                # Vitesse vers le but (reculer)
                car_vel = car.physics.linear_velocity
                vel_toward_goal = np.dot(car_vel, car_to_goal / (dist_car_goal + 1e-6))

                # Shadow defense = bien aligné + recule vers le but
                if alignment > 0.85 and vel_toward_goal > 500 and dist_car_goal < 2000:
                    rewards[agent] = 3.0  # Reward pour shadow defense
                else:
                    rewards[agent] = 0.0
            else:
                rewards[agent] = 0.0

        return rewards


class FlipCancelReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les flip cancels"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.flipping = {agent: False for agent in agents}
        self.flip_start_pitch = {agent: 0.0 for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        for agent in agents:
            car = state.cars[agent]
            car_pitch = car.physics.euler_angles[0]
            pitch_vel = car.physics.angular_velocity[1]  # Pitch angular velocity

            # Détection flip (changement rapide de pitch)
            if abs(pitch_vel) > 3.0 and not car.on_ground:
                if not self.flipping[agent]:
                    self.flipping[agent] = True
                    self.flip_start_pitch[agent] = car_pitch

            # Flip cancel = arrêt du flip avant complétion
            if self.flipping[agent] and abs(pitch_vel) < 1.0:
                pitch_change = abs(car_pitch - self.flip_start_pitch[agent])

                # Cancel détecté si pitch change < 90° (flip incomplet)
                if 0.3 < pitch_change < 1.3:  # Entre ~20° et ~75°
                    rewards[agent] = 7.0  # Reward pour flip cancel
                else:
                    rewards[agent] = 0.0

                self.flipping[agent] = False
            else:
                rewards[agent] = 0.0

            # Reset si touche le sol
            if car.on_ground:
                self.flipping[agent] = False

        return rewards


class TurtleReward(RewardFunction[AgentID, GameState, float]):
    """Récompense le turtle (jouer sur le toit)"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.last_touches = {agent: 0 for agent in agents}
        self.turtle_time = {agent: 0 for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        for agent in agents:
            car = state.cars[agent]
            current_touches = car.ball_touches
            is_upside_down = car.physics.up[2] < -0.8  # Toit vers le sol

            # Turtle = upside down au sol
            if is_upside_down and car.on_ground:
                self.turtle_time[agent] += 1
                rewards[agent] = 0.5  # Petit bonus pour turtle

                # GROS bonus si touche la balle en turtle
                if current_touches > self.last_touches[agent]:
                    rewards[agent] = 10.0  # Turtle shot

                    # MEGA bonus si balle va vite (turtle powershot)
                    ball_vel = np.linalg.norm(state.ball.linear_velocity)
                    if ball_vel > 1500:
                        rewards[agent] = 15.0  # Turtle powershot
            else:
                self.turtle_time[agent] = 0
                rewards[agent] = 0.0

            self.last_touches[agent] = current_touches

        return rewards


class StallReward(RewardFunction[AgentID, GameState, float]):
    """Récompense les stalls (rester en l'air sans boost)"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.airborne_time = {agent: 0 for agent in agents}
        self.stalling = {agent: False for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        for agent in agents:
            car = state.cars[agent]
            car_height = car.physics.position[2]
            vertical_vel = car.physics.linear_velocity[2]

            # Stall = en l'air, pas de boost, vitesse verticale proche de 0
            if not car.on_ground and car_height > 200:
                self.airborne_time[agent] += 1

                if not car.is_boosting and abs(vertical_vel) < 100 and car_height > 300:
                    self.stalling[agent] = True
                    # Reward croissant pour stall prolongé
                    rewards[agent] = min(self.airborne_time[agent] * 0.1, 8.0)
                else:
                    self.stalling[agent] = False
                    rewards[agent] = 0.0
            else:
                self.airborne_time[agent] = 0
                self.stalling[agent] = False
                rewards[agent] = 0.0

        return rewards


class CeilingShuffleReward(RewardFunction[AgentID, GameState, float]):
    """Récompense le ceiling shuffle (déplacement rapide au plafond)"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.on_ceiling_time = {agent: 0 for agent in agents}

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        for agent in agents:
            car = state.cars[agent]
            car_height = car.physics.position[2]
            horizontal_speed = np.linalg.norm(car.physics.linear_velocity[:2])

            # Ceiling shuffle = au plafond + vitesse horizontale élevée
            if car_height > 1900 and car.on_ground:  # On ground = sur le plafond
                self.on_ceiling_time[agent] += 1

                if horizontal_speed > 1200:  # Vitesse élevée
                    rewards[agent] = 4.0  # Reward pour ceiling shuffle
                else:
                    rewards[agent] = 1.0  # Bonus pour être au plafond
            else:
                self.on_ceiling_time[agent] = 0
                rewards[agent] = 0.0

        return rewards


# ============================================================================
# REWARD FUNCTIONS DE BASE (réutilisées)
# ============================================================================

class VelocityPlayerToBallReward(RewardFunction[AgentID, GameState, float]):
    """Reward for moving toward ball"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        pass

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        for agent in agents:
            car = state.cars[agent]
            player_vel = car.physics.linear_velocity
            pos_diff = state.ball.position - car.physics.position
            dist_to_ball = np.linalg.norm(pos_diff)

            if dist_to_ball < 1e-6:
                rewards[agent] = 0.0
            else:
                dir_to_ball = pos_diff / dist_to_ball
                speed_toward_ball = np.dot(player_vel, dir_to_ball)
                rewards[agent] = np.clip(speed_toward_ball / common_values.CAR_MAX_SPEED, -1.0, 1.0)
        return rewards


class FaceBallReward(RewardFunction[AgentID, GameState, float]):
    """Reward for facing the ball"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        pass

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        for agent in agents:
            car = state.cars[agent]
            pos_diff = state.ball.position - car.physics.position
            dist = np.linalg.norm(pos_diff)

            if dist < 1e-6:
                rewards[agent] = 0.0
            else:
                pitch = car.physics.euler_angles[0]
                yaw = car.physics.euler_angles[1]

                forward = np.array([
                    np.cos(yaw) * np.cos(pitch),
                    np.sin(yaw) * np.cos(pitch),
                    np.sin(pitch)
                ])

                dir_to_ball = pos_diff / dist
                dot = np.dot(forward, dir_to_ball)
                rewards[agent] = max(dot, 0.0)
        return rewards


class VelocityBallToGoalReward(RewardFunction[AgentID, GameState, float]):
    """Reward for hitting ball toward opponent goal"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        pass

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}
        for agent in agents:
            car = state.cars[agent]
            ball = state.ball

            if car.is_orange:
                goal_pos = np.array([0, -common_values.BACK_NET_Y, 100])
            else:
                goal_pos = np.array([0, common_values.BACK_NET_Y, 100])

            pos_diff = goal_pos - ball.position
            dist = np.linalg.norm(pos_diff)

            if dist < 1e-6:
                rewards[agent] = 0.0
            else:
                dir_to_goal = pos_diff / dist
                ball_vel = ball.linear_velocity
                vel_toward_goal = np.dot(ball_vel, dir_to_goal)
                rewards[agent] = max(vel_toward_goal / common_values.BALL_MAX_SPEED, 0.0)
        return rewards


class GoalReward(RewardFunction[AgentID, GameState, float]):
    """Reward for scoring goals"""

    def reset(self, agents: List[AgentID], initial_state: GameState, shared_info: Dict[str, Any]) -> None:
        self.last_goal_scored = False

    def get_rewards(self, agents: List[AgentID], state: GameState, is_terminated: Dict[AgentID, bool],
                    is_truncated: Dict[AgentID, bool], shared_info: Dict[str, Any]) -> Dict[AgentID, float]:
        rewards = {}

        if state.goal_scored:
            for agent in agents:
                car = state.cars[agent]
                # Reward team that scored, penalize other team
                if car.is_orange:
                    rewards[agent] = 10.0 if state.scoring_team == 1 else -10.0
                else:
                    rewards[agent] = 10.0 if state.scoring_team == 0 else -10.0
        else:
            for agent in agents:
                rewards[agent] = 0.0

        return rewards


# ============================================================================
# CONSTRUCTION DE L'ENVIRONNEMENT
# ============================================================================

def build_rlgym_v2_env():
    """Build PRO RLGym environment with ALL advanced mechanics"""
    from rlgym.api import RLGym
    from rlgym.rocket_league.action_parsers import LookupTableAction, RepeatAction
    from rlgym.rocket_league.done_conditions import GoalCondition, NoTouchTimeoutCondition, TimeoutCondition, AnyCondition
    from rlgym.rocket_league.obs_builders import DefaultObs
    from rlgym.rocket_league.reward_functions import CombinedReward
    from rlgym.rocket_league.sim import RocketSimEngine
    from rlgym.rocket_league.state_mutators import MutatorSequence, FixedTeamSizeMutator, KickoffMutator
    from rlgym_ppo.util import RLGymV2GymWrapper

    # 2v2 configuration
    spawn_opponents = True
    team_size = 2
    blue_team_size = team_size
    orange_team_size = team_size if spawn_opponents else 0

    action_repeat = 4
    no_touch_timeout_seconds = 20
    game_timeout_seconds = 180

    action_parser = RepeatAction(LookupTableAction(), repeats=action_repeat)
    termination_condition = GoalCondition()
    truncation_condition = AnyCondition(
        NoTouchTimeoutCondition(timeout_seconds=no_touch_timeout_seconds),
        TimeoutCondition(timeout_seconds=game_timeout_seconds)
    )

    # SYSTÈME DE REWARDS ULTRA-COMPLET POUR SSL+++
    reward_fn = CombinedReward(
        # BASES FONDAMENTALES
        (VelocityPlayerToBallReward(), 0.2),
        (FaceBallReward(), 0.3),
        (VelocityBallToGoalReward(), 6.0),

        # POWERSHOTS (TOUTES VARIATIONS)
        (PowershotReward(), 12.0),
        (BackboardReward(), 10.0),

        # DRIBBLING AVANCÉ
        (AdvancedDribblingReward(), 15.0),  # Tous les flicks
        (BounceDribbleReward(), 6.0),
        (AirDribbleReward(), 14.0),  # Ground to air + wall to air

        # AERIALS PRO
        (FastAerialReward(), 5.0),
        (FlipResetReward(), 20.0),
        (MustyAerialReward(), 18.0),
        (HeliResetReward(), 25.0),

        # CEILING & DOUBLE TAP
        (CeilingShotReward(), 15.0),
        (DoubleTapReward(), 18.0),

        # RECOVERIES AVANCÉES
        (WavedashReward(), 5.0),
        (ChainDashReward(), 8.0),
        (HalfFlipReward(), 8.0),

        # MÉCANIQUES TECHNIQUES
        (RedirectReward(), 12.0),
        (PinchReward(), 15.0),
        (ShadowDefenseReward(), 4.0),
        (FlipCancelReward(), 7.0),

        # MÉCANIQUES SPÉCIALES
        (TurtleReward(), 10.0),
        (StallReward(), 8.0),
        (CeilingShuffleReward(), 6.0),

        # GOALS (OBJECTIF FINAL)
        (GoalReward(), 30.0),
    )

    obs_builder = DefaultObs(
        zero_padding=None,
        pos_coef=np.asarray([1 / common_values.SIDE_WALL_X,
                            1 / common_values.BACK_NET_Y,
                            1 / common_values.CEILING_Z]),
        ang_coef=1 / np.pi,
        lin_vel_coef=1 / common_values.CAR_MAX_SPEED,
        ang_vel_coef=1 / common_values.CAR_MAX_ANG_VEL,
        boost_coef=1 / 100.0
    )

    state_mutator = MutatorSequence(
        FixedTeamSizeMutator(blue_size=blue_team_size, orange_size=orange_team_size),
        KickoffMutator()
    )

    rlgym_env = RLGym(
        state_mutator=state_mutator,
        obs_builder=obs_builder,
        action_parser=action_parser,
        reward_fn=reward_fn,
        termination_cond=termination_condition,
        truncation_cond=truncation_condition,
        transition_engine=RocketSimEngine()
    )

    return RLGymV2GymWrapper(rlgym_env)


# ============================================================================
# MAIN TRAINING LOOP
# ============================================================================

if __name__ == "__main__":
    from rlgym_ppo import Learner

    # Find and load best checkpoint
    checkpoint_dir = find_best_checkpoint()

    print("=" * 80)
    print("ZENITOBOT PRO TRAINING - SSL+++ MECHANICS MASTERY")
    print("=" * 80)
    if checkpoint_dir:
        print(f"Resuming from checkpoint: {checkpoint_dir}")
    else:
        print("Starting FRESH pro-level training")

    print(f"\nTARGET: 1.5 BILLION timesteps (SSL+++ Level)")
    print(f"\nADVANCED MECHANICS IMPLEMENTED:")
    print("  - Powershots (wall, upside down, air roll, ground, aerial)")
    print("  - Backboard clears/shots")
    print("  - Advanced dribbling (musty, 45/90/180 flicks, wavedash, breezy, mawkzy)")
    print("  - Bounce dribble")
    print("  - Ground to air & wall to air dribbles")
    print("  - Fast aerials")
    print("  - Flip resets")
    print("  - Musty aerials")
    print("  - Heli resets")
    print("  - Ceiling shots & ceiling shuffle")
    print("  - Double taps")
    print("  - Redirects")
    print("  - Wavedash & chain dash")
    print("  - Half flips")
    print("  - Pinches (wall, ground, ceiling, goal post)")
    print("  - Shadow defense")
    print("  - Flip cancels")
    print("  - Turtle shots")
    print("  - Stalls")
    print("=" * 80)

    # Configuration optimale pour training pro
    n_proc = 16
    min_inference_size = max(1, int(round(n_proc * 0.9)))

    # Fix Unicode encoding
    from rlgym_ppo.util import reporting
    original_report_metrics = reporting.report_metrics
    def safe_report_metrics(*args, **kwargs):
        try:
            original_report_metrics(*args, **kwargs)
        except UnicodeEncodeError:
            print("Iteration complete (metrics display skipped due to encoding)")
    reporting.report_metrics = safe_report_metrics

    learner = Learner(
        build_rlgym_v2_env,
        n_proc=n_proc,
        min_inference_size=min_inference_size,

        # CHECKPOINT SYSTEM
        checkpoint_load_folder=checkpoint_dir,

        # HYPERPARAMETERS OPTIMISÉS POUR PRO LEVEL
        ppo_batch_size=200_000,
        policy_layer_sizes=[2048, 2048, 2048, 1024],  # Network plus profond
        critic_layer_sizes=[2048, 2048, 2048, 1024],
        ts_per_iteration=200_000,
        exp_buffer_size=600_000,
        ppo_minibatch_size=100_000,
        ppo_ent_coef=0.01,

        # Learning rates
        policy_lr=8e-5,  # Légèrement réduit pour stabilité
        critic_lr=8e-5,

        # Plus d'epochs pour mieux apprendre les mécaniques complexes
        ppo_epochs=6,

        # Device (CPU-only since CUDA not available)
        device="cpu",

        # Training settings
        standardize_returns=True,
        standardize_obs=False,

        # Save progress every 1M timesteps
        save_every_ts=1_000_000,

        # Train to SSL+++ level (1.5 billion timesteps)
        timestep_limit=1_500_000_000,

        # Logging
        log_to_wandb=False,
        metrics_logger=None
    )

    print("\nStarting PRO TRAINING...")
    print("This will teach the bot ALL advanced mechanics!")
    print("Press Ctrl+C to stop safely (progress will be saved)\n")

    try:
        learner.learn()
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user. Progress has been saved!")
        print("You can resume by running this script again.")

    print("\n" + "=" * 80)
    print("TRAINING COMPLETE!")
    print("=" * 80)
