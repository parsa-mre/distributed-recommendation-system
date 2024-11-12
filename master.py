from flask import Flask, request, jsonify
import requests
import math
import time

app = Flask(__name__)

# List of worker endpoints (assuming workers are running and accessible via these URLs)
workers = [
    "http://localhost:5001/process",  # Worker 1's endpoint (running on port 5001)
]

# Function to distribute work among workers
def distribute_work(movie_name, reviews_data):
    chunk_size = math.ceil(len(reviews_data) / len(workers))
    chunks = [reviews_data[i:i + chunk_size] for i in range(0, len(reviews_data), chunk_size)]
    
    results = []
    for i, chunk in enumerate(chunks):
        response = requests.post(workers[i], json={"movie_name": movie_name, "reviews": chunk})
        
        if response.status_code == 200:
            results.append(response.json()["recommended_movies"])
        else:
            results.append(None)

    # Aggregate the results: In this case, we can merge the recommendations from each worker
    final_recommendations = set()  # Using a set to avoid duplicate recommendations
    for result in results:
        if result:
            final_recommendations.update(result)

    return list(final_recommendations)  # Convert set back to list

# Route to handle user requests for movie recommendations
@app.route('/recommend', methods=['POST'])
def recommend():
    # Extracting movie name and reviews data from the incoming request
    data = request.json
    movie_name = data.get('movie_name')
    reviews_data = data.get('reviews_data')
    
    if not movie_name or not reviews_data:
        return jsonify({"error": "Movie name and reviews data must be provided"}), 400
    
    # Timing the process to evaluate performance
    start_time = time.time()

    # Distribute the work to workers
    recommended_movies = distribute_work(movie_name, reviews_data)

    # Calculate the time taken for processing
    end_time = time.time()
    time_taken = end_time - start_time
    
    # Returning the recommended movies and the time taken to process the request
    return jsonify({
        "recommended_movies": recommended_movies,
        "time_taken": time_taken
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
