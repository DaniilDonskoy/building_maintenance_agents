from __future__ import annotations

from typing import Dict

import numpy as np
from stable_baselines3 import PPO, A2C
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
import os

from .building_incident_env import BuildingIncidentEnv


def make_env(env_config: Dict, rank: int, seed: int = 0):
    def _init():
        env = BuildingIncidentEnv(**env_config)
        env.reset(seed=seed + rank)
        return env
    return _init


def make_masked_env(env_config: Dict, rank: int, seed: int = 0):
    def _init():
        env = BuildingIncidentEnv(**env_config)
        env = ActionMasker(env, lambda e: e.action_masks())
        env.reset(seed=seed + rank)
        return env
    return _init


def train_agent(
    env_config: Dict,
    total_timesteps: int = 200000,
    algorithm: str = "PPO",
    n_envs: int = 4,
    save_path: str = "./models/"
):
    os.makedirs(save_path, exist_ok=True)

    envs = SubprocVecEnv([
        make_env(env_config, i) for i in range(n_envs)
    ])

    eval_env = BuildingIncidentEnv(**env_config)
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=save_path,
        log_path=save_path,
        eval_freq=10000,
        deterministic=True,
        render=False
    )

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
        callback=eval_callback,
        tb_log_name=f"{algorithm}_incident_control"
    )

    model.save(f"{save_path}/{algorithm}_incident_model")

    return model


def train_masked_agent(
    env_config: Dict,
    total_timesteps: int = 200_000,
    n_envs: int = 4,
    save_path: str = "./models/",
    learning_rate: float = 3e-4,
    net_arch: list | None = None,
) -> MaskablePPO:
    """Обучение MaskablePPO — REPAIR и WITHDRAW недоступны пока нет команды на поле."""
    os.makedirs(save_path, exist_ok=True)

    if net_arch is None:
        net_arch = [256, 256]

    envs = DummyVecEnv([make_masked_env(env_config, i, seed=42)
                       for i in range(n_envs)])

    eval_env_raw = BuildingIncidentEnv(**env_config)
    eval_env = ActionMasker(eval_env_raw, lambda e: e.action_masks())
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=save_path,
        log_path=save_path,
        eval_freq=max(10_000 // n_envs, 1),
        deterministic=True,
        render=False,
    )

    model = MaskablePPO(
        "MlpPolicy",
        envs,
        verbose=0,
        learning_rate=learning_rate,
        n_steps=512,
        batch_size=128,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        policy_kwargs=dict(net_arch=net_arch),
        seed=42,
        tensorboard_log=f"{save_path}/tensorboard/",
    )

    model.learn(
        total_timesteps=total_timesteps,
        callback=eval_callback,
        tb_log_name="MaskablePPO",
        progress_bar=True,
    )

    model.save(f"{save_path}/masked_ppo_model")
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

        print(
            f"Episode {episode + 1}: reward={episode_reward:.2f}, steps={step}")

        metrics = env.get_metrics()
        print(
            f"  Incidents handled: {metrics['incident_stats']['total_incidents']}")
        print(f"  Resources used: {metrics['resources_used']:.1f}")

    print(
        f"\nAverage reward: {np.mean(episode_rewards):.2f} +/- {np.std(episode_rewards):.2f}")
    print(f"Average episode length: {np.mean(episode_lengths):.2f}")

    env.close()
    return episode_rewards, episode_lengths


def compare_strategies():
    # TODO
    def heuristic_strategy(env):
        action = np.zeros(4, dtype=np.float32)

        if len(env.simulator.active_incidents) > 0:
            worst_incident = max(
                env.simulator.active_incidents, key=lambda x: x.severity)

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
            results[strategy]["incidents"].append(
                info.get("active_incidents", 0))

    print("\nStrategy Comparison:")
    for strategy in ["heuristic", "random"]:
        rewards = results[strategy]["rewards"]
        print(f"\n{strategy.upper()}:")
        print(
            f"  Mean reward: {np.mean(rewards):.2f} +/- {np.std(rewards):.2f}")
        print(f"  Min reward: {np.min(rewards):.2f}")
        print(f"  Max reward: {np.max(rewards):.2f}")
