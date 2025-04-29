import pandas as pd
NYTIMES_REVIEWS = pd.read_csv(
  'https://docs.google.com/spreadsheets/d/e/2PACX-1vR6OOi2L9Ein88tZG6nNNeb6zxYfdYiO2id4x6ZmxwAqXQgkvtwjDIjFlfsJw7s0gYl5FDP57fXmNkD/pub?output=csv',
  index_col=0, 
  parse_dates=['date of review']
)
