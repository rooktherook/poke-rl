"""
Do NOT edit this file as it runs the evaluation methodology for the Trained Pokemon agents.
"""

import argparse
import json
import logging
from pathlib import Path

import cares_reinforcement_learning.util.configurations as configurations
from cares_reinforcement_learning.util.network_factory import NetworkFactory
from pyboy_environment.environments.pokemon.tasks.brock import PokemonBrock

logging.basicConfig(level=logging.INFO)


def get_args():
    parse_args = argparse.ArgumentParser()

    parse_args.add_argument("--upi", type=str, required=True)

    parse_args.add_argument("-p", "--model_path", type=str, required=True)

    parse_args.add_argument("-n", "--model_name", type=str, required=True)

    parse_args.add_argument("-r", "--results_path", type=str, required=True)

    return parse_args.parse_args()


def run_agent(env, agent, num_episodes, results_path):

    state = env.reset()
    for step in range(0, num_episodes):
        if step % 100 == 0:
            logging.info(f"Step: {step}")
        action = agent.select_action_from_policy(state, evaluation=True)
        next_state, reward, done, _ = env.step(action)
        state = next_state
        if done:
            
            ep_stats = env._generate_game_stats()
            
            ep_stats["actions"] = step

            logging.info(f"Episode-{step} Stats: {ep_stats}")

            with open(f"{results_path}/Episode-{step}results.json", "w", encoding="utf-8") as file:
                json.dump(ep_stats, file)
            
            state = env.reset()

    final_stats = env._generate_game_stats()

    final_stats["actions"] = step

    logging.info(f"Final Stats: {final_stats}")

    with open(f"{results_path}/results.json", "w", encoding="utf-8") as file:
        json.dump(final_stats, file)


def run(results_path, model_file_path, model_file_name):
    algorithm = model_file_name.split("-")[0]

    class_ = getattr(configurations, f"{algorithm}Config")
    algorithm_config = class_()

    network_factory = NetworkFactory()

    brock_task = PokemonBrock(act_freq=24, headless=True)

    agent = network_factory.create_network(
        brock_task.observation_space, brock_task.action_num, algorithm_config
    )

    agent.load_models(model_file_path, model_file_name)

    run_agent(brock_task, agent, 10000, results_path)


def main():
    args = get_args()

    run(args.results_path, args.model_path, args.model_name)


if __name__ == "__main__":
    main()
