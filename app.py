from flask import Flask, render_template, request , redirect, url_for
from models import db, Transaction, User
from dotenv import load_dotenv
import os
from datetime import datetime
from collections import defaultdict
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
@login_required
def dashboard():
    
    now = datetime.now()
    month = now.month 
    year = now.year 

    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        db.extract('month', Transaction.date) == now.month,
        db.extract('year', Transaction.date) == now.year
    ).order_by(Transaction.date.desc()).all()

    category_expenses = defaultdict(float)
    for t in transactions:
        if t.type == 'expense':
            category_expenses[t.category] += t.amount

    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
    balance = total_income - total_expenses
    
    return render_template(
        'dashboard.html',
        transactions=transactions,
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        month=month,
        year=year,
        category_labels=list(category_expenses.keys()),
        category_data=list(category_expenses.values())
)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        amount = request.form.get('amount')
        type = request.form.get('type')
        category = request.form.get('category')
        description = request.form.get('description')
        transaction = Transaction(
        amount=float(amount),
        type=type,
        category=category,
        description=description,
        user_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()
        
        return redirect(url_for('dashboard'))
    return render_template('add.html')

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    if request.method == 'POST':
        amount = request.form.get('amount')
        type = request.form.get('type')
        category = request.form.get('category')
        description = request.form.get('description')
        transaction.amount = float(amount)
        transaction.type = type
        transaction.category = category
        transaction.description = description
        db.session.commit()
        
        return redirect(url_for('dashboard'))
    else:
        return render_template('edit.html', transaction=transaction)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', error='Username already exists')
        
        user = User()
        user.username = username
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)