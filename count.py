import pandas as pd
import sys
import json


def process_ranked_choice_voting(filename):
    """Process ranked choice voting from a CSV file and return results."""
    results = []
    
    df = pd.read_csv(filename)
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

    # Display the groups
    for race, cols in race_groups.items():
        print(f"{race}: {cols}")


    # Create separate DataFrames for each race
    race_dfs = {}
    for race_name, columns in race_groups.items():
        race_dfs[race_name] = df[columns].copy()

    # Display the race names
    print("Available races:", list(race_dfs.keys()))

    race_dfs_copy = {race: df.copy() for race, df in race_dfs.items()}

    for race_name, race_df in race_dfs_copy.items():
        race_result = {
            'race_name': race_name,
            'rounds': [],
            'winner': None,
            'final_message': None
        }
        
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
            
            print(f"\n=== Starting round for {race_name} ===")
            for index, ballot in race_df.iterrows():
                # print(ballot)
                # 0) Process the ballot
                # Handled: ballot[0] = first choice

                # 1) Count first choice votes for each candidate
                if ballot[0] not in candidates and ballot[0] != None and ballot[0] != "nan":
                    candidates[ballot[0]] = 1
                else:       
                    candidates[ballot[0]] += 1

                # print(candidates)
            
            round_info['candidates'] = candidates.copy()

            # 6) If one has 60% -> they win; if not, no endorsement
            if len(candidates) == 2 and elimination:
                message = f"No endorsement for {race_name} with candidates {list(candidates.keys())} at {candidates} votes"
                print(message)
                race_result['final_message'] = message
                elimination = False

            # 2) If a candidate has > 60%, they win
            max_votes = max(candidates.values())
            if max_votes / len(race_df) >= 0.6:                  
                winner = max(candidates, key=candidates.get)
                message = f"{winner} wins the {race_name} endorsement with {max_votes} votes ({max_votes / len(race_df) * 100:.2f}%)"
                print("Winner: ", candidates)
                print(message)
                race_result['winner'] = winner
                race_result['final_message'] = message
                
                elimination = False                 

            # 3) If no candidate has > 60%, eliminate the candidate with the fewest votes
            if elimination:

                min_votes = min(candidates.values())
                candidates_to_eliminate = [candidate for candidate, votes in candidates.items() if votes == min_votes]
                # 3.1) If there is a tie, eliminate the candidate with the fewest votes in the previous round (if applicable)
                if candidates_to_eliminate and len(candidates_to_eliminate) > 1 and candidates_back:
                    previous_min_votes = min(candidates_back[candidate] for candidate in candidates_to_eliminate if candidate in candidates_back)
                    candidates_to_eliminate = [candidate for candidate in candidates_to_eliminate if candidates_back.get(candidate, float('inf')) == previous_min_votes]

                    # TO-DO: what do we do here?
                    # Use the second place votes as a tie breaker (ballot[1])
                    if len(candidates_to_eliminate) > 1:
                        # print("Idk what to do help :(")
                        # print("Candidates tied for elimination in both rounds: ", candidates_to_eliminate)
                        # race_result['final_message'] = f"Unable to determine winner for {race_name} - tie between {', '.join(candidates_to_eliminate)}"
                        # race_result['rounds'].append(round_info)
                        print("Second place: ", ballot[1])
                        elimination = False
                        break
                    
                    print("Tie breaker—the candidates with the fewest votes in the previous round: ", candidates_to_eliminate)

                candidate_to_eliminate = candidates_to_eliminate[0]
                message = f"Eliminating {candidate_to_eliminate} with {min_votes} votes ({min_votes / len(race_df) * 100:.2f}%)"
                print("Elimination: ", candidates)
                print(message)
                candidates_back = candidates.copy()
                
                round_info['eliminated'] = candidate_to_eliminate
                round_info['elimination_votes'] = min_votes
                round_info['elimination_percentage'] = f"{min_votes / len(race_df) * 100:.2f}%"
                
                del candidates[candidate_to_eliminate]

                # 4) Redistribute the votes by removing the eliminated candidate from all ballots
                # and shifting remaining candidates up
                for index, ballot in race_df.iterrows():
                    # Create a list of choices without the eliminated candidate
                    new_ballot = [choice for choice in ballot if choice != candidate_to_eliminate]
                    # Pad with None if needed to maintain the same number of columns
                    while len(new_ballot) < len(ballot):
                        new_ballot.append(None)
                    # Update the row in the DataFrame
                    race_df.loc[index] = new_ballot
                
                # Reset candidates dictionary for next round
                # print(candidates)
                candidates = {}

                print(f"Preserved candidates: {candidates_back}:")
            
            race_result['rounds'].append(round_info)

            # 5) Repeat the process until a candidate has > 60% or only two candidates remain 
        
        results.append(race_result)
    
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count.py <filename.csv>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    try:
        results = process_ranked_choice_voting(filename)
        print("\n\n=== FINAL RESULTS ===")
        for race_result in results:
            print(f"\nRace: {race_result['race_name']}")
            if race_result['winner']:
                print(f"Winner: {race_result['winner']}")
            print(f"Result: {race_result['final_message']}")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)
