import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, MoctaleRating, VibeChart
from omdb_service import search_movies as omdb_search

# Home
@app.route('/')
def index():
    omdb_key = os.getenv('OMDB_API_KEY', '')
    return render_template('index.html', omdb_key=omdb_key)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken!', 'error')
            return redirect(url_for('login'))

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"EMAIL: {email}, PASSWORD: {password}")
        user = User.query.filter_by(email=email).first()
        print(f"USER FOUND: {user}")
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    return render_template('auth/login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# API Search
@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    movies = omdb_search(query)
    return jsonify({'movies': movies})

# Movie Detail Page
@app.route('/movie/<imdb_id>')
def movie_detail(imdb_id):
    return render_template('movie/movie.html')

# API Movie Details
@app.route('/api/movie/<imdb_id>')
def api_movie(imdb_id):
    from omdb_service import get_movie_details
    movie = get_movie_details(imdb_id)
    return jsonify({'movie': movie})

# API Ratings
@app.route('/api/ratings/<imdb_id>')
def api_ratings(imdb_id):
    results = {'Skip': 0, 'Timepass': 0, 'Go for It': 0, 'Perfection': 0}
    ratings = MoctaleRating.query.filter_by(movie_id=imdb_id).all()
    for r in ratings:
        if r.meter_value in results:
            results[r.meter_value] += 1
    return jsonify({'results': results})

# API Rate Movie
@app.route('/api/rate', methods=['POST'])
@login_required
def api_rate():
    data = request.get_json()
    rating = MoctaleRating(
        user_id=current_user.user_id,
        movie_id=data['movie_id'],
        meter_value=data['meter_value']
    )
    db.session.add(rating)
    db.session.commit()
    return jsonify({'success': True})

# API Vibe Chart
@app.route('/api/vibe', methods=['POST'])
@login_required
def api_vibe():
    data = request.get_json()
    vibe = VibeChart(
        user_id=current_user.user_id,
        movie_id=data['movie_id'],
        action=data.get('action', 0),
        romance=data.get('romance', 0),
        comedy=data.get('comedy', 0),
        thriller=data.get('thriller', 0),
        drama=data.get('drama', 0)
    )
    db.session.add(vibe)
    db.session.commit()
    return jsonify({'success': True})

 # Dashboard API
@app.route('/api/dashboard')
@login_required
def api_dashboard():
    ratings_count = MoctaleRating.query.filter_by(user_id=current_user.user_id).count()
    vibes_count = VibeChart.query.filter_by(user_id=current_user.user_id).count()
    return jsonify({
        'user': {
            'username': current_user.username,
            'email': current_user.email,
            'joined': current_user.created_at.strftime('%B %Y')
        },
        'ratings_count': ratings_count,
        'vibes_count': vibes_count,
        'watchlist_count': 0
    })

# My Ratings API
@app.route('/api/my-ratings')
@login_required
def api_my_ratings():
    from omdb_service import get_movie_details
    ratings = MoctaleRating.query.filter_by(user_id=current_user.user_id).all()
    result = []
    for r in ratings:
        movie = get_movie_details(r.movie_id)
        result.append({
            'movie_id': r.movie_id,
            'meter_value': r.meter_value,
            'title': movie.get('Title', r.movie_id) if movie else r.movie_id,
            'year': movie.get('Year', '') if movie else '',
            'poster': movie.get('Poster', '') if movie else ''
        })
    return jsonify({'ratings': result})

# My Vibes API
@app.route('/api/my-vibes')
@login_required
def api_my_vibes():
    from omdb_service import get_movie_details
    vibes = VibeChart.query.filter_by(user_id=current_user.user_id).all()
    result = []
    for v in vibes:
        movie = get_movie_details(v.movie_id)
        result.append({
            'movie_id': v.movie_id,
            'title': movie.get('Title', v.movie_id) if movie else v.movie_id,
            'year': movie.get('Year', '') if movie else '',
            'thriller': v.thriller,
            'mystery': v.mystery,
            'drama': v.drama,
            'action': v.action,
            'romance': v.romance
        })
    return jsonify({'vibes': result})

# My Watchlist API
@app.route('/api/my-watchlist')
@login_required
def api_my_watchlist():
    return jsonify({'movies': []})   