import socket
import json
import pygame
import threading
import sys
import time


class PongClient:
    def __init__(self, server_ip, server_port=6000):
        # Initialize pygame
        pygame.init()

        # Game window dimensions - full width for reference, but we'll only show half
        self.total_width = 1920*2
        self.height = 1200
        self.width = self.total_width // 2  # Each client shows half the width

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Pong Client - Split Screen')

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
        self.ball_x = self.total_width // 2
        self.ball_y = self.height // 2
        self.score1 = 0
        self.score2 = 0
        self.running = False

        # Font for displaying score
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 24)

        # Create socket and connect to server
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((server_ip, server_port))
            print(f"Connected to server at {server_ip}:{server_port}")

            # Receive player number
            self.player_number = int(self.client.recv(1024).decode())
            print(f"You are Player {self.player_number}")

            # Set window title based on player number
            if self.player_number == 1:
                pygame.display.set_caption('Pong Client - Left Side')
            else:
                pygame.display.set_caption('Pong Client - Right Side')

        except Exception as e:
            print(f"Failed to connect to server: {e}")
            pygame.quit()
            sys.exit()

        # Add controls for movement state
        self.moving_up = False
        self.moving_down = False
        self.last_movement_sent = 0

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

        # Frame rate control
        target_fps = 60

        while running:
            frame_start_time = time.time()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.moving_up = True
                    elif event.key == pygame.K_DOWN:
                        self.moving_down = True
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        self.moving_up = False
                    elif event.key == pygame.K_DOWN:
                        self.moving_down = False

            # Handle continuous movement based on key state
            current_time = time.time()
            if current_time - self.last_movement_sent > 0.02:  # Send movement command at most 50 times per second
                if self.moving_up:
                    self.client.send("up".encode())
                    self.last_movement_sent = current_time
                elif self.moving_down:
                    self.client.send("down".encode())
                    self.last_movement_sent = current_time

            # Draw everything
            self.screen.fill(self.BLACK)

            # Calculate x offset based on player number
            x_offset = 0 if self.player_number == 1 else self.width

            # Draw only what should be visible on this half
            if self.player_number == 1:  # Left side
                # Draw left paddle (always visible for player 1)
                pygame.draw.rect(self.screen, self.WHITE,
                                 [0, self.paddle1_pos - self.paddle_height // 2,
                                  self.paddle_width, self.paddle_height])

                # Draw ball only if it's on the left half
                if self.ball_x < self.width:
                    pygame.draw.rect(self.screen, self.WHITE,
                                     [self.ball_x, self.ball_y - self.ball_size // 2,
                                      self.ball_size, self.ball_size])

                # Draw an arrow pointing right if ball is on the other side
                elif self.running:
                    pygame.draw.polygon(self.screen, self.WHITE, [
                        (self.width - 30, self.height // 2),
                        (self.width - 10, self.height // 2 - 10),
                        (self.width - 10, self.height // 2 + 10)
                    ])

            else:  # Right side (player 2)
                # Draw right paddle (always visible for player 2)
                pygame.draw.rect(self.screen, self.WHITE,
                                 [self.width - self.paddle_width,
                                  self.paddle2_pos - self.paddle_height // 2,
                                  self.paddle_width, self.paddle_height])

                # Draw ball only if it's on the right half
                if self.ball_x >= self.width:
                    pygame.draw.rect(self.screen, self.WHITE,
                                     [self.ball_x - x_offset, self.ball_y - self.ball_size // 2,
                                      self.ball_size, self.ball_size])

                # Draw an arrow pointing left if ball is on the other side
                elif self.running:
                    pygame.draw.polygon(self.screen, self.WHITE, [
                        (30, self.height // 2),
                        (10, self.height // 2 - 10),
                        (10, self.height // 2 + 10)
                    ])

            # Draw scores at the top
            score_display = f"{self.score1} - {self.score2}"
            score_text = self.small_font.render(score_display, True, self.WHITE)
            self.screen.blit(score_text, (self.width // 2 - score_text.get_width() // 2, 10))

            # Draw waiting message if not enough players
            if not self.running:
                font = pygame.font.Font(None, 36)
                waiting_text = font.render("Waiting for both players...", True, self.WHITE)
                self.screen.blit(waiting_text,
                                 (self.width // 2 - waiting_text.get_width() // 2,
                                  self.height // 2))

            # Display player number
            player_text = self.small_font.render(f"Player {self.player_number}", True, self.WHITE)
            self.screen.blit(player_text, (10, self.height - 30))

            # Display FPS
            fps = clock.get_fps()
            fps_text = self.small_font.render(f"FPS: {fps:.1f}", True, self.WHITE)
            self.screen.blit(fps_text, (self.width - fps_text.get_width() - 10, self.height - 30))

            # Update display
            pygame.display.flip()

            # Strict frame timing for smooth animation
            frame_time = time.time() - frame_start_time
            remaining_time = max(0, (1.0 / target_fps) - frame_time)
            if remaining_time > 0:
                time.sleep(remaining_time)

            # Update clock
            clock.tick(target_fps)

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
