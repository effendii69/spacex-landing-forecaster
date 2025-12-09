# backend/data_collection.py
import requests
import pandas as pd
from pathlib import Path

print("Downloading latest SpaceX data from IBM source...")
url = "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/datasets/dataset_part_2.csv"
df = pd.read_csv(url)

# Create data directory if it doesn't exist
data_dir = Path(__file__).parent.parent / "data"
data_dir.mkdir(exist_ok=True)

output_path = data_dir / "spacex_landing_dataset.csv"
df.to_csv(output_path, index=False)
print(f"Fresh dataset saved to {output_path}")
print("Now run: python backend/model.py")