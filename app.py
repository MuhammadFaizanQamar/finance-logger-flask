from flask import Flask, render_template
from models import db, Transaction
from dotenv import load_dotenv
import os
from flask import request
from flask import redirect, url_for

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def dashboard():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
    balance = total_income - total_expenses
    
    return render_template('dashboard.html',
        transactions=transactions,
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance
    )

@app.route('/add', methods=['GET', 'POST'])
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
        description=description
        )
        db.session.add(transaction)
        db.session.commit()
        
        return redirect(url_for('dashboard'))
    return render_template('add.html')

@app.route('/delete/<int:id>', methods=['POST'])
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
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

if __name__ == '__main__':
    app.run(debug=True)