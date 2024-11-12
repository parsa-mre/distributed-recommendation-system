from flask import Flask, jsonify, request
from celery import Celery
import pandas as pd
import numpy as np

app = Flask(__name__)

# Configure Celery
celery = Celery("tasks", broker="redis://redis:6379/0", backend="redis://redis:6379/0")


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})


@app.route("/similar", methods=["POST"])
def get_similar_movies():
    data = request.json
    movie_name = data.get("movie_name")

    if not movie_name:
        return jsonify({"error": "Movie name is required"}), 400

    # Create async tasks for workers
    job_ids = []
    num_partitions = 4  # Number of workers

    # First, get the movie_id for the given movie name
    task = celery.send_task("tasks.get_movie_id", args=[movie_name])
    movie_id = task.get()

    if not movie_id:
        return jsonify({"error": "Movie not found"}), 404

    # Then distribute the similarity computation
    for partition in range(num_partitions):
        task = celery.send_task(
            "tasks.find_similar_movies", args=[movie_id, partition, num_partitions]
        )
        job_ids.append(task.id)

    # Wait for all results
    results = []
    for job_id in job_ids:
        result = celery.AsyncResult(job_id).get()
        if result:
            results.extend(result)

    # Aggregate results
    final_recommendations = aggregate_results(results)

    return jsonify({"movie_name": movie_name, "similar_movies": final_recommendations})


def aggregate_results(results):
    if not results:
        return []

    # Convert results to DataFrame for easier processing
    df = pd.DataFrame(results)

    # Group by movie and take average of similarity scores
    aggregated = df.groupby(["movie_id", "movie_name"])["similarity_score"].mean()

    # Sort by similarity score and get top 10
    top_recommendations = aggregated.sort_values(ascending=False)[:10]

    # Convert to list of dictionaries
    return [
        {
            "movie_id": movie_id,
            "movie_name": movie_name,
            "similarity_score": float(score),
        }
        for (movie_id, movie_name), score in top_recommendations.items()
    ]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
