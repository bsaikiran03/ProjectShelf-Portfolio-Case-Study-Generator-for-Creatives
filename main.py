from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from bcrypt import hashpw, checkpw, gensalt
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'projectshelf-secret-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.Text, nullable=False)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    theme = db.Column(db.String(50), default='light')

class CaseStudy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    overview = db.Column(db.Text)
    media = db.Column(db.Text)  # JSON as text
    timeline = db.Column(db.Text)
    tools = db.Column(db.Text)  # JSON as text
    outcomes = db.Column(db.Text)

class Analytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_study_id = db.Column(db.Integer, nullable=False)
    page_views = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)

# Create database
with app.app_context():
    db.create_all()
    # Add test user
    if not User.query.filter_by(username='saikiran').first():
        hashed = hashpw('testpass'.encode('utf-8'), gensalt()).decode('utf-8')
        user = User(username='saikiran', email='saikiran@example.com', password=hashed)
        db.session.add(user)
        db.session.commit()

# Routes
@app.route('/')
def index():
    return '<h1>Welcome to ProjectShelf</h1><a href="/login">Login</a> | <a href="/signup">Signup</a>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            return render_template('signup.html', error='Username or email already exists')
        hashed = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')
        user = User(username=username, email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    portfolios = Portfolio.query.filter_by(user_id=user.id).all()
    # Fetch case studies and analytics safely
    case_studies = []
    analytics = []
    if portfolios:
        portfolio_ids = [p.id for p in portfolios]
        case_studies = CaseStudy.query.filter(CaseStudy.portfolio_id.in_(portfolio_ids)).all()
        if case_studies:
            case_study_ids = [cs.id for cs in case_studies]
            analytics = Analytics.query.filter(Analytics.case_study_id.in_(case_study_ids)).all()
    # Create copies for JSON decoding
    case_studies_data = []
    for cs in case_studies:
        try:
            media = json.loads(cs.media) if cs.media else []
            tools = json.loads(cs.tools) if cs.tools else []
        except json.JSONDecodeError:
            media = []
            tools = []
        case_studies_data.append({
            'id': cs.id,
            'title': cs.title,
            'overview': cs.overview,
            'media': media,
            'timeline': cs.timeline,
            'tools': tools,
            'outcomes': cs.outcomes
        })
    return render_template('dashboard.html', user=user, portfolios=portfolios, case_studies=case_studies_data, analytics=analytics)

@app.route('/<username>')
def portfolio_page(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(404)
    portfolio = Portfolio.query.filter_by(user_id=user.id).first()
    case_studies = CaseStudy.query.filter_by(portfolio_id=portfolio.id).all() if portfolio else []
    # Create copies for JSON decoding
    case_studies_data = []
    for cs in case_studies:
        try:
            media = json.loads(cs.media) if cs.media else []
            tools = json.loads(cs.tools) if cs.tools else []
        except json.JSONDecodeError:
            media = []
            tools = []
        case_studies_data.append({
            'id': cs.id,
            'title': cs.title,
            'overview': cs.overview,
            'media': media,
            'timeline': cs.timeline,
            'tools': tools,
            'outcomes': cs.outcomes
        })
    analytics = Analytics.query.filter_by(case_study_id=case_studies[0].id).first() if case_studies else None
    if case_studies and not analytics:
        analytics = Analytics(case_study_id=case_studies[0].id, page_views=1, clicks=0)
        db.session.add(analytics)
    elif analytics:
        analytics.page_views += 1
        db.session.commit()
    return render_template('portfolio.html', user=user, portfolio=portfolio, case_studies=case_studies_data, analytics=analytics)

@app.route('/portfolios', methods=['POST'])
def create_portfolio():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.form
    portfolio = Portfolio(
        user_id=session['user_id'],
        title=data['title'],
        description=data.get('description'),
        theme=data.get('theme', 'light')
    )
    db.session.add(portfolio)
    db.session.commit()
    return jsonify({'message': 'Portfolio created'})

@app.route('/case_studies', methods=['POST'])
def create_case_study():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.form
    portfolio = Portfolio.query.filter_by(user_id=session['user_id']).first()
    if not portfolio:
        return jsonify({'error': 'Portfolio not found'}), 400
    media = [url.strip() for url in data.get('media', '').split(',') if url.strip()]
    tools = [tool.strip() for tool in data.get('tools', '').split(',') if tool.strip()]
    case_study = CaseStudy(
        portfolio_id=portfolio.id,
        title=data['title'],
        overview=data.get('overview'),
        media=json.dumps(media),
        timeline=data.get('timeline'),
        tools=json.dumps(tools),
        outcomes=data.get('outcomes')
    )
    db.session.add(case_study)
    db.session.commit()
    return jsonify({'message': 'Case study added'})

@app.route('/analytics/<int:case_study_id>/track', methods=['POST'])
def track_analytics(case_study_id):
    action = request.args.get('action')
    analytics = Analytics.query.filter_by(case_study_id=case_study_id).first()
    if not analytics:
        analytics = Analytics(case_study_id=case_study_id, page_views=0, clicks=0)
        db.session.add(analytics)
    if action == 'view':
        analytics.page_views += 1
    elif action == 'click':
        analytics.clicks += 1
    db.session.commit()
    return jsonify({'status': 'tracked'})

if __name__ == '__main__':
    app.run(debug=True)