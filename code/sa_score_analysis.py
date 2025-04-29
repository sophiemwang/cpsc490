import os
import pandas as pd
import argparse
from .restaurant import Restaurant
from .sentiment_analysis import load_restaurant, REVIEWS_DIR_DEFAULT
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import multiprocess

# Get base directory (project root) relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_dir = os.path.join(BASE_DIR, 'data', 'output')

# Wrapper function for multiprocessing: loads a restaurant and runs sentiment analysis using NLTK
def process_restaurant(file_path):
    try:
        restaurant = load_restaurant(file_path)
        default_df, custom_df = run_nltk_analysis(restaurant)
        return default_df, custom_df
    except Exception as e:
        print(f"Failed to load or analyze {os.path.basename(file_path)}: {e}")
        return pd.DataFrame(), pd.DataFrame()

"""
Runs sentiment analysis on a restaurant's Yelp reviews using both the default and a custom NLTK VADER lexicon.
Parameters:
    restaurant (Restaurant): A Restaurant object containing review data.
Returns:
    tuple[pd.DataFrame, pd.DataFrame]: Two DataFrames containing sentiment analysis results:
        - The first uses the default VADER lexicon.
        - The second uses a custom restaurant-specific lexicon.
"""
def run_nltk_analysis(restaurant: Restaurant) -> tuple[pd.DataFrame, pd.DataFrame]:
    print(f"Running NLTK analysis for {restaurant.title}...")
    # Perform sentiment analysis with default lexicon
    try:
        default_df = restaurant.analyze_sentiment(use_custom_lexicon=False)
    except Exception as e:
        print(f"Error analyzing sentiment with default lexicon for {restaurant.title}: {e}")
        return pd.DataFrame(), pd.DataFrame()
    # Perform sentiment analysis with custom lexicon
    try:
        custom_df = restaurant.analyze_sentiment(use_custom_lexicon=True)
    except Exception as e:
        print(f"Error analyzing sentiment with custom lexicon for {restaurant.title}: {e}")
        return pd.DataFrame(), pd.DataFrame()
    # Process default lexicon results
    default_df['review_text'] = default_df['review_text'].str.replace('\n', ' ', regex=False)
    default_analysis = default_df[['date', 'rating', 'sentiment_compound', 'review_text']].copy()
    default_analysis.rename(columns={'sentiment_compound': 'nltk_sentiment_score'}, inplace=True)
    default_analysis['restaurant'] = restaurant.title
    default_analysis['lexicon'] = 'default'
    # Process custom lexicon results  
    custom_df['review_text'] = custom_df['review_text'].str.replace('\n', ' ', regex=False)
    custom_analysis = custom_df[['date', 'rating', 'sentiment_compound', 'review_text']].copy()
    custom_analysis.rename(columns={'sentiment_compound': 'nltk_sentiment_score'}, inplace=True)
    custom_analysis['restaurant'] = restaurant.title
    custom_analysis['lexicon'] = 'custom'
    
    return default_analysis, custom_analysis

"""
Calculates sentiment scores for all restaurants using both default and custom lexicons.
"""
def calculate_nltk_scores():
    # Get all restaurant files from the default directory
    restaurant_files = [os.path.join(REVIEWS_DIR_DEFAULT, f) for f in os.listdir(REVIEWS_DIR_DEFAULT) 
                       if f.endswith('.json')]
    # Process all restaurants and combine results
    default_results = []
    custom_results = []
    print(f"Analyzing all {len(restaurant_files)} restaurants...")
    # Set up multiprocessing pool to process restaurants in parallel
    num_cores = multiprocess.cpu_count()
    print(f"Using {num_cores} CPU cores for parallel processing")
    with multiprocess.Pool(processes=num_cores) as pool:
        results = pool.map(process_restaurant, restaurant_files)
    # Separate results
    for default_df, custom_df in results:
        if not default_df.empty:
            default_results.append(default_df)
        if not custom_df.empty:
            custom_results.append(custom_df)
    os.makedirs(output_dir, exist_ok=True)

    if default_results:
        default_combined = pd.concat(default_results, ignore_index=True)
        default_output = os.path.join(output_dir, "nltk_score_analysis_default_lexicon.csv")
        try:
            default_combined.to_csv(default_output, index=False)
            print(f"Saved default lexicon analysis results to {default_output}")
        except Exception as e:
            print(f"Error saving default lexicon CSV: {e}")
    if custom_results:
        custom_combined = pd.concat(custom_results, ignore_index=True)
        custom_output = os.path.join(output_dir, "nltk_score_analysis_custom_lexicon.csv")
        try:
            custom_combined.to_csv(custom_output, index=False)
            print(f"Saved custom lexicon analysis results to {custom_output}")
        except Exception as e:
            print(f"Error saving custom lexicon CSV: {e}")

"""
Analyzes correlations between ratings and sentiment scores for both lexicons.
"""
def analyze_correlations():
    # Load datasets
    default_path = os.path.join(output_dir, "nltk_score_analysis_default_lexicon.csv")
    custom_path = os.path.join(output_dir, "nltk_score_analysis_custom_lexicon.csv")   
    try:
        default_df = pd.read_csv(default_path)
        custom_df = pd.read_csv(custom_path)
    except Exception as e:
        print(f"Error loading analysis files: {e}")
        return
    # Clean data
    default_df = default_df.dropna(subset=['rating', 'nltk_sentiment_score'])
    custom_df = custom_df.dropna(subset=['rating', 'nltk_sentiment_score'])
    # Calculate correlations
    default_corr, default_p = stats.pearsonr(default_df['rating'], default_df['nltk_sentiment_score'])
    custom_corr, custom_p = stats.pearsonr(custom_df['rating'], custom_df['nltk_sentiment_score'])
    print("\nCorrelation Analysis Results:")
    print(f"Default Lexicon - Correlation: {default_corr:.3f}, p-value: {default_p:.3e}")
    print(f"Custom Lexicon - Correlation: {custom_corr:.3f}, p-value: {custom_p:.3e}")
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    # Default lexicon plot
    sns.boxplot(data=default_df, x='rating', y='nltk_sentiment_score', 
                ax=ax1)
    sns.regplot(data=default_df, x='rating', y='nltk_sentiment_score', 
                ax=ax1, scatter=False, color='red', truncate=False)
    ax1.set_title(f'Default Lexicon\nCorrelation: {default_corr:.3f}')
    ax1.set_xlabel('Rating')
    ax1.set_ylabel('Sentiment Score')
    # Custom lexicon plot
    sns.boxplot(data=custom_df, x='rating', y='nltk_sentiment_score', 
                ax=ax2)
    sns.regplot(data=custom_df, x='rating', y='nltk_sentiment_score', 
                ax=ax2, scatter=False, color='red', truncate=False)
    ax2.set_title(f'Custom Lexicon\nCorrelation: {custom_corr:.3f}')
    ax2.set_xlabel('Rating')
    ax2.set_ylabel('Sentiment Score')
    plt.tight_layout()
    correlation_plot_path = os.path.join(output_dir, "sentiment_correlation_analysis.png")
    try:
        plt.savefig(correlation_plot_path)
        print(f"\nCorrelation plot saved to: {correlation_plot_path}")
    except Exception as e:
        print(f"Error saving correlation plot: {e}")
    
    plt.close()

if __name__ == "__main__":
    calculate_nltk_scores()
    analyze_correlations()
    
