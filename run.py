"""
Entry point for the intelligent-npc framework.

Usage:
    python run.py                                  # runs default scenario
    python run.py scenarios/grad_students.yaml     # runs specific scenario
    python run.py scenarios/grad_students.yaml --load saves/checkpoint.json
    python run.py scenarios/grad_students.yaml --save saves/checkpoint.json
"""

import sys
import argparse
from ScenarioLoader import ScenarioLoader


def main():
    parser = argparse.ArgumentParser(description="Run an NPC simulation scenario.")
    parser.add_argument("scenario", nargs="?", default="scenarios/grad_students.yaml",
                        help="Path to scenario YAML file")
    parser.add_argument("--ticks", type=int, default=None,
                        help="Number of ticks to run (overrides scenario config)")
    parser.add_argument("--save", type=str, default=None,
                        help="Save simulation state to this path after running")
    parser.add_argument("--load", type=str, default=None,
                        help="Load simulation state from this path before running")
    args = parser.parse_args()

    print(f"\nLoading scenario: {args.scenario}")
    sim = ScenarioLoader.load(args.scenario)

    if args.load:
        print(f"Restoring state from: {args.load}")
        sim.load(args.load)

    ticks = args.ticks or sim._default_ticks
    sim.run(ticks=ticks)

    if args.save:
        print(f"\nSaving state to: {args.save}")
        sim.save(args.save)

    print("\n" + "=" * 60)
    print("  FULL EVENT LOG")
    print("=" * 60)
    for i, event in enumerate(sim.world.event_log, 1):
        print(f"\n  [{i}]\n{event.to_str(for_prompt=False)}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
