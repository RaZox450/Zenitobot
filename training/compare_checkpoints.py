"""
Script pour comparer les performances de différents checkpoints
Permet de voir l'évolution du bot au fil du training
"""

import os
from pathlib import Path
import json
from datetime import datetime


def get_all_checkpoints():
    """Récupère tous les checkpoints disponibles"""
    base_dir = Path("data/checkpoints")

    if not base_dir.exists():
        return []

    checkpoints = []
    for run_dir in base_dir.iterdir():
        if run_dir.is_dir():
            for ts_dir in run_dir.iterdir():
                if ts_dir.is_dir() and (ts_dir / "PPO_POLICY.pt").exists():
                    try:
                        timesteps = int(ts_dir.name)
                        mod_time = datetime.fromtimestamp((ts_dir / "PPO_POLICY.pt").stat().st_mtime)
                        checkpoints.append({
                            'timesteps': timesteps,
                            'path': str(ts_dir),
                            'run': run_dir.name,
                            'date': mod_time
                        })
                    except ValueError:
                        pass

    return sorted(checkpoints, key=lambda x: x['timesteps'])


def format_number(n):
    """Format numbers with K, M, B suffixes"""
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    else:
        return str(n)


def main():
    print("=" * 80)
    print(" " * 25 + "CHECKPOINT COMPARISON")
    print("=" * 80)
    print()

    checkpoints = get_all_checkpoints()

    if not checkpoints:
        print("❌ No checkpoints found!")
        return

    # Display all checkpoints
    print(f"📋 AVAILABLE CHECKPOINTS ({len(checkpoints)} total)")
    print("─" * 80)
    print(f"{'#':<4} {'Timesteps':<15} {'Date':<20} {'Path':<30}")
    print("─" * 80)

    for i, cp in enumerate(checkpoints, 1):
        print(f"{i:<4} {format_number(cp['timesteps']):<15} "
              f"{cp['date'].strftime('%Y-%m-%d %H:%M'):<20} "
              f"{cp['path'][-30:]:<30}")

    print()

    # Key milestones
    milestones = [
        (50_000_000, "Grand Champion Level"),
        (200_000_000, "SSL Level"),
        (500_000_000, "SSL+ Level"),
        (1_000_000_000, "SSL++ Level"),
        (1_500_000_000, "SSL+++ (Pro) Level"),
    ]

    print(f"🎯 MILESTONE CHECKPOINTS")
    print("─" * 80)

    for ts, name in milestones:
        # Find closest checkpoint to this milestone
        closest = min(checkpoints, key=lambda x: abs(x['timesteps'] - ts), default=None)
        if closest:
            diff = closest['timesteps'] - ts
            if abs(diff) < 50_000_000:  # Within 50M timesteps
                status = "✅" if closest['timesteps'] >= ts else "⏳"
                print(f"{status} {format_number(ts):<10} - {name:<25} "
                      f"(actual: {format_number(closest['timesteps'])})")
            else:
                print(f"⏳ {format_number(ts):<10} - {name:<25} (not reached)")
        else:
            print(f"⏳ {format_number(ts):<10} - {name:<25} (not reached)")

    print()

    # Progress analysis
    if len(checkpoints) >= 2:
        first = checkpoints[0]
        latest = checkpoints[-1]

        print(f"📊 TRAINING PROGRESS ANALYSIS")
        print("─" * 80)
        print(f"First checkpoint:      {format_number(first['timesteps'])}")
        print(f"Latest checkpoint:     {format_number(latest['timesteps'])}")
        print(f"Total progress:        {format_number(latest['timesteps'] - first['timesteps'])}")
        print()

        # Time analysis
        time_diff = (latest['date'] - first['date']).total_seconds()
        ts_diff = latest['timesteps'] - first['timesteps']

        if time_diff > 0:
            ts_per_hour = (ts_diff / time_diff) * 3600
            ts_per_day = ts_per_hour * 24

            print(f"⏱️  TRAINING RATE")
            print("─" * 80)
            print(f"Training duration:     {time_diff / 3600:.1f} hours ({time_diff / 86400:.1f} days)")
            print(f"Rate per hour:         {format_number(int(ts_per_hour))}")
            print(f"Rate per day:          {format_number(int(ts_per_day))}")
            print()

            remaining = 1_500_000_000 - latest['timesteps']
            if remaining > 0 and ts_per_hour > 0:
                hours_left = remaining / ts_per_hour
                days_left = hours_left / 24

                print(f"⏳ TIME TO COMPLETION")
                print("─" * 80)
                print(f"Remaining timesteps:   {format_number(remaining)}")
                print(f"Estimated time left:   {days_left:.1f} days ({hours_left:.1f} hours)")
                print(f"Expected completion:   {datetime.now().timestamp() + (hours_left * 3600)}")

    print()
    print("=" * 80)
    print("💡 TIP: You can load any checkpoint by modifying pro_training.py")
    print("=" * 80)


if __name__ == "__main__":
    main()
