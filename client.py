import argparse
import requests
import json
import time
import sys
import os
import asyncio
import websockets
from typing import Dict, List, Any, Optional
import getpass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
import logging
from rich.logging import RichHandler

# Server configuration
DEFAULT_SERVER_URL = "http://localhost:8000"

# Initialize rich console for pretty output
console = Console()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
log = logging.getLogger("poker_client")

class PokerClient:
    """Command-line client for the Texas Hold'em Poker server"""
    
    def __init__(self, server_url=DEFAULT_SERVER_URL):
        self.server_url = server_url
        self.game_id = None
        self.player_id = None
        self.player_name = None
        self.ws_connection = None
        self.game_state = None
        self.running = True
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.debug_mode = False
        self.local_command_mode = False
    
    def create_game(self, small_blind=1, big_blind=2, max_players=9):
        """Create a new poker game on the server"""
        try:
            response = requests.post(
                f"{self.server_url}/games",
                params={"small_blind": small_blind, "big_blind": big_blind, "max_players": max_players}
            )
            response.raise_for_status()
            data = response.json()
            self.game_id = data["game_id"]
            console.print(f"[green]Created game with ID: {self.game_id}[/green]")
            return True
        except requests.RequestException as e:
            console.print(f"[red]Error creating game: {str(e)}[/red]")
            return False
    
    def join_game(self, game_id, name, chips):
        """Join an existing poker game"""
        try:
            response = requests.post(
                f"{self.server_url}/games/{game_id}/join",
                json={"name": name, "chips": chips}
            )
            response.raise_for_status()
            data = response.json()
            self.game_id = game_id
            self.player_id = data["player_id"]
            self.player_name = name
            console.print(f"[green]Joined game as {name} (Player ID: {self.player_id})[/green]")
            return True
        except requests.RequestException as e:
            console.print(f"[red]Error joining game: {str(e)}[/red]")
            return False
    
    def start_game(self):
        """Start a new hand in the game"""
        try:
            response = requests.post(f"{self.server_url}/games/{self.game_id}/start")
            response.raise_for_status()
            console.print("[green]Game started successfully[/green]")
            return True
        except requests.RequestException as e:
            console.print(f"[red]Error starting game: {str(e)}[/red]")
            return False
    
    def get_game_state(self):
        """Get the current game state"""
        try:
            response = requests.get(
                f"{self.server_url}/games/{self.game_id}",
                params={"player_id": self.player_id}
            )
            response.raise_for_status()
            self.game_state = response.json()
            return self.game_state
        except requests.RequestException as e:
            console.print(f"[red]Error getting game state: {str(e)}[/red]")
            return None
    
    def send_action(self, action, amount=0):
        """Send a player action to the server"""
        try:
            response = requests.post(
                f"{self.server_url}/games/{self.game_id}/action",
                json={
                    "player_id": self.player_id,
                    "action": action,
                    "amount": amount
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            console.print(f"[red]Error sending action: {str(e)}[/red]")
            return None
    
    def display_game_state(self):
        """Display the current game state in a visually appealing way"""
        if not self.game_state:
            console.print("[yellow]No game state available[/yellow]")
            return
        
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Create layout
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=5)
        )
        
        # Header with game info
        phase = self.game_state.get("current_phase", "Not started")
        pot = self.game_state.get("pot", 0)
        current_bet = self.game_state.get("current_bet", 0)
        
        # Ensure phase is never None
        if phase is None:
            phase = "Not started"
        
        header_text = Text.from_markup(
            f"[bold green]Poker Game[/bold green] | [bold]Phase: {phase.upper()}[/bold] | "
            f"Pot: ${pot} | Current Bet: ${current_bet}"
        )
        layout["header"].update(Panel(header_text))
        
        # Body with community cards and players
        body_layout = Layout()
        layout["body"].update(body_layout)
        body_layout.split_row(
            Layout(name="players", ratio=2),
            Layout(name="game_info", ratio=3)
        )
        
        # Players table
        players_table = Table(title="Players", show_header=True)
        players_table.add_column("ID")
        players_table.add_column("Name")
        players_table.add_column("Chips")
        players_table.add_column("Bet")
        players_table.add_column("Status")
        
        active_player_id = self.game_state.get("active_player")
        
        for player in self.game_state.get("players", []):
            player_id = player.get("id")
            name = player.get("name", "")
            chips = player.get("chips", 0)
            current_bet = player.get("current_bet", 0)
            
            # Determine status
            status = ""
            if not player.get("is_active", True):
                status = "Folded"
            elif player.get("is_all_in", False):
                status = "All-In"
            elif player_id == active_player_id:
                status = "Active"
            
            # Highlight current player and your player
            style = ""
            if player_id == self.player_id:
                style = "bold green"
            elif player_id == active_player_id:
                style = "bold blue"
            
            players_table.add_row(
                f"{player_id}", name, f"${chips}", f"${current_bet}", status, 
                style=style
            )
        
        body_layout["players"].update(players_table)
        
        # Game info section (community cards, your cards)
        game_info_layout = Layout()
        body_layout["game_info"].update(game_info_layout)
        game_info_layout.split(
            Layout(name="community_cards", size=5),
            Layout(name="your_cards", size=5),
            Layout(name="winners", size=10 if "winners" in self.game_state and self.game_state["winners"] else 0)
        )
        
        # Community cards
        community_cards = self.game_state.get("community_cards", [])
        cc_text = Text("Community Cards: ", style="bold")
        if community_cards:
            for card in community_cards:
                card_text = Text(f" {card} ", style="bold")
                if card.endswith('H') or card.endswith('D'):
                    card_text.stylize("red")
                else:
                    card_text.stylize("black")
                cc_text.append(card_text)
        else:
            cc_text.append(Text(" None ", style="dim"))
        
        game_info_layout["community_cards"].update(Panel(cc_text))
        
        # Your cards
        your_cards = []
        for player in self.game_state.get("players", []):
            if player.get("id") == self.player_id and "cards" in player:
                your_cards = player["cards"]
                break
        
        yc_text = Text("Your Cards: ", style="bold")
        if your_cards:
            for card in your_cards:
                card_text = Text(f" {card} ", style="bold")
                if card.endswith('H') or card.endswith('D'):
                    card_text.stylize("red")
                else:
                    card_text.stylize("black")
                yc_text.append(card_text)
        else:
            yc_text.append(Text(" None ", style="dim"))
        
        game_info_layout["your_cards"].update(Panel(yc_text))
        
        # Winners info if available
        if "winners" in self.game_state and self.game_state["winners"]:
            winners_table = Table(title="Winners", show_header=True)
            winners_table.add_column("Player")
            winners_table.add_column("Hand")
            winners_table.add_column("Amount")
            
            for winner in self.game_state["winners"]:
                winners_table.add_row(
                    winner.get("player_name", ""),
                    winner.get("hand_name", ""),
                    f"${winner.get('amount', 0)}"
                )
            
            game_info_layout["winners"].update(winners_table)
        
        # Footer with valid actions
        valid_actions = self.game_state.get("valid_actions", {})
        action_text = Text()
        
        if active_player_id == self.player_id:
            action_text.append(Text("Your turn! Available actions: ", style="bold green"))
            
            for action, details in valid_actions.items():
                action_text.append(Text(f"\n{action.upper()}", style="bold"))
                
                if action in ["bet", "raise"] and "min" in details and "max" in details:
                    action_text.append(Text(f" (Min: ${details['min']}, Max: ${details['max']})"))
                elif action == "call" and "amount" in details:
                    action_text.append(Text(f" (Amount: ${details['amount']})"))
        else:
            action_text.append(Text(f"Waiting for Player {active_player_id} to act...", style="yellow"))
        
        layout["footer"].update(Panel(action_text))
        
        # Render the layout
        console.print(layout)
        
        # Display message if provided
        if "message" in self.game_state and self.game_state["message"]:
            console.print(f"[bold blue]{self.game_state['message']}[/bold blue]")
    
    async def reconnect(self):
        """Attempt to reconnect to the game"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            console.print("[red]Maximum reconnection attempts reached. Exiting...[/red]")
            self.running = False
            return False
            
        self.reconnect_attempts += 1
        console.print(f"[yellow]Attempting to reconnect (Attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})...[/yellow]")
        
        try:
            # First, try to reconnect via the reconnection endpoint
            response = requests.post(
                f"{self.server_url}/games/{self.game_id}/reconnect",
                params={"player_id": self.player_id}
            )
            response.raise_for_status()
            
            # Reset reconnect counter on successful reconnection
            self.reconnect_attempts = 0
            console.print("[green]Successfully reconnected to the game![/green]")
            return True
        except requests.RequestException as e:
            console.print(f"[red]Reconnection failed: {str(e)}[/red]")
            return False

    async def connect_websocket(self):
        """Connect to the WebSocket for real-time updates"""
        while self.running:
            uri = f"ws://localhost:8000/ws/{self.game_id}/{self.player_id}"
            try:
                async with websockets.connect(uri) as websocket:
                    self.ws_connection = websocket
                    console.print("[green]Connected to game via WebSocket[/green]")
                    # Reset reconnect counter on successful connection
                    self.reconnect_attempts = 0
                    
                    # Listen for updates
                    while self.running:
                        try:
                            # Check if in local command mode
                            if self.local_command_mode:
                                await self.process_local_commands()
                                self.local_command_mode = False
                                
                            # Receive message with timeout
                            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            self.game_state = json.loads(message)
                            self.display_game_state()
                            
                            # If it's our turn, prompt for action
                            if self.game_state.get("active_player") == self.player_id:
                                await self.prompt_action()
                        except asyncio.TimeoutError:
                            # No message received within timeout period, continue loop
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            console.print("[red]WebSocket connection closed[/red]")
                            if await self.reconnect():
                                break  # Break inner loop to reconnect WebSocket
                            else:
                                self.running = False
                                break
                        except Exception as e:
                            if self.debug_mode:
                                console.print(f"[red]Error in WebSocket connection: {str(e)}[/red]")
                                # In debug mode, print a more detailed stack trace
                                import traceback
                                console.print(f"[red]{traceback.format_exc()}[/red]")
                            else:
                                console.print(f"[red]Error in WebSocket connection: {str(e)}[/red]")
                            
                            # Try to reconnect if error persists
                            if await self.reconnect():
                                break  # Break inner loop to reconnect WebSocket
                            else:
                                await asyncio.sleep(5)  # Wait before next attempt
            except Exception as e:
                if self.debug_mode:
                    console.print(f"[red]Connection error: {str(e)}[/red]")
                    import traceback
                    console.print(f"[red]{traceback.format_exc()}[/red]")
                else:
                    console.print(f"[red]Connection error: {str(e)}[/red]")
                
                # Attempt to reconnect
                if not await self.reconnect():
                    await asyncio.sleep(5)  # Wait before next attempt
                    
                    # If too many failed attempts, give up
                    if self.reconnect_attempts >= self.max_reconnect_attempts:
                        self.running = False
                        break
    
    async def process_local_commands(self):
        """Process local client commands"""
        console.print("\n[bold yellow]Local Command Mode[/bold yellow]")
        console.print("Available commands:")
        console.print("  [green]refresh[/green] - Refresh game state")
        console.print("  [green]debug[/green] - Toggle debug mode")
        console.print("  [green]status[/green] - Check connection status")
        console.print("  [green]quit[/green] - Exit the game")
        console.print("  [green]resume[/green] - Return to game")
        
        command = console.input("[bold yellow]Enter command: [/bold yellow]")
        
        if command.lower() == "refresh":
            state = self.get_game_state()
            if state:
                self.display_game_state()
                console.print("[green]Game state refreshed[/green]")
            else:
                console.print("[red]Failed to refresh game state[/red]")
                
        elif command.lower() == "debug":
            self.debug_mode = not self.debug_mode
            console.print(f"[yellow]Debug mode {'enabled' if self.debug_mode else 'disabled'}[/yellow]")
            
        elif command.lower() == "status":
            try:
                response = requests.get(f"{self.server_url}/games/{self.game_id}")
                if response.status_code == 200:
                    console.print("[green]Server connection: OK[/green]")
                    console.print(f"[green]Game ID: {self.game_id}[/green]")
                    console.print(f"[green]Player ID: {self.player_id}[/green]")
                    console.print(f"[green]Player Name: {self.player_name}[/green]")
                else:
                    console.print("[red]Server connection: Error[/red]")
            except Exception as e:
                console.print(f"[red]Server connection error: {str(e)}[/red]")
                
        elif command.lower() == "quit":
            self.running = False
            console.print("[yellow]Exiting game...[/yellow]")
            
        elif command.lower() == "resume":
            console.print("[green]Returning to game...[/green]")
            
        else:
            console.print("[red]Unknown command[/red]")
            
        # Add a small delay to read the output before returning to the game
        await asyncio.sleep(2)
        self.display_game_state()
    
    async def prompt_action(self):
        """Prompt the player to select an action"""
        valid_actions = self.game_state.get("valid_actions", {})
        
        if not valid_actions:
            console.print("[yellow]No valid actions available[/yellow]")
            return
        
        # Print prompt
        console.print("[bold green]Your turn! Choose an action:[/bold green]")
        
        # Add special command for client
        console.print("[dim](Press Ctrl+C for local command mode)[/dim]")
        
        # Display available actions
        for i, (action, details) in enumerate(valid_actions.items(), 1):
            action_str = f"{i}. {action.upper()}"
            
            if action in ["bet", "raise"] and "min" in details and "max" in details:
                action_str += f" (Min: ${details['min']}, Max: ${details['max']})"
            elif action == "call" and "amount" in details:
                action_str += f" (Amount: ${details['amount']})"
            
            console.print(action_str)
        
        # Get player input
        try:
            choice = console.input("[bold]Enter action number: [/bold]")
        except KeyboardInterrupt:
            # Enter local command mode
            self.local_command_mode = True
            return
            
        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(valid_actions):
                console.print("[red]Invalid choice[/red]")
                await self.prompt_action()
                return
                
            action = list(valid_actions.keys())[choice_idx]
            amount = 0
            
            # For bet or raise, ask for amount
            if action in ["bet", "raise"]:
                details = valid_actions[action]
                min_amount = details.get("min", 0)
                max_amount = details.get("max", 0)
                
                while True:
                    try:
                        amount_str = console.input(f"[bold]Enter amount (${min_amount}-${max_amount}): [/bold]")
                        amount = int(amount_str)
                        if min_amount <= amount <= max_amount:
                            break
                        else:
                            console.print(f"[red]Amount must be between ${min_amount} and ${max_amount}[/red]")
                    except ValueError:
                        console.print("[red]Please enter a valid number[/red]")
                    except KeyboardInterrupt:
                        # Enter local command mode
                        self.local_command_mode = True
                        return
            
            # For call, use the specified amount
            elif action == "call" and "amount" in valid_actions[action]:
                amount = valid_actions[action]["amount"]
            
            # Send the action to the server
            console.print(f"[blue]Sending action: {action.upper()} {f'with amount ${amount}' if amount > 0 else ''}[/blue]")
            self.send_action(action, amount)
            
        except (ValueError, IndexError):
            console.print("[red]Invalid choice. Please enter a number.[/red]")
            await self.prompt_action()

async def main():
    parser = argparse.ArgumentParser(description="Poker Game Command Line Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create game parser
    create_parser = subparsers.add_parser("create", help="Create a new poker game")
    create_parser.add_argument("--small-blind", type=int, default=1, help="Small blind amount")
    create_parser.add_argument("--big-blind", type=int, default=2, help="Big blind amount")
    create_parser.add_argument("--max-players", type=int, default=9, help="Maximum number of players")
    
    # Join game parser
    join_parser = subparsers.add_parser("join", help="Join an existing poker game")
    join_parser.add_argument("game_id", help="ID of the game to join")
    join_parser.add_argument("--name", help="Your player name")
    join_parser.add_argument("--chips", type=int, default=1000, help="Starting chip amount")
    join_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    # Start game parser
    start_parser = subparsers.add_parser("start", help="Start a new hand in the current game")
    
    # Reconnect parser
    reconnect_parser = subparsers.add_parser("reconnect", help="Reconnect to an existing game")
    reconnect_parser.add_argument("game_id", help="ID of the game to reconnect to")
    reconnect_parser.add_argument("player_id", type=int, help="Your player ID")
    
    args = parser.parse_args()
    
    client = PokerClient()
    
    # Enable debug mode if specified
    if hasattr(args, 'debug') and args.debug:
        client.debug_mode = True
        log.setLevel(logging.DEBUG)
        log.debug("Debug mode enabled")
    
    if args.command == "create":
        success = client.create_game(
            small_blind=args.small_blind,
            big_blind=args.big_blind,
            max_players=args.max_players
        )
        if success:
            console.print("[yellow]To join this game, use the following command:[/yellow]")
            console.print(f"[bold]python client.py join {client.game_id} --name <your_name> --chips <amount>[/bold]")
    
    elif args.command == "join":
        name = args.name
        if not name:
            name = input("Enter your player name: ")
        
        success = client.join_game(args.game_id, name, args.chips)
        if success:
            # Get initial game state
            client.get_game_state()
            client.display_game_state()
            
            # Ask if user wants to start the game if not already started
            if not client.game_state.get("current_phase"):
                start_game = input("Start a new hand? (y/n): ").lower() == 'y'
                if start_game:
                    client.start_game()
            
            # Connect to WebSocket for real-time updates
            try:
                await client.connect_websocket()
            except KeyboardInterrupt:
                console.print("[yellow]Interrupted by user[/yellow]")
    
    elif args.command == "start":
        if not client.game_id:
            game_id = input("Enter the game ID: ")
            client.game_id = game_id
            
        if not client.player_id:
            try:
                player_id = int(input("Enter your player ID: "))
                client.player_id = player_id
            except ValueError:
                console.print("[red]Invalid player ID[/red]")
                return
        
        client.start_game()
        client.get_game_state()
        client.display_game_state()
    
    elif args.command == "reconnect":
        client.game_id = args.game_id
        client.player_id = args.player_id
        
        try:
            # Try to reconnect
            success = await client.reconnect()
            if success:
                # Get current state
                client.get_game_state()
                client.display_game_state()
                
                # Connect to WebSocket
                await client.connect_websocket()
            else:
                console.print("[red]Failed to reconnect to the game[/red]")
        except KeyboardInterrupt:
            console.print("[yellow]Interrupted by user[/yellow]")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[yellow]Exiting...[/yellow]")
        sys.exit(0) 