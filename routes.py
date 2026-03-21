import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db, mail
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
            return redirect(url_for('register'))

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            is_verified=False
        )
        db.session.add(new_user)
        db.session.commit()

        # Send verification email
        from itsdangerous import URLSafeTimedSerializer
        from flask_mail import Message
        s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        token = s.dumps(email, salt='email-verify')
        verify_url = url_for('verify_email', token=token, _external=True)
        msg = Message('Verify your CineVerse account', sender='pradeep962065@gmail.com', recipients=[email])
        msg.body = f'Click this link to verify your account: {verify_url}'
        mail.send(msg)

        flash('Account created! Please check your email to verify.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if not user.is_verified:
                flash('Please verify your email first!', 'error')
                return redirect(url_for('login'))
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

    # API Get User's Rating
@app.route('/api/my-rating/<imdb_id>')
@login_required
def api_my_rating(imdb_id):
    rating = MoctaleRating.query.filter_by(
        user_id=current_user.user_id,
        movie_id=imdb_id
    ).first()
    if rating:
        return jsonify({'rated': True, 'meter_value': rating.meter_value})
    return jsonify({'rated': False, 'meter_value': None})

# API Rate Movie
@app.route('/api/rate', methods=['POST'])
@login_required
def api_rate():
    data = request.get_json()
    existing = MoctaleRating.query.filter_by(
        user_id=current_user.user_id,
        movie_id=data['movie_id']
    ).first()
    if existing:
        return jsonify({'success': False, 'message': 'You have already rated this movie!'})
    rating = MoctaleRating(
        user_id=current_user.user_id,
        movie_id=data['movie_id'],
        meter_value=data['meter_value']
    )
    db.session.add(rating)
    db.session.commit()
    return jsonify({'success': True})
    # API Get User's Vibe
@app.route('/api/my-vibe/<imdb_id>')
@login_required
def api_my_vibe(imdb_id):
    vibe = VibeChart.query.filter_by(
        user_id=current_user.user_id,
        movie_id=imdb_id
    ).first()
    if vibe:
        return jsonify({'vibed': True, 'action': vibe.action, 'romance': vibe.romance, 'comedy': vibe.comedy, 'thriller': vibe.thriller, 'drama': vibe.drama})
    return jsonify({'vibed': False})

# API Vibe Chart
@app.route('/api/vibe', methods=['POST'])
@login_required
def api_vibe():
    data = request.get_json()
    existing = VibeChart.query.filter_by(
        user_id=current_user.user_id,
        movie_id=data['movie_id']
    ).first()
    if existing:
        return jsonify({'success': False, 'message': 'You have already submitted a vibe for this movie!'})
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
    from models import Watchlist
    ratings_count = MoctaleRating.query.filter_by(user_id=current_user.user_id).count()
    vibes_count = VibeChart.query.filter_by(user_id=current_user.user_id).count()
    watchlist_count = Watchlist.query.filter_by(user_id=current_user.user_id).count()
    return jsonify({
        'user': {
            'username': current_user.username,
            'email': current_user.email,
            'joined': current_user.created_at.strftime('%B %Y')
        },
        'ratings_count': ratings_count,
        'vibes_count': vibes_count,
        'watchlist_count': watchlist_count
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
            'drama': v.drama,
            'action': v.action,
            'romance': v.romance
        })
    return jsonify({'vibes': result})

# Add to Watchlist
@app.route('/api/watchlist/add', methods=['POST'])
@login_required
def add_watchlist():
    from models import Watchlist
    data = request.get_json()
    existing = Watchlist.query.filter_by(user_id=current_user.user_id, movie_id=data['movie_id']).first()
    if existing:
        return jsonify({'success': False, 'message': 'Already in watchlist!'})
    watch = Watchlist(user_id=current_user.user_id, movie_id=data['movie_id'])
    db.session.add(watch)
    db.session.commit()
    return jsonify({'success': True})

# Remove from Watchlist
@app.route('/api/watchlist/remove', methods=['POST'])
@login_required
def remove_watchlist():
    from models import Watchlist
    data = request.get_json()
    Watchlist.query.filter_by(user_id=current_user.user_id, movie_id=data['movie_id']).delete()
    db.session.commit()
    return jsonify({'success': True})

# My Watchlist API
@app.route('/api/my-watchlist')
@login_required
def api_my_watchlist():
    from models import Watchlist
    from omdb_service import get_movie_details
    watches = Watchlist.query.filter_by(user_id=current_user.user_id).all()
    result = []
    for w in watches:
        movie = get_movie_details(w.movie_id)
        if movie:
            result.append(movie)
    return jsonify({'movies': result})

# Post Comment
@app.route('/api/comment', methods=['POST'])
@login_required
def post_comment():
    from models import Comment
    data = request.get_json()
    comment = Comment(
        user_id=current_user.user_id,
        movie_id=data['movie_id'],
        content=data['content']
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({'success': True})

# Get Comments
@app.route('/api/comments/<imdb_id>')
def get_comments(imdb_id):
    from models import Comment
    comments = Comment.query.filter_by(movie_id=imdb_id).order_by(Comment.created_at.desc()).all()
    result = []
    for c in comments:
        user = User.query.get(c.user_id)
        result.append({
            'username': user.username if user else 'Unknown',
            'content': c.content,
            'date': c.created_at.strftime('%b %d, %Y')
        })
    return jsonify({'comments': result})

# Forgot Password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            from itsdangerous import URLSafeTimedSerializer
            from flask_mail import Message
            s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
            token = s.dumps(email, salt='password-reset')
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Reset your CineVerse password', sender='pradeep962065@gmail.com', recipients=[email])
            msg.body = f'Click this link to reset your password: {reset_url}'
            mail.send(msg)
        flash('If that email exists, a reset link has been sent!', 'success')
        return redirect(url_for('login'))
    return render_template('auth/forgot_password.html')

# Reset Password
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)
    except SignatureExpired:
        flash('Reset link expired!', 'error')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(password)
            db.session.commit()
            flash('Password reset! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('auth/reset_password.html', token=token)

# Admin Dashboard
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    return render_template('admin/dashboard.html')

# Admin API - Movie Stats
@app.route('/api/admin/stats')
@login_required
def admin_stats():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    from models import Comment, Watchlist
    from sqlalchemy import func
    
    # Get all rated movies with counts
    ratings = db.session.query(
        MoctaleRating.movie_id,
        func.count(MoctaleRating.rating_id).label('total'),
        func.sum(db.case((MoctaleRating.meter_value == 'Skip', 1), else_=0)).label('skip'),
        func.sum(db.case((MoctaleRating.meter_value == 'Timepass', 1), else_=0)).label('timepass'),
        func.sum(db.case((MoctaleRating.meter_value == 'Go for It', 1), else_=0)).label('goforit'),
        func.sum(db.case((MoctaleRating.meter_value == 'Perfection', 1), else_=0)).label('perfection')
    ).group_by(MoctaleRating.movie_id).all()

    # Get watchlist counts
    watchlist = db.session.query(
        Watchlist.movie_id,
        func.count(Watchlist.watch_id).label('total')
    ).group_by(Watchlist.movie_id).all()

    # Get vibe counts
    vibes = db.session.query(
        VibeChart.movie_id,
        func.count(VibeChart.vibe_id).label('total'),
        func.avg(VibeChart.action).label('action'),
        func.avg(VibeChart.romance).label('romance'),
        func.avg(VibeChart.comedy).label('comedy'),
        func.avg(VibeChart.thriller).label('thriller'),
        func.avg(VibeChart.drama).label('drama')
    ).group_by(VibeChart.movie_id).all()

    # Get comment counts
    comments = db.session.query(
        Comment.movie_id,
        func.count(Comment.comment_id).label('total')
    ).group_by(Comment.movie_id).all()

    # Get date wise ratings
    date_ratings = db.session.query(
        func.date(MoctaleRating.rated_on).label('date'),
        func.count(MoctaleRating.rating_id).label('total')
    ).group_by(func.date(MoctaleRating.rated_on)).order_by(func.date(MoctaleRating.rated_on)).all()

    # Get total users
    total_users = User.query.count()

    return jsonify({
        'ratings': [{'movie_id': r.movie_id, 'total': r.total, 'skip': r.skip, 'timepass': r.timepass, 'goforit': r.goforit, 'perfection': r.perfection} for r in ratings],
        'watchlist': [{'movie_id': w.movie_id, 'total': w.total} for w in watchlist],
        'vibes': [{'movie_id': v.movie_id, 'total': v.total, 'action': round(v.action or 0, 1), 'romance': round(v.romance or 0, 1), 'comedy': round(v.comedy or 0, 1), 'thriller': round(v.thriller or 0, 1), 'drama': round(v.drama or 0, 1)} for v in vibes],
        'comments': [{'movie_id': c.movie_id, 'total': c.total} for c in comments],
        'date_ratings': [{'date': str(d.date), 'total': d.total} for d in date_ratings],
        'total_users': total_users
    })

# Email Verification
@app.route('/verify/<token>')
def verify_email(token):
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='email-verify', max_age=3600)
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_verified = True
            db.session.commit()
            flash('Email verified! Please login.', 'success')
    except SignatureExpired:
        flash('Verification link expired!', 'error')
    return redirect(url_for('login'))
