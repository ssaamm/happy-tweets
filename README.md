# Real-time Sentiment Analysis

## Setup

1. Replace the access token in `frontend/script.js` with your [Mapbox](https://www.mapbox.com/studio/account/tokens/)
access token

2. Start Kafka

3. ```
   pip install -r requirements.txt
   ```

4. Start the Twitter to Kafka bridge with whatever keywords you're interested in:
   ```
   python ingestor.py python
   ```

5. Start the websocket handler
   ```
   python server.py
   ```

6. Point your browser to `frontend/index.html`
