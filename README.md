# cpsc490
## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd <project-directory>
    ```

2.  **Create and Activate Virtual Environment (Recommended):**
    ```bash
    # Create virtual environment
    python3 -m venv venv

    # Activate virtual environment
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Prepare Data:**
    *   Place restaurant review JSON files inside the `data/restaurant_reviews/` directory.
    *   Ensure the `data/dict.csv` file exists and contains word-to-category mappings (format: `category,word`).

5.  **Download NLTK Data (Required for Sentiment Analysis):**
    The first time you run either the CLI tool or the web app, it might attempt to download the 'vader_lexicon'. You can also pre-download it:
    ```bash
    python -c "import nltk; nltk.download('vader_lexicon')"
    ```

## Usage

Ensure your virtual environment is activated before running any commands.

### Command-Line Analysis (`src/sentiment_analysis.py`)
### Command-Line Metrics (`src/sa_score_analysis.py`)

Output files (CSVs and PNGs) will be saved in the `data/output/` directory by default.

### Web Application (`src/app.py`)

1.  **Run the Flask development server:**
    ```bash
    python -m src.app
    ```
2.  **Access the application:** Open your web browser and navigate to `http://127.0.0.1:5000` (or the address provided by Flask).
