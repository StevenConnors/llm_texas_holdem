#!/bin/bash

# Set terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Texas Hold'em Poker Demo ===${NC}"
echo "This script will simulate a 3-player poker game"
echo

# Start the server in the background with output redirection
echo -e "${YELLOW}Starting the poker server...${NC}"
python3 server.py > server_log.txt 2>&1 &
SERVER_PID=$!
echo -e "${GREEN}Server started with PID: $SERVER_PID${NC}"

# Give the server time to start
echo "Waiting for server to start..."
sleep 3
echo "Attempting to continue..."

# Create a new game
echo -e "${YELLOW}Creating a new poker game...${NC}"
GAME_INFO=$(python3 client.py create --small-blind 5 --big-blind 10)
echo "$GAME_INFO"

# Extract the game ID using regex
if [[ $GAME_INFO =~ Created\ game\ with\ ID:\ ([a-zA-Z0-9-]+) ]]; then
    GAME_ID="${BASH_REMATCH[1]}"
    echo -e "${GREEN}Extracted Game ID: $GAME_ID${NC}"
else
    echo -e "${RED}Failed to extract Game ID. Exiting.${NC}"
    echo -e "${YELLOW}Client command output: ${GAME_INFO}${NC}"
    kill $SERVER_PID
    exit 1
fi

# Open separate terminals for each player plus admin view
# For macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Opening terminals for players on macOS..."
    # Player 1
    osascript -e "tell application \"Terminal\" to do script \"cd $(pwd) && python3 client.py join $GAME_ID --name \\\"Player1\\\" --chips 1000\""
    sleep 1
    
    # Player 2
    osascript -e "tell application \"Terminal\" to do script \"cd $(pwd) && python3 client.py join $GAME_ID --name \\\"Player2\\\" --chips 1000\""
    sleep 1
    
    # Player 3
    osascript -e "tell application \"Terminal\" to do script \"cd $(pwd) && python3 client.py join $GAME_ID --name \\\"Player3\\\" --chips 1000\""
    sleep 1
    
    # Admin/Spectator view
    osascript -e "tell application \"Terminal\" to do script \"cd $(pwd) && python3 admin_client.py $GAME_ID\""

# For Linux/Ubuntu and other X11 systems
elif [ -x "$(command -v xterm)" ]; then
    # Player 1
    xterm -e "cd $(pwd) && python3 client.py join $GAME_ID --name \"Player1\" --chips 1000; bash" &
    sleep 1
    
    # Player 2
    xterm -e "cd $(pwd) && python3 client.py join $GAME_ID --name \"Player2\" --chips 1000; bash" &
    sleep 1
    
    # Player 3
    xterm -e "cd $(pwd) && python3 client.py join $GAME_ID --name \"Player3\" --chips 1000; bash" &
    sleep 1
    
    # Admin/Spectator view
    xterm -e "cd $(pwd) && python3 admin_client.py $GAME_ID; bash" &

# Windows PowerShell (via WSL or Git Bash)
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Player 1
    powershell.exe -Command "Start-Process cmd -ArgumentList '/c cd $(pwd) && python3 client.py join $GAME_ID --name \"Player1\" --chips 1000 && pause'"
    sleep 1
    
    # Player 2
    powershell.exe -Command "Start-Process cmd -ArgumentList '/c cd $(pwd) && python3 client.py join $GAME_ID --name \"Player2\" --chips 1000 && pause'"
    sleep 1
    
    # Player 3
    powershell.exe -Command "Start-Process cmd -ArgumentList '/c cd $(pwd) && python3 client.py join $GAME_ID --name \"Player3\" --chips 1000 && pause'"
    sleep 1
    
    # Admin/Spectator view
    powershell.exe -Command "Start-Process cmd -ArgumentList '/c cd $(pwd) && python3 admin_client.py $GAME_ID && pause'"
else
    echo -e "${RED}Your operating system is not directly supported by this script.${NC}"
    echo -e "${YELLOW}Please manually open 4 terminal windows and run:${NC}"
    echo "1. python3 client.py join $GAME_ID --name \"Player1\" --chips 1000"
    echo "2. python3 client.py join $GAME_ID --name \"Player2\" --chips 1000"
    echo "3. python3 client.py join $GAME_ID --name \"Player3\" --chips 1000"
    echo "4. python3 admin_client.py $GAME_ID"
fi

echo
echo -e "${GREEN}Game setup complete! Game ID: $GAME_ID${NC}"
echo "Players should now start the game by typing 'y' when prompted to start a new hand"
echo "Press Ctrl+C to stop the server when finished playing"

# Create a background monitoring loop instead of waiting
echo "Server is running in the background. Press Ctrl+C to stop."
disown $SERVER_PID 