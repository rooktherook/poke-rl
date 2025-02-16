from functools import cached_property

import numpy as np
from pyboy.utils import WindowEvent

from pyboy_environment.environments.pokemon.pokemon_environment import (
    PokemonEnvironment,
)
from pyboy_environment.environments.pokemon import pokemon_constants as pkc


class PokemonBrock(PokemonEnvironment):
    def __init__(
        self,
        act_freq: int,
        emulation_speed: int = 0,
        headless: bool = False,
    ) -> None:

        valid_actions: list[WindowEvent] = [
            WindowEvent.PRESS_ARROW_DOWN,
            WindowEvent.PRESS_ARROW_LEFT,
            WindowEvent.PRESS_ARROW_RIGHT,
            WindowEvent.PRESS_ARROW_UP,
            WindowEvent.PRESS_BUTTON_A,
            WindowEvent.PRESS_BUTTON_B,
            # WindowEvent.PRESS_BUTTON_START,
        ]

        release_button: list[WindowEvent] = [
            WindowEvent.RELEASE_ARROW_DOWN,
            WindowEvent.RELEASE_ARROW_LEFT,
            WindowEvent.RELEASE_ARROW_RIGHT,
            WindowEvent.RELEASE_ARROW_UP,
            WindowEvent.RELEASE_BUTTON_A,
            WindowEvent.RELEASE_BUTTON_B,
            # WindowEvent.RELEASE_BUTTON_START,
        ]


        self.visited_locations = {}

        super().__init__(
            act_freq=act_freq,
            task="brock",
            init_name="has_pokedex.state",
            emulation_speed=emulation_speed,
            valid_actions=valid_actions,
            release_button=release_button,
            headless=headless,
        )
        
    def _get_state(self) -> np.ndarray:
        # Implement your state retrieval logic here
        game_stats = self._generate_game_stats()
        state = [game_stats["badges"]]
        
        state.append(game_stats["location"]["x"])
        state.append(game_stats["location"]["y"])
        state.append(game_stats["location"]["map_id"])
        
        return state

    def _calculate_reward(self, new_state: dict) -> float:
        # Implement your reward calculation logic here
        reward = -1
        
        reward += self._explore_reward(new_state)
        reward += self._battle_reward(new_state)
        
        return reward

    def _battle_reward(self, new_state: dict[str, any]) -> int:
        if (new_state["battle_type"] != 0 and self.prior_game_stats["battle_type"] == 0):
                return 200
        return 0
        

    def _explore_reward(self, new_state: dict):
        reward = 0
        
        
        current_loc = new_state["location"]
        map_id = current_loc["map_id"]
        current_x = current_loc["x"]
        current_y = current_loc["y"]

        if map_id not in self.visited_locations:
            self.visited_locations[map_id] = set()  # Initialize a set for this map_id

        # Check if the current (x, y) location has been visited within this map
        current_loc_tuple = (current_x, current_y)
        if current_loc_tuple not in self.visited_locations[map_id]:
            # Reward for visiting a new (x, y) location within this map
            reward += 10  # Assign a reward for discovering a new location

            # Add the location to the visited set for the current map
            self.visited_locations[map_id].add(current_loc_tuple)
            # print(f"New location visited in map {map_id}: {current_loc_tuple}")

        # wiggle
        if new_state["location"]["x"] != self.prior_game_stats["location"]["x"]:
            reward += int(1)
        
        if new_state["location"]["y"] < self.prior_game_stats["location"]["y"]:
            reward += int(1)


        return reward
        
    def _reset_vars(self) -> None:
        self.visited_locations.clear()
        return


    def _check_if_done(self, game_stats: dict[str, any]) -> bool:
        # Setting done to true if agent beats first gym (temporary)
        return game_stats["badges"] > self.prior_game_stats["badges"]

    def _check_if_truncated(self, game_stats: dict) -> bool:
        # Implement your truncation check logic here

        # Maybe if we run out of pokeballs...? or a max step count
        
        if self.steps >= 1000:
            self._reset_vars()

            return True
        return False

