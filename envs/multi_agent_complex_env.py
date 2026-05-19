from __future__ import annotations

import gymnasium as gym
import numpy as np
from pettingzoo import ParallelEnv
from typing import Dict, List, Optional, Tuple

from incident_simulator import IncidentSimulator, IncidentType
from house_graph import House
from house_graph.samples import House15Factory, House16Factory, House27Factory

from .building_incident_core import BuildingIncidentCore
from .agent_action_type import AgentActionType
from .agent_action import AgentAction
from .reward import CurrentReward
from .element_state import AgentStateMachine


class MultiAgentComplexEnv(ParallelEnv):
    metadata = {"render_modes": ["human"]}

    def __init__(self, house_types, max_steps=200, render_mode=None,
                 incident_probability=0.03, max_active_incidents_per_building=10,
                 enable_spread=True, random_seed=None, max_teams=5):
        super().__init__()
        self.house_types = house_types
        self.max_steps = max_steps
        self.render_mode = render_mode
        self.incident_probability = incident_probability
        self.max_active_incidents_per_building = max_active_incidents_per_building
        self.enable_spread = enable_spread
        self.random_seed = random_seed
        self.max_teams = max_teams

        self.cores = []
        for htype in house_types:
            house = self._create_house(htype)
            sim = IncidentSimulator(house, base_incident_probability=incident_probability,
                                    random_seed=random_seed, enable_spread=enable_spread)
            core = BuildingIncidentCore(sim, max_active_incidents_per_building)
            self.cores.append(core)

        self.state_machine = AgentStateMachine(max_teams=max_teams)
        self.reward_strategy = CurrentReward()

        self.possible_agents = [f"team_{i}" for i in range(max_teams)]
        self.agents = self.possible_agents[:]

        self.current_step = 0
        self.total_reward = 0.0
        self.history = []

        sample_obs = self._get_observation()
        self.observation_spaces = {
            agent: gym.spaces.Box(low=-np.inf, high=np.inf,
                                  shape=sample_obs.shape, dtype=np.float32)
            for agent in self.possible_agents
        }

        self._max_targets = max(core.max_targets for core in self.cores)
        self.action_spaces = {
            agent: gym.spaces.MultiDiscrete([
                len(house_types),
                len(AgentActionType),
                self._max_targets,
                2,
            ]) for agent in self.possible_agents
        }

    def _create_house(self, house_type: str) -> House:
        factories = {"15": House15Factory,
                     "16": House16Factory, "27": House27Factory}
        return factories.get(house_type, House16Factory).build()

    def _get_observation(self) -> np.ndarray:
        building_obs = []
        for idx, core in enumerate(self.cores):
            building_obs.append(core.get_observation(self.state_machine, idx))
        total_incidents = sum(len(c.simulator.active_incidents)
                              for c in self.cores)
        global_feats = np.array([
            total_incidents / (len(self.cores) *
                               self.max_active_incidents_per_building),
            self.state_machine.active_teams / self.max_teams,
            self.current_step / self.max_steps,
        ], dtype=np.float32)
        return np.concatenate(building_obs + [global_feats])

    def _parse_action(self, agent_action: np.ndarray) -> Tuple[int, AgentAction]:
        building_idx = int(agent_action[0])
        action_type_idx = int(agent_action[1])
        target_idx = int(agent_action[2])
        target_type = int(agent_action[3])
        core = self.cores[building_idx]
        action_type = list(AgentActionType)[action_type_idx]
        target_id = None
        if target_type == 0 and target_idx < len(core.node_ids):
            target_id = core.node_ids[target_idx]
        elif target_type == 1 and target_idx < len(core.edge_ids):
            target_id = core.edge_ids[target_idx]
        return building_idx, AgentAction(action_type, target_id, "node" if target_type == 0 else "edge")

    def step(self, actions: Dict[str, np.ndarray]) -> Tuple[
        Dict[str, np.ndarray], Dict[str, float], Dict[str,
                                                      bool], Dict[str, bool], Dict[str, Dict]
    ]:
        agent_rewards = []
        for agent_name, act in actions.items():
            building_idx, agent_action = self._parse_action(act)
            core = self.cores[building_idx]

            class EnvShim:
                def __init__(self, sim, sm, node_by_id, edge_by_id, bidx):
                    self.simulator = sim
                    self.state_machine = sm
                    self.node_by_id = node_by_id
                    self.edge_by_id = edge_by_id
                    self.building_idx = bidx
                    self.max_active_incidents = core.max_active_incidents
            shim = EnvShim(core.simulator, self.state_machine,
                           core.node_by_id, core.edge_by_id, building_idx)
            reward = self.reward_strategy.calculate_action_reward(
                shim, agent_action)
            agent_rewards.append(reward)

        for core in self.cores:
            core.simulator.step()

        global_step_reward = self._global_step_reward()
        total_reward = sum(agent_rewards) + global_step_reward
        per_agent = [r + global_step_reward /
                     self.num_agents for r in agent_rewards]

        self.total_reward += total_reward
        self.current_step += 1

        terminated = False
        truncated = self.current_step >= self.max_steps
        obs = self._get_observation()
        obs_dict = {agent: obs for agent in self.agents}
        reward_dict = {agent: per_agent[i]
                       for i, agent in enumerate(self.agents)}
        terminated_dict = {agent: terminated for agent in self.agents}
        truncated_dict = {agent: truncated for agent in self.agents}
        info_dict = {agent: {"step": self.current_step,
                             "total_reward": self.total_reward} for agent in self.agents}

        if self.render_mode == "human":
            self.render()
        return obs_dict, reward_dict, terminated_dict, truncated_dict, info_dict

    def _global_step_reward(self) -> float:
        total_severity = 0.0
        total_incidents = 0
        for core in self.cores:
            total_severity += sum(inc.severity for inc in core.simulator.active_incidents)
            total_incidents += len(core.simulator.active_incidents)
        reward = -total_severity * \
            self.reward_strategy.config.active_incident_penalty_multiplier
        if total_incidents == 0:
            reward += self.reward_strategy.config.no_incidents_bonus
        if total_incidents > len(self.cores) * self.max_active_incidents_per_building:
            reward += self.reward_strategy.config.too_many_incidents_penalty
        return reward

    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[Dict[str, np.ndarray], Dict[str, Dict]]:
        if seed is not None:
            np.random.seed(seed)
        self.cores = []
        for htype in self.house_types:
            house = self._create_house(htype)
            sim = IncidentSimulator(house, base_incident_probability=self.incident_probability,
                                    random_seed=seed, enable_spread=self.enable_spread)
            core = BuildingIncidentCore(
                sim, self.max_active_incidents_per_building)
            if np.random.random() < 0.2:
                sim.create_incident(np.random.choice(list(IncidentType)),
                                    np.random.choice(house.nodes),
                                    severity=np.random.uniform(0.3, 0.7))
            self.cores.append(core)
        self.state_machine.reset()
        self.current_step = 0
        self.total_reward = 0.0
        obs = self._get_observation()
        obs_dict = {agent: obs for agent in self.agents}
        info_dict = {agent: {"num_buildings": len(
            self.cores)} for agent in self.agents}
        return obs_dict, info_dict

    def render(self):
        if self.render_mode == "human":
            print(f"\nStep {self.current_step}")
            print(f"Active teams: {self.state_machine.active_teams}")
            for i, core in enumerate(self.cores):
                print(
                    f"Building {i}: {len(core.simulator.active_incidents)} incidents")
