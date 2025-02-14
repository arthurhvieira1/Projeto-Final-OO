from flask import Flask, redirect, render_template, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersenha'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    email = db.Column(db.String(150), unique=True, nullable=False, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cargo = db.Column(db.String(50), nullable=False)
    senha = db.Column(db.String(150), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        cargo = request.form['cargo']
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email já registrado. Tente fazer login.')
            return redirect(url_for('login'))
        
        new_user = User(nome=nome, email=email, senha=senha, cargo=cargo)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = User.query.filter_by(email=email).first()
        
        if user and user.senha == senha:
            session['user_id'] = user.email
            session['tipo'] = user.cargo
            session['nome'] = user.nome
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha incorretos.')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/users', methods=['GET', 'POST'])
def users():
    users = User.query.all()
    if request.method == 'GET':
        users = User.query.all()
        return render_template('admin/read.html', users=users)
    
    elif request.method == 'POST' and request.form.get('_method') == 'DELETE':
        email = request.form.get('email')
        try:
            user = User.query.filter_by(email=email).first_or_404()
            db.session.delete(user)
            db.session.commit()
            flash('Usuário deletado com sucesso!')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao deletar usuário.')
        return redirect(url_for('users'))
    return render_template('admin/read.html', users=users)


@app.route('/admin/create', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        cargo = request.form['cargo']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email já está cadastrado. Por favor, use outro email.')
            return render_template('admin/create.html')
            
        else:
            new_user = User(nome=nome, email=email, senha=senha, cargo=cargo)
            db.session.add(new_user)
            db.session.commit()
            flash('Usuário criado com sucesso!')
            return redirect(url_for('users'))
    return render_template('admin/create.html')

@app.route('/admin/update/<email>', methods=['GET', 'POST'])
def update_user(email):
    user = User.query.get_or_404(email)
    if request.method == 'POST':
        user.nome = request.form['nome']
        user.senha = request.form['senha']
        user.cargo = request.form['cargo']
        db.session.commit()
        return redirect(url_for('users'))
    return render_template('admin/update.html', user=user)

@app.route('/admin/delete/<email>', methods=['GET', 'POST'])
def delete_user(email):
    user = User.query.get_or_404(email)
    if request.method == 'POST':
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('read_users'))
    return render_template('admin/delete.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)