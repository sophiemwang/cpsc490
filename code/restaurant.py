from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import json
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
import numpy as np
import os
from .nyt_reviews import NYTIMES_REVIEWS
import yaml

@dataclass
class Address:
    city: str
    regionCode: str
    addressLine1: str
    addressLine2: Optional[str]
    addressLine3: Optional[str]
    postalCode: str
    formatted: str

@dataclass
class Coordinates:
    latitude: float
    longitude: float

@dataclass
class PhotoUrls:
    mediaItemSrcUrl: str
    mediaItemSrcSetUrl200x: str
    mediaItemSrcSetUrl300x: str
    userSrc: str
    userSrcSet200x: str
    userSrcSet300x: str

@dataclass
class Author:
    id: str
    name: str
    location: str
    photoUrls: Optional[PhotoUrls]
    friendCount: int
    reviewCount: int
    businessPhotoCount: int
    isElite: bool

@dataclass
class Feedback:
    usefulCount: int
    funnyCount: int
    coolCount: int

@dataclass
class Review:
    userName: str
    userUrl: str
    isElite: bool
    rating: float
    date: datetime
    review: str
    reviewLanguage: str
    reviewLink: str
    author: Author
    feedback: Feedback

@dataclass
class Restaurant:
    businessId: str
    type: str
    url: str
    title: str
    rating: float
    reviewCount: int
    priceRange: str
    categories: List[str]
    isClaimed: bool
    isBusinessClosed: bool
    yearEstablished: Optional[int]
    history: Optional[str]
    address: Address
    coordinates: List[Coordinates]
    highlights: List[str]
    primaryPhoto: str
    reviews: List[Review]
    nyt_review: Optional[pd.Series] = None
    nyt_review_date: Optional[datetime] = None
    nyt_review_rating: Optional[float] = None
    nyt_review_text: Optional[str] = None

    """
    Initializea NYT review data after object creation.
    """   
    def __post_init__(self):
        try:
            self.nyt_review = NYTIMES_REVIEWS.loc[self.title]
            self.nyt_review_date = self.nyt_review['date of review']
            self.nyt_review_rating = self.nyt_review['PW star rating']
        except KeyError:
            self.nyt_review = None
    """
    Converts the restaurant's reviews to a pandas DataFrame.
    Returns:
        - pd.DataFrame: DataFrame containing review data
    """   
    def to_dataframe(self) -> pd.DataFrame:
        data = []
        for review in self.reviews:
            data.append({
                'date': review.date,
                'rating': review.rating,
                'review_text': review.review,
                'is_elite': review.isElite,
                'useful_count': review.feedback.usefulCount,
                'funny_count': review.feedback.funnyCount,
                'cool_count': review.feedback.coolCount,
                'user_name': review.userName,
                'language': review.reviewLanguage
            })
        
        df = pd.DataFrame(data)
        df.sort_values('date', inplace=True)
        return df

    """
    Analyzes the sentiment of the reviews
    Parameters:
        - use_custom_lexicon (bool, optional): Whether to load and use the custom VADER lexicon.
                                                Defaults to True.
    Returns:
        - pd.DataFrame: DataFrame with sentiment scores
    """    
    def analyze_sentiment(self, use_custom_lexicon: bool = True) -> pd.DataFrame:
        # Downloads VADER lexicon (if not already downloaded)
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon')
        # Initialize the VADER sentiment analyzer
        sid = SentimentIntensityAnalyzer()
        # Conditionally loads and updates with custom lexicon
        if use_custom_lexicon:
            # Defines path to the custom lexicon file relative to this script
            current_dir = os.path.dirname(__file__)
            lexicon_path = os.path.join(current_dir, '..', 'data', 'vader_custom_lexicon.yaml')  # Updated extension
            new_words = {}
            try:
                with open(lexicon_path, 'r') as f:
                    new_words = yaml.safe_load(f)            
                # Updates the VADER lexicon with the custom words if loaded successfully
                # Doubles the value for it
                if new_words:
                    for word, score in new_words.items():
                        sid.lexicon[word] = score * 2
            except FileNotFoundError:
                print(f"Warning: Custom lexicon file not found at {lexicon_path}. Using default VADER lexicon.")
            except Exception as e:
                print(f"Warning: Error loading custom lexicon from {lexicon_path}: {e}. Using default VADER lexicon.")

        df = self.to_dataframe()       
        # Calculates sentiment scores
        df['sentiment_scores'] = df['review_text'].apply(lambda text: sid.polarity_scores(text))
        df['sentiment_compound'] = df['sentiment_scores'].apply(lambda score: score['compound'])
        df['sentiment_pos'] = df['sentiment_scores'].apply(lambda score: score['pos'])
        df['sentiment_neg'] = df['sentiment_scores'].apply(lambda score: score['neg'])
        df['sentiment_neu'] = df['sentiment_scores'].apply(lambda score: score['neu'])       
        # Classifies sentiment based on compound score
        df['sentiment'] = df['sentiment_compound'].apply(
            lambda score: 'positive' if score >= 0.05 else ('negative' if score <= -0.05 else 'neutral')
        )
        return df
    
    """
    Creates time-series visualizations of sentiment scores.
    Parameters: 
        - resample (str, optional): Time period for resampling
                'ME' for monthly (default)
                'QE' for quarterly
     """    
    def visualize_sentiment_over_time(self, resample='ME'):
        df = self.analyze_sentiment()
        df.set_index('date', inplace=True)
        date_format = '%Y-%m' if resample == 'ME' else '%Y-Q%q'
        # Counts positive and negative reviews by time period
        sentiment_counts = pd.DataFrame({
            'positive': df[df['sentiment'] == 'positive'].resample(resample).size(),
            'neutral': df[df['sentiment'] == 'neutral'].resample(resample).size(),
            'negative': df[df['sentiment'] == 'negative'].resample(resample).size()
        }).fillna(0)

        fig, ax = plt.subplots(figsize=(12, 6))
        # Plots sentiment counts
        sentiment_counts.plot(kind='bar', stacked=True, ax=ax,
                            color={'positive':'green', 'neutral':'yellow', 'negative':'red'})
        ax.set_title(f'Sentiment Distribution for {self.title}')
        ax.set_ylabel('Number of Reviews')
        # Formats x-axis dates with fewer labels to avoid crowding
        total_bars = len(sentiment_counts)
        step = max(3, total_bars // 10) if resample == 'ME' else max(1, total_bars // 8)
        positions = range(0, total_bars, step)
        ax.set_xticks(positions)
        date_labels = [sentiment_counts.index[i].strftime(date_format) for i in positions]
        ax.set_xticklabels(date_labels, rotation=45, ha='right')

        # Adds NYT review date if available
        if self.nyt_review_date is not None:
            nyt_period = pd.Timestamp(self.nyt_review_date).to_period(resample[0]) # 'ME' or 'QE'
            try:
                nyt_index_pos = sentiment_counts.index.to_period(resample[0]).get_loc(nyt_period)
                label_text = f'NYT Review ({self.nyt_review_date.strftime("%Y-%m-%d")}'
                if hasattr(self, 'nyt_review_rating') and self.nyt_review_rating:
                    label_text += f', Rating: {self.nyt_review_rating}'
                label_text += ')'
                ax.axvline(x=nyt_index_pos, color='blue', linestyle='--', linewidth=2, label=label_text)
                ax.legend()
            except KeyError:
                print(f"Warning: NYT review date {self.nyt_review_date} is outside the range of user reviews.")
        plt.tight_layout()
        return fig

    """
    Creates a Restaurant instance from JSON data.
    Parameters: 
        - data (dict): A dictionary containing all attributes needed to instantiate a Restaurant,
                 including nested review, address, and author structures.
    Returns: 
        - Restaurant: A fully initialized Restaurant instance with all related sub-objects (e.g., Reviews).
    """
    @classmethod
    def from_dict(cls, data: dict) -> 'Restaurant':
        address = Address(**data['address'])
        coordinates = [Coordinates(**coord) for coord in data['coordinates']]    
        reviews = []
        for review_data in data['reviews']:
            # Converts author data
            author_data = review_data['author']
            photo_urls = None
            if 'photoUrls' in author_data and author_data['photoUrls']:
                photo_urls = PhotoUrls(**{k: v for k, v in author_data['photoUrls'].items() 
                                        if k != '__typename'})           
            author = Author(
                id=author_data['id'],
                name=author_data['name'],
                location=author_data['location'],
                photoUrls=photo_urls,
                friendCount=author_data['friendCount'],
                reviewCount=author_data['reviewCount'],
                businessPhotoCount=author_data['businessPhotoCount'],
                isElite=author_data['isElite']
            )           
            # Converts feedback data
            feedback = Feedback(**review_data['feedback'])
            # Converts date string to datetime
            date = datetime.fromisoformat(review_data['date'].replace('Z', '+00:00'))
            
            # Creates Review instance
            review = Review(
                userName=review_data['userName'],
                userUrl=review_data['userUrl'],
                isElite=review_data['isElite'],
                rating=review_data['rating'],
                date=date,
                review=review_data['review'],
                reviewLanguage=review_data['reviewLanguage'],
                reviewLink=review_data['reviewLink'],
                author=author,
                feedback=feedback
            )
            reviews.append(review)
        
        # Creates Restaurant instance
        return cls(
            businessId=data['businessId'],
            type=data['type'],
            url=data['url'],
            title=data['title'],
            rating=data['rating'],
            reviewCount=data['reviewCount'],
            priceRange=data['priceRange'],
            categories=data['categories'],
            isClaimed=data['isClaimed'],
            isBusinessClosed=data['isBusinessClosed'],
            yearEstablished=data['yearEstablished'],
            history=data['history'],
            address=address,
            coordinates=coordinates,
            highlights=data['highlights'],
            primaryPhoto=data['primaryPhoto'],
            reviews=reviews
        )
