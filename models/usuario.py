class Usuario:
    def __init__(self, id, nome, email, senha, tipo):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha = senha
        self.tipo = tipo

class Aluno(Usuario):
    def __init__(self, id, nome, email, senha, matricula):
        super().__init__(id, nome, email, senha, 'aluno')
        self.matricula = matricula

class Professor(Usuario):
    def __init__(self, id, nome, email, senha, disciplina):
        super().__init__(id, nome, email, senha, 'professor')
        self.disciplina = disciplina

class Admin(Usuario):
    def __init__(self, id, nome, email, senha):
        super().__init__(id, nome, email, senha, 'admin')