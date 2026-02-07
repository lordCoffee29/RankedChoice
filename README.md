# Ranked Choice Voting Counter

## Usage

### Command Line (Python)
```bash
python count.py <filename.csv>
```

Example:
```bash
python count.py ballot_data.csv
```

### Web Interface

1. Install required dependencies:
```bash
pip install flask flask-cors pandas
```

2. Start the Flask server:
```bash
python server.py
```

3. Open `index.html` in your web browser

4. Upload a CSV file and click "Process CSV" to see the results

The web interface will display:
- Winner for each race (if applicable)
- All elimination rounds
- Vote counts for each candidate in each round
- Which candidates were eliminated and why
