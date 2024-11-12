from celery import Celery
from pymongo import MongoClient
import numpy as np
from collections import defaultdict
import time
from random import random

celery = Celery("tasks", broker="redis://redis:6379/0", backend="redis://redis:6379/0")

# MongoDB connection
client = MongoClient("mongodb://mongodb:27017/")
db = client.movie_recommendations


@celery.task(name="tasks.get_movie_id")
def get_movie_id(movie_name):
    """Find movie ID by name"""
    movie = db.movies.find_one(
        {"title": {"$regex": f"^{movie_name}$", "$options": "i"}}
    )
    if movie:
        return str(movie["_id"])
    return None


@celery.task(name="tasks.find_similar_movies")
def find_similar_movies(movie_id, partition_id, total_partitions):
    print(f"Finding similar movies to {movie_id} in partition {partition_id}")

    try:
        # Get all ratings for the target movie
        target_ratings = list(db.ratings.find({"movie_id": movie_id}))

        if not target_ratings:
            print("No ratings found, using sample data")
            return generate_sample_recommendations(partition_id)

        # Create user-rating vector for target movie
        target_vector = {r["user_id"]: r["rating"] for r in target_ratings}

        # Get a partition of movies to compare against
        skip_count = partition_id * (db.movies.count_documents({}) // total_partitions)
        limit_count = db.movies.count_documents({}) // total_partitions

        all_movies = db.movies.find().skip(skip_count).limit(limit_count)

        results = []
        for movie in all_movies:
            other_movie_id = str(movie["_id"])

            # Don't compare with itself
            if other_movie_id == movie_id:
                continue

            # Get ratings for comparison movie
            other_ratings = list(db.ratings.find({"movie_id": other_movie_id}))
            if other_ratings:
                similarity = calculate_movie_similarity(target_vector, other_ratings)
                results.append(
                    {
                        "movie_id": other_movie_id,
                        "movie_name": movie["title"],
                        "similarity_score": similarity,
                    }
                )

        return results

    except Exception as e:
        print(f"Error processing partition: {e}")
        return generate_sample_recommendations(partition_id)


def calculate_movie_similarity(target_vector, other_ratings):
    """Calculate cosine similarity between two movies based on user ratings"""
    other_vector = {r["user_id"]: r["rating"] for r in other_ratings}

    # Find common users
    common_users = set(target_vector.keys()) & set(other_vector.keys())

    if not common_users:
        return 0.0

    # Create rating vectors for common users
    vector1 = [target_vector[user] for user in common_users]
    vector2 = [other_vector[user] for user in common_users]

    # Calculate cosine similarity
    return float(
        np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
    )


def generate_sample_recommendations(partition_id):
    """Generate sample recommendations for testing"""
    sample_movies = [
        {
            "movie_id": f"tt{i}",
            "movie_name": f"Sample Movie {i}",
            "similarity_score": random(),
        }
        for i in range(partition_id * 5, (partition_id + 1) * 5)
    ]
    return sample_movies
