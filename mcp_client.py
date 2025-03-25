import argparse
import requests
import json
import time
import sys
import random
from typing import Dict, List, Any, Optional

# Server configuration
DEFAULT_SERVER_URL = "http://localhost:8000"

class MCPPokerAgent:
    """
    Model Context Protocol (MCP) client for AI agents to play poker
    
    This demonstrates how an AI agent could interact with the poker server
    using the MCP protocol. It provides a framework for more sophisticated
    AI implementations.
    """
    
    def __init__(self, server_url=DEFAULT_SERVER_URL, agent_name="MCPAgent", 
                 game_id=None, player_id=None, strategy="basic"):
        self.server_url = server_url
        self.agent_name = agent_name
        self.game_id = game_id
        self.player_id = player_id
        self.strategy = strategy
        self.mcp_state = None
        
        # Agent context (knowledge maintained across interactions)
        self.context = {
            "previous_actions": [],
            "player_profiles": {},
            "hand_history": [],
            "chips_trend": [],
            "session_stats": {
                "hands_played": 0,
                "hands_won": 0,
                "total_profit": 0
            }
        }
    
    def join_game(self, game_id, chips=1000):
        """Join an existing poker game"""
        try:
            response = requests.post(
                f"{self.server_url}/games/{game_id}/join",
                json={"name": self.agent_name, "chips": chips}
            )
            response.raise_for_status()
            data = response.json()
            self.game_id = game_id
            self.player_id = data["player_id"]
            print(f"Agent {self.agent_name} joined game {game_id} as player {self.player_id}")
            return True
        except requests.RequestException as e:
            print(f"Error joining game: {str(e)}")
            return False
    
    def get_mcp_state(self):
        """Get the game state formatted for MCP"""
        try:
            response = requests.post(
                f"{self.server_url}/mcp/game_state",
                params={"game_id": self.game_id}
            )
            response.raise_for_status()
            self.mcp_state = response.json()
            return self.mcp_state
        except requests.RequestException as e:
            print(f"Error getting MCP state: {str(e)}")
            return None
    
    def send_action(self, action, amount=0):
        """Send a player action to the server via MCP endpoint"""
        try:
            response = requests.post(
                f"{self.server_url}/mcp/action",
                params={"game_id": self.game_id},
                json={
                    "player_id": self.player_id,
                    "action": action,
                    "amount": amount
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Update the agent's context with the action taken
            self.context["previous_actions"].append({
                "action": action,
                "amount": amount,
                "timestamp": time.time()
            })
            
            return result
        except requests.RequestException as e:
            print(f"Error sending action: {str(e)}")
            return None
    
    def decide_action(self):
        """
        Decide on an action based on the current game state and strategy
        
        For a real AI agent, this would involve:
        1. Analyzing the game state using NLP/LLM
        2. Considering the agent's context/history
        3. Applying poker strategy algorithms
        4. Selecting an optimal action
        
        This implementation uses a very simple strategy for demonstration.
        """
        if not self.mcp_state:
            return None, 0
        
        game_state = self.mcp_state["context"]["game_state"]
        valid_actions = self.mcp_state["context"]["valid_actions"]
        
        # Check if it's our turn
        if game_state["active_player"] != self.player_id:
            return None, 0
        
        # Find our player data
        our_player = next((p for p in game_state["players"] if p["id"] == self.player_id), None)
        if not our_player:
            return None, 0
        
        # Very basic strategy just for demonstration
        if self.strategy == "basic":
            # Simple rules-based strategy:
            # 1. If check is available, use it 60% of the time
            # 2. If fold is available and there's a big bet, fold
            # 3. If bet/raise is available, use a simple betting strategy
            # 4. Otherwise, call if not too expensive
            
            # Prefer to check when possible
            if "check" in valid_actions and random.random() < 0.6:
                return "check", 0
            
            # If the bet is too high relative to our chips, consider folding
            current_bet = game_state["current_bet"]
            our_chips = our_player["chips"]
            if "fold" in valid_actions and current_bet > our_chips * 0.4:
                return "fold", 0
            
            # Betting strategy
            if "bet" in valid_actions:
                bet_details = valid_actions["bet"]
                bet_amount = max(bet_details["min"], min(our_chips * 0.1, bet_details["max"]))
                return "bet", int(bet_amount)
            
            if "raise" in valid_actions:
                raise_details = valid_actions["raise"]
                raise_amount = max(raise_details["min"], min(our_chips * 0.15, raise_details["max"]))
                return "raise", int(raise_amount)
            
            # Call if not too expensive
            if "call" in valid_actions:
                call_amount = valid_actions["call"]["amount"]
                if call_amount <= our_chips * 0.3:
                    return "call", call_amount
            
            # Default: fold if nothing else
            if "fold" in valid_actions:
                return "fold", 0
            
        elif self.strategy == "aggressive":
            # Always bet/raise when possible
            if "raise" in valid_actions:
                raise_details = valid_actions["raise"]
                # Bet 30% of our chips or the max allowed
                raise_amount = min(our_chips * 0.3, raise_details["max"])
                raise_amount = max(raise_details["min"], raise_amount)
                return "raise", int(raise_amount)
            
            if "bet" in valid_actions:
                bet_details = valid_actions["bet"]
                bet_amount = min(our_chips * 0.25, bet_details["max"])
                bet_amount = max(bet_details["min"], bet_amount)
                return "bet", int(bet_amount)
            
            if "call" in valid_actions:
                return "call", valid_actions["call"]["amount"]
            
            if "check" in valid_actions:
                return "check", 0
            
            # Fold as last resort
            return "fold", 0
            
        elif self.strategy == "conservative":
            # Prefer checking and calling, rarely betting
            if "check" in valid_actions:
                return "check", 0
            
            if "call" in valid_actions:
                call_amount = valid_actions["call"]["amount"]
                # Only call if it's not too expensive
                if call_amount <= our_chips * 0.15:
                    return "call", call_amount
            
            # Small bet occasionally
            if "bet" in valid_actions and random.random() < 0.3:
                bet_details = valid_actions["bet"]
                bet_amount = max(bet_details["min"], min(our_chips * 0.05, bet_details["max"]))
                return "bet", int(bet_amount)
            
            # Default to folding
            return "fold", 0
        
        # Default strategy (random)
        available_actions = list(valid_actions.keys())
        if not available_actions:
            return None, 0
            
        action = random.choice(available_actions)
        amount = 0
        
        if action == "bet" or action == "raise":
            details = valid_actions[action]
            amount = random.randint(details["min"], details["max"])
        elif action == "call":
            amount = valid_actions[action]["amount"]
            
        return action, amount

    def update_player_profiles(self):
        """
        Update profiles of other players based on their actions
        
        This would be used by a sophisticated AI to build models of opponents.
        For now, it's just a placeholder.
        """
        if not self.mcp_state:
            return
            
        game_state = self.mcp_state["context"]["game_state"]
        
        for player in game_state["players"]:
            player_id = player["id"]
            if player_id == self.player_id:
                continue
                
            # Create profile if it doesn't exist
            if player_id not in self.context["player_profiles"]:
                self.context["player_profiles"][player_id] = {
                    "name": player["name"],
                    "playing_style": "unknown",
                    "aggression_level": 0.5,  # 0-1 scale
                    "observed_actions": []
                }
    
    def run_agent_loop(self, polling_interval=2):
        """Run the agent in a continuous loop"""
        print(f"Starting MCP agent {self.agent_name} in game {self.game_id}")
        
        while True:
            try:
                # Get the current MCP game state
                self.get_mcp_state()
                
                if not self.mcp_state:
                    print("Could not get game state, retrying...")
                    time.sleep(polling_interval)
                    continue
                
                game_state = self.mcp_state["context"]["game_state"]
                
                # Update player profiles
                self.update_player_profiles()
                
                # Check if it's our turn
                if game_state["active_player"] == self.player_id:
                    print(f"It's our turn (Player {self.player_id})")
                    
                    # Decide on an action
                    action, amount = self.decide_action()
                    
                    if action:
                        print(f"Taking action: {action.upper()} {f'with amount {amount}' if amount > 0 else ''}")
                        result = self.send_action(action, amount)
                        
                        if result:
                            print(f"Action result: {result.get('success', False)}")
                        else:
                            print("Failed to send action")
                    else:
                        print("No valid action determined")
                else:
                    active_player = game_state["active_player"]
                    if active_player is not None:
                        print(f"Waiting for player {active_player} to act...")
                
                # Sleep to avoid hammering the server
                time.sleep(polling_interval)
                
            except KeyboardInterrupt:
                print("Agent stopping...")
                break
            except Exception as e:
                print(f"Error in agent loop: {str(e)}")
                time.sleep(polling_interval)

def main():
    parser = argparse.ArgumentParser(description="MCP Poker Agent")
    parser.add_argument("--name", default="MCPAgent", help="Name for the agent")
    parser.add_argument("--game-id", required=True, help="ID of the game to join")
    parser.add_argument("--chips", type=int, default=1000, help="Starting chip amount")
    parser.add_argument("--strategy", choices=["basic", "aggressive", "conservative", "random"],
                      default="basic", help="Agent strategy")
    parser.add_argument("--server", default=DEFAULT_SERVER_URL, help="Server URL")
    
    args = parser.parse_args()
    
    agent = MCPPokerAgent(
        server_url=args.server,
        agent_name=args.name,
        game_id=args.game_id,
        strategy=args.strategy
    )
    
    # Join the game
    if agent.join_game(args.game_id, args.chips):
        # Run the agent loop
        agent.run_agent_loop()
    else:
        print("Failed to join game. Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0) 