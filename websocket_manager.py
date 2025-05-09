from flask import session
from flask_socketio import SocketIO, join_room, leave_room, emit

socketio = SocketIO(async_mode='threading')

@socketio.on('connect')
def handle_connect():
    try:
        if 'email' in session:
            join_room(session['email'])
            print(f'Cliente conectado: {session["email"]}')
            emit('connection_response', {'status': 'success'}, room=session['email'])
    except Exception as e:
        print(f'Erro na conexão: {str(e)}')

@socketio.on('disconnect')
def handle_disconnect():
    try:
        if 'email' in session:
            leave_room(session['email'])
            print(f'Cliente desconectado: {session["email"]}')
    except Exception as e:
        print(f'Erro na desconexão: {str(e)}')

@socketio.on('grade_update')
def handle_grade_update(data):
    try:
        required_fields = ['aluno_email', 'disciplina', 'nota_tipo', 'valor']
        if not all(field in data for field in required_fields):
            raise ValueError("Dados incompletos para atualização de nota")

        emit('grade_notification', {
            'message': f'Nova nota lançada em {data["disciplina"]}: {data["nota_tipo"]} = {data["valor"]}',
            'disciplina': data['disciplina'],
            'nota_tipo': data['nota_tipo'],
            'valor': data['valor']
        }, room=data['aluno_email'])
        
        return True
    except Exception as e:
        print(f'Erro ao atualizar nota: {str(e)}')
        return False

def notify_grade_update(aluno_email, disciplina):
    try:
        socketio.emit('grade_update', {
            'message': f'Notas atualizadas na disciplina {disciplina}!',
            'disciplina': disciplina
        }, room=aluno_email)
        return True
    except Exception as e:
        print(f'Erro ao notificar atualização de nota: {str(e)}')
        return False

def init_socketio(app):
    if not app:
        raise ValueError("Flask app é obrigatório")
    
    try:
        socketio.init_app(app, 
                         cors_allowed_origins="*",
                         async_mode='threading',
                         logger=True,
                         engineio_logger=True)
        print("WebSocket inicializado com sucesso")
        return socketio
    except Exception as e:
        print(f'Erro ao inicializar WebSocket: {str(e)}')
        raise