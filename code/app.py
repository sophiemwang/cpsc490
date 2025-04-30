from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
from collections import Counter
import re
import os
from .restaurant import Restaurant
from datetime import datetime, timezone
import pandas as pd

# Loads word categories
def load_word_categories():
    word_categories = {}
    # Constructs path relative to this file's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dict_path = os.path.join(current_dir, '..', 'data', 'dict.csv')
    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            for line in f:
                category, word = line.strip().split(',')
                word_categories[word.lower()] = category
    except Exception as e:
        print(f"Error loading word categories: {str(e)}")
    return word_categories

WORD_CATEGORIES = load_word_categories()

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# Loads restaurants
def load_restaurants():
    restaurants = []
    # Constructs path relative to this file's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, '..', 'data', 'restaurant_reviews')
    # Checks if data directory exists
    if not os.path.isdir(data_dir):
        print(f"Error: Data directory not found at {data_dir}")
        return []
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(data_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        restaurant = Restaurant.from_dict(data[0])
                    else:
                        restaurant = Restaurant.from_dict(data)
                    restaurants.append(restaurant)
            except Exception as e:
                print(f"Error loading {filename}: {str(e)}")
    return restaurants

RESTAURANTS = load_restaurants()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/restaurants')
# Returns the list of available restaurants with their review date ranges
def get_restaurants():
    restaurant_list = []
    for r in RESTAURANTS:
        if r.reviews:
            dates = [review.date.replace(tzinfo=None) for review in r.reviews]
            min_date = min(dates).strftime('%Y-%m-%d')
            max_date = max(dates).strftime('%Y-%m-%d')
        else:
            min_date = None
            max_date = None           
        restaurant_list.append({
            "id": r.businessId, 
            "name": r.title,
            "min_date": min_date,
            "max_date": max_date
        })
    return jsonify(restaurant_list)

@app.route('/wordcloud')
def generate_wordcloud():
    restaurant_id = request.args.get('restaurant_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    top_n = int(request.args.get('top_n', 50))
    sentiment_filter = request.args.get('sentiment_filter', 'all')
    restaurant = next((r for r in RESTAURANTS if r.businessId == restaurant_id), None)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    df = restaurant.analyze_sentiment()
    # Applies timezone removal to each date
    df['date'] = df['date'].apply(lambda x: x.replace(tzinfo=None) if x is not None else x)
    # Creates mask for filtering
    mask = pd.Series(True, index=df.index)
    # Applies date filter if provided
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        mask &= (df['date'] >= start) & (df['date'] <= end)
    # Applies sentiment filter if specified
    if sentiment_filter != 'all':
        selected_sentiments = sentiment_filter.split(',')
        mask &= df['sentiment'].isin(selected_sentiments)  
    filtered_df = df[mask]
    reviews = [restaurant.reviews[i] for i in filtered_df.index]
    Total_filtered_reviews = len(reviews)
    Word_review_count = Counter()
    Category_review_count = Counter()
    # Defines stopwords
    stopwords = {'and', 'the', 'to', 'of', 'a', 'in', 'for', 'is', 'on', 'that', 'was', 
                 'with', 'it', 'we', 'i', 'at', 'be', 'this', 'had', 'our', 'my', 'were',
                 'but', 'by', 'from', 'as', 'they', 'are', 'so', 'very', 'an', 'have', 'their',
                 'would', 'could', 'not', 'which', 'you', 'when', 'what', 'just', 'all', 'has',
                 'there', 'one', 'some', 'will', 'your', 'us', 'if', 'who', 'his', 'her', 'them', 
                 'its', 'also', 'ive', 'can', 'either', 'got', 'because',"it's"}
    All_filtered_words = []

    # Processes reviews to count words per review
    for r in reviews:
        cleaned_text = re.sub(r'[^\w\s]', '', r.review.lower())
        words = cleaned_text.split()
        filtered_review_words = [word for word in words if word not in stopwords and len(word) > 2]
        All_filtered_words.extend(filtered_review_words)
        unique_words = set(filtered_review_words)
        for word in unique_words:
            Word_review_count[word] += 1
        categories = [WORD_CATEGORIES.get(word, 'other') for word in unique_words]
        unique_categories = set(categories)
        for category in unique_categories:
            Category_review_count[category] += 1
    # Calculates word proportions
    word_counts = Counter(All_filtered_words)
    top_words = word_counts.most_common(top_n)  
    word_results = []
    for word, count in top_words:
        proportion = Word_review_count[word] / Total_filtered_reviews if Total_filtered_reviews > 0 else 0
        word_results.append({"word":word, "review_count": count, "proportion": proportion})

    # Calculates category proportions
    category_results = []
    for category, count in Category_review_count.items():
        proportion = count / Total_filtered_reviews if Total_filtered_reviews > 0 else 0
        category_results.append({"category": category, "category_review_count": count, "proportion": proportion})

    result = {
        "words": word_results,
        "categories": category_results
    }
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
    
