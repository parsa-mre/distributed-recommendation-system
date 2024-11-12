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
def recommend_movies(movie_name, reviews_data):
    movie_rating = dummy_movie_db.get(movie_name, {}).get("rating", None)
    
    if not movie_rating:
        return []

    recommended_movies = []
    for movie, data in dummy_movie_db.items():
        if abs(data["rating"] - movie_rating) <= 0.1 and movie != movie_name:
            recommended_movies.append(movie)

    return recommended_movies

# Route to process the request from the Master
@app.route('/process', methods=['POST'])
def process():
    # Extract the movie name and reviews data from the request
    data = request.json
    movie_name = data.get('movie_name')
    reviews = data.get('reviews')
    
    if not movie_name or not reviews:
        return jsonify({"error": "Movie name and reviews must be provided"}), 400
    
    # Recommend movies based on the provided movie name
    recommended_movies = recommend_movies(movie_name, reviews)
    
    return jsonify({"recommended_movies": recommended_movies})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)  # Worker listens on port 5001
