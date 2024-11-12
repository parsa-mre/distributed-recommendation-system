from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# List of worker URLs to distribute requests
worker_urls = [
    "http://localhost:5001/process",
    "http://localhost:5002/process",
    "http://localhost:5003/process"
]

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    movie_name = data.get('movie_name')

    if not movie_name:
        return jsonify({"error": "Movie name must be provided"}), 400

    recommendations = set()

    # Distribute the request to each worker
    for url in worker_urls:
        try:
            response = requests.post(url, json={"movie_name": movie_name})
            if response.status_code == 200:
                worker_recommendations = response.json().get("recommended_movies", [])
                recommendations.update(worker_recommendations)
            else:
                print(f"Worker at {url} responded with an error.")
        except requests.RequestException as e:
            print(f"Worker at {url} is not available: {e}")

    # Send back aggregated recommendations as a unique list
    return jsonify({"recommended_movies": list(recommendations)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)  # Master listens on port 5000
