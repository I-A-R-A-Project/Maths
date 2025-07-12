import sys
from calculator import solve_expression

def solve_and_show(expression, label):
    result = solve_expression(expression, log=True)
    print(f"\n{label}: {expression} = {result}")
    return result

def force(mass, acceleration):
    return solve_and_show(f"{mass} * {acceleration}", "Force (F = m × a)")

def work(force, distance):
    return solve_and_show(f"{force} * {distance}", "Work (W = F × d)")

def kinetic_energy(mass, velocity):
    return solve_and_show(f"0.5 * {mass} * ({velocity} ** 2)", "Kinetic Energy (KE = ½ × m × v²)")

def potential_energy(mass, gravity, height):
    return solve_and_show(f"{mass} * {gravity} * {height}", "Potential Energy (PE = m × g × h)")

def velocity(distance, time):
    return solve_and_show(f"{distance} / {time}", "Velocity (v = d / t)")

def acceleration(final_v, initial_v, time):
    return solve_and_show(f"({final_v} - {initial_v}) / {time}", "Acceleration (a = (vf - vi) / t)")

def show_help():
    print("""
Physics Calculator - Supported commands:

  force m a             → F = m × a
  work f d              → W = F × d
  kinetic_energy m v    → KE = ½ × m × v²
  potential_energy m g h→ PE = m × g × h
  velocity d t          → v = d / t
  acceleration vf vi t  → a = (vf - vi) / t

Examples:
  python physics.py force 10 2
  python physics.py kinetic_energy 5 3
""")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["help", "-h", "--help"]:
        show_help()
        return

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    try:
        match command:
            case "force":
                force(*args)
            case "work":
                work(*args)
            case "kinetic_energy":
                kinetic_energy(*args)
            case "potential_energy":
                potential_energy(*args)
            case "velocity":
                velocity(*args)
            case "acceleration":
                acceleration(*args)
            case _:
                print("Unknown command.")
                show_help()
    except Exception as e:
        print("Error:", e)
        show_help()

if __name__ == "__main__":
    main()
