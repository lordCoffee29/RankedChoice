from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import pandas as pd
import io
import os

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    try:
        with open('index.html', 'r') as f:
            return Response(f.read(), mimetype='text/html')
    except Exception as e:
        return f"Error: {e}", 500


@app.route('/style.css')
def css():
    try:
        with open('style.css', 'r') as f:
            return Response(f.read(), mimetype='text/css')
    except Exception as e:
        return f"Error: {e}", 500


@app.route('/script.js')
def js():
    try:
        with open('script.js', 'r') as f:
            return Response(f.read(), mimetype='application/javascript')
    except Exception as e:
        return f"Error: {e}", 500


def process_ranked_choice_voting(csv_content):
    """Process ranked choice voting from CSV content and return results."""
    results = []
    
    df = pd.read_csv(io.StringIO(csv_content))
    df.drop('Timestamp', axis=1, inplace=True)
    df.drop('Name', axis=1, inplace=True)
    df.drop(' [Row 1]', axis=1, inplace=True)

    # Group columns by race (everything before the opening bracket)
    race_groups = {}
    for col in df.columns:
        if '[' in col:
            race_name = col.split('[')[0].strip()
            if race_name not in race_groups:
                race_groups[race_name] = []
            race_groups[race_name].append(col)

    # Create separate DataFrames for each race
    race_dfs = {}
    for race_name, columns in race_groups.items():
        race_dfs[race_name] = df[columns].copy()

    race_dfs_copy = {race: df.copy() for race, df in race_dfs.items()}

    for race_name, race_df in race_dfs_copy.items():
        race_result = {
            'race_name': race_name,
            'rounds': [],
            'winner': None,
            'final_message': None,
            'error': None
        }
        
        try:
            candidates = {}
            candidates_back = {}
            elimination = True

            while(elimination):
                round_info = {
                    'candidates': {},
                    'eliminated': None,
                    'elimination_votes': None,
                    'elimination_percentage': None
                }
                
                for index, ballot in race_df.iterrows():
                    # 1) Count first choice votes for each candidate
                    if ballot[0] not in candidates and ballot[0] != None and ballot[0] != "nan":
                        candidates[ballot[0]] = 1
                    else:       
                        candidates[ballot[0]] += 1
                
                round_info['candidates'] = candidates.copy()

                # 6) If only 2 candidates remain -> no endorsement
                if len(candidates) == 2 and elimination:
                    message = f"No endorsement for {race_name} with candidates {list(candidates.keys())}"
                    race_result['final_message'] = message
                    elimination = False

                # 2) If a candidate has > 60%, they win
                max_votes = max(candidates.values())
                if max_votes / len(race_df) >= 0.6:                  
                    winner = max(candidates, key=candidates.get)
                    message = f"{winner} wins with {max_votes} votes ({max_votes / len(race_df) * 100:.2f}%)"
                    race_result['winner'] = winner
                    race_result['final_message'] = message
                    elimination = False                 

                # 3) If no candidate has > 60%, eliminate the candidate with the fewest votes
                if elimination:
                    min_votes = min(candidates.values())
                    candidates_to_eliminate = [candidate for candidate, votes in candidates.items() if votes == min_votes]
                    
                    # 3.1) If there is a tie, eliminate the candidate with the fewest votes in the previous round
                    if candidates_to_eliminate and len(candidates_to_eliminate) > 1 and candidates_back:
                        previous_min_votes = min(candidates_back[candidate] for candidate in candidates_to_eliminate if candidate in candidates_back)
                        candidates_to_eliminate = [candidate for candidate in candidates_to_eliminate if candidates_back.get(candidate, float('inf')) == previous_min_votes]

                        if len(candidates_to_eliminate) > 1:
                            race_result['final_message'] = f"Unable to determine winner for {race_name} - tie between {', '.join(candidates_to_eliminate)}"
                            race_result['rounds'].append(round_info)
                            elimination = False
                            break

                    candidate_to_eliminate = candidates_to_eliminate[0]
                    
                    candidates_back = candidates.copy()
                    
                    round_info['eliminated'] = candidate_to_eliminate
                    round_info['elimination_votes'] = min_votes
                    round_info['elimination_percentage'] = f"{min_votes / len(race_df) * 100:.2f}%"
                    
                    del candidates[candidate_to_eliminate]

                    # 4) Redistribute the votes
                    for index, ballot in race_df.iterrows():
                        new_ballot = [choice for choice in ballot if choice != candidate_to_eliminate]
                        while len(new_ballot) < len(ballot):
                            new_ballot.append(None)
                        race_df.loc[index] = new_ballot
                    
                    candidates = {}
                
                race_result['rounds'].append(round_info)
        
        except Exception as e:
            race_result['error'] = str(e)
        
        results.append(race_result)
    
    return results


@app.route('/process', methods=['POST'])
def process_csv():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Read the file content
        csv_content = file.read().decode('utf-8')
        
        # Process the voting
        results = process_ranked_choice_voting(csv_content)
        
        return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
