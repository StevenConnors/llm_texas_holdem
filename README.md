# Texas Hold'em Poker - Client-Server Architecture

This project extends a core Texas Hold'em poker implementation into a client-server architecture with a text-based CLI client and a state-maintaining server. It also provides a foundation for AI agent integration through the Model Context Protocol (MCP).

## Components

1. **Core Poker Implementation**
   - Complete implementation of Texas Hold'em rules
   - Hand evaluation, pot management, player actions, etc.

2. **Server**
   - FastAPI server that maintains game state
   - RESTful endpoints for game management and player actions
   - WebSocket support for real-time updates
   - MCP integration for AI agents

3. **CLI Client**
   - Text-based user interface
   - Real-time updates via WebSocket
   - Visual representation of cards, chips, and player status

4. **MCP Agent Client**
   - Demonstrates AI agent integration
   - Configurable strategies (basic, aggressive, conservative)
   - Framework for building more sophisticated AI players

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd texas-holdem-poker
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

### Starting the Server

Start the FastAPI server with:

```bash
python server.py
```

The server will run on http://localhost:8000 by default. You can access the interactive API documentation at http://localhost:8000/docs.

### Using the CLI Client

The CLI client supports three main commands:

1. **Create a new game**:
   ```bash
   python client.py create --small-blind 5 --big-blind 10 --max-players 5
   ```

2. **Join an existing game**:
   ```bash
   python client.py join <game-id> --name "Player1" --chips 1000
   ```

3. **Start a new hand** (if you've already joined a game):
   ```bash
   python client.py start
   ```

### Using the MCP Agent

The MCP agent can join and play in any game:

```bash
python mcp_client.py --name "AIPlayer" --game-id <game-id> --chips 1000 --strategy basic
```

Available strategies:
- `basic` - A balanced approach with some strategic folding and betting
- `aggressive` - Always bets and raises when possible
- `conservative` - Prefers checking and folding, rarely betting
- `random` - Makes random decisions (for testing)

## Game Flow

1. **Create a game** using the CLI client
2. **Join the game** with one or more human players (CLI clients)
3. Optionally, add AI players using the MCP agent client
4. **Start a new hand** when all players are ready
5. Players take turns according to poker rules
6. After a hand completes, you can start a new one

## API Endpoints

The server provides the following main endpoints:

- `POST /games` - Create a new game
- `POST /games/{game_id}/join` - Join an existing game
- `POST /games/{game_id}/start` - Start a new hand
- `GET /games/{game_id}` - Get the current game state
- `POST /games/{game_id}/action` - Process a player action
- `WebSocket /ws/{game_id}/{player_id}` - Real-time game updates

MCP-specific endpoints:
- `POST /mcp/game_state` - Get game state formatted for MCP
- `POST /mcp/action` - Process an action from an MCP agent

## Future Extensions

This implementation provides a foundation for further extensions:

1. **Enhanced AI Agents**: Implement more sophisticated poker strategies using LLMs or reinforcement learning
2. **Web Client**: Create a graphical web interface for a better user experience
3. **Persistent Storage**: Add database integration to save game history and player statistics
4. **Tournament Mode**: Implement tournament structures with blinds progression
5. **Multi-Table Support**: Allow players to join multiple games simultaneously

## License

[MIT License](LICENSE) 