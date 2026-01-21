class PlayerStats:
    def __init__(self):
        self.hp = 100
        self.mp = 50
        self.sp = 20

def display_stats():
    player = PlayerStats()
    print(f"HP: {player.hp}, MP: {player.mp}, SP: {player.sp}")

if __name__ == "__main__":
    display_stats()