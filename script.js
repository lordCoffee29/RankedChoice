const uploadBtn = document.getElementById('uploadBtn');
const csvFile = document.getElementById('csvFile');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const results = document.getElementById('results');

uploadBtn.addEventListener('click', async () => {
    const file = csvFile.files[0];
    
    if (!file) {
        showError('Please select a CSV file first');
        return;
    }
    
    if (!file.name.endsWith('.csv')) {
        showError('Please upload a CSV file');
        return;
    }
    
    // Show loading, hide error and results
    loading.classList.remove('hidden');
    error.classList.add('hidden');
    results.innerHTML = '';
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        loading.classList.add('hidden');
        
        if (response.ok) {
            displayResults(data.results);
        } else {
            showError(data.error || 'An error occurred');
        }
    } catch (err) {
        loading.classList.add('hidden');
        showError('Failed to connect to server. Make sure server.py is running on port 5001.');
    }
});

function showError(message) {
    error.textContent = message;
    error.classList.remove('hidden');
}

function displayResults(resultData) {
    results.innerHTML = '';
    
    resultData.forEach(race => {
        const raceDiv = document.createElement('div');
        raceDiv.className = 'race-result';
        
        // Race title
        const raceTitle = document.createElement('h2');
        raceTitle.textContent = race.race_name;
        raceDiv.appendChild(raceTitle);
        
        // Check for error first
        if (race.error) {
            const errorBox = document.createElement('div');
            errorBox.className = 'error';
            errorBox.textContent = race.error;
            raceDiv.appendChild(errorBox);
        }
        // Winner or no endorsement
        else if (race.winner) {
            const winnerBox = document.createElement('div');
            winnerBox.className = 'winner-box';
            winnerBox.innerHTML = `
                <h3>🏆 Winner: ${race.winner}</h3>
                <p>${race.final_message}</p>
            `;
            raceDiv.appendChild(winnerBox);
        } else if (race.final_message) {
            const noEndorsement = document.createElement('div');
            noEndorsement.className = 'no-endorsement';
            noEndorsement.textContent = race.final_message;
            raceDiv.appendChild(noEndorsement);
        }
        
        // Elimination rounds
        if (race.rounds && race.rounds.length > 0) {
            const roundsDiv = document.createElement('div');
            roundsDiv.className = 'rounds';
            
            const roundsTitle = document.createElement('h3');
            roundsTitle.textContent = 'Elimination Rounds';
            roundsDiv.appendChild(roundsTitle);
            
            race.rounds.forEach((round, index) => {
                const roundDiv = document.createElement('div');
                roundDiv.className = 'round';
                
                const roundHeader = document.createElement('div');
                roundHeader.className = 'round-header';
                roundHeader.textContent = `Round ${index + 1}`;
                roundDiv.appendChild(roundHeader);
                
                // Display candidates and votes
                const candidatesDiv = document.createElement('div');
                candidatesDiv.className = 'candidates';
                
                for (const [candidate, votes] of Object.entries(round.candidates)) {
                    if (candidate !== 'null' && candidate !== 'undefined' && candidate !== 'None') {
                        const candidateDiv = document.createElement('div');
                        candidateDiv.className = 'candidate';
                        candidateDiv.innerHTML = `
                            <span class="candidate-name">${candidate}</span>
                            <span class="candidate-votes">${votes} votes</span>
                        `;
                        candidatesDiv.appendChild(candidateDiv);
                    }
                }
                
                roundDiv.appendChild(candidatesDiv);
                
                // Display elimination
                if (round.eliminated) {
                    const eliminationDiv = document.createElement('div');
                    eliminationDiv.className = 'elimination';
                    eliminationDiv.innerHTML = `
                        <strong>Eliminated:</strong> ${round.eliminated} 
                        (${round.elimination_votes} votes, ${round.elimination_percentage})
                    `;
                    roundDiv.appendChild(eliminationDiv);
                }
                
                roundsDiv.appendChild(roundDiv);
            });
            
            raceDiv.appendChild(roundsDiv);
        }
        
        results.appendChild(raceDiv);
    });
}
