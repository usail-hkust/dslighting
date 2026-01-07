"""
Generate sample house price data

Creates raw data for the custom-house-price-prediction task.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def generate_house_data(n_samples=100, seed=42):
    """
    Generate synthetic house price data.

    Args:
        n_samples: Number of samples to create.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame: Features and prices for each house.
    """
    np.random.seed(seed)

    # Create features
    data = {
        'house_id': range(1, n_samples + 1),
        'area': np.random.randint(800, 3500, n_samples),  # Living area (sqft)
        'bedrooms': np.random.randint(1, 6, n_samples),  # Bedrooms
        'age': np.random.randint(0, 50, n_samples),  # House age
        'location_score': np.random.randint(1, 11, n_samples),  # Location score (1-10)
    }

    df = pd.DataFrame(data)

    # Simulate prices: linear combo of features + noise
    df['price'] = (
        df['area'] * 100 +  # Area effect
        df['bedrooms'] * 15000 +  # Bedroom effect
        df['location_score'] * 20000 +  # Location effect
        -df['age'] * 500 +  # Depreciation
        np.random.normal(0, 20000, n_samples)  # Random noise
    )

    # Ensure prices stay positive
    df['price'] = df['price'].clip(lower=50000)

    return df


def main():
    """Generate and save the sample data."""
    # Create directories
    raw_dir = Path(__file__).parent / "data" / "custom-house-price-prediction" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Generate data
    print("Generating house price data...")
    df = generate_house_data(n_samples=100)

    # Save to CSV
    output_file = raw_dir / "houses.csv"
    df.to_csv(output_file, index=False)

    # Show stats
    print(f"\n✓ Generated {len(df)} house price rows")
    print(f"✓ Saved to: {output_file}")
    print(f"\nData stats:")
    print("=" * 60)
    print(df.describe())
    print(f"\nPrice range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
    print(f"Average price: ${df['price'].mean():.2f}")


if __name__ == "__main__":
    main()
