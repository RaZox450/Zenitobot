"""
Configuration centralisée pour le training
Permet d'ajuster facilement les hyperparamètres et les poids des rewards
"""

# ============================================================================
# HYPERPARAMÈTRES D'ENTRAÎNEMENT
# ============================================================================

# Configuration du training
TRAINING_CONFIG = {
    # Nombre de processus parallèles (ajuster selon votre CPU)
    'n_proc': 16,

    # Taille de batch PPO
    'ppo_batch_size': 200_000,

    # Architecture du réseau de neurones
    'policy_layer_sizes': [2048, 2048, 2048, 1024],
    'critic_layer_sizes': [2048, 2048, 2048, 1024],

    # Timesteps par itération
    'ts_per_iteration': 200_000,

    # Taille du buffer d'expérience
    'exp_buffer_size': 600_000,

    # Taille des mini-batches
    'ppo_minibatch_size': 100_000,

    # Coefficient d'entropie
    'ppo_ent_coef': 0.01,

    # Learning rates
    'policy_lr': 8e-5,
    'critic_lr': 8e-5,

    # Nombre d'epochs PPO
    'ppo_epochs': 6,

    # Device (cuda ou cpu)
    'device': 'cuda',

    # Fréquence de sauvegarde (en timesteps)
    'save_every_ts': 1_000_000,

    # Limite de timesteps totaux
    'timestep_limit': 1_500_000_000,

    # Logging
    'log_to_wandb': False,
}

# ============================================================================
# CONFIGURATION DU MATCH
# ============================================================================

MATCH_CONFIG = {
    # Mode de jeu
    'spawn_opponents': True,
    'team_size': 2,  # 2v2 optimal

    # Action repeat (120Hz / action_repeat = decision frequency)
    'action_repeat': 4,  # 30Hz decisions

    # Timeouts
    'no_touch_timeout_seconds': 20,
    'game_timeout_seconds': 180,
}

# ============================================================================
# POIDS DES REWARDS
# ============================================================================

# Poids pour chaque reward function
# Plus le poids est élevé, plus la mécanique est importante pour le training
REWARD_WEIGHTS = {
    # FONDAMENTAUX (faible poids - guident le comportement de base)
    'velocity_player_to_ball': 0.2,
    'face_ball': 0.3,
    'velocity_ball_to_goal': 6.0,

    # POWERSHOTS (poids élevé - mécaniques offensives importantes)
    'powershot': 12.0,
    'backboard': 10.0,

    # DRIBBLING AVANCÉ (poids très élevé - mécaniques complexes)
    'advanced_dribbling': 15.0,  # Tous les flicks
    'bounce_dribble': 6.0,
    'air_dribble': 14.0,  # Ground to air + wall to air

    # AERIALS PRO (poids variables selon difficulté)
    'fast_aerial': 5.0,
    'flip_reset': 20.0,  # Très difficile
    'musty_aerial': 18.0,  # Très difficile
    'heli_reset': 25.0,  # Ultra difficile

    # CEILING & DOUBLE TAP (poids élevé - mécaniques avancées)
    'ceiling_shot': 15.0,
    'double_tap': 18.0,

    # RECOVERIES AVANCÉES (poids moyen - importantes pour la vitesse)
    'wavedash': 5.0,
    'chain_dash': 8.0,
    'half_flip': 8.0,

    # MÉCANIQUES TECHNIQUES (poids élevé - difficiles à maîtriser)
    'redirect': 12.0,
    'pinch': 15.0,
    'shadow_defense': 4.0,
    'flip_cancel': 7.0,

    # MÉCANIQUES SPÉCIALES (poids élevé - très rares)
    'turtle': 10.0,
    'stall': 8.0,
    'ceiling_shuffle': 6.0,

    # GOALS (poids maximum - objectif final)
    'goal': 30.0,
}

# ============================================================================
# DÉTAILS DES REWARDS POUR CHAQUE MÉCANIQUE
# ============================================================================

# Détails des rewards individuels (pour documentation)
REWARD_DETAILS = {
    'powershot': {
        'base': 5.0,
        'wall_bonus': 3.0,
        'upside_down_bonus': 4.0,
        'air_roll_bonus': 3.5,
        'aerial_bonus': 4.0,
        'ground_bonus': 2.0,
        'combo_bonus': 5.0,
    },
    'backboard': {
        'clear': 8.0,
        'shot': 10.0,
    },
    'flicks': {
        'musty': 15.0,
        '180_degree': 12.0,
        '90_degree': 10.0,
        '45_degree': 8.0,
        'delayed': 11.0,
        'powerslide': 9.0,
        'wavedash': 13.0,
        'breezy_mawkzy': 16.0,
    },
    'aerial_advanced': {
        'flip_reset': 20.0,
        'musty': 18.0,
        'heli_reset': 25.0,
    },
    'ceiling': {
        'ceiling_shot_basic': 8.0,
        'ceiling_shot_to_goal': 15.0,
    },
    'pinches': {
        'goal_post': 25.0,
        'ceiling': 18.0,
        'wall': 15.0,
        'ground': 14.0,
    },
}

# ============================================================================
# NIVEAUX DE PROGRESSION
# ============================================================================

# Progression attendue selon les timesteps
PROGRESSION_MILESTONES = {
    0: {
        'level': 'Champion 3',
        'description': 'Début du training',
    },
    50_000_000: {
        'level': 'Grand Champion',
        'description': 'Maîtrise des aerials basiques et flicks simples',
    },
    200_000_000: {
        'level': 'SSL',
        'description': 'Fast aerials, flip resets (learning), dribbles avancés',
    },
    500_000_000: {
        'level': 'SSL+',
        'description': 'Double taps, ceiling shots, redirects, musty aerials',
    },
    1_000_000_000: {
        'level': 'SSL++',
        'description': 'Heli resets, pinches avancés, toutes recoveries',
    },
    1_500_000_000: {
        'level': 'SSL+++ (Pro)',
        'description': 'Maîtrise complète de toutes les mécaniques',
    },
}

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_config():
    """Retourne la configuration complète"""
    return {
        'training': TRAINING_CONFIG,
        'match': MATCH_CONFIG,
        'reward_weights': REWARD_WEIGHTS,
        'reward_details': REWARD_DETAILS,
        'progression': PROGRESSION_MILESTONES,
    }


def print_config():
    """Affiche la configuration actuelle"""
    print("=" * 80)
    print("CONFIGURATION DU TRAINING")
    print("=" * 80)
    print()

    print("HYPERPARAMÈTRES:")
    for key, value in TRAINING_CONFIG.items():
        print(f"  {key}: {value}")
    print()

    print("CONFIGURATION MATCH:")
    for key, value in MATCH_CONFIG.items():
        print(f"  {key}: {value}")
    print()

    print("POIDS DES REWARDS:")
    sorted_weights = sorted(REWARD_WEIGHTS.items(), key=lambda x: x[1], reverse=True)
    for key, value in sorted_weights:
        print(f"  {key}: {value}")
    print()

    print("=" * 80)


if __name__ == "__main__":
    print_config()
