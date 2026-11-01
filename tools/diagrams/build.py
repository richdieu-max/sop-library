"""Rebuild every figure that has a spec.

    python3 tools/diagrams/build.py            # render all specs into their diagrams/ folders
    python3 tools/diagrams/build.py az-102-2   # render one spec

Each spec in specs/ is a small Python file that describes one figure with the kit and renders it
to the runbook's diagrams folder. Exits non-zero if any spec fails or prints a layout warning,
so CI can refuse a figure whose text would overflow its box.
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPECS = os.path.join(HERE, "specs")


def main():
    wanted = set(sys.argv[1:])
    specs = sorted(f for f in os.listdir(SPECS) if f.endswith(".py"))
    if wanted:
        specs = [f for f in specs if f[:-3] in wanted]
        missing = wanted - {f[:-3] for f in specs}
        if missing:
            sys.exit(f"no spec named: {', '.join(sorted(missing))}")
    failures = 0
    for f in specs:
        sys.path.insert(0, HERE)
        try:
            ns = runpy.run_path(os.path.join(SPECS, f), run_name="__main__")
            warnings = ns.get("d").warnings if ns.get("d") is not None else []
            if warnings:
                failures += 1
                print(f"FAIL {f}: {len(warnings)} layout warning(s)")
            else:
                print(f"ok   {f}")
        except Exception as e:  # noqa: BLE001 - report and continue so one bad spec does not hide the rest
            failures += 1
            print(f"FAIL {f}: {type(e).__name__}: {e}")
    print(f"{len(specs) - failures} of {len(specs)} figures built")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
