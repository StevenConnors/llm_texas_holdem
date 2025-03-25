import argparse
import requests
import json
import time
import sys
import os
import asyncio
import websockets
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.prompt import Prompt

# Server configuration
DEFAULT_SERVER_URL = "http://localhost:8000"
DEFAULT_ADMIN_KEY = "admin123"

# Initialize rich console for pretty output
console = Console()

class PokerAdminClient:
    """Admin client for the Texas Hold'em Poker server - provides a 'god view' of all game state"""
    
    def __init__(self, server_url=DEFAULT_SERVER_URL, admin_key=DEFAULT_ADMIN_KEY):
        self.server_url = server_url
        self.admin_key = admin_key
        self.game_id = None
        self.game_state = None
        self.running = True
        self.debug_mode = False
    
    def get_admin_game_state(self):
        """Get the full game state with admin privileges"""
        try:
            response = requests.get(
                f"{self.server_url}/admin/games/{self.game_id}",
                params={"admin_key": self.admin_key}
            )
            response.raise_for_status()
            self.game_state = response.json()
            return self.game_state
        except requests.RequestException as e:
            console.print(f"[red]Error getting admin game state: {str(e)}[/red]")
            return None
    
    def display_admin_view(self):
        """Display the god view of the game state"""
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
            Layout(name="commands", size=7)
        )
        
        # Header with game info
        phase = self.game_state.get("phase", "Not started")
        if phase is None:
            phase = "Not started"
        pot = self.game_state.get("pot", 0)
        current_bet = self.game_state.get("current_bet", 0)
        
        header_text = Text.from_markup(
            f"[bold red]ADMIN VIEW - Poker Game[/bold red] | [bold]Phase: {phase.upper()}[/bold] | "
            f"Pot: ${pot} | Current Bet: ${current_bet}"
        )
        layout["header"].update(Panel(header_text, border_style="red"))
        
        # Body layout
        body_layout = Layout()
        layout["body"].update(body_layout)
        body_layout.split(
            Layout(name="community_cards", size=7),
            Layout(name="players"),
            Layout(name="debug_info", size=15 if self.debug_mode else 0)
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
        
        body_layout["community_cards"].update(Panel(cc_text, title="Community Cards"))
        
        # Players table with all cards visible
        players_table = Table(title="All Players (Admin View)")
        players_table.add_column("ID")
        players_table.add_column("Name")
        players_table.add_column("Chips")
        players_table.add_column("Bet")
        players_table.add_column("Cards")
        players_table.add_column("Status")
        
        active_player_id = self.game_state.get("active_player")
        dealer_position = self.game_state.get("dealer")
        small_blind_position = self.game_state.get("small_blind")
        big_blind_position = self.game_state.get("big_blind")
        
        for player in self.game_state.get("players", []):
            player_id = player.get("id")
            name = player.get("name", "")
            chips = player.get("chips", 0)
            current_bet = player.get("current_bet", 0)
            
            # Display player's cards
            cards_text = ""
            cards = player.get("cards", [])
            for card in cards:
                if card.endswith('H') or card.endswith('D'):
                    cards_text += f"[red]{card}[/red] "
                else:
                    cards_text += f"{card} "
            
            # Determine position and status
            position = ""
            if player_id == dealer_position:
                position += "D "
            if player_id == small_blind_position:
                position += "SB "
            if player_id == big_blind_position:
                position += "BB "
                
            status = position
            if not player.get("is_active", True):
                status += "[red]Folded[/red]"
            elif player.get("is_all_in", False):
                status += "[yellow]All-In[/yellow]"
            elif player_id == active_player_id:
                status += "[green]Active[/green]"
            
            # Highlight active player
            style = "bold" if player_id == active_player_id else ""
            
            players_table.add_row(
                f"{player_id}", name, f"${chips}", f"${current_bet}", 
                cards_text, status, style=style
            )
        
        body_layout["players"].update(players_table)
        
        # Debug information
        if self.debug_mode:
            debug_table = Table(title="Debug Information")
            debug_table.add_column("Property")
            debug_table.add_column("Value")
            
            # Add key game state properties for debugging
            debug_table.add_row("Game ID", self.game_id)
            debug_table.add_row("Phase", str(phase))
            debug_table.add_row("Dealer", str(dealer_position))
            debug_table.add_row("Small Blind", str(small_blind_position))
            debug_table.add_row("Big Blind", str(big_blind_position))
            debug_table.add_row("Active Player", str(active_player_id))
            debug_table.add_row("Pot Size", f"${pot}")
            debug_table.add_row("Current Bet", f"${current_bet}")
            
            body_layout["debug_info"].update(debug_table)
        
        # Command help panel
        commands_text = Text("Available Admin Commands:\n", style="bold")
        commands_text.append(Text("refresh    ", style="green"))
        commands_text.append(Text("- Refresh the game state\n"))
        commands_text.append(Text("debug      ", style="green"))
        commands_text.append(Text("- Toggle debug information\n"))
        commands_text.append(Text("status     ", style="green"))
        commands_text.append(Text("- Check connection status\n"))
        commands_text.append(Text("start      ", style="green"))
        commands_text.append(Text("- Start a new hand\n"))
        commands_text.append(Text("quit       ", style="green"))
        commands_text.append(Text("- Exit the admin view"))
        
        layout["commands"].update(Panel(commands_text, title="Admin Commands"))
        
        # Render the full layout
        console.print(layout)
    
    async def spectate_game(self):
        """Spectate the game and provide admin functionality"""
        # Add spectator/admin identifier to the WebSocket URI
        uri = f"ws://localhost:8000/ws/{self.game_id}/admin"
        
        try:
            async with websockets.connect(uri) as websocket:
                console.print("[green]Connected to game via WebSocket as spectator[/green]")
                
                # Initial game state
                self.get_admin_game_state()
                self.display_admin_view()
                
                # Command input task
                async def process_commands():
                    while self.running:
                        command = Prompt.ask("[bold]Admin command[/bold]")
                        
                        if command.lower() == "refresh":
                            self.get_admin_game_state()
                            self.display_admin_view()
                        
                        elif command.lower() == "debug":
                            self.debug_mode = not self.debug_mode
                            console.print(f"[yellow]Debug mode {'enabled' if self.debug_mode else 'disabled'}[/yellow]")
                            self.display_admin_view()
                            
                        elif command.lower() == "status":
                            try:
                                status_response = requests.get(f"{self.server_url}/games/{self.game_id}")
                                if status_response.status_code == 200:
                                    console.print("[green]Server connection: OK[/green]")
                                    players_connected = sum(1 for player in self.game_state.get("players", []))
                                    console.print(f"[green]Players in game: {players_connected}[/green]")
                                else:
                                    console.print("[red]Server connection: Error[/red]")
                            except Exception as e:
                                console.print(f"[red]Server connection error: {str(e)}[/red]")
                        
                        elif command.lower() == "start":
                            try:
                                start_response = requests.post(f"{self.server_url}/games/{self.game_id}/start")
                                if start_response.status_code == 200:
                                    console.print("[green]New hand started successfully[/green]")
                                else:
                                    console.print(f"[red]Error starting new hand: {start_response.json().get('detail', 'Unknown error')}[/red]")
                            except Exception as e:
                                console.print(f"[red]Error starting new hand: {str(e)}[/red]")
                        
                        elif command.lower() == "quit":
                            console.print("[yellow]Exiting admin view...[/yellow]")
                            self.running = False
                            break
                        
                        else:
                            console.print("[red]Unknown command. Try: refresh, debug, status, start, quit[/red]")
                
                # WebSocket message reception task
                async def receive_updates():
                    while self.running:
                        try:
                            # Receive WebSocket message
                            message = await websocket.recv()
                            
                            # Update with admin view (which has more information)
                            self.get_admin_game_state()
                            self.display_admin_view()
                        except websockets.exceptions.ConnectionClosed:
                            console.print("[red]WebSocket connection closed[/red]")
                            break
                        except Exception as e:
                            console.print(f"[red]Error in WebSocket connection: {str(e)}[/red]")
                            # Try to reconnect or recover
                            await asyncio.sleep(2)
                
                # Run both tasks concurrently
                command_task = asyncio.create_task(process_commands())
                updates_task = asyncio.create_task(receive_updates())
                
                # Wait for either task to complete
                done, pending = await asyncio.wait(
                    [command_task, updates_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel the remaining task
                for task in pending:
                    task.cancel()
                
        except websockets.exceptions.ConnectionClosed:
            console.print("[red]WebSocket connection closed[/red]")
        except Exception as e:
            console.print(f"[red]Error in admin client: {str(e)}[/red]")

async def main():
    parser = argparse.ArgumentParser(description="Poker Game Admin Client")
    parser.add_argument("game_id", help="ID of the game to spectate")
    parser.add_argument("--server", default=DEFAULT_SERVER_URL, help="Server URL")
    parser.add_argument("--admin-key", default=DEFAULT_ADMIN_KEY, help="Admin authentication key")
    
    args = parser.parse_args()
    
    admin_client = PokerAdminClient(server_url=args.server, admin_key=args.admin_key)
    admin_client.game_id = args.game_id
    
    # Get initial game state to ensure the game exists
    state = admin_client.get_admin_game_state()
    if state is None:
        console.print("[red]Could not access game. Check the Game ID and admin key.[/red]")
        return
    
    admin_client.display_admin_view()
    await admin_client.spectate_game()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[yellow]Exiting Admin Client...[/yellow]")
        sys.exit(0) 