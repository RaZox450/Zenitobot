"""
Script de monitoring pour suivre la progression du training
Affiche les statistiques des checkpoints et la progression globale
"""

import os
from pathlib import Path
from datetime import datetime
import json


def format_number(n):
    """Format large numbers with K, M, B suffixes"""
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    else:
        return str(n)


def get_checkpoint_info():
    """Get information about all checkpoints"""
    base_dir = Path("data/checkpoints")

    if not base_dir.exists():
        return None

    all_checkpoints = []
    for run_dir in base_dir.iterdir():
        if run_dir.is_dir():
            for ts_dir in run_dir.iterdir():
                if ts_dir.is_dir() and (ts_dir / "PPO_POLICY.pt").exists():
                    try:
                        timesteps = int(ts_dir.name)
                        file_size = (ts_dir / "PPO_POLICY.pt").stat().st_size
                        mod_time = datetime.fromtimestamp((ts_dir / "PPO_POLICY.pt").stat().st_mtime)
                        all_checkpoints.append({
                            'run': run_dir.name,
                            'timesteps': timesteps,
                            'path': str(ts_dir),
                            'size_mb': file_size / (1024 * 1024),
                            'date': mod_time
                        })
                    except ValueError:
                        pass

    return sorted(all_checkpoints, key=lambda x: x['timesteps'])


def estimate_level(timesteps):
    """Estimate skill level based on timesteps"""
    if timesteps < 50_000_000:
        return "Champion 3 - Grand Champion"
    elif timesteps < 200_000_000:
        return "Grand Champion - SSL"
    elif timesteps < 500_000_000:
        return "SSL"
    elif timesteps < 1_000_000_000:
        return "SSL+"
    else:
        return "SSL+++ (Pro)"


def get_mechanics_progress(timesteps):
    """Get expected mechanics at current level"""
    mechanics = []

    if timesteps >= 10_000_000:
        mechanics.append("✓ Basic aerials")
    if timesteps >= 25_000_000:
        mechanics.append("✓ Basic flicks")
    if timesteps >= 50_000_000:
        mechanics.append("✓ Fast aerials")
    if timesteps >= 100_000_000:
        mechanics.append("✓ Flip resets (learning)")
    if timesteps >= 200_000_000:
        mechanics.append("✓ Advanced dribbling")
    if timesteps >= 300_000_000:
        mechanics.append("✓ Double taps")
    if timesteps >= 400_000_000:
        mechanics.append("✓ Ceiling shots")
    if timesteps >= 600_000_000:
        mechanics.append("✓ Musty aerials")
    if timesteps >= 800_000_000:
        mechanics.append("✓ Heli resets")
    if timesteps >= 1_000_000_000:
        mechanics.append("✓ Advanced pinches")
    if timesteps >= 1_200_000_000:
        mechanics.append("✓ All mechanics mastered")

    return mechanics if mechanics else ["⏳ Still learning basics..."]


def main():
    print("=" * 80)
    print(" " * 20 + "ZENITOBOT TRAINING MONITOR")
    print("=" * 80)
    print()

    checkpoints = get_checkpoint_info()

    if not checkpoints:
        print("❌ No checkpoints found!")
        print("   The training hasn't started yet or no checkpoints have been saved.")
        print()
        print("   Run START_PRO_TRAINING.bat to start training.")
        return

    # Latest checkpoint
    latest = checkpoints[-1]
    total_checkpoints = len(checkpoints)

    print(f"📊 TRAINING STATISTICS")
    print(f"{'─' * 80}")
    print(f"Total checkpoints:     {total_checkpoints}")
    print(f"Current timesteps:     {format_number(latest['timesteps'])} ({latest['timesteps']:,})")
    print(f"Target timesteps:      1.5B (1,500,000,000)")
    print(f"Progress:              {latest['timesteps'] / 1_500_000_000 * 100:.2f}%")
    print(f"Last update:           {latest['date'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Checkpoint size:       {latest['size_mb']:.1f} MB")
    print()

    # Level estimation
    level = estimate_level(latest['timesteps'])
    print(f"🎮 SKILL LEVEL ESTIMATION")
    print(f"{'─' * 80}")
    print(f"Estimated level:       {level}")
    print()

    # Mechanics progress
    mechanics = get_mechanics_progress(latest['timesteps'])
    print(f"🎪 EXPECTED MECHANICS")
    print(f"{'─' * 80}")
    for mech in mechanics:
        print(f"  {mech}")
    print()

    # Progress bar
    progress = latest['timesteps'] / 1_500_000_000
    bar_length = 50
    filled = int(bar_length * progress)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"📈 PROGRESS TO SSL+++")
    print(f"{'─' * 80}")
    print(f"[{bar}] {progress * 100:.1f}%")
    print()

    # Milestones
    milestones = [
        (50_000_000, "Grand Champion"),
        (200_000_000, "SSL"),
        (500_000_000, "SSL+"),
        (1_000_000_000, "SSL++"),
        (1_500_000_000, "SSL+++ (Pro)")
    ]

    print(f"🎯 MILESTONES")
    print(f"{'─' * 80}")
    for ts, name in milestones:
        if latest['timesteps'] >= ts:
            print(f"  ✅ {format_number(ts):>6} - {name}")
        else:
            remaining = ts - latest['timesteps']
            print(f"  ⏳ {format_number(ts):>6} - {name} (remaining: {format_number(remaining)})")
    print()

    # Recent checkpoints
    recent = checkpoints[-5:] if len(checkpoints) >= 5 else checkpoints
    print(f"📋 RECENT CHECKPOINTS")
    print(f"{'─' * 80}")
    print(f"{'Timesteps':<15} {'Date':<20} {'Size':<10}")
    print(f"{'─' * 80}")
    for cp in reversed(recent):
        print(f"{format_number(cp['timesteps']):<15} {cp['date'].strftime('%Y-%m-%d %H:%M'):<20} {cp['size_mb']:>6.1f} MB")
    print()

    # Training rate estimation
    if len(checkpoints) >= 2:
        first = checkpoints[0]
        time_diff = (latest['date'] - first['date']).total_seconds()
        ts_diff = latest['timesteps'] - first['timesteps']

        if time_diff > 0:
            ts_per_hour = (ts_diff / time_diff) * 3600
            hours_to_complete = (1_500_000_000 - latest['timesteps']) / ts_per_hour if ts_per_hour > 0 else 0

            print(f"⏱️  TRAINING RATE")
            print(f"{'─' * 80}")
            print(f"Average rate:          {format_number(int(ts_per_hour))}/hour")
            if hours_to_complete > 0:
                days = hours_to_complete / 24
                print(f"Estimated completion:  {days:.1f} days ({hours_to_complete:.1f} hours)")
            print()

    print("=" * 80)
    print("💡 TIP: Run this script anytime to check training progress!")
    print("=" * 80)


if __name__ == "__main__":
    main()
