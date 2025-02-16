from functools import cached_property
import numpy as np
from datetime import datetime

from pyboy.utils import WindowEvent
from pyboy_environment.environments.pokemon.pokemon_environment import (
    PokemonEnvironment,
)
from pyboy_environment.environments.pokemon import pokemon_constants as pkc
import keyboard
import time


do_nothing_base = -1
start_battle_multiplier = 200
enemy_health_loss_multiplier = 20
xp_multiplier = 1
level_up_multiplier = 100


class PokemonTest(PokemonEnvironment):
    def __init__(
        self,
        act_freq: int,
        emulation_speed: int = 1,
        headless: bool = False,
    ) -> None:

        valid_actions: list[WindowEvent] = [
            # WindowEvent.PRESS_ARROW_DOWN,
            # WindowEvent.PRESS_ARROW_LEFT,
            # WindowEvent.PRESS_ARROW_RIGHT,
            # WindowEvent.PRESS_ARROW_UP,
            # WindowEvent.PRESS_BUTTON_A,
            # WindowEvent.PRESS_BUTTON_B,
            WindowEvent.PRESS_BUTTON_START,
        ]

        release_button: list[WindowEvent] = [
            # WindowEvent.RELEASE_ARROW_DOWN,
            # WindowEvent.RELEASE_ARROW_LEFT,
            # WindowEvent.RELEASE_ARROW_RIGHT,
            # WindowEvent.RELEASE_ARROW_UP,
            # WindowEvent.RELEASE_BUTTON_A,
            # WindowEvent.RELEASE_BUTTON_B,
            WindowEvent.RELEASE_BUTTON_START,
        ]
        super().__init__(
            act_freq=4,
            task="test",
            init_name="has_pokedex.state",
            emulation_speed=4,
            valid_actions=valid_actions,
            release_button=release_button,
            headless=False,
        )

        self.firstFight = False

        self.episode_max_steps = 1000
        self.current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.prior_game_stats = self._generate_game_stats()
        self.currentGameArea = self.game_area()
        print("fuk", len(self.currentGameArea) * len(self.currentGameArea[0]))
        self.previousGameAreas = [self.currentGameArea]

        # Location tracker
        self.loc_tracker = {}

    def capture_input(self):
        key_mapping = {
            "up": WindowEvent.PRESS_ARROW_UP,
            "down": WindowEvent.PRESS_ARROW_DOWN,
            "left": WindowEvent.PRESS_ARROW_LEFT,
            "right": WindowEvent.PRESS_ARROW_RIGHT,
            "a": WindowEvent.PRESS_BUTTON_A,
            "b": WindowEvent.PRESS_BUTTON_B,
            "s": WindowEvent.PRESS_BUTTON_START,
        }

        for key, action in key_mapping.items():
            if keyboard.is_pressed(key):
                return action

        return None

    def _get_state(self) -> np.ndarray:
        # Implement your state retrieval logic here
        game_stats = self._generate_game_stats()
        return [game_stats["badges"]]

    def _start_battle_reward(self, new_state: dict[str, any]) -> int:

        if self.firstFight == False:
            if (
                new_state["battle_type"] != 0
                and self.prior_game_stats["battle_type"] == 0
            ):
                self.firstFight = True
                return 1
        return 0

    def _enemy_health_decrease_reward(self, new_state: dict[str, any]) -> int:
        if new_state["battle_type"] != 0 and self.prior_game_stats["battle_type"] != 0:
            health_diff = (
                self.prior_game_stats["enemy_pokemon_health"]
                - new_state["enemy_pokemon_health"]
            )
            if health_diff > 0:
                print("Enemy Damaged.")
            return health_diff
        return 0

    def _explore_reward(self, new_state: dict):
        self.currentGameArea = self.game_area()
        count = 0
        reward = 25
        startLen = len(self.previousGameAreas)

        current_x = new_state["location"]["x"]
        current_y = new_state["location"]["y"]
        curr_loc = new_state["location"]["map_id"]

        for z in range(len(self.previousGameAreas)):
            count = 0
            for i in range(len(self.currentGameArea)):
                for j in range(len(self.currentGameArea[0])):
                    if self.currentGameArea[i][j] == self.previousGameAreas[z][i][j]:
                        count += 1

            if count > 75:
                reward = 0

        if reward == 25:
            self.previousGameAreas.append(self.currentGameArea)

        if startLen < len(self.previousGameAreas):
            print(len(self.previousGameAreas))

        if new_state["location"]["x"] != self.prior_game_stats["location"]["x"]:
            reward += int(((startLen + 1) / 20) + 1)

        if new_state["location"]["y"] < self.prior_game_stats["location"]["y"]:
            reward += int(((startLen + 1) / 10) + 1)

        print(f"Loc Check:{curr_loc}")
        return reward

    def _up_reward(self, new_state: dict):
        reward = 0
        current_loc = new_state["location"]
        map_id = current_loc["map_id"]
        current_y = current_loc["y"]

        # Pewter City
        if map_id == 3:
            return reward

        # Oak's lab force down.
        if map_id == 40:
            if map_id in self.loc_tracker:
                if current_y > self.loc_tracker[map_id]:
                    reward = 10
                    self.loc_tracker[map_id] = current_y
                else:
                    self.loc_tracker[map_id] = current_y

        if map_id in self.loc_tracker:
            if current_y < self.loc_tracker[map_id]:

                reward = 10
                self.loc_tracker[map_id] = current_y
        else:
            self.loc_tracker[map_id] = current_y

        print(f"current loc {current_loc}")
        print(f"Current Reward {reward} Location Tracker {self.loc_tracker}")

        return reward

    def _calculate_reward(self, new_state: dict) -> float:
        reward = -1
        reward += self._up_reward(new_state)
        reward += self._explore_reward(new_state)
        reward += self._start_battle_reward(new_state) * start_battle_multiplier
        reward += (
            self._enemy_health_decrease_reward(new_state) * enemy_health_loss_multiplier
        )

        return reward

    def _check_if_done(self, game_stats: dict[str, any]) -> bool:
        return game_stats["badges"] > self.prior_game_stats["badges"]

    def _check_if_truncated(self, game_stats: dict) -> bool:
        return self.steps >= 10000


def main():
    env = PokemonTest(act_freq=10, emulation_speed=1, headless=False)
    steps = 0

    while True:
        steps += 1
        action = env.capture_input()
        if action is not None:
            [state, reward, done, truncated] = env.step(action)
            print(
                f"\rAction: {action}, Steps: {steps}, Reward: {reward}, Done/Trunc: {done or truncated}\r"
            )
        time.sleep(0.1)


if __name__ == "__main__":
    main()
