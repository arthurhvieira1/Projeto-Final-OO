# Sistema de Gerenciamento Acadêmico

## Descrição
Sistema desenvolvido para a disciplina de Orientação a Objetos da Universidade de Brasília (UnB), ministrada pelo professor Henrique. O projeto implementa um sistema de gerenciamento acadêmico com funcionalidades para administradores, professores e alunos.

## Funcionalidades Principais

### Administrador
- Gerenciamento completo de usuários (CRUD)
  - Criar novos usuários (professores/alunos)
  - Visualizar todos os usuários
  - Atualizar informações de usuários
  - Remover usuários
- Gerenciamento completo de turmas (CRUD)
  - Criar novas turmas
  - Visualizar todas as turmas
  - Atualizar informações de turmas
  - Remover turmas
- Gestão de matrículas
  - Adicionar alunos às turmas
  - Remover alunos das turmas
  - Visualizar alunos matriculados

### Professores
- Visualização das turmas ministradas
- Lançamento e edição de notas
- Visualização de alunos matriculados
- Gerenciamento de perfil
- Sistema de notificações em tempo real

### Alunos
- Visualização das turmas matriculadas
- Consulta de notas e médias
- Gerenciamento de perfil
- Recebimento de notificações em tempo real

## Tecnologias Utilizadas
- Python 3.11+
- Flask (Framework Web)
- SQLAlchemy (ORM)
- SQLite (Banco de Dados)
- Socket.IO (Notificações)
- HTML/CSS/JavaScript
- Docker

## Pré-requisitos

- Docker
- Docker Compose
- Python 3.11 ou superior (para desenvolvimento local)

## Instalação

### Usando Docker

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/sistema-academico-unb.git
cd sistema-academico-unb
```

2. Construa e execute com Docker:
```bash
docker-compose up --build
```

3. Acesse a aplicação:
```
http://localhost:5000
```

4. Para parar o container:
```bash
docker-compose down
```

### Instalação Local

1. Crie e ative um ambiente virtual:
```bash
python -m venv venv
venv\Scripts\activate
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
python app.py
```

## Estrutura do Projeto
```
projetofinal_OO/
├── app.py                 # Arquivo principal
├── websocket_manager.py   # Gerenciador de WebSocket
├── static/
│   ├── css/              # Estilos
│   │   ├── CRUD_turmas/
│   │   └── CRUD_usuarios/
│   └── js/               # Scripts
│       └── notifications.js
├── templates/
│   ├── admin/
│   │   ├── CRUD_turmas/
│   │   └── CRUD_usuarios/
│   ├── professor/
│   ├── aluno/
│   ├── home.html
│   ├── login.html
│   └── signup.html
├── requirements.txt       # Dependências
├── docker-compose.yml    # Configuração Docker
├── Dockerfile           
└── data/                 # Banco de dados
```

## Credenciais de Acesso

### Administrador
```
Email: admin@admin.com
Senha: admin123
```

## Modelos de Dados

### User
- email (PK)
- nome
- cargo (Professor/Aluno)
- senha

### Turma
- codigo_disciplina (PK)
- nome
- professor_email (FK)
- ano
- semestre

### Nota
- id (PK)
- aluno_email (FK)
- turma_codigo (FK)
- nota1
- nota2
- nota3

## Funcionalidades em Destaque

- Sistema de autenticação multi-nível
- Notificações em tempo real (websocket)
- Cálculo automático de médias
- Interface parcialmente responsiva
- Proteção contra CSRF
- Sessões persistentes
- Validações de entrada
- Pilares da orientação a objetos aplicados

## Contribuidores

- Kaua Vale Leão - 232014057
- Arthur Henrique Vieira - 231034064
- Jânio Lucas Pereira Carrilho - 232013891

## Professor Orientador
Prof. Henrique - Universidade de Brasília (UnB)

## Video com apresentaçao (resumida) do projeto:

https://www.youtube.com/watch?v=6OZ9DS8HSsA