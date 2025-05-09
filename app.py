from flask import Flask, redirect, render_template, request, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from websocket_manager import init_socketio, notify_grade_update
from datetime import timedelta
import uuid

ADMIN_LOGIN = {
    'email': 'admin@admin.com',
    'senha': 'admin123'
}


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)  

DB_PATH = os.path.join(BASE_DIR, 'data', 'users.db')  

app = Flask(__name__)
app.secret_key = 'supersenha'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(BASE_DIR, 'flask_session')

db = SQLAlchemy(app)

class Usuario:
    def __init__(self, nome, email, senha):
        self.nome = nome
        self.email = email
        self.senha = senha

class Aluno(Usuario):
    def __init__(self, nome, email, senha):
        super().__init__(nome, email, senha)
        self.historico = Historico()  

    def verificar_acesso(self):
        return "Aluno"

class Professor(Usuario):
    def __init__(self, nome, email, senha):
        super().__init__(nome, email, senha)
        self.disciplinas = []  

    def verificar_acesso(self):
        return "professor"

class Historico:
    def __init__(self):
        self.notas = {}
        
    def adicionar_nota(self, disciplina, nota):
        self.notas[disciplina] = nota
        
    def calcular_media(self):
        if not self.notas:
            return 0
        return sum(self.notas.values()) / len(self.notas)

class User(db.Model):
    email = db.Column(db.String(150), unique=True, nullable=False, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cargo = db.Column(db.String(50), nullable=False)
    senha = db.Column(db.String(150), nullable=False)

    def criar_usuario_especifico(self):
        if self.cargo == 'Aluno':
            return Aluno(self.nome, self.email, self.senha)
        elif self.cargo == 'Professor':
            return Professor(self.nome, self.email, self.senha)
        return None

    def verificar_permissoes(self):
        usuario = self.criar_usuario_especifico()
        if usuario:
            return usuario.verificar_acesso()
        return None

alunos_turmas = db.Table('alunos_turmas',
    db.Column('aluno_email', db.String(150), db.ForeignKey('user.email'), primary_key=True),
    db.Column('turma_codigo', db.String(100), db.ForeignKey('turma.codigo_disciplina'), primary_key=True)
)

class Turma(db.Model):
    codigo_disciplina = db.Column(db.String(100), nullable=False, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    professor_email = db.Column(db.String(150), db.ForeignKey('user.email'), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    semestre = db.Column(db.Integer, nullable=False)

    professor = db.relationship('User', backref='turmas_ministradas', foreign_keys=[professor_email])

    alunos = db.relationship('User',
                           secondary=alunos_turmas,
                           lazy='subquery',
                           backref=db.backref('turmas', lazy=True))

class Nota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aluno_email = db.Column(db.String(150), db.ForeignKey('user.email'), nullable=False)
    turma_codigo = db.Column(db.String(100), db.ForeignKey('turma.codigo_disciplina'), nullable=False)
    nota1 = db.Column(db.Float, nullable=True)
    nota2 = db.Column(db.Float, nullable=True)
    nota3 = db.Column(db.Float, nullable=True)
    
    aluno = db.relationship('User', backref='notas')
    turma = db.relationship('Turma', backref='notas')
    
    __table_args__ = (db.UniqueConstraint('aluno_email', 'turma_codigo', name='unique_aluno_turma'),)

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
        else:
            try:
                new_user = User(nome=nome, email=email, senha=senha, cargo=cargo)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))
            except Exception:
                db.session.rollback()
                flash('Erro ao realizar cadastro. Tente novamente.')
                return redirect(url_for('signup'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        if email == ADMIN_LOGIN['email'] and senha == ADMIN_LOGIN['senha']:
            session.clear()  
            session.permanent = True
            session['id'] = str(uuid.uuid4())  
            session['nome'] = 'Administrador'
            session['cargo'] = 'admin'
            return redirect(url_for('gerenciar_usuarios'))
        
        user = User.query.filter_by(email=email).first()
        if user and user.senha == senha:
            session.clear() 
            session.permanent = True
            session['id'] = str(uuid.uuid4())  
            session['nome'] = user.nome
            session['cargo'] = user.verificar_permissoes()
            session['email'] = user.email
            if session['cargo'] == 'Aluno':
                return redirect(url_for('visualizar_turmas_aluno'))
            elif session['cargo'] == 'professor':
                return redirect(url_for('visualizar_turmas'))
        else:
            flash('Credenciais inválidas. Tente novamente.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/CRUD_usuarios/gerenciar_usuarios', methods=['GET', 'POST'])
def gerenciar_usuarios():
    if 'cargo' not in session or session['cargo'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'GET':
        users = User.query.all()
        return render_template('admin/CRUD_usuarios/gerenciar_usuarios.html', users=users)
    
    elif request.method == 'POST' and request.form.get('_method') == 'DELETE':
        email = request.form.get('email')
        try:
            user = User.query.get_or_404(email)
            
            if user.cargo == 'Aluno':
                for turma in user.turmas:
                    turma.alunos.remove(user)
            
            if user.cargo == 'Professor':
                Turma.query.filter_by(professor_email=email).delete()
            
            Nota.query.filter_by(aluno_email=email).delete()
            
            db.session.delete(user)
            db.session.commit()
            flash('Usuário deletado com sucesso!')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao deletar usuário: {str(e)}')
        
        return redirect(url_for('gerenciar_usuarios'))
    
    return redirect(url_for('gerenciar_usuarios'))


@app.route('/admin/CRUD_usuarios/criar_usuario', methods=['GET', 'POST'])
def criar_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        cargo = request.form['cargo']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email já está cadastrado. Por favor, use outro email.')
            return render_template('/admin/CRUD_usuarios/criar_usuario.html')
            
        else:
            new_user = User(nome=nome, email=email, senha=senha, cargo=cargo)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('gerenciar_usuarios'))
    return render_template('/admin/CRUD_usuarios/criar_usuario.html')

@app.route('/admin/CRUD_usuarios/atualizar_usuario/<email>', methods=['GET', 'POST'])
def atualizar_usuario(email):
    user = User.query.get_or_404(email)
    if request.method == 'POST':
        user.nome = request.form['nome']
        user.senha = request.form['senha']
        user.cargo = request.form['cargo']
        db.session.commit()
        return redirect(url_for('gerenciar_usuarios'))
    return render_template('admin/CRUD_usuarios/atualizar_usuario.html', user=user)



@app.route('/admin/CRUD_turmas/gerenciar_turmas', methods=['GET', 'POST'])
def gerenciar_turmas():
    turmas = Turma.query.all()
    if request.method == 'GET':
        return render_template('admin/CRUD_turmas/gerenciar_turmas.html', turmas=turmas)
    
    elif request.method == 'POST' and request.form.get('_method') == 'DELETE':
        codigo = request.form.get('codigo_disciplina')
        try:
            turma = Turma.query.filter_by(codigo_disciplina=codigo).first_or_404()
            db.session.delete(turma)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Erro ao deletar turma.')
        return redirect(url_for('gerenciar_turmas'))
    return render_template('admin/CRUD_turmas/gerenciar_turmas.html', turmas=turmas)


@app.route('/admin/CRUD_turmas/criar_turma', methods=['GET', 'POST'])
def criar_turma():
    professores = User.query.filter_by(cargo='Professor').all()
    if request.method == 'POST':
        try:
            codigo = request.form['codigo_disciplina']
            nome = request.form['nome']
            professor_email = request.form['professor_email']
            ano = int(request.form['ano'])
            semestre = int(request.form['semestre'])
            
            existing_turma = Turma.query.filter_by(codigo_disciplina=codigo).first()
            if existing_turma:
                flash('Código de disciplina já existe.')
                return render_template('admin/CRUD_turmas/criar_turma.html', professores=professores)
            
            nova_turma = Turma(
                codigo_disciplina=codigo,
                nome=nome,
                professor_email=professor_email,
                ano=ano,
                semestre=semestre
            )
            
            db.session.add(nova_turma)
            db.session.commit()
            return redirect(url_for('gerenciar_turmas'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar turma: ' + str(e))
            return render_template('admin/CRUD_turmas/criar_turma.html', professores=professores)
    
    return render_template('admin/CRUD_turmas/criar_turma.html', professores=professores)

@app.route('/admin/CRUD_turmas/atualizar_turma/<codigo>', methods=['GET', 'POST'])
def atualizar_turma(codigo):
    turma = Turma.query.get_or_404(codigo)
    professores = User.query.filter_by(cargo='Professor').all()
    
    if request.method == 'POST':
        try:
            turma.nome = request.form['nome']
            turma.professor_email = request.form['professor_email']
            turma.ano = int(request.form['ano'])
            turma.semestre = int(request.form['semestre'])
            
            db.session.commit()
            return redirect(url_for('gerenciar_turmas'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar turma.')
            
    return render_template('admin/CRUD_turmas/atualizar_turma.html', turma=turma, professores=professores)

@app.route('/admin/CRUD_turmas/adicionar_alunos/<codigo>', methods=['GET', 'POST'])
def adicionar_alunos(codigo):
    turma = Turma.query.get_or_404(codigo)
    
    if request.method == 'POST':
        alunos_selecionados = request.form.getlist('alunos[]')
        try:
            for email in alunos_selecionados:
                aluno = User.query.get(email)
                if aluno and aluno.cargo == 'Aluno':
                    turma.alunos.append(aluno)
            
            db.session.commit()
            return redirect(url_for('adicionar_alunos', codigo=codigo))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao adicionar alunos.')
    
    alunos_matriculados = turma.alunos
    alunos_disponiveis = User.query.filter_by(cargo='Aluno').filter(
        ~User.turmas.any(Turma.codigo_disciplina == codigo)
    ).all()
    
    return render_template('admin/CRUD_turmas/adicionar_alunos.html',
                         turma=turma,
                         alunos_disponiveis=alunos_disponiveis,
                         alunos_matriculados=alunos_matriculados)

@app.route('/admin/CRUD_turmas/remover_aluno/<email>', methods=['POST'])
def remover_aluno(email):
    data = request.get_json()
    turma_codigo = data.get('turma_codigo')
    
    try:
        turma = Turma.query.get_or_404(turma_codigo)
        aluno = User.query.get_or_404(email)
        
        turma.alunos.remove(aluno)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/admin/CRUD_turmas/visualizar_alunos/<codigo>')
def vizualizar_alunos(codigo):
    turma = Turma.query.get_or_404(codigo)
    alunos = turma.alunos
    return render_template('admin/CRUD_turmas/vizualizar_alunos.html', 
                         turma=turma, 
                         alunos=alunos)


@app.route('/professor/visualizar_turmas', methods=['GET'])
def visualizar_turmas():
    email = session['email']
    turmas = Turma.query.filter_by(professor_email=email).all()
    return render_template('professor/visualizar_turmas.html', turmas=turmas)


@app.route('/professor/visualizar_turmas/alunos/<codigo>', methods=['GET'])
def visualizar_alunos_prof(codigo):
    turma = Turma.query.get_or_404(codigo)
    alunos = turma.alunos
    return render_template('professor/visualizar_alunos_prof.html', 
                         turma=turma, 
                         alunos=alunos)

@app.route('/professor/visualizar_turmas/alunos/<codigo>/matricula', methods=['GET', 'POST'])
def gerenciamento_aluno_prof(codigo):
    turma = Turma.query.get_or_404(codigo)
    
    if request.method == 'POST':
        alunos_selecionados = request.form.getlist('alunos[]')
        try:
            for email in alunos_selecionados:
                aluno = User.query.get(email)
                if aluno and aluno.cargo == 'Aluno':
                    turma.alunos.append(aluno)
            
            db.session.commit()
            return redirect(url_for('gerenciamento_aluno_prof', codigo=codigo))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao adicionar alunos.')
    elif request.method == 'DELETE':
        data = request.get_json()
        email = data.get('email')

        try:
            aluno = User.query.get_or_404(email)
            turma.alunos.remove(aluno)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 400
        
    alunos_matriculados = turma.alunos
    alunos_disponiveis = User.query.filter_by(cargo='Aluno').filter(
        ~User.turmas.any(Turma.codigo_disciplina == codigo)
    ).all()
    
    return render_template('professor/gerenciamento_aluno_prof.html',
                         turma=turma,
                         alunos_disponiveis=alunos_disponiveis,
                         alunos_matriculados=alunos_matriculados)


@app.route('/gerenciar_perfil_professor/<email>', methods=['GET', 'POST'])
def gerenciar_perfil(email):
    user = User.query.get_or_404(email)
    if request.method == 'POST':
        try:
            user.nome = request.form['nome']
            user.senha = request.form['senha']
            db.session.commit()
            return redirect(url_for('visualizar_turmas'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('gerenciar_perfil_professor', email=email))
    return render_template('professor/gerenciar_perfil_professor.html', user=user)

@app.route('/aluno/visualizar_turmas_aluno')
def dashboard_aluno():
    if 'email' not in session or session['cargo'] != 'Aluno':
        return redirect(url_for('login'))
    
    aluno = User.query.filter_by(email=session['email']).first()
    turmas = aluno.turmas
    return render_template('aluno/visualizar_turmas_aluno.html', turmas=turmas)

@app.route('/aluno/visualizar_turmas_aluno')
def visualizar_turmas_aluno():
    if 'email' not in session or session['cargo'] != 'Aluno':
        return redirect(url_for('login'))
    
    aluno = User.query.filter_by(email=session['email']).first()
    turmas = aluno.turmas

    from datetime import datetime
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    semestre_atual = 1 if mes_atual <= 6 else 2

    turmas_atuais = [turma for turma in turmas if turma.ano == ano_atual and turma.semestre == semestre_atual]
    
    return render_template('aluno/visualizar_turmas_aluno.html', 
                         turmas=turmas_atuais,
                         ano_atual=ano_atual,
                         semestre_atual=semestre_atual)

@app.route('/aluno/visualizar_turmas_aluno/<codigo>')
def visualizar_detalhes_turma_aluno(codigo):
    if 'email' not in session or session['cargo'] != 'Aluno':
        return redirect(url_for('login'))
    
    turma = Turma.query.get_or_404(codigo)
    aluno = User.query.filter_by(email=session['email']).first()
    
    if aluno not in turma.alunos:
        return redirect(url_for('visualizar_turmas_aluno'))
    
    return render_template('aluno/visualizar_turmas_aluno.html', 
                         turma=turma,
                         aluno=aluno)

@app.route('/aluno/gerenciar_perfil_aluno', methods=['GET', 'POST'])
def gerenciar_perfil_aluno():
    if 'email' not in session or session['cargo'] != 'Aluno':
        return redirect(url_for('login'))
    user = User.query.get_or_404(session['email'])
    if request.method == 'POST':
        try:
            user.nome = request.form['nome']
            user.senha = request.form['senha']
            db.session.commit()
            return redirect(url_for('dashboard_aluno'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('gerenciar_perfil_aluno'))
    return render_template('aluno/gerenciar_perfil_aluno.html', user=user)

@app.route('/professor/lancar_notas/<codigo>', methods=['GET', 'POST'])
def lancar_notas(codigo):
    if 'email' not in session or session['cargo'] != 'professor':
        return redirect(url_for('login'))
        
    turma = Turma.query.get_or_404(codigo)
    
    if request.method == 'POST':
        try:
            for aluno in turma.alunos:
                nota = Nota.query.filter_by(
                    aluno_email=aluno.email,
                    turma_codigo=codigo
                ).first()
                
                if not nota:
                    nota = Nota(
                        aluno_email=aluno.email,
                        turma_codigo=codigo
                    )
                    db.session.add(nota)
                
                nota.nota1 = float(request.form.get(f'nota1_{aluno.email}') or 0)
                nota.nota2 = float(request.form.get(f'nota2_{aluno.email}') or 0)
                nota.nota3 = float(request.form.get(f'nota3_{aluno.email}') or 0)
                
                notify_grade_update(aluno.email, turma.nome)
            
            db.session.commit()
            flash('Notas lançadas com sucesso!')
            return redirect(url_for('lancar_notas', codigo=codigo))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao lançar notas.')
    
    alunos_notas = []
    for aluno in turma.alunos:
        nota = Nota.query.filter_by(
            aluno_email=aluno.email,
            turma_codigo=codigo
        ).first()
        
        if not nota:
            nota = Nota(
                aluno_email=aluno.email,
                turma_codigo=codigo,
                nota1=0,
                nota2=0,
                nota3=0
            )
            db.session.add(nota)
            db.session.commit()
        
        alunos_notas.append({
            'aluno': aluno,
            'notas': nota
        })
    
    return render_template('professor/lancar_notas.html',
                         turma=turma,
                         alunos_notas=alunos_notas)

@app.route('/aluno/visualizar_notas')
def visualizar_notas():
    if 'email' not in session or session['cargo'] != 'Aluno':
        return redirect(url_for('login'))
    
    aluno = User.query.filter_by(email=session['email']).first()
    turmas = aluno.turmas
    
    periodos = sorted(set(f"{turma.ano}.{turma.semestre}" for turma in turmas), reverse=True)
    
    for turma in turmas:
        nota = Nota.query.filter_by(
            aluno_email=aluno.email,
            turma_codigo=turma.codigo_disciplina
        ).first()
        
        if not nota:
            nota = Nota(
                aluno_email=aluno.email,
                turma_codigo=turma.codigo_disciplina,
                nota1=None,
                nota2=None,
                nota3=None
            )
            db.session.add(nota)
    db.session.commit()
    
    return render_template('aluno/visualizar_notas.html', 
                         turmas=turmas,
                         periodos=periodos)

if __name__ == '__main__':
    socketio = init_socketio(app)
    socketio.run(app, 
                debug=True, 
                host='0.0.0.0', 
                port=5000,
                allow_unsafe_werkzeug=True)