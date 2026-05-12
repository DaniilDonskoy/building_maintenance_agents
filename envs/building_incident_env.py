from __future__ import annotations

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Optional, Tuple, Any
from loguru import logger

from incident_simulator import (
    IncidentSimulator, IncidentType
)
from house_graph import House
from house_graph.samples import House15Factory, House16Factory, House27Factory
from .incident_observation import IncidentObservation
from .agent_action_type import AgentActionType
from .agent_action import AgentAction
from .reward import CurrentReward


class BuildingIncidentEnv(gym.Env):
    
    metadata = {'render_modes': ['human', 'ansi'], 'render_fps': 4}
    
    def __init__(
        self,
        house_type: str = "16",
        max_steps: int = 200,
        render_mode: Optional[str] = None,
        incident_probability: float = 0.03,
        max_active_incidents: int = 10,
        resource_budget: float = 100.0,
        resource_regen_rate: float = 0.5,
        enable_spread: bool = True,
        random_seed: Optional[int] = None
    ):
        super().__init__()
        
        self.house_type = house_type
        self.max_steps = max_steps
        self.render_mode = render_mode
        self.incident_probability = incident_probability
        self.max_active_incidents = max_active_incidents
        self.resource_budget = resource_budget
        self.initial_resource_budget = resource_budget
        self.resource_regen_rate = resource_regen_rate
        self.enable_spread = enable_spread
        self.random_seed = random_seed
        
        self.house = self._create_house()
        self.simulator = IncidentSimulator(
            self.house,
            base_incident_probability=incident_probability,
            random_seed=random_seed,
            enable_spread=enable_spread
        )
        
        self.observer = IncidentObservation(self.simulator)
        
        self.current_step = 0
        self.resources = resource_budget
        self.resources_used = 0.0
        self.reward_total = 0.0
        self.episode_rewards = []
        self.reward_strategy = CurrentReward()
        
        self.node_ids = [id(node) for node in self.house.nodes]
        self.edge_ids = [id(edge) for edge in self.house.edges]
        self.node_by_id = {id(node): node for node in self.house.nodes}
        self.edge_by_id = {id(edge): edge for edge in self.house.edges}
        
        self._setup_spaces()
        
        self.history = []
    
    def _create_house(self) -> House:
        factories = {
            "15": House15Factory,
            "16": House16Factory,
            "27": House27Factory
        }
        factory = factories.get(self.house_type, House16Factory)
        return factory.build()
    
    def _setup_spaces(self):
        # actions: [action_type, target_index, target_type, resource_multiplier]
        # action_type: 0-12
        # target_index: 0 to max(nodes, edges)
        # target_type: 0=node, 1=edge
        # resource_multiplier: 0-2
        self.action_space = spaces.Box(
            low=np.array([0, 0, 0, 0.5], dtype=np.float32),
            high=np.array([
                len(AgentActionType) - 1,
                max(len(self.node_ids), len(self.edge_ids)) - 1,
                1,
                2.0
            ], dtype=np.float32),
            dtype=np.float32
        )
        
        sample_obs = self.observer.get_observation()
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=sample_obs.shape,
            dtype=np.float32
        )
    
    def _parse_action(self, action: np.ndarray) -> AgentAction:
        action_type_idx = int(np.clip(action[0], 0, len(AgentActionType) - 1))
        target_idx = int(np.clip(action[1], 0, max(len(self.node_ids), len(self.edge_ids)) - 1))
        target_type = int(np.clip(action[2], 0, 1))
        resource_multiplier = float(np.clip(action[3], 0.5, 2.0))
        
        action_type = list(AgentActionType)[action_type_idx]
        
        target_id = None
        if target_type == 0 and target_idx < len(self.node_ids):
            target_id = self.node_ids[target_idx]
        elif target_type == 1 and target_idx < len(self.edge_ids):
            target_id = self.edge_ids[target_idx]
        
        return AgentAction(
            action_type=action_type,
            target_id=target_id,
            target_type="node" if target_type == 0 else "edge",
            resource_multiplier=resource_multiplier
        )
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        parsed_action = self._parse_action(action)
        action_reward = self.reward_strategy.calculate_action_reward(self, parsed_action)
        
        sim_results = self.simulator.step()  # update simulator
        
        reward = self.reward_strategy.calculate_step_reward(self, action_reward)
        self.reward_total += reward
        self.episode_rewards.append(reward)
        
        observation = self.observer.get_observation()
        
        # checking completion
        self.current_step += 1
        terminated = False
        truncated = False
        
        if self.current_step >= self.max_steps:
            truncated = True
        
        if self.resources <= 0:
            terminated = True
            logger.warning("Resources depleted!")
        
        if len(self.simulator.active_incidents) > self.max_active_incidents * 2:
            terminated = True
            logger.warning("Too many active incidents!")
        
        info = {
            "step": self.current_step,
            "resources": self.resources,
            "active_incidents": len(self.simulator.active_incidents),
            "new_incidents": len(sim_results.get("new_incidents", [])),
            "resolved_incidents": len(sim_results.get("resolved_incidents", [])),
            "total_reward": self.reward_total,
            "action": parsed_action.action_type.name
        }
        
        self.history.append({
            "step": self.current_step,
            "action": parsed_action,
            "reward": reward,
            "info": info
        })
        
        if self.render_mode == "human":
            self.render()
        
        return observation, reward, terminated, truncated, info
    
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        super().reset(seed=seed)
        
        # create new building
        self.house = self._create_house()
        self.simulator = IncidentSimulator(
            self.house,
            base_incident_probability=self.incident_probability,
            random_seed=seed if seed is not None else self.random_seed,
            enable_spread=self.enable_spread
        )
        
        self.observer = IncidentObservation(self.simulator)  # update observations
        
        # reset states
        self.current_step = 0
        self.resources = self.resource_budget
        self.resources_used = 0.0
        self.reward_total = 0.0
        self.episode_rewards = []
        self.history = []
        
        self.node_ids = [id(node) for node in self.house.nodes]
        self.edge_ids = [id(edge) for edge in self.house.edges]
        self.node_by_id = {id(node): node for node in self.house.nodes}
        self.edge_by_id = {id(edge): edge for edge in self.house.edges}
        
        if np.random.random() < 0.2:
            self.simulator.create_incident(
                np.random.choice(list(IncidentType)),
                np.random.choice(self.house.nodes),
                severity=np.random.uniform(0.3, 0.7)
            )
        
        observation = self.observer.get_observation()
        info = {
            "status": "reset",
            "num_nodes": len(self.house.nodes),
            "num_edges": len(self.house.edges)
        }
        
        return observation, info
    
    def render(self):
        if self.render_mode == "human":
            print()
            print(f"Step: {self.current_step}")
            print(f"Resources: {self.resources:.1f}/{self.resource_budget:.1f}")
            print(f"Active incidents: {len(self.simulator.active_incidents)}")
            print(f"Total reward: {self.reward_total:.2f}")
            
            if self.simulator.active_incidents:
                print("\nActive incidents:")
                for inc in self.simulator.active_incidents[:5]:
                    element = self.simulator._get_element(inc.location_id, inc.location_type)
                    element_name = type(element).__name__ if element else "Unknown"
                    print(f"  [{inc.incident_id}] {inc.incident_type.value}: severity={inc.severity:.2f}, "
                          f"duration={inc.duration}, at {inc.location_type} {element_name}")
            
            stats = self.simulator.get_statistics()
            print(f"\nStatistics: total incidents={stats['total_incidents']}, "
                  f"max active={stats['max_active_incidents']}")
    
    def get_metrics(self) -> Dict[str, Any]:
        return {
            "total_reward": self.reward_total,
            "average_reward": np.mean(self.episode_rewards) if self.episode_rewards else 0,
            "steps": self.current_step,
            "resources_used": self.resources_used,
            "resources_left": self.resources,
            "incident_stats": self.simulator.get_statistics(),
            "affected_elements": self.simulator.get_affected_elements()
        }
