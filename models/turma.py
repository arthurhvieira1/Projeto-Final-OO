class Turma:
    def __init__(self, id, nome, professor_id):
        self.id = id
        self.nome = nome
        self.professor_id = professor_id  # Associação
        self.alunos = []  # Composição

    def adicionar_aluno(self, aluno):
        self.alunos.append(aluno)