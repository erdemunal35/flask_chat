from turtle import color
from flask import Flask, render_template, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_socketio import SocketIO, send, join_room, leave_room, emit
from datetime import datetime
import random

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'
db = SQLAlchemy(app)
socketio = SocketIO(app, manage_session=False)
Session(app)

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    room = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    color = db.Column(db.String(6), default="#000000")
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __rep__(self):
        return '<Message %r>' % self.id
        
@app.route('/', methods=['GET', 'POST'])
def index():
    print("in index()")
    
    print(session.get('username'))
    if request.method == 'POST':
        # try:
        colorcode = "#"+''.join([random.choice('ABCDEF0123456789') for i in range(6)])
        username = request.form['username']
        room = request.form['room']
        print(username)
        print(room)
        print(colorcode)
        session['username'] = username
        session['room'] = room
        session['color'] = colorcode
        if(db.session.query(db.exists().where(Messages.username == username)).scalar()):
            pass
        else:
            new_user_message = Messages(username=username, room=room, content=f'{username} just joined our chat channel!', color=colorcode)
            print(new_user_message)
            db.session.add(new_user_message)
            db.session.commit()
            
        messages = Messages.query.order_by(Messages.date_created).where(Messages.room == room).all()
        return render_template('user.html', messages=messages, username=username, room=room, color=colorcode)
        # except:
            # print("In except")
            # return render_template('index.html')
    else:
        return render_template('index.html')

@app.route('/chat', methods=['GET', 'POST'])
def send():
    print("in send()")
    print(session.get('username'))
    username = session.get('username')
    room = session.get('room')
    color = session['color']
    if request.method == 'POST':
        try:
            content = request.form['text']
            print(content)
            new_user_message = Messages(username=username, room=room, content=content, color=color)
            db.session.add(new_user_message) 
            db.session.commit()
        except:
            pass
        messages = Messages.query.order_by(Messages.date_created).where(Messages.room == room).all()
        return render_template('user.html', messages=messages, username=username, room=room, color=color)
    else:
        messages = Messages.query.order_by(Messages.date_created).where(Messages.room == room).all()
        return render_template('user.html', messages=messages, username=username, room=room, color=color)


@socketio.on('join', namespace='/chat')
def join(message):
    print("In socket join")
    join_room(room=message['msg2'])
    emit('status', {'msg':  message['msg'] + ' has entered the room.'}, room=message['msg2'])


@socketio.on('text', namespace='/chat')
def text(message):
    print("In socket text")
    print(message)
    print("Out socket text")
    emit('message', {'content': message['msg'], 'username': message['msg2'], 'color': message['msg4']}, room=message['msg3'])


@socketio.on('left', namespace='/chat')
def left(message):
    print("In socket left")
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    session.clear()
    emit('status', {'msg': username + ' has left the room.'}, room=room)

if __name__ == "__main__":
    #app.run(debug=True)
    socketio.run(app)