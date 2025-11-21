    let countdown = 3;
    let interval;

    // Start the countdown and show manual weight input after countdown completes
    function startProcess() {
        console.log("Start process triggered");
        document.getElementById('intro-screen').classList.add('hidden');
        document.getElementById('countdown').classList.remove('hidden');

        interval = setInterval(() => {
            if (countdown <= 0) {
                clearInterval(interval);
                document.getElementById('countdown').classList.add('hidden');
                document.getElementById('manual-weight-section').classList.remove('hidden');
                console.log("Countdown complete, showing manual weight section");
            } else {
                countdown -= 1;
                document.getElementById('countdown-timer').textContent = countdown;
                console.log(`Countdown: ${countdown}`);
            }
        }, 1000);
    }

    // Fetch weight from the backend API
    async function getWeight() {
        const response = await fetch('/get_weight?weight=70');  // Fetch weight, either from scale or manual input
        const data = await response.json();  // Parse the JSON response
        displayPlanetWeights(data.earth_kg, data.planets);  // Display the weight on different planets
    }

    // Display weight on each planet dynamically
    function displayPlanetWeights(earthWeight, planetData) {
        const planets = Object.keys(planetData);  // Get the planet names
        const planetWeightsDiv = document.getElementById("planet-weights");
        planetWeightsDiv.innerHTML = '';  // Clear existing content

        // Loop through the planets data and display each
        planets.forEach(planet => {
            const planetDiv = document.createElement("div");
            planetDiv.classList.add("planet-weight");
            planetDiv.innerHTML = `<h3>${planet}</h3><p>${planetData[planet].toFixed(2)} kg</p>`;
            planetWeightsDiv.appendChild(planetDiv);
        });
    }

    // Manual Weight Input Submission
    function submitWeight() {
        const manualWeight = parseFloat(document.getElementById('manual-weight-input').value);

        if (isNaN(manualWeight) || manualWeight <= 0) {
            document.getElementById('manual-weight-input').style.borderColor = "red";
            document.getElementById('manual-weight-error').textContent = "Please enter a valid weight!";
            return;
        }

        // Disable the submit button after submission
        document.getElementById('submit-weight-btn').disabled = true;

        // Provide feedback
        alert("Weight submitted successfully!");

        // Calculate the planet weights with the manual input
        calculatePlanetWeights(manualWeight);

        // Optionally, clear the input field after submission
        document.getElementById('manual-weight-input').value = '';
    }

    function calculatePlanetWeights(weight) {
        const planetWeights = {
            "Mercury": weight * 0.38,
            "Venus": weight * 0.91,
            "Earth": weight,
            "Mars": weight * 0.38,
            "Jupiter": weight * 2.53,
            "Saturn": weight * 1.07
        };

        let planetHtml = '';
        for (let planet in planetWeights) {
            planetHtml += `
                <div class="planet-card">
                    <h3>${planet}</h3>
                    <p>${planetWeights[planet].toFixed(2)} kg</p>
                </div>
            `;
        }

        document.getElementById('planet-weights').innerHTML = planetHtml;
        document.getElementById('planet-selection').classList.remove('hidden');
    }
