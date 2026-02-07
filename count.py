import pandas as pd

df = pd.read_csv('ballot_data.csv')
df.drop('Timestamp', axis=1, inplace=True)
df.drop('Name', axis=1, inplace=True)
df.drop(' [Row 1]', axis=1, inplace=True)

df.head()

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
    # print(f"Processing race: {race_name}")
    # print(race_df)
    # print()  # blank line for readability
    candidates = {}
    elimination = True

    while(elimination):
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

        # 6) If one has 60% -> they win; if not, no endorsement
        if len(candidates) == 2 and elimination:
            print(f"No endorsement for {race_name} with candidates {list(candidates.keys())} at {candidates} votes")
            elimination = False

        # 2) If a candidate has > 60%, they win
        max_votes = max(candidates.values())
        if max_votes / len(race_df) >= 0.6:                  
            winner = max(candidates, key=candidates.get)
            print("Winner: ", candidates)
            print(f"{winner} wins the {race_name} endorsement with {max_votes} votes ({max_votes / len(race_df) * 100:.2f}%)")
            
            elimination = False                 

        # 3) If no candidate has > 60%, eliminate the candidate with the fewest votes
        if elimination:
            min_votes = min(candidates.values())
            candidates_to_eliminate = [candidate for candidate, votes in candidates.items() if votes == min_votes]
            # Assuming no ties for elimination
            candidate_to_eliminate = candidates_to_eliminate[0]
            print("Elimination: ", candidates)
            print(f"Eliminating {candidate_to_eliminate} with {min_votes} votes ({min_votes / len(race_df) * 100:.2f}%)")
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

        # 5) Repeat the process until a candidate has > 60% or only two candidates remain 


