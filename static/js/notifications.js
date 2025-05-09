document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    
    socket.on('connect', function() {
        console.log('Conectado ao servidor WebSocket');
    });

    socket.on('grade_update', function(data) {
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = data.message;
        
        document.body.appendChild(notification);
        
        const audio = new Audio('/static/notification.mp3');
        audio.play().catch(e => console.log('Erro ao tocar som:', e));
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.5s ease-in';
            setTimeout(() => notification.remove(), 500);
        }, 5000);

        if (window.location.pathname.includes('/visualizar_notas')) {
            setTimeout(() => window.location.reload(), 1000);
        }
    });
});