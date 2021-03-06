import os
import sys

from flask import Flask, render_template, url_for, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import defaultdict
import time

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

channels = [
    {
        'channelName': 'General',
        'description': 'Discuss anything',
    },
    {
        'channelName':'Programming',
        'description': 'Discuss programming'
    }
]

messages = defaultdict(list)
messages['General'].append({"time":time.time(), "username":"Moderator", "message":"Welcome to the Wave chatroom."})

@app.route('/channels')
def renderChannels():
    return jsonify(channels)

@app.route("/chatroom/<string:channel>")
def channel(channel):
    for channelData in channels:
        if channelData['channelName'] == channel:
            description = channelData['description']

    data = {
        'meta': {
            'channel': channel,
            'description': description,
        },
        'messages': messages[channel]
    }

    return jsonify(data)

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/chatroom/")
def chatroom():
    return render_template("chatroom.html", channels=channels, messages=messages['general'])

@socketio.on("sendMessage")
def sendMessage(message):
    channel = message["channel"]
    channel = channel

    username = message["username"]
    message = message["message"]

    messages.setdefault(channel, []).append({"time":time.time(),"username":username, "message":message})

    if len(messages[channel]) >= 100:
        messages[channel].pop(0)

    emit('message',
        {'time':time.time(),'username':username, 'message': message},
        room=channel,
        broadcast=True)


@socketio.on('joinChannel')
def joinChannel(data):
    username = data['username']
    channelName = data['channelName']
    join_room(channelName)

    emit('message',
        {'message': username + ' has entered the room ' + channelName + '.'},
        broadcast=True,
        room=channelName)

@socketio.on('leaveChannel')
def leaveChannel(data):
    username = data['username']
    channelName = data['channelName']
    leave_room(channelName)
    emit('message',
        {'message': username + ' has left the room ' + channelName + '.'},
        broadcast=True,
        room=channelName)

@socketio.on('createChannel')
def createChannel(data):
    for channel in channels:
        if channel['channelName'] == data['channelName']:
            return

    channels.append(data)
    channelName = data['channelName']
    description = data['description']

    emit('channelCreated',
        {'channelName': channelName, 'description': description},
        broadcast=True)

if __name__ == '__main__':
    socketio.run(app)
