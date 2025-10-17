# Room Rant API Documentation

## Overview

Room Rant is a real-time chat room API that enables users to join rooms, send messages, and receive live updates using Server-Sent Events (SSE). The API follows RESTful principles with consistent JSON response formats.

**Base URL:** `http://localhost:8000`
**API Version:** 1.0
**Swagger Documentation:** `/docs/`

## Response Format

All API endpoints follow a consistent response structure:

```json
{
  "status": <HTTP_STATUS_CODE>,
  "success": <BOOLEAN>,
  "message": "<HUMAN_READABLE_MESSAGE>",
  "data": <RESPONSE_DATA_OR_NULL>
}
```

## Authentication

Currently, no authentication is required. Users are identified by `user_id` and `user_name` provided in requests.

## Endpoints

### 1. Get Rooms List

**Endpoint:** `GET /rooms`
**Description:** Retrieve a list of all available chat rooms with their details.

**Request:** No parameters required

**Response:**

````json
**Response:**
```json
{
  "status": 200,
  "success": true,
  "message": "Rooms retrieved successfully",
  "data": {
    "rooms": [
      {
        "id": "room1a2b3c",
        "name": "Chelsea vs Barca",
        "description": "Live discussion for Chelsea vs Barcelona match",
        "league": "Champions League",
        "kickoff_time": "2025-10-18T20:00:00Z",
        "stadium": "Stamford Bridge",
        "created_at": "2025-10-16T12:00:00Z",
        "active_users": 2
      },
      {
        "id": "room2d4e5f",
        "name": "Arsenal vs Liverpool",
        "description": "Live discussion for Arsenal vs Liverpool match",
        "league": "Premier League",
        "kickoff_time": "2025-10-19T15:30:00Z",
        "stadium": "Emirates Stadium",
        "created_at": "2025-10-17T15:00:00Z",
        "active_users": 0
      }
    ],
    "total_rooms": 2
  }
}
````

````

**Response Codes:**

- `200` - Success: Rooms retrieved successfully

---

### 2. Join Room

**Endpoint:** `POST /rooms/{room_id}/join`
**Description:** Join a specific chat room by providing user credentials.

**Path Parameters:**

- `room_id` (string, required) - Alphanumeric room identifier (e.g., "room1a2b3c" or "room2d4e5f")

**Request Body:**

```json
{
  "user_id": "user123",
  "user_name": "John Doe"
}
````

**Request Fields:**

- `user_id` (string, required) - Unique identifier for the user
- `user_name` (string, required) - Display name that will be shown with messages

**Success Response:**

```json
{
  "status": 200,
  "success": true,
  "message": "Successfully joined room room1a2b3c",
  "data": {
    "room_id": "room1a2b3c",
    "user_id": "user123",
    "user_name": "John Doe"
  }
}
```

**Error Responses:**

- `400` - Bad Request: Missing required fields

```json
{
  "status": 400,
  "success": false,
  "message": "user_id and user_name are required",
  "data": null
}
```

- `404` - Not Found: Room does not exist

```json
{
  "status": 404,
  "success": false,
  "message": "Room not found",
  "data": null
}
```

- `500` - Internal Server Error

```json
{
  "status": 500,
  "success": false,
  "message": "Error joining room: <error_details>",
  "data": null
}
```

---

### 3. Send Message

**Endpoint:** `POST /rooms/{room_id}/messages`
**Description:** Send a message to a chat room. The message is immediately broadcasted to all connected clients via Server-Sent Events.

**Path Parameters:**

- `room_id` (string, required) - Alphanumeric room identifier

**Request Body:**

```json
{
  "user_id": "user123",
  "user_name": "John Doe",
  "message": "Hello everyone!"
}
```

**Request Fields:**

- `user_id` (string, required) - Unique identifier for the user sending the message
- `user_name` (string, required) - Display name that will be shown with the message
- `message` (string, required) - The actual message content to be sent

**Success Response:**

```json
{
  "status": 200,
  "success": true,
  "message": "Message sent successfully",
  "data": {
    "message_id": "550e8400-e29b-41d4-a716-446655440000",
    "room_id": "room1a2b3c"
  }
}
```

**Error Responses:**

- `400` - Bad Request: Missing required fields

```json
{
  "status": 400,
  "success": false,
  "message": "user_id, user_name, and message are required",
  "data": null
}
```

- `404` - Not Found: Room does not exist
- `500` - Internal Server Error

---

### 4. Message Stream (Server-Sent Events)

**Endpoint:** `GET /rooms/{room_id}/stream`
**Description:** Real-time message streaming using Server-Sent Events. Provides persistent HTTP connection for live message updates.

**Path Parameters:**

- `room_id` (string, required) - Alphanumeric room identifier

**Response Type:** `text/event-stream`

**Usage:**

- JavaScript: `new EventSource('/rooms/{room_id}/stream')`
- Each message is sent as a 'data:' event with JSON payload
- Historical messages are sent immediately upon connection
- Keep-alive pings sent every 30 seconds

**Message Format:**
Each SSE message contains JSON data:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "user_name": "John Doe",
  "message": "Hello everyone!",
  "timestamp": "2025-10-16T18:30:00.000Z",
  "room_id": "room1a2b3c",
  "connected_clients": 3
}
```

**Keep-alive Ping Format:**

```json
{
  "type": "ping"
}
```

**Error Responses:**

- `404` - Room not found (returns JSON error format)

**Connection Management:**

- Automatic cleanup when client disconnects
- Thread-safe client management
- Clients receive all historical messages upon connection

---

## Data Models

### Room Object

````json
### Room Object
```json
{
  "id": "string (alphanumeric)",
  "name": "string",
  "description": "string",
  "league": "string",
  "kickoff_time": "string (ISO timestamp)",
  "stadium": "string",
  "created_at": "string (ISO timestamp)",
  "active_users": "integer"
}
````

`````

### Message Object

````json
### Message Object
```json
{
  "id": "string (UUID)",
  "user_id": "string",
  "user_name": "string",
  "message": "string",
  "timestamp": "string (ISO timestamp)",
  "room_id": "string",
  "connected_clients": "integer"
}
`````

````

### Standard Response Format

```json
{
  "status": "integer (HTTP status code)",
  "success": "boolean",
  "message": "string (human readable)",
  "data": "object or null"
}
````

## Usage Flow

1. **Get Available Rooms:** `GET /rooms` to see available chat rooms
2. **Join a Room:** `POST /rooms/{room_id}/join` with user credentials
3. **Connect to Live Stream:** `GET /rooms/{room_id}/stream` to receive real-time messages
4. **Send Messages:** `POST /rooms/{room_id}/messages` to send messages to the room

## Implementation Notes

- **Real-time Updates:** Messages are broadcasted immediately to all connected SSE clients
- **Message History:** New connections receive all historical messages for the room
- **User Identification:** Each message includes user_id and user_name for identification
- **Thread Safety:** All operations are thread-safe for concurrent users
- **Connection Persistence:** SSE connections are maintained with keep-alive pings
- **Error Handling:** Consistent error response format across all endpoints

## Current Limitations

- Two available rooms: "room1a2b3c" (Chelsea vs Barca) and "room2d4e5f" (Arsenal vs Liverpool)
- No user authentication or session management
- Messages stored in memory (not persistent across server restarts)
- No message history pagination
- No user management or dynamic room creation endpoints

## Example Client Integration

### JavaScript EventSource Example:

```javascript
// Join room first
fetch("/rooms/room1a2b3c/join", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: "user123",
    user_name: "John Doe",
  }),
});

// Connect to message stream
const eventSource = new EventSource("/rooms/room1a2b3c/stream");
eventSource.onmessage = function (event) {
  const message = JSON.parse(event.data);
  if (message.type !== "ping") {
    console.log("New message:", message);
  }
};

// Send a message
fetch("/rooms/room1a2b3c/messages", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id: "user123",
    user_name: "John Doe",
    message: "Hello everyone!",
  }),
});
```

This documentation provides complete API specifications for integration with the Room Rant chat system.
