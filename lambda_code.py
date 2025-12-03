import os
import json
import requests  # This is needed for the newsapi-python client!
from newsapi import NewsApiClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import psycopg2

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_PORT = 5432

def lambda_handler(event, context):
    conn = None
    try:
        # The variables defined above are used here
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()"""
    # Main handler function: fetches news, performs sentiment analysis, 
    # and returns the augmented data.
    # """
    
    # --- 1. Configuration and Initialization ---
    
    # Get API key from environment variables (BEST PRACTICE!)
    # Ensure NEWS_API_KEY is set in your Lambda configuration.
        NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    
        if not NEWS_API_KEY:
            return {
            'statusCode': 400,
            'body': json.dumps({'error': 'NEWS_API_KEY environment variable is not set.'})
            }
        
    # Initialize News API Client
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)
    
    # Initialize VADER Sentiment Analyzer
        analyzer = SentimentIntensityAnalyzer()

    # --- 2. News Data Fetch (Focusing on 'US Stock Market') ---
    
        try:
        # Fetch the top 100 recent articles related to the stock market
            top_headlines = newsapi.get_everything(
            q='US Stock Market',
            language='en',
            sort_by='publishedAt',
            page_size=100
        )
        except requests.exceptions.HTTPError as http_err:
        # Handle specific HTTP errors (like 429 too many requests)
            print(f"HTTP error occurred: {http_err}")
            return {
            'statusCode': 503,
            'body': json.dumps({'error': f'News API HTTP Error: {http_err}'})
        }
        except Exception as e:
            print(f"An unexpected error occurred during news fetch: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to fetch news data'})
        }

        articles = top_headlines.get('articles', [])
    
        if not articles:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No articles found for the query.'})
            }

    # --- 3. Sentiment Analysis and Data Transformation ---
    
        processed_articles = []
    
        for article in articles:
        # Use the headline for concise sentiment analysis
            headline = article.get('title', '')
        
            if headline:
            # Get the VADER sentiment scores
                vs = analyzer.polarity_scores(headline)
            
            # The Compound Score is the normalized, weighted composite score (-1 to +1)
                compound_score = vs['compound']
            
            # Classify sentiment based on standard VADER thresholds
                if compound_score >= 0.05:
                    sentiment_label = 'Positive'
                elif compound_score <= -0.05:
                    sentiment_label = 'Negative'
                else:
                    sentiment_label = 'Neutral'

            # Create a simplified, augmented data structure
                processed_articles.append({
                    'title': headline,
                    'source': article.get('source', {}).get('name', 'N/A'),
                    'publishedAt': article.get('publishedAt'),
                    'url': article.get('url'),
                    'sentiment_score': compound_score,
                    'sentiment_label': sentiment_label
             })

        conn.commit()
        conn.close()
            
    # --- 4. Prepare Final Output ---
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'totalArticlesProcessed': len(processed_articles),
            'articles': processed_articles
        }, indent=4)
    }
    except Exception as e:
        # If any error occurred (e.g., network failure, SQL error)
        print(f"ERROR: {e}")
        if conn:
            # If a connection was established, roll back any partial changes
            conn.rollback() 
        raise e # Re-raise the exception to signal failure to Lambda

    finally:
        # 4. CLOSE (Guaranteed to run, cleans up the connection)
        if conn:
            conn.close()