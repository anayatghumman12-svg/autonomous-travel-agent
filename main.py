import sys
from graph import build_graph

def main():
    # Agar user terminal command mein prompt deta hai toh wo use karo, nahi toh default prompt
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        user_prompt = "Plan a 5-day trip to Hunza under PKR 120,000."

    print(f"\n--- Processing Request: '{user_prompt}' ---\n")

    app = build_graph()
    result = app.invoke({"request": user_prompt})

    print("\n================ FINAL ITINERARY ================\n")
    print(result.get("final", "No output generated."))
    print("\n=================================================\n")

if __name__ == "__main__":
    main()