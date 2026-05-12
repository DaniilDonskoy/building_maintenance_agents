from __future__ import annotations

from typing import Dict

import numpy as np
from stable_baselines3 import PPO, A2C
from stable_baselines3.common.callbacks import BaseCallback, CallbackList, EvalCallback
from stable_baselines3.common.vec_env import SubprocVecEnv
import os

from .building_incident_env import BuildingIncidentEnv


class NotebookProgressCallback(BaseCallback):
    def __init__(self):
        super().__init__()
        self.progress = None
        self.last_percent = -1

    def _on_training_start(self) -> None:
        try:
            from tqdm.auto import tqdm

            self.progress = tqdm(total=self.locals["total_timesteps"], desc="Training")
        except Exception:
            self.progress = None
            print("Training progress: 0%")

    def _on_step(self) -> bool:
        if self.progress is not None:
            current = min(self.num_timesteps, self.locals["total_timesteps"])
            self.progress.update(current - self.progress.n)
        else:
            percent = int(100 * self.num_timesteps / self.locals["total_timesteps"])
            if percent >= self.last_percent + 5:
                self.last_percent = percent
                print(f"Training progress: {percent}%")
        return True

    def _on_training_end(self) -> None:
        if self.progress is not None:
            self.progress.close()


def make_env(env_config: Dict, rank: int, seed: int = 0):
    def _init():
        from loguru import logger

        logger.disable("building_maintenance_agents")
        env = BuildingIncidentEnv(**env_config)
        env.reset(seed=seed + rank)
        return env
    return _init


def train_agent(
    env_config: Dict,
    total_timesteps: int = 200000,
    algorithm: str = "PPO",
    n_envs: int = 4,
    save_path: str = "./models/",
    progress_bar: bool = False
):
    from loguru import logger

    logger.disable("building_maintenance_agents")
    os.makedirs(save_path, exist_ok=True)
    
    envs = SubprocVecEnv([
        make_env(env_config, i) for i in range(n_envs)
    ])
    
    eval_env = BuildingIncidentEnv(**env_config)
    callbacks = [
        EvalCallback(
            eval_env,
            best_model_save_path=save_path,
            log_path=save_path,
            eval_freq=10000,
            deterministic=True,
            render=False
        )
    ]

    if progress_bar:
        callbacks.append(NotebookProgressCallback())
    
    if algorithm == "PPO":
        model = PPO(
            "MlpPolicy",
            envs,
            verbose=1,
            learning_rate=0.0003,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            tensorboard_log=f"{save_path}/tensorboard/"
        )
    elif algorithm == "A2C":
        model = A2C(
            "MlpPolicy",
            envs,
            verbose=1,
            learning_rate=0.0007,
            n_steps=5,
            gamma=0.99,
            gae_lambda=1.0,
            ent_coef=0.01,
            tensorboard_log=f"{save_path}/tensorboard/"
        )
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    model.learn(
        total_timesteps=total_timesteps,
        callback=CallbackList(callbacks),
        tb_log_name=f"{algorithm}_incident_control",
        progress_bar=False
    )
    
    model.save(f"{save_path}/{algorithm}_incident_model")
    
    return model


def evaluate_agent(model_path: str, n_episodes: int = 10):
    from stable_baselines3 import PPO, A2C
    
    if "PPO" in model_path:
        model = PPO.load(model_path)
    else:
        model = A2C.load(model_path)
    
    env = BuildingIncidentEnv(
        house_type="16",
        max_steps=100,
        render_mode="human",
        incident_probability=0.03
    )
    
    episode_rewards = []
    episode_lengths = []
    
    for episode in range(n_episodes):
        obs, info = env.reset()
        done = False
        episode_reward = 0
        step = 0
        
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            step += 1
            done = terminated or truncated
        
        episode_rewards.append(episode_reward)
        episode_lengths.append(step)
        
        print(f"Episode {episode + 1}: reward={episode_reward:.2f}, steps={step}")
        
        metrics = env.get_metrics()
        print(f"  Incidents handled: {metrics['incident_stats']['total_incidents']}")
        print(f"  Resources used: {metrics['resources_used']:.1f}")
    
    print(f"\nAverage reward: {np.mean(episode_rewards):.2f} +/- {np.std(episode_rewards):.2f}")
    print(f"Average episode length: {np.mean(episode_lengths):.2f}")
    
    env.close()
    return episode_rewards, episode_lengths


def compare_strategies():
    def heuristic_strategy(env):
        action = np.zeros(4, dtype=np.float32)
        
        if len(env.simulator.active_incidents) > 0:
            worst_incident = max(env.simulator.active_incidents, key=lambda x: x.severity)
            
            if worst_incident.location_type == "node":
                try:
                    idx = env.node_ids.index(worst_incident.location_id)
                    action[0] = 0  # DEPLOY_FIREFIGHTERS
                    action[1] = idx
                    action[2] = 0
                    action[3] = 1.0
                except ValueError:
                    action[0] = 10  # MONITOR
            else:
                try:
                    idx = env.edge_ids.index(worst_incident.location_id)
                    action[0] = 8  # REPAIR_ELEMENT
                    action[1] = idx
                    action[2] = 1
                    action[3] = 1.0
                except ValueError:
                    action[0] = 10
        else:
            action[0] = 10  # MONITOR
        
        return action
    
    env = BuildingIncidentEnv(house_type="16", max_steps=100, render_mode=None)
    
    results = {
        "heuristic": {"rewards": [], "incidents": []},
        "random": {"rewards": [], "incidents": []}
    }
    
    for strategy in ["heuristic", "random"]:
        for episode in range(10):
            obs, info = env.reset()
            episode_reward = 0
            
            for step in range(100):
                if strategy == "heuristic":
                    action = heuristic_strategy(env)
                else:
                    action = env.action_space.sample()
                
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
                
                if terminated or truncated:
                    break
            
            results[strategy]["rewards"].append(episode_reward)
            results[strategy]["incidents"].append(info.get("active_incidents", 0))
    
    print("\nStrategy Comparison:")
    for strategy in ["heuristic", "random"]:
        rewards = results[strategy]["rewards"]
        print(f"\n{strategy.upper()}:")
        print(f"  Mean reward: {np.mean(rewards):.2f} +/- {np.std(rewards):.2f}")
        print(f"  Min reward: {np.min(rewards):.2f}")
        print(f"  Max reward: {np.max(rewards):.2f}")
