import socket
import json
import pygame
import threading
import sys


class PongClient:
    def __init__(self, server_ip, server_port=6000):
        # Initialize pygame
        pygame.init()

        # Game window dimensions
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Pong Client')

        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)

        # Paddle dimensions
        self.paddle_width = 15
        self.paddle_height = 100

        # Ball dimensions
        self.ball_size = 10

        # Game state
        self.player_number = 0
        self.paddle1_pos = self.height // 2
        self.paddle2_pos = self.height // 2
        self.ball_x = self.width // 2
        self.ball_y = self.height // 2
        self.score1 = 0
        self.score2 = 0
        self.running = False

        # Font for displaying score
        self.font = pygame.font.Font(None, 74)

        # Create socket and connect to server
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((server_ip, server_port))
            print(f"Connected to server at {server_ip}:{server_port}")

            # Receive player number
            self.player_number = int(self.client.recv(1024).decode())
            print(f"You are Player {self.player_number}")

        except Exception as e:
            print(f"Failed to connect to server: {e}")
            pygame.quit()
            sys.exit()

    def receive_game_state(self):
        """Continuously receive game state from server"""
        while True:
            try:
                data = self.client.recv(1024).decode()
                if not data:
                    break

                game_state = json.loads(data)

                # Update local game state
                self.paddle1_pos = game_state["paddle1"]
                self.paddle2_pos = game_state["paddle2"]
                self.ball_x = game_state["ball_x"]
                self.ball_y = game_state["ball_y"]
                self.score1 = game_state["score1"]
                self.score2 = game_state["score2"]
                self.running = game_state["running"]

            except Exception as e:
                print(f"Error receiving game state: {e}")
                break

    def run(self):
        # Start thread to receive game state
        receive_thread = threading.Thread(target=self.receive_game_state)
        receive_thread.daemon = True
        receive_thread.start()

        # Main game loop
        clock = pygame.time.Clock()
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Handle key presses
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                self.client.send("up".encode())
            elif keys[pygame.K_DOWN]:
                self.client.send("down".encode())

            # Draw everything
            self.screen.fill(self.BLACK)

            # Draw middle line
            pygame.draw.aaline(self.screen, self.WHITE,
                               [self.width // 2, 0],
                               [self.width // 2, self.height])

            # Draw paddles
            pygame.draw.rect(self.screen, self.WHITE,
                             [0, self.paddle1_pos - self.paddle_height // 2,
                              self.paddle_width, self.paddle_height])
            pygame.draw.rect(self.screen, self.WHITE,
                             [self.width - self.paddle_width,
                              self.paddle2_pos - self.paddle_height // 2,
                              self.paddle_width, self.paddle_height])

            # Draw ball
            pygame.draw.rect(self.screen, self.WHITE,
                             [self.ball_x - self.ball_size // 2,
                              self.ball_y - self.ball_size // 2,
                              self.ball_size, self.ball_size])

            # Draw scores
            score_text = self.font.render(f"{self.score1} - {self.score2}", True, self.WHITE)
            self.screen.blit(score_text,
                             (self.width // 2 - score_text.get_width() // 2, 10))

            # Draw waiting message if not enough players
            if not self.running:
                font = pygame.font.Font(None, 36)
                waiting_text = font.render("Waiting for both players to connect...",
                                           True, self.WHITE)
                self.screen.blit(waiting_text,
                                 (self.width // 2 - waiting_text.get_width() // 2,
                                  self.height // 2))

            # Indicate which player you are
            player_font = pygame.font.Font(None, 24)
            player_text = player_font.render(f"You are Player {self.player_number}",
                                             True, self.WHITE)
            self.screen.blit(player_text, (10, 10))

            # Update display
            pygame.display.flip()

            # Cap the frame rate
            clock.tick(60)

        # Clean up
        pygame.quit()
        self.client.close()


if __name__ == "__main__":
    # Get server IP from command line or use default
    server_ip = "10.16.8.220"  # Default IP
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]

    # Create and run client
    client = PongClient(server_ip)
    client.run()
