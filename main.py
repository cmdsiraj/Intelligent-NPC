from ScenarioLoader import ScenarioLoader

sim = ScenarioLoader.load("scenarios/grad_students.yaml")
sim.run(ticks=sim._default_ticks)

print("\n" + "=" * 60)
print("  FULL EVENT LOG")
print("=" * 60)
for i, event in enumerate(sim.world.event_log, 1):
    print(f"\n  [{i}]\n{event.to_str(for_prompt=False)}")
print("\n" + "=" * 60)
