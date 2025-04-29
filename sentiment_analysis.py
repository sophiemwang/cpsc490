from .restaurant import Restaurant
import json
import os
import matplotlib.pyplot as plt
import pandas as pd
import argparse
from datetime import datetime, timedelta
from typing import List
import numpy as np

# Get base directory (project root) relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVIEWS_DIR_DEFAULT = os.path.join(BASE_DIR, 'data', 'restaurant_reviews')
OUTPUT_DIR_DEFAULT = os.path.join(BASE_DIR, 'data', 'output')

def get_available_restaurants(reviews_dir: str = REVIEWS_DIR_DEFAULT) -> List[str]:
    if not os.path.exists(reviews_dir):
        raise FileNotFoundError(f"Reviews directory '{reviews_dir}' not found")
    json_files = [f for f in os.listdir(reviews_dir) if f.endswith('.json')]
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in '{reviews_dir}'")
    return json_files

"""
Allows user select a restaurant file from available options. 
A user input of 0 means review all available restaurant files.
"""
def select_restaurant_file() -> str:
    # Use default path constant
    reviews_dir = REVIEWS_DIR_DEFAULT
    try:
        json_files = get_available_restaurants(reviews_dir)
        print("\nAvailable restaurants:")
        print("0. Analyze all restaurants")
        for i, filename in enumerate(json_files, 1):
            print(f"{i}. {filename}")           
        while True:
            try:
                choice = int(input("\nSelect a restaurant (enter number): "))
                if choice == 0:
                    return [os.path.join(reviews_dir, json_file) for json_file in json_files]
                if 1 <= choice <= len(json_files):
                    return [os.path.join(reviews_dir, json_files[choice-1])]
                print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")               
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)

"""
Loads restaurant data from JSON file.
"""
def load_restaurant(file_path):
    with open(file_path) as f:
        data = json.load(f)
    return Restaurant.from_dict(data[0])


"""
Processes a restaurant's Yelp reviews to generate structured data, sentiment analysis, and visualizations.
This function:
- Converts raw review data to a DataFrame and saves it as a CSV.
- Applies sentiment analysis model to label each review as positive, neutral, or negative.
- Aggregates sentiment counts by month and saves the monthly summary to a CSV file.
- Generates a time-based visualization of sentiment trends.
Parameters:
- restaurant (Restaurant): A Restaurant object containing review data and other relevant data.
- output_dir (str): Directory where the output CSVs and visualization will be saved.
"""
def analyze_restaurant(restaurant, output_dir=OUTPUT_DIR_DEFAULT):
    print(f"Analyzing {restaurant.title}...")
    os.makedirs(output_dir, exist_ok=True) # Create output directory if it doesn't exist
    # Convert to data frame and save
    df = restaurant.to_dataframe() 
    df_path = os.path.join(output_dir, f"{restaurant.title.replace(' ', '_')}_reviews.csv")
    df.to_csv(df_path)
    print(f"Saved reviews data to {df_path}")
    
    # Analyze sentiment
    sentiment_df = restaurant.analyze_sentiment() 
    sentiment_path = os.path.join(output_dir, f"{restaurant.title.replace(' ', '_')}_sentiment.csv")
    sentiment_df.to_csv(sentiment_path)
    print(f"Saved sentiment analysis to {sentiment_path}")
    
    # Generate monthly sentiment summary
    sentiment_df['month'] = pd.to_datetime(sentiment_df['date']).dt.to_period('M') 
    monthly_summary = sentiment_df.groupby('month')['sentiment'].value_counts().unstack(fill_value=0)
    monthly_summary = monthly_summary.rename(columns={'positive': 'num_pos', 'negative': 'num_neg', 'neutral': 'num_neu'})
    monthly_summary = monthly_summary.reset_index()
    monthly_summary['month'] = monthly_summary['month'].astype(str)
    summary_path = os.path.join(output_dir, f"{restaurant.title.replace(' ', '_')}_monthly_summary.csv")
    monthly_summary.to_csv(summary_path, index=False)
    print(f"Saved monthly sentiment summary to {summary_path}")
    
    # Produce time-based visualitzation of sentiment trends
    fig = restaurant.visualize_sentiment_over_time() 
    fig_path = os.path.join(output_dir, f"{restaurant.title.replace(' ', '_')}_sentiment.png")
    fig.savefig(fig_path)
    plt.close(fig)
    print(f"Saved visualization to {fig_path}")

"""
Analyzes the impact of Pete Wells' reviews on restaurant sentiment.
For each restaurant in the input list, this function:
- Filters reviews to a window surrounding the NYT review date (default: 30 days before and after).
- Categorizes each Yelp review as positive, neutral, or negative.
- Calculates the count and proportion of sentiment categories before and after the NYT review.
- Classifies the NYT review as positive or negative based on its star rating.
- Saves the raw counts and proportions to a CSV file.
- Computes and saves summary statistics (mean and standard deviation) by NYT review sentiment.
- Generates a bar chart visualizing sentiment shifts in Yelp reviews around the NYT review.
Parameters:
- restaurants (List[Restaurant]): List of Restaurant objects with Yelp and NYT review data.
- output_dir (str): Directory to save the output CSV files and plots.
- shift (int): Optional offset in days to shift the review window (e.g., to allow for review lag).
- duration (int): Number of days before and after the NYT review to include in analysis.
"""
def analyze_nyt_review_impact(restaurants: List[Restaurant], output_dir=OUTPUT_DIR_DEFAULT, shift=30, duration=30):
    results = []
    for restaurant in restaurants:
        print(f"Analyzing {restaurant.title}...")
        if not restaurant.nyt_review_date:
            continue            
        sentiment_df = restaurant.analyze_sentiment() 
        sentiment_df['date'] = pd.to_datetime(sentiment_df['date']).dt.tz_localize(None)       
        nyt_date = pd.to_datetime(restaurant.nyt_review_date + timedelta(days=shift))
        month_before = pd.to_datetime(restaurant.nyt_review_date - timedelta(days=duration) + timedelta(days=shift))
        month_after = pd.to_datetime(restaurant.nyt_review_date + timedelta(days=duration) + timedelta(days=shift))        
        before_df = sentiment_df[(sentiment_df['date'] >= month_before) & 
                               (sentiment_df['date'] < nyt_date)]
        after_df = sentiment_df[(sentiment_df['date'] >= nyt_date) & 
                              (sentiment_df['date'] <= month_after)]
        result = {
            'restaurant_name': restaurant.title,
            'nyt_review_date': restaurant.nyt_review_date.strftime('%Y-%m-%d'),
            'nyt_review_rating': restaurant.nyt_review_rating,
            'num_reviews_before': len(before_df),
            'num_reviews_after': len(after_df),
            'num_positive_reviews_before': len(before_df[before_df['sentiment'] == 'positive']),
            'num_positive_reviews_after': len(after_df[after_df['sentiment'] == 'positive']), 
            'num_negative_reviews_before': len(before_df[before_df['sentiment'] == 'negative']),
            'num_negative_reviews_after': len(after_df[after_df['sentiment'] == 'negative']),
            'num_neutral_reviews_before': len(before_df[before_df['sentiment'] == 'neutral']),
            'num_neutral_reviews_after': len(after_df[after_df['sentiment'] == 'neutral'])
        }
        results.append(result)

    if results: 
        df = pd.DataFrame(results)
        output_path = os.path.join(output_dir, f'nyt_review_impact_s{shift}_d{duration}.csv')
        df.to_csv(output_path, index=False)
        print(f"Saved NYT review impact analysis to {output_path}")
        # Classify Pete Wells'own review as positive or negative
        df['nyt_sentiment'] = df['nyt_review_rating'].apply(
            lambda x: 'Negative' if x <= 2 else 'Positive'
        )
        # Compute customer-review proportions
        for period in ['before', 'after']: 
            df[f'prop_positive_{period}'] = df[f'num_positive_reviews_{period}'] / df[f'num_reviews_{period}'].clip(lower=1)
            df[f'prop_negative_{period}'] = df[f'num_negative_reviews_{period}'] / df[f'num_reviews_{period}'].clip(lower=1)
        # Compute means and standard deviations
        grouped = df.groupby('nyt_sentiment')
        stats = pd.DataFrame({
            'pos_before_mean': grouped['prop_positive_before'].mean(),
            'pos_before_std': grouped['prop_positive_before'].std(),
            'pos_after_mean': grouped['prop_positive_after'].mean(),
            'pos_after_std': grouped['prop_positive_after'].std(),
            'neg_before_mean': grouped['prop_negative_before'].mean(),
            'neg_before_std': grouped['prop_negative_before'].std(),
            'neg_after_mean': grouped['prop_negative_after'].mean(),
            'neg_after_std': grouped['prop_negative_after'].std()
        }).reset_index()        
        # Save statistical summary
        stats_path = os.path.join(output_dir, f'nyt_impact_stats_s{shift}_d{duration}.csv')
        stats.to_csv(stats_path, index=False)
        print(f"Saved NYT impact statistical summary to {stats_path}")       
        # Plot with matplotlib
        fig, ax = plt.subplots(figsize=(10, 6))
        width = 0.2
        x = np.arange(len(stats['nyt_sentiment']))
        # Positive reviews
        ax.bar(x - width, stats['pos_before_mean'], width, label='Positive Before', 
               yerr=stats['pos_before_std'], capsize=5, color='lightblue')
        ax.bar(x, stats['pos_after_mean'], width, label='Positive After', 
               yerr=stats['pos_after_std'], capsize=5, color='darkblue')
        # Negative reviews
        ax.bar(x + width, stats['neg_before_mean'], width, label='Negative Before', 
               yerr=stats['neg_before_std'], capsize=5, color='lightcoral')
        ax.bar(x + 2*width, stats['neg_after_mean'], width, label='Negative After', 
               yerr=stats['neg_after_std'], capsize=5, color='darkred')
        # Set labels and title
        ax.set_xlabel('NYT Review Sentiment')
        ax.set_ylabel('Proportion of Customer Reviews')
        ax.set_title('Impact of NYT Reviews on Customer Review Sentiment')
        ax.set_xticks(x + width/2)
        ax.set_xticklabels(stats['nyt_sentiment'])
        ax.legend()
    
        fig_path = os.path.join(output_dir, f'nyt_impact_visualization_s{shift}_d{duration}.png')
        plt.savefig(fig_path)
        plt.close(fig)
        print(f"Saved NYT impact visualization to {fig_path}")
    else:
        print("No restaurants with NYT reviews found for analysis")

    
def main():
    parser = argparse.ArgumentParser(description="Analyze restaurant reviews")
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR_DEFAULT, help=f'Output directory for results (default: {OUTPUT_DIR_DEFAULT})')
    args = parser.parse_args()

    # Get all restaurant files
    restaurant_files = select_restaurant_file()
    restaurants = [load_restaurant(file) for file in restaurant_files]
    
    # Analyze NYT review impact
    shift = int(input("Enter the number of days to shift the analysis window (default: 0): ") or 0)
    duration = int(input("Enter the duration in days to analyze (default: 30): ") or 30)
    analyze_nyt_review_impact(restaurants, args.output_dir, shift=shift, duration=duration)

    # Analyze sentiment for each restaurant
    for restaurant in restaurants:
        analyze_restaurant(restaurant, args.output_dir)

if __name__ == "__main__":
    main()
    
