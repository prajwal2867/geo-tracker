const status = document.querySelector("#status");
const button = document.querySelector("#share-location");

function shareLocation() {
    if (!navigator.geolocation) {
        status.textContent = "This browser does not support geolocation.";
        return;
    }

    button.disabled = true;
    status.textContent = "Waiting for browser location permission...";

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            try {
                const response = await fetch("/location", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    })
                });

                if (!response.ok) {
                    const result = await response.json();
                    throw new Error(result.error || "The server could not save the location.");
                }

                status.textContent = "Your location was sent to the server.";
            } catch (error) {
                status.textContent = `Unable to send location: ${error.message}`;
            } finally {
                button.disabled = false;
            }
        },
        (error) => {
            const messages = {
                1: "Location permission was denied.",
                2: "Your location is currently unavailable.",
                3: "The location request timed out."
            };
            status.textContent = messages[error.code] || "Unable to get your location.";
            button.disabled = false;
        }
    );
}

button.addEventListener("click", shareLocation);
shareLocation();
