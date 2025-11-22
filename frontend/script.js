const BACKEND_URL = "http://127.0.0.1:5001/api/hello";

document.getElementById("btn").addEventListener("click", async () => {
    const output = document.getElementById("output");
    output.textContent = "Loading...";

    try {
        const res = await fetch(BACKEND_URL);
        const data = await res.json();
        output.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
        output.textContent = "Error connecting to backend.";
    }
});