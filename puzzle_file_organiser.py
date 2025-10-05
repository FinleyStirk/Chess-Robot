import pandas as pd
import json

def extract_puzzles(path: str, output_path: str, num_puzzles: int):
    df = pd.read_csv(path, compression="zstd")
    
    sample_df = df.sample(n=num_puzzles, random_state=42)
    
    sample_df = sample_df.where(pd.notna(sample_df), None)
    
    sample_df["Moves"] = sample_df["Moves"].apply(lambda s: s.split())
    
    records = sample_df.to_dict(orient="records")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


# Example usage
extract_puzzles(
    path="lichess_db_puzzle.csv.zst",
    output_path="puzzle.json",
    num_puzzles=2000
)