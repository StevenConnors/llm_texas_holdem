from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Union
import uvicorn
import uuid
import asyncio
import json
from datetime import datetime

from game import TexasHoldemGame
from constants import (
    ACTION_FOLD, ACTION_CHECK, ACTION_CALL, ACTION_BET, ACTION_RAISE, ACTION_ALL_IN,
    PHASE_PREFLOP, PHASE_FLOP, PHASE_TURN, PHASE_RIVER, PHASE_SHOWDOWN
)

app = FastAPI(title="Poker Server", description="Texas Hold'em Poker Game Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class Player(BaseModel):
    name: str
    chips: int

class GameAction(BaseModel):
    player_id: int
    action: str
    amount: int = 0

class GameStateResponse(BaseModel):
    game_id: str
    current_phase: Optional[str]
    community_cards: List[str]
    pot: int
    current_bet: int
    active_player: Optional[int]
    players: List[Dict[str, Any]]
    valid_actions: Dict[str, Any]
    winners: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None

# In-memory storage for games
games = {}
player_game_mapping = {}
connected_clients = {}

# Add these new data structures
player_connection_status = {}  # Tracks if a player is connected
reconnection_timeouts = {}     # Tracks timeouts for disconnected players

# Game management functions
def get_game(game_id: str) -> TexasHoldemGame:
    if game_id not in games:
        raise HTTPException(status_code=404, detail=f"Game with ID {game_id} not found")
    return games[game_id]["game"]

def create_game_state_response(game_id: str, player_id: Optional[int] = None, message: Optional[str] = None):
    """Create a standardized game state response"""
    game = get_game(game_id)
    game_state = game.get_game_state()
    
    # Convert phase name from hyphenated format to underscore format for test compatibility
    game_state["phase"] = game_state["phase"].replace("-", "_") if game_state["phase"] else None
    
    # Add player-specific information if available
    if player_id is not None:
        valid_actions = game.get_valid_actions(player_id)
        player_info = next((p for p in game.players if p.player_id == player_id), None)
        
        player_cards = []
        if player_info:
            player_cards = [str(card) for card in player_info.cards]
            
        # Add player-specific details
        response = {
            "game_id": game_id,
            "player_id": player_id,
            "phase": game_state["phase"],
            "community_cards": game_state["community_cards"],
            "pot": sum(pot['amount'] for pot in game.pots),
            "current_bet": game_state["current_bet"],
            "active_player": game_state["active_player"],
            "dealer": game_state["dealer"],
            "small_blind": game_state["small_blind"],
            "big_blind": game_state["big_blind"],
            "your_cards": player_cards,
            "players": [], # Will fill with filtered player info
            "valid_actions": valid_actions if game_state["active_player"] == player_id else {}
        }
        
        # Add other players with limited info
        for p in game_state["players"]:
            player_obj = {
                "id": p["id"],
                "name": p["name"],
                "chips": p["chips"],
                "current_bet": p["current_bet"],
                "is_active": p["is_active"],
                "is_all_in": p["is_all_in"],
                "position": p.get("position", "")
            }
            # Only show cards for this player
            if p["id"] == player_id:
                player_obj["cards"] = player_cards
            
            response["players"].append(player_obj)
    else:
        # For spectators, show limited info
        response = {
            "game_id": game_id,
            "phase": game_state["phase"],
            "community_cards": game_state["community_cards"],
            "pot": sum(pot['amount'] for pot in game.pots),
            "current_bet": game_state["current_bet"],
            "active_player": game_state["active_player"],
            "dealer": game_state["dealer"],
            "small_blind": game_state["small_blind"],
            "big_blind": game_state["big_blind"],
            "players": [{
                "id": p["id"],
                "name": p["name"],
                "chips": p["chips"],
                "current_bet": p["current_bet"],
                "is_active": p["is_active"],
                "is_all_in": p["is_all_in"],
                "position": p.get("position", "")
            } for p in game_state["players"]]
        }
    
    # Add optional message
    if message:
        response["message"] = message
        
    return response

# API Endpoints
@app.post("/games", status_code=201)
async def create_game(small_blind: int = 1, big_blind: int = 2, max_players: int = 9):
    """Create a new poker game"""
    game_id = str(uuid.uuid4())
    games[game_id] = {
        "game": TexasHoldemGame(small_blind=small_blind, big_blind=big_blind, max_players=max_players),
        "created_at": datetime.now(),
        "players": []
    }
    return {"game_id": game_id, "message": "Game created successfully"}

@app.post("/games/{game_id}/join")
async def join_game(game_id: str, player: Player):
    """Join an existing game"""
    game = get_game(game_id)
    
    try:
        player_id = game.add_player(name=player.name, chips=player.chips)
        player_game_mapping[player_id] = game_id
        games[game_id]["players"].append(player_id)
        return {"player_id": player_id, "message": f"Successfully joined game as {player.name}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/games/{game_id}/start")
async def start_game(game_id: str):
    """Start a new hand in the game"""
    game = get_game(game_id)
    
    if len(game.players) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 players to start a game")
    
    success = game.start_new_hand()
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start a new hand")
    
    # Notify connected clients that the game has started
    await notify_state_change(game_id)
    
    return create_game_state_response(game_id, message="New hand started")

@app.get("/games/{game_id}")
def get_game_state(game_id: str, player_id: Optional[int] = None):
    """Get the current state of the game"""
    # Verify the game exists
    _ = get_game(game_id)
    return create_game_state_response(game_id, player_id)

@app.post("/games/{game_id}/action")
async def player_action(game_id: str, action: GameAction):
    """Process a player's action in the game"""
    game = get_game(game_id)
    
    try:
        result = game.process_player_action(action.player_id, action.action, action.amount)
        
        # Store winners for later reference if showdown
        if "winners" in result and result["showdown"]:
            game.last_winners = result["winners"]
        
        # Notify connected clients about the state change
        await notify_state_change(game_id)
        
        message = f"Player {action.player_id} performed {action.action}"
        if action.action in [ACTION_BET, ACTION_RAISE, ACTION_CALL]:
            message += f" with amount {action.amount}"
        
        return create_game_state_response(game_id, message=message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# WebSocket Connection
@app.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: Optional[int] = None):
    await websocket.accept()
    
    if game_id not in games:
        await websocket.send_text(json.dumps({"error": "Game not found"}))
        await websocket.close()
        return
    
    # Register the client
    if game_id not in connected_clients:
        connected_clients[game_id] = {}
    
    client_id = f"player_{player_id}" if player_id is not None else f"spectator_{uuid.uuid4()}"
    connected_clients[game_id][client_id] = websocket
    
    # Mark player as connected
    if player_id is not None:
        player_connection_status[player_id] = True
        
        # Cancel any pending reconnection timeout
        if player_id in reconnection_timeouts:
            reconnection_timeouts[player_id].cancel()
            reconnection_timeouts.pop(player_id, None)
    
    try:
        # Send initial game state
        game_state = create_game_state_response(game_id, player_id)
        await websocket.send_text(game_state.json())
        
        # Keep connection alive for notifications
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        # Clean up on disconnect
        if game_id in connected_clients and client_id in connected_clients[game_id]:
            del connected_clients[game_id][client_id]
            if not connected_clients[game_id]:
                del connected_clients[game_id]
                
        # Handle player disconnect
        if player_id is not None:
            player_connection_status[player_id] = False
            # Schedule cleanup if player doesn't reconnect within timeout
            reconnection_timeouts[player_id] = asyncio.create_task(handle_player_timeout(game_id, player_id))
            
            # Notify other players about the disconnection
            await notify_state_change(game_id, f"Player {player_id} disconnected. Waiting for reconnection...")

async def handle_player_timeout(game_id: str, player_id: int, timeout: int = 60):
    """Handle a player disconnection with a timeout for reconnection"""
    try:
        # Wait for timeout period
        await asyncio.sleep(timeout)
        
        # If the player hasn't reconnected, handle accordingly
        if player_id in player_connection_status and not player_connection_status[player_id]:
            game = get_game(game_id)
            
            # If it's the player's turn, auto-fold
            if game.get_game_state()["active_player"] == player_id:
                try:
                    result = game.process_player_action(player_id, ACTION_FOLD, 0)
                    if "winners" in result and result["showdown"]:
                        game.last_winners = result["winners"]
                    await notify_state_change(game_id, f"Player {player_id} timed out and automatically folded")
                except ValueError as e:
                    pass  # Handle errors silently
            
            # Note: For more complex scenarios you might want to:
            # 1. Remove the player from future hands
            # 2. Save their chips for a future reconnection
            # 3. Add an AI to play their position
    except asyncio.CancelledError:
        # Task was cancelled because player reconnected
        pass
    except Exception as e:
        print(f"Error in timeout handler: {str(e)}")
    finally:
        # Clean up
        if player_id in reconnection_timeouts:
            reconnection_timeouts.pop(player_id, None)

async def notify_state_change(game_id: str, custom_message: Optional[str] = None):
    """Notify all connected clients about a game state change"""
    if game_id not in connected_clients:
        return
    
    for client_id, websocket in connected_clients[game_id].items():
        # Extract player_id from client_id if it's a player
        player_id = None
        if client_id.startswith("player_"):
            try:
                player_id = int(client_id.split("_")[1])
            except (IndexError, ValueError):
                pass
        
        # Create personalized game state for the client
        game_state = create_game_state_response(game_id, player_id, message=custom_message)
        await websocket.send_text(game_state.json())

# MCP Integration
# This is a placeholder for future MCP integration
@app.post("/mcp/game_state")
def get_mcp_game_state(game_id: str):
    """Get game state formatted for MCP (Model Context Protocol)"""
    game = get_game(game_id)
    game_state = game.get_game_state()
    
    # Format the game state according to MCP specifications
    # This would be expanded in the future
    mcp_state = {
        "context": {
            "game_state": {
                "phase": game_state["phase"],
                "community_cards": [str(card) for card in game.community_cards],
                "pot": sum(pot['amount'] for pot in game.pots),
                "current_bet": game_state["current_bet"],
                "active_player": game_state["active_player"],
                "players": game_state["players"]
            },
            "valid_actions": {}
        }
    }
    
    if game_state["active_player"] is not None:
        mcp_state["context"]["valid_actions"] = game.get_valid_actions(game_state["active_player"])
    
    return mcp_state

@app.post("/mcp/action")
async def mcp_action(game_id: str, action_data: Dict[str, Any]):
    """Process an action from an MCP agent"""
    game = get_game(game_id)
    
    try:
        player_id = action_data.get("player_id")
        action = action_data.get("action")
        amount = action_data.get("amount", 0)
        
        result = game.process_player_action(player_id, action, amount)
        
        # Store winners for later reference if showdown
        if "winners" in result and result["showdown"]:
            game.last_winners = result["winners"]
        
        # Notify connected clients about the state change
        await notify_state_change(game_id)
        
        return {"success": True, "action": action, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add a reconnection endpoint
@app.post("/games/{game_id}/reconnect")
async def reconnect_player(game_id: str, player_id: int):
    """Allow a player to reconnect to a game after disconnection"""
    game = get_game(game_id)
    
    # Check if player exists in the game
    player_exists = False
    for player in game.players:
        if player.player_id == player_id:
            player_exists = True
            break
            
    if not player_exists:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found in game {game_id}")
    
    # Return connection details
    return {
        "game_id": game_id,
        "player_id": player_id,
        "message": f"Reconnected to game as player {player_id}. Use WebSocket to continue playing."
    }

# Add a new debug/admin endpoint
@app.get("/admin/games/{game_id}")
def admin_get_game_state(game_id: str, admin_key: str = "admin123"):
    """Admin endpoint to get complete game state including all player cards"""
    # Simple admin authentication
    if admin_key != "admin123":  # In production, use proper authentication
        raise HTTPException(status_code=403, detail="Invalid admin key")
        
    game = get_game(game_id)
    game_state = game.get_game_state()
    
    # Get player cards
    players_with_cards = []
    for player in game.players:
        player_info = {
            "id": player.player_id,
            "name": player.name,
            "chips": player.chips,
            "current_bet": player.current_bet,
            "is_active": player.is_active,
            "is_all_in": player.is_all_in,
            "cards": [str(card) for card in player.cards]
        }
        players_with_cards.append(player_info)
    
    # Convert phase name from hyphenated format to underscore format for test compatibility
    phase = game_state["phase"].replace("-", "_") if game_state["phase"] else None
    
    # Create full game state with all cards visible
    admin_state = {
        "game_id": game_id,
        "phase": phase,
        "community_cards": [str(card) for card in game.community_cards],
        "pot": sum(pot['amount'] for pot in game.pots),
        "current_bet": game_state["current_bet"],
        "active_player": game_state["active_player"],
        "players": players_with_cards,
        "dealer": game_state["dealer"],
        "small_blind": game_state["small_blind"],
        "big_blind": game_state["big_blind"]
    }
    
    return admin_state

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True) 