import socket
import threading
import time
import json
import random


class PongGame:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.paddle_height = 100
        self.paddle_width = 15
        self.ball_size = 10

        # Paddles position [y position]
        self.paddle1_pos = self.height // 2
        self.paddle2_pos = self.height // 2

        # Ball position and velocity
        self.ball_x = self.width // 2
        self.ball_y = self.height // 2
        self.ball_speed_x = 5 * random.choice([-1, 1])
        self.ball_speed_y = 5 * random.choice([-1, 1])

        # Score
        self.score1 = 0
        self.score2 = 0

        # Game state
        self.running = False
        self.players_connected = 0

    def update(self):
        if not self.running:
            return

        # Move the ball
        self.ball_x += self.ball_speed_x
        self.ball_y += self.ball_speed_y

        # Ball collision with top and bottom
        if self.ball_y <= 0 or self.ball_y >= self.height:
            self.ball_speed_y *= -1

        # Ball collision with paddles
        if self.ball_x <= self.paddle_width and self.paddle1_pos - self.paddle_height // 2 <= self.ball_y <= self.paddle1_pos + self.paddle_height // 2:
            self.ball_speed_x *= -1

        if self.ball_x >= self.width - self.paddle_width and self.paddle2_pos - self.paddle_height // 2 <= self.ball_y <= self.paddle2_pos + self.paddle_height // 2:
            self.ball_speed_x *= -1

        # Score points
        if self.ball_x < 0:
            self.score2 += 1
            self.reset_ball()

        if self.ball_x > self.width:
            self.score1 += 1
            self.reset_ball()

    def reset_ball(self):
        self.ball_x = self.width // 2
        self.ball_y = self.height // 2
        self.ball_speed_x = 5 * random.choice([-1, 1])
        self.ball_speed_y = 5 * random.choice([-1, 1])

    def move_paddle1(self, direction):
        if direction == "up":
            self.paddle1_pos = max(self.paddle_height // 2, self.paddle1_pos - 10)
        elif direction == "down":
            self.paddle1_pos = min(self.height - self.paddle_height // 2, self.paddle1_pos + 10)

    def move_paddle2(self, direction):
        if direction == "up":
            self.paddle2_pos = max(self.paddle_height // 2, self.paddle2_pos - 10)
        elif direction == "down":
            self.paddle2_pos = min(self.height - self.paddle_height // 2, self.paddle2_pos + 10)

    def get_state(self):
        return {
            "paddle1": self.paddle1_pos,
            "paddle2": self.paddle2_pos,
            "ball_x": self.ball_x,
            "ball_y": self.ball_y,
            "score1": self.score1,
            "score2": self.score2,
            "running": self.running
        }


def handle_client(client_socket, player_number, game):
    """Handle communication with a client"""
    try:
        # Send player number
        client_socket.send(str(player_number).encode())

        # If we have both players, start the game
        if game.players_connected == 2:
            game.running = True

        while True:
            # Try to receive data
            try:
                data = client_socket.recv(1024).decode().strip()
                if not data:
                    break

                # Handle commands from client
                if data == "up":
                    if player_number == 1:
                        game.move_paddle1("up")
                    else:
                        game.move_paddle2("up")
                elif data == "down":
                    if player_number == 1:
                        game.move_paddle1("down")
                    else:
                        game.move_paddle2("down")

                # Send game state to client
                game_state = json.dumps(game.get_state())
                client_socket.send(game_state.encode())

            except socket.timeout:
                # Send game state periodically
                game_state = json.dumps(game.get_state())
                client_socket.send(game_state.encode())
    except:
        print(f"Player {player_number} disconnected")
    finally:
        client_socket.close()
        game.players_connected -= 1
        if game.players_connected < 2:
            game.running = False


def game_loop(game):
    """Update game state in a loop"""
    while True:
        game.update()
        time.sleep(0.03)  # ~30 FPS


def start_master(port=6000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen()

    game = PongGame()

    # Start game update thread
    game_thread = threading.Thread(target=game_loop, args=(game,))
    game_thread.daemon = True
    game_thread.start()

    print(f"Master is waiting for clients to connect on port {port}")

    while True:
        client_socket, client_address = server.accept()
        client_socket.settimeout(0.1)  # Set a timeout for non-blocking receives

        # Max two players
        if game.players_connected < 2:
            game.players_connected += 1
            player_number = game.players_connected
            print(f"Player {player_number} ({client_address}) connected")

            client_thread = threading.Thread(target=handle_client, args=(client_socket, player_number, game))
            client_thread.daemon = True
            client_thread.start()
        else:
            print(f"Rejected connection from {client_address} - game is full")
            client_socket.close()


if __name__ == "__main__":
    start_master()
