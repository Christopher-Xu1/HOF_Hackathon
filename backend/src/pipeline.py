import sys, os, json

def fake_pipeline(input_path):
    output = {
        "company": "Amazon",
        "quarter": "Q4 2025",   
        "structured_data": {
            "Revenue": 149204,
            "Net Income": 10724,
            "EPS": 1.39
        },
        "guidance": "Amazon expects Q1 2026 revenue between $138B–$143.5B.",
        "sentiment": "Positive",
        "kpis": ["AWS growth 13%", "Advertising revenue up 24%"]
    }
    filename = os.path.basename(input_path).replace(".pdf", ".json")
    with open(f"outputs/{filename}", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    input_file = sys.argv[1]
    fake_pipeline(input_file)
