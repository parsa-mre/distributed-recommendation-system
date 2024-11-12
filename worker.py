from flask import Flask, request, jsonify

app = Flask(__name__)

# Dummy database of movies with their average ratings
dummy_movie_db = {
    "Inception": {"rating": 4.9},
    "Interstellar": {"rating": 4.8},
    "The Matrix": {"rating": 4.7},
    "Memento": {"rating": 4.6},
    "The Dark Knight": {"rating": 4.9},
    "The Prestige": {"rating": 4.8},
    "Fight Club": {"rating": 4.7},
    "Shutter Island": {"rating": 4.6},
    "Gladiator": {"rating": 4.8},
    "The Godfather": {"rating": 4.9},
    "Pulp Fiction": {"rating": 4.7},
    "The Shawshank Redemption": {"rating": 4.9},
    "The Social Network": {"rating": 4.5},
}

# Function to recommend movies based on rating similarity
def recommend_movies(movie_name):
    # Get the rating of the requested movie
    movie_rating = dummy_movie_db.get(movie_name, {}).get("rating", None)
    
    if movie_rating is None:
        # If the movie is not in the database, return an error message
        return [], "Movie not found in database."
    
    # Recommend movies with ratings within 0.1 of the requested movie
    recommended_movies = [
        movie for movie, data in dummy_movie_db.items()
        if abs(data["rating"] - movie_rating) <= 0.1 and movie != movie_name
    ]

    return recommended_movies, None

# Route to process the request from the Master
@app.route('/process', methods=['POST'])
def process():
    # Extract the movie name from the request
    data = request.json
    movie_name = data.get('movie_name')
    
    if not movie_name:
        return jsonify({"error": "Movie name must be provided"}), 400
    
    # Get movie recommendations
    recommended_movies, error = recommend_movies(movie_name)
    
    if error:
        return jsonify({"error": error}), 404

    return jsonify({"recommended_movies": recommended_movies})

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001  # Default port is 5001 if not specified
    app.run(host="0.0.0.0", port=port)
