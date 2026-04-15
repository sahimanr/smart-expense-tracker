from flask import Flask,render_template,request, redirect, url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from flask_login import login_user,logout_user,current_user,login_required
from datetime import datetime


app=Flask(__name__)
app.secret_key='first123'
app.config['SQLALCHEMY_DATABASE_URI']="mysql+pymysql://root:simple123@127.0.0.1/practice?charset=utf8mb4"
db= SQLAlchemy(app)

login_manager=LoginManager()
login_manager.init_app(app)

bcrypt=Bcrypt(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        pwd = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            if bcrypt.check_password_hash(user.password, pwd):
                login_user(user)
                return redirect(url_for('index'))
            else:
                return "Wrong password"
        else:
            return "User not found"

    return render_template("login.html")  


@app.route('/dashboard')
@login_required
def dashboard():
    expenses = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc()).all()

    total_expenses = sum(exp.amount for exp in expenses)

    # 🔥 Create category-wise data
    data = {}
    for exp in expenses:
        data[exp.category] = data.get(exp.category, 0) + exp.amount

    labels = list(data.keys())
    values = list(data.values())

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total_expenses,
        labels=labels,
        values=values
    )

@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=='GET':
        return render_template("signup.html")
    elif request.method=='POST':
        email=request.form.get('email')
        pwd=request.form.get('password')
        hashed_pwd=bcrypt.generate_password_hash(pwd)
        okok=User(email=email,password=hashed_pwd)
        db.session.add(okok)
        db.session.commit()  
        return redirect(url_for('login'))
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description')
        date_str = request.form.get('date')
        
        try:
            amount = float(amount)
            # Parse date from HTML5 date input (YYYY-MM-DD)
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
            
            new_expense = Expense(
                amount=amount, 
                category=category, 
                description=description, 
                date=date_obj,
                user_id=current_user.id
            )
            db.session.add(new_expense)
            db.session.commit()
            flash('Expense added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Invalid input or missing required fields.', 'danger')
            
    return render_template('add_expense.html')

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    # Ensure a user only deletes their own
    if expense.user_id == current_user.id:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted.', 'success')
    else:
        flash('You are not authorized to delete this expense.', 'danger')
    return redirect(url_for('dashboard'))

if __name__=="__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)