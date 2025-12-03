import streamlit as st
import pandas as pd
import psycopg2
import os

# --- Configuration (Environment variables for ECS) ---
# DB_HOST = os.environ.get("DB_HOST", "news-sentiment-db-instance-2.crokgysyorow.ap-south-1.rds.amazonaws.com")
# DB_NAME = os.environ.get("DB_NAME", "postgres")
# DB_USER = os.environ.get("DB_USER", "postgres")
# DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres_root")
# DB_PORT = os.environ.get("DB_PORT", "5432")

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT")

# --- Database Connection Function ---
@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None

# --- Data Fetching Function ---
def fetch_data(conn, query):
    if conn:
        df = pd.read_sql(query, conn)
        return df
    return pd.DataFrame()


# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Real-Time US Stock Market Sentiment Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

conn = get_db_connection()

if conn:
    # 1. Overall KPI
    kpi_query = """
    SELECT 
        CAST(AVG(sentiment_score) AS NUMERIC(10, 4)) AS overall_average_sentiment
    FROM 
        news_articles
    WHERE 
        published_at >= NOW() - INTERVAL '24 hours';
    """
    kpi_df = fetch_data(conn, kpi_query)

    # overall_sentiment = kpi_df.iloc[0]['overall_average_sentiment'] if not kpi_df.empty else 0.0000
    # if not kpi_df.empty and kpi_df.iloc[0]['overall_average_sentiment'] is not None:
    #     overall_sentiment = float(kpi_df.iloc[0]['overall_average_sentiment'])
    # else:
    #     overall_sentiment = 0.0000 # Default to neutral (0.0) if no data or NULL average
    overall_sentiment = 0.0000 # Default to 0.0 (neutral)
    
    # Check if DataFrame is not empty AND the extracted value is not None
    if not kpi_df.empty:
        db_value = kpi_df.iloc[0]['overall_average_sentiment']
        if db_value is not None:
            # We explicitly convert it to float to ensure the comparison works
            overall_sentiment = float(db_value)

    color = (
        "green" if overall_sentiment > 0.1 else
        "red" if overall_sentiment < -0.1 else
        "orange"
    )

    st.markdown(
        f"## Current 24-Hour Sentiment: <span style='color:{color};'>{overall_sentiment}</span>",
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2 = st.columns([7, 3])

    with col1:
        # 2. Daily Trend Chart
        st.header("Daily Sentiment Trend")
        trend_query = """
        SELECT
            DATE(published_at) AS news_date,
            CAST(AVG(sentiment_score) AS NUMERIC(10, 4)) AS average_sentiment
        FROM
            news_articles
        GROUP BY
            news_date
        ORDER BY
            news_date ASC;
        """
        trend_df = fetch_data(conn, trend_query)
        st.line_chart(trend_df.set_index("news_date")["average_sentiment"])

    with col2:
        # 3. Recent Headlines
        st.header("Recent Headlines")
        headlines_query = """
        SELECT
            DATE(published_at),
            title,
            CAST(sentiment_score AS NUMERIC(10, 4)) AS sentiment_score
        FROM
            news_articles
        ORDER BY
            published_at DESC
        LIMIT 10;
        """
        headlines_df = fetch_data(conn, headlines_query)

        st.dataframe(
            headlines_df,
            column_config={
                "sentiment_score": st.column_config.ProgressColumn(
                    "Sentiment",
                    help="Sentiment Score (-1.0 to 1.0)",
                    format="%f",
                    min_value=-1.0,
                    max_value=1.0
                ),
            },
            hide_index=True
        )

# Close DB connection
if conn:
    conn.close()
