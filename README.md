# Pokemon Agent


## Setup
Please use **python3.10** for this

### Install Required Packages
This assignment requires three key packages to operate - you'll need to install them in a specific order as laid out below. 

#### 0: CUDA Acceleration (Nvidia GPU only)
If you want to utilise the GPU with Pytorch install CUDA first - https://developer.nvidia.com/cuda-toolkit

#### 1: cares_reinforcement_learning
The cares_reinforcement_learning package provides implementations of modern Reinforcement Learning algorithms and utlities for doing research. This package contains the reinforcement learning algorithms and implementations you can leverage to learn to play Pokemon. Further details can be explored here: https://github.com/UoA-CARES/cares_reinforcement_learning

```
mkdir ~/poke
cd ~/poke
git clone https://github.com/UoA-CARES/cares_reinforcement_learning.git
cd cares_reinforcement_learning
pip3 install -r requirements.txt
pip3 install --editable .
```

#### 2: pokemon_agent (primary package)
This is the current package - it contains the requirements for implementing the Pokemon Environment for this project. All your work will be done in this specific package. This is explained in further details below. 

```
cd ~/poke
git clone (This package)
cd (This package)
pip3 install -r requirements.txt
pip3 install --editable .
```

#### 3: gymnasium_envrionments
We have created a standardised general purpose gym that wraps the most common simulated environments used in reinforcement learning into a single easy to use place. This package serves as an example of how to develop and setup new environments - perticularly for the robotic environments. This package utilises the algorithms implemented in the repository https://github.com/UoA-CARES/cares_reinforcement_learning/ and the Pokemon Environment you will implement here. Additional information can found here: https://github.com/UoA-CARES/gymnasium_envrionments

This package is how you will run the training agent and test your Pokemon Environment. 

```
cd ~/poke
git clone https://github.com/UoA-CARES/gymnasium_envrionments.git 
cd gymnasium_envrionments
pip3 install -r requirements.txt
```

### Download ROM
Download the Pokemon ROM from a source

We will then unzip and copy the downloaded files into a roms folder in the "~/cares_rl_configs" folder in the home directory.

```
mkdir ~/cares_rl_configs
cd ~/Downloads
unzip pokemon-*.zip
cp -r pokemon ~/cares_rl_configs
```

## Usage
This package provides the baseline code for the pyboy environments - you run these envrionments through gymnasium_envrionment.

`train.py` takes in hyperparameters that allow you to customise the training run enviromment – OpenAI or DMCS Environment - or RL algorithm. Use `python3 train.py -h` for help on what parameters are available for customisation.

An example is found below for running on an example of the openai environment with TD3 through console

```
cd gymnasium_envrionments/scripts
python train.py run --gym openai --task HalfCheetah-v4 TD3 --display 1
```

### Running Pokemon Task
To run the base Pokemon Environment that has a very simple implementation you need to run it through the ***gymnasium_envrionments*** package. The environments are not currently implemented as that is your job - but you will see the agent randomly exploring before trying to "learn" from a very limited reward function and action space. 

```
cd gymnasium_envrionments/scripts
python3 train.py run --gym pyboy --domain pokemon --task brock TD3
```

### Viewing Training Results
The results of training the agents is saved into this folder: ***~/cares_rl_logs/*** by default. The structure of the results is saved as below.

The saved trained models contain the weights of your trained agent and will be uploaded as per the instructions below for the competition. 

```
├─ALGORITHM/ALGORITHM-TASK-YY_MM_DD:HH:MM:SS/
├─ SEED
|  ├─ env_config.py
|  ├─ alg_config.py
|  ├─ train_config.py
|  ├─ data
|  |  ├─ train.csv
|  |  ├─ eval.csv
|  ├─ figures
|  |  ├─ eval.png
|  |  ├─ train.png
|  ├─ models
|  |  ├─ model.pht
|  |  ├─ CHECKPOINT_N.pht
|  |  ├─ ...
|  ├─ videos
|  |  ├─ STEP.mp4
|  |  ├─ ...
├─ SEED...
├─ ...
```

# Implementing your Pokemon Environment
Your Pokemon Environment will be fully implemented in ***pyboy_environment/environments/pokemon/tasks/brock.py***. The goal is to determine a suitable state representation for an agent to learn from, a suitable set of actions, and a suitable reward function to enable the agent to learn to complete the task of beating the first gym leader Brock. 

## Task Brock (brock.py)
You are free to modify and expand the class inside of ***pyboy_environment/environments/pokemon/tasks/brock.py*** and add additional features/functions required to implement your environment. This is not best coding practice but it makes the lecturers lives easier.

Brock.py contains one class as an example of how to implement this project - PokemonBrock.

### PokemonBrock
The PokemonBrock class represents the Pokemon game environment for the task of beating Brock that extends the generic PokemonEnvironment and inherits all of its functions. 

You can build upon this class all you want to implement your Task of beating Brock - this class enables you to read the game state, and define the actions the Pokemon Trainer can take.

The key requirements are implementing the class functions below:

```
def _get_state(self) -> np.ndarray:
    # Implement your state retrieval logic here
    game_stats = self._generate_game_stats()
    return [game_stats["badges"]]

def _calculate_reward(self, new_state: dict) -> float:
    # Implement your reward calculation logic here
    return new_state["badges"] - self.prior_game_stats["badges"]

def _check_if_done(self, game_stats: dict[str, any]) -> bool:
    # Setting done to true if agent beats first gym (temporary)
    return game_stats["badges"] > self.prior_game_stats["badges"]

def _check_if_truncated(self, game_stats: dict) -> bool:
    # Implement your truncation check logic here

    # Maybe if we run out of pokeballs...? or a max step count
    return self.steps >= 1000
```