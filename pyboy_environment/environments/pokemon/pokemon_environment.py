import random
from functools import cached_property
from abc import abstractmethod

import numpy as np
from pyboy.utils import WindowEvent

from pyboy_environment.environments.pyboy_environment import PyboyEnvironment
from pyboy_environment.environments.pokemon import pokemon_constants as pkc


class PokemonEnvironment(PyboyEnvironment):
    def __init__(
        self,
        act_freq: int,
        valid_actions: list[WindowEvent],
        release_button: list[WindowEvent],
        task: str,
        emulation_speed: int,
        headless: bool = False,
        init_name: str = "has_pokedex.state",
    ) -> None:
        super().__init__(
            task=task,
            rom_name="PokemonRed.gb",
            domain="pokemon",
            init_state_file_name=init_name,
            act_freq=act_freq,
            emulation_speed=emulation_speed,
            valid_actions=valid_actions,
            release_button=release_button,
            headless=headless,
        )

    @cached_property
    def min_action_value(self) -> float:
        return 0

    @cached_property
    def max_action_value(self) -> float:
        return 1

    @cached_property
    def observation_space(self) -> int:
        return len(self._get_state())

    @cached_property
    def action_num(self) -> int:
        # Single button input at each step
        # No requirement for multiple buttons to be pressed at once like Mario
        return 1

    def sample_action(self) -> int:
        return random.uniform(0, 1)

    def _get_state(self) -> np.ndarray:
        # Implement your state retrieval logic here - compact state based representation
        raise NotImplementedError(
            "Non-image based observation space not implemented - override this method to implement it"
        )

    def _run_action_on_emulator(self, action_array: np.ndarray) -> None:
        action = action_array[0]
        action = min(action, 0.99)

        # Continuous Action is a float between 0 - 1 from Value based methods
        # We need to convert this to an action that the emulator can understand
        bins = np.linspace(0, 1, len(self.valid_actions) + 1)
        button = np.digitize(action, bins) - 1

        # Push the button for a few frames
        self.pyboy.send_input(self.valid_actions[button])

        for _ in range(self.act_freq):
            self.pyboy.tick()

        # Release the button
        self.pyboy.send_input(self.release_button[button])

    def _generate_game_stats(self) -> dict[str, any]:
        return {
            "location": self._get_location(),
            "party_size": self._get_party_size(),
            "ids": self._read_party_id(),
            "pokemon": [pkc.get_pokemon(id) for id in self._read_party_id()],
            "levels": self._read_party_level(),
            "type_id": self._read_party_type(),
            "type": [pkc.get_type(id) for id in self._read_party_type()],
            "hp": self._read_party_hp(),
            "xp": self._read_party_xp(),
            "status": self._read_party_status(),
            "badges": self._get_badge_count(),
            "caught_pokemon": self._read_caught_pokemon_count(),
            "seen_pokemon": self._read_seen_pokemon_count(),
            "money": self._read_money(),
            "events": self._read_events(),
            # Check if entering batrtle. 
            "battle_type": self._read_battle_type(),
            "enemy_pokemon_health": self._read_enemy_pokemon_health(),
            "current_pokemon_health": self._read_current_pokemon_health(),
            "items": self._read_items_(),
            "max_opponent_level": self._read_max_opponent_level(),
        }

    @abstractmethod
    def _calculate_reward(self, new_state: dict) -> float:
        # Implement your reward calculation logic here
        pass

    def _check_if_done(self, game_stats: dict[str, any]) -> bool:
        # Setting done to true if agent beats first gym (temporary)
        return game_stats["badges"] > 0

    def _check_if_truncated(self, game_stats: dict) -> bool:
        # Implement your truncation check logic here
        return False

    def _get_location(self) -> dict[str, any]:
        x_pos = self._read_m(0xD362)
        y_pos = self._read_m(0xD361)
        map_n = self._read_m(0xD35E)

        return {
            "x": x_pos,
            "y": y_pos,
            "map_id": map_n,
            "map": pkc.get_map_location(map_n),
        }

    def _get_party_size(self) -> int:
        return self._read_m(0xD163)

    def _get_badge_count(self) -> int:
        return self._bit_count(self._read_m(0xD356))

    def _is_grass_tile(self) -> bool:
        grass_tile_index = self._read_m(0xD535)
        player_sprite_status = self._read_m(0xC207)  # Assuming player is sprite 0
        return player_sprite_status == 0x80

    # in grass reward function that returns reward
    def _grass_reward(self, new_state: dict[str, any]) -> int:
        if self._is_grass_tile():
            return 1
        return 0

    def _read_party_id(self) -> list[int]:
        # https://github.com/pret/pokered/blob/91dc3c9f9c8fd529bb6e8307b58b96efa0bec67e/constants/pokemon_constants.asm
        return [
            self._read_m(addr)
            for addr in [0xD164, 0xD165, 0xD166, 0xD167, 0xD168, 0xD169]
        ]

    def _read_party_type(self) -> list[int]:
        # https://github.com/pret/pokered/blob/91dc3c9f9c8fd529bb6e8307b58b96efa0bec67e/constants/type_constants.asm
        return [
            self._read_m(addr)
            for addr in [
                0xD170,
                0xD171,
                0xD19C,
                0xD19D,
                0xD1C8,
                0xD1C9,
                0xD1F4,
                0xD1F5,
                0xD220,
                0xD221,
                0xD24C,
                0xD24D,
            ]
        ]

    def _read_party_level(self) -> list[int]:
        return [
            self._read_m(addr)
            for addr in [0xD18C, 0xD1B8, 0xD1E4, 0xD210, 0xD23C, 0xD268]
        ]

    def _read_party_status(self) -> list[int]:
        # https://github.com/pret/pokered/blob/91dc3c9f9c8fd529bb6e8307b58b96efa0bec67e/constants/status_constants.asm
        return [
            self._read_m(addr)
            for addr in [0xD16F, 0xD19B, 0xD1C7, 0xD1F3, 0xD21F, 0xD24B]
        ]

    def _read_party_hp(self) -> dict[str, list[int]]:
        hp = [
            self._read_hp(addr)
            for addr in [0xD16C, 0xD198, 0xD1C4, 0xD1F0, 0xD21C, 0xD248]
        ]
        max_hp = [
            self._read_hp(addr)
            for addr in [0xD18D, 0xD1B9, 0xD1E5, 0xD211, 0xD23D, 0xD269]
        ]
        return {"current": hp, "max": max_hp}

    def _read_party_xp(self) -> list[int]:
        return [
            self._read_triple(addr)
            for addr in [0xD179, 0xD1A5, 0xD1D1, 0xD1FD, 0xD229, 0xD255]
        ]

    def _read_hp(self, start: int) -> int:
        return 256 * self._read_m(start) + self._read_m(start + 1)

    def _read_caught_pokemon_count(self) -> int:
        return sum(
            list(self._bit_count(self._read_m(i)) for i in range(0xD2F7, 0xD30A))
        )

    def _read_seen_pokemon_count(self) -> int:
        return sum(
            list(self._bit_count(self._read_m(i)) for i in range(0xD30A, 0xD31D))
        )

    def _read_money(self) -> int:
        return (
            100 * 100 * self._read_bcd(self._read_m(0xD347))
            + 100 * self._read_bcd(self._read_m(0xD348))
            + self._read_bcd(self._read_m(0xD349))
        )

    def _read_events(self) -> list[int]:
        event_flags_start = 0xD747
        event_flags_end = 0xD886
        # museum_ticket = (0xD754, 0)
        # base_event_flags = 13
        return [
            self._bit_count(self._read_m(i))
            for i in range(event_flags_start, event_flags_end)
        ]
    
    def _read_battle_type(self) -> int:
        return self._read_m(0xD057)  
    
    def _read_enemy_pokemon_health(self) -> int:
        return self._read_hp(0xCFE6)

    def _read_current_pokemon_health(self) -> int:
        return self._read_hp(0xD015)
    
    def _read_items_(self) -> dict:
        total_items = self._read_m(0xD31D)
        if (total_items == 0):
            return {}

        addr = 0xD31E
        items = {}

        for i in range(total_items):
            item_id = self._read_m(addr + 2 * i)
            item_count = self._read_m(addr + 2 * i + 1)
            items[item_id] = item_count

        return items

    def _read_max_opponent_level(self):
        return max([self._read_m(a) for a in 
                    [0xD8C5, 0xD8F1, 0xD91D, 0xD949, 0xD975, 0xD9A1]]) - 5
    def _get_screen_background_tilemap(self):
        ### SIMILAR TO CURRENT pyboy.game_wrapper()._game_area_np(), BUT ONLY FOR BACKGROUND TILEMAP, SO NPC ARE SKIPPED
        bsm = self.pyboy.botsupport_manager()
        ((scx, scy), (wx, wy)) = bsm.screen().tilemap_position()
        tilemap = np.array(bsm.tilemap_background()[:, :])
        return np.roll(np.roll(tilemap, -scy // 8, axis=0), -scx // 8, axis=1)[:18, :20]

    def _get_screen_walkable_matrix(self):
        walkable_tiles_indexes = []
        collision_ptr = self.pyboy.get_memory_value(0xD530) + (
            self.pyboy.get_memory_value(0xD531) << 8
        )
        tileset_type = self.pyboy.get_memory_value(0xFFD7)
        if tileset_type > 0:
            grass_tile_index = self.pyboy.get_memory_value(0xD535)
            if grass_tile_index != 0xFF:
                walkable_tiles_indexes.append(grass_tile_index + 0x100)
        for i in range(0x180):
            tile_index = self.pyboy.get_memory_value(collision_ptr + i)
            if tile_index == 0xFF:
                break
            else:
                walkable_tiles_indexes.append(tile_index + 0x100)
        screen_tiles = self._get_screen_background_tilemap()
        bottom_left_screen_tiles = screen_tiles[1 : 1 + screen_tiles.shape[0] : 2, ::2]
        walkable_matrix = np.isin(
            bottom_left_screen_tiles, walkable_tiles_indexes
        ).astype(np.uint8)
        return walkable_matrix

    def game_area_collision(self):
        shape = (20, 18)
        game_area_section = (0, 0) + shape
        width = game_area_section[2]
        height = game_area_section[3]

        game_area = np.ndarray(shape=(height, width), dtype=np.uint32)
        _collision = self._get_screen_walkable_matrix()
        for i in range(height // 2):
            for j in range(width // 2):
                game_area[i * 2][j * 2 : j * 2 + 2] = _collision[i][j]
                game_area[i * 2 + 1][j * 2 : j * 2 + 2] = _collision[i][j]
        return game_area

    # Note: These are all examples of rewards we can calculate based on the stats, you can implement and modify your own as you please

    def _caught_reward(self, new_state: dict[str, any]) -> int:
        return new_state["caught_pokemon"] - self.prior_game_stats["caught_pokemon"]

    def _seen_reward(self, new_state: dict[str, any]) -> int:
        return new_state["seen_pokemon"] - self.prior_game_stats["seen_pokemon"]

    def _health_reward(self, new_state: dict[str, any]) -> int:
        return sum(new_state["hp"]["current"]) - sum(
            self.prior_game_stats["hp"]["current"]
        )

    def _xp_reward(self, new_state: dict[str, any]) -> int:
        return sum(new_state["xp"]) - sum(self.prior_game_stats["xp"])

    def _levels_reward(self, new_state: dict[str, any]) -> int:
        return sum(new_state["levels"]) - sum(self.prior_game_stats["levels"])

    def _badges_reward(self, new_state: dict[str, any]) -> int:
        return new_state["badges"] - self.prior_game_stats["badges"]

    def _money_reward(self, new_state: dict[str, any]) -> int:
        return new_state["money"] - self.prior_game_stats["money"]

    def _event_reward(self, new_state: dict[str, any]) -> int:
        return sum(new_state["events"]) - sum(self.prior_game_stats["events"])
