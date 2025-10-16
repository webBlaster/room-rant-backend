from flask import Flask, jsonify, request, Response
from flask_restx import Api, Resource, fields, Namespace
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import time
from datetime import datetime
import uuid
from collections import defaultdict
import threading

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Enable CORS
CORS(app)

# Initialize Flask-RESTX API with documentation
api = Api(
    app,
    version='1.0',
    title='Room Rant API',
    description='A real-time chat room API with Server-Sent Events for live messaging',
    doc='/docs/'
)

# Create namespaces for better organization
rooms_ns = Namespace('rooms', description='Room management and messaging operations')
api.add_namespace(rooms_ns)

# In-memory storage for room messages and connected clients
room_messages = defaultdict(list)
room_clients = defaultdict(list)
clients_lock = threading.Lock()

# Define API models for Swagger documentation
room_model = api.model('Room', {
    'id': fields.String(required=True, description='Unique alphanumeric room identifier', example='room1a2b3c'),
    'name': fields.String(required=True, description='Display name of the room', example='Chelsea vs Barca'),
    'description': fields.String(required=True, description='Brief description of the room', example='Live discussion for Chelsea vs Barcelona match'),
    'created_at': fields.String(required=True, description='ISO timestamp when room was created', example='2025-10-16T12:00:00Z'),
    'active_users': fields.Integer(required=True, description='Number of currently active users', example=0)
})

rooms_response_model = api.model('RoomsResponse', {
    'status': fields.Integer(required=True, description='HTTP status code', example=200),
    'success': fields.Boolean(required=True, description='Indicates if operation was successful', example=True),
    'message': fields.String(required=True, description='Human readable message', example='Rooms retrieved successfully'),
    'data': fields.Nested(api.model('RoomsData', {
        'rooms': fields.List(fields.Nested(room_model), description='List of available rooms'),
        'total_rooms': fields.Integer(description='Total number of rooms', example=1)
    }))
})

join_room_request_model = api.model('JoinRoomRequest', {
    'user_id': fields.String(required=True, description='Unique identifier for the user', example='user123'),
    'user_name': fields.String(required=True, description='Display name of the user', example='John Doe')
})

join_room_response_model = api.model('JoinRoomResponse', {
    'status': fields.Integer(required=True, description='HTTP status code', example=200),
    'success': fields.Boolean(required=True, description='Indicates if operation was successful', example=True),
    'message': fields.String(required=True, description='Human readable message', example='Successfully joined room room1a2b3c'),
    'data': fields.Nested(api.model('JoinRoomData', {
        'room_id': fields.String(description='ID of the joined room', example='room1a2b3c'),
        'user_id': fields.String(description='ID of the user who joined', example='user123'),
        'user_name': fields.String(description='Name of the user who joined', example='John Doe')
    }))
})

send_message_request_model = api.model('SendMessageRequest', {
    'user_id': fields.String(required=True, description='Unique identifier for the user', example='user123'),
    'user_name': fields.String(required=True, description='Display name of the user', example='John Doe'),
    'message': fields.String(required=True, description='Message content to be sent', example='Hello everyone!')
})

message_model = api.model('Message', {
    'id': fields.String(description='Unique message identifier', example='550e8400-e29b-41d4-a716-446655440000'),
    'user_id': fields.String(description='ID of the user who sent the message', example='user123'),
    'user_name': fields.String(description='Name of the user who sent the message', example='John Doe'),
    'message': fields.String(description='Message content', example='Hello everyone!'),
    'timestamp': fields.String(description='ISO timestamp when message was sent', example='2025-10-16T18:30:00.000Z'),
    'room_id': fields.String(description='ID of the room where message was sent', example='room1a2b3c')
})

send_message_response_model = api.model('SendMessageResponse', {
    'status': fields.Integer(required=True, description='HTTP status code', example=200),
    'success': fields.Boolean(required=True, description='Indicates if operation was successful', example=True),
    'message': fields.String(required=True, description='Human readable message', example='Message sent successfully'),
    'data': fields.Nested(api.model('SendMessageData', {
        'message_id': fields.String(description='ID of the sent message', example='550e8400-e29b-41d4-a716-446655440000'),
        'room_id': fields.String(description='ID of the room where message was sent', example='room1a2b3c')
    }))
})

error_response_model = api.model('ErrorResponse', {
    'status': fields.Integer(required=True, description='HTTP error status code', example=400),
    'success': fields.Boolean(required=True, description='Always false for errors', example=False),
    'message': fields.String(required=True, description='Error message description', example='user_id and user_name are required'),
    'data': fields.Raw(description='Additional error data (usually null)', example=None)
})

@app.route('/')
def hello():
    """Welcome endpoint - redirects to API documentation"""
    return jsonify({"message": "Welcome to Room Rant API! Visit /docs/ for documentation, /demo for chat demo"})

@app.route('/demo')
def chat_demo():
    """Serve the chat demo page"""
    return app.send_static_file('chat-demo.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@rooms_ns.route('')
class RoomsList(Resource):
    @rooms_ns.doc('get_rooms')
    @rooms_ns.marshal_with(rooms_response_model)
    @rooms_ns.response(200, 'Success - Rooms retrieved successfully')
    def get(self):
        """
        Get list of available chat rooms
        
        Returns a list of all available chat rooms with their details including:
        - Room ID (alphanumeric identifier)
        - Room name and description
        - Creation timestamp
        - Number of active users
        """
        rooms = [
            {
                "id": "room1a2b3c",
                "name": "Chelsea vs Barca",
                "description": "Live discussion for Chelsea vs Barcelona match",
                "created_at": "2025-10-16T12:00:00Z",
                "active_users": 0
            }
        ]
        return {
            "status": 200,
            "success": True,
            "message": "Rooms retrieved successfully",
            "data": {
                "rooms": rooms,
                "total_rooms": len(rooms)
            }
        }

@rooms_ns.route('/<string:room_id>/join')
class JoinRoom(Resource):
    @rooms_ns.doc('join_room')
    @rooms_ns.expect(join_room_request_model)
    @rooms_ns.marshal_with(join_room_response_model)
    @rooms_ns.response(200, 'Success - Successfully joined room')
    @rooms_ns.response(400, 'Bad Request - Missing required fields', error_response_model)
    @rooms_ns.response(404, 'Not Found - Room does not exist', error_response_model)
    @rooms_ns.response(500, 'Internal Server Error', error_response_model)
    def post(self, room_id):
        """
        Join a chat room
        
        Allows a user to join a specific chat room by providing their user ID and display name.
        This endpoint validates the room exists and registers the user's intent to participate.
        
        Required in request body:
        - user_id: Unique identifier for the user
        - user_name: Display name that will be shown with messages
        
        Returns success confirmation with room and user details.
        """
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            user_name = data.get('user_name')
            
            if not user_id or not user_name:
                return {
                    "status": 400,
                    "success": False,
                    "message": "user_id and user_name are required",
                    "data": None
                }, 400
            
            # Check if room exists (for now, we'll accept the hardcoded room)
            if room_id != "room1a2b3c":
                return {
                    "status": 404,
                    "success": False,
                    "message": "Room not found",
                    "data": None
                }, 404
            
            return {
                "status": 200,
                "success": True,
                "message": f"Successfully joined room {room_id}",
                "data": {
                    "room_id": room_id,
                    "user_id": user_id,
                    "user_name": user_name
                }
            }
            
        except Exception as e:
            return {
                "status": 500,
                "success": False,
                "message": f"Error joining room: {str(e)}",
                "data": None
            }, 500

@rooms_ns.route('/<string:room_id>/messages')
class SendMessage(Resource):
    @rooms_ns.doc('send_message')
    @rooms_ns.expect(send_message_request_model)
    @rooms_ns.marshal_with(send_message_response_model)
    @rooms_ns.response(200, 'Success - Message sent successfully')
    @rooms_ns.response(400, 'Bad Request - Missing required fields', error_response_model)
    @rooms_ns.response(404, 'Not Found - Room does not exist', error_response_model)
    @rooms_ns.response(500, 'Internal Server Error', error_response_model)
    def post(self, room_id):
        """
        Send a message to a chat room
        
        Sends a message to the specified room and broadcasts it in real-time to all connected clients
        via Server-Sent Events. The message includes user information and timestamp.
        
        Required in request body:
        - user_id: Unique identifier for the user sending the message
        - user_name: Display name that will be shown with the message
        - message: The actual message content to be sent
        
        The message is immediately broadcasted to all clients connected to the room's SSE stream.
        Returns confirmation with the generated message ID.
        """
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            user_name = data.get('user_name')
            message_content = data.get('message')
            
            if not all([user_id, user_name, message_content]):
                return {
                    "status": 400,
                    "success": False,
                    "message": "user_id, user_name, and message are required",
                    "data": None
                }, 400
            
            # Check if room exists
            if room_id != "room1a2b3c":
                return {
                    "status": 404,
                    "success": False,
                    "message": "Room not found",
                    "data": None
                }, 404
            
            # Create message object
            message = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "user_name": user_name,
                "message": message_content,
                "timestamp": datetime.now().isoformat(),
                "room_id": room_id
            }
            
            # Store message
            room_messages[room_id].append(message)
            
            # Broadcast to all connected clients in this room
            with clients_lock:
                for client in room_clients[room_id]:
                    try:
                        client.put(f"data: {json.dumps(message)}\n\n")
                    except:
                        # Remove disconnected clients
                        room_clients[room_id].remove(client)
            
            return {
                "status": 200,
                "success": True,
                "message": "Message sent successfully",
                "data": {
                    "message_id": message["id"],
                    "room_id": room_id
                }
            }
            
        except Exception as e:
            return {
                "status": 500,
                "success": False,
                "message": f"Error sending message: {str(e)}",
                "data": None
            }, 500

@app.route('/rooms/<room_id>/stream')
def stream_messages(room_id):
    """
    Server-Sent Events stream for real-time messages
    
    **IMPORTANT: This endpoint is not documented in Swagger UI as it returns Server-Sent Events**
    
    This endpoint provides a persistent HTTP connection that streams messages in real-time
    using Server-Sent Events (SSE). Clients should connect to this endpoint to receive
    live messages from the specified room.
    
    **Usage:**
    - Connect via EventSource in JavaScript: `new EventSource('/rooms/{room_id}/stream')`
    - Each message is sent as a 'data:' event with JSON payload
    - Connection includes keep-alive pings every 30 seconds
    - Historical messages are sent immediately upon connection
    
    **Message Format:**
    Each SSE message contains JSON data with the following structure:
    {
        "id": "uuid-string",
        "user_id": "user123", 
        "user_name": "John Doe",
        "message": "Hello everyone!",
        "timestamp": "2025-10-16T18:30:00.000Z",
        "room_id": "room1a2b3c"
    }
    
    **Parameters:**
    - room_id (string): The alphanumeric ID of the room to stream messages from
    
    **Responses:**
    - 200: Successful connection, returns text/event-stream
    - 404: Room not found
    
    **Connection Management:**
    - Automatic cleanup when client disconnects
    - Keep-alive pings to maintain connection
    - Thread-safe client management
    """
    def event_stream():
        # Create a queue for this client
        import queue
        client_queue = queue.Queue()
        
        # Add client to room
        with clients_lock:
            room_clients[room_id].append(client_queue)
        
        try:
            # Send existing messages first
            for message in room_messages[room_id]:
                yield f"data: {json.dumps(message)}\n\n"
            
            # Send keep-alive and new messages
            while True:
                try:
                    # Wait for new message with timeout
                    message = client_queue.get(timeout=30)
                    yield message
                except queue.Empty:
                    # Send keep-alive ping
                    yield "data: {\"type\": \"ping\"}\n\n"
                except:
                    break
        finally:
            # Remove client from room when connection closes
            with clients_lock:
                if client_queue in room_clients[room_id]:
                    room_clients[room_id].remove(client_queue)
    
    # Check if room exists
    if room_id != "room1a2b3c":
        return jsonify({
            "status": 404,
            "success": False,
            "message": "Room not found",
            "data": None
        }), 404
    
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)