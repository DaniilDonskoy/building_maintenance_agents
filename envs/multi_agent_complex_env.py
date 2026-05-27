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
from .reward import CurrentReward, RewardConfig
from .element_state import AgentStateMachine


class MultiAgentComplexEnv(ParallelEnv):
    metadata = {"render_modes": ["human"]}

    def __init__(self, house_types, max_steps=200, render_mode=None,
                 incident_probability=0.03, max_active_incidents_per_building=10,
                 enable_spread=True, random_seed=None, max_teams=5,
                 reward_config: RewardConfig | None = None):
        super().__init__()
        self.house_types = house_types
        self.max_steps = max_steps
        self.render_mode = render_mode
        self.incident_probability = incident_probability
        self.max_active_incidents_per_building = max_active_incidents_per_building
        self.enable_spread = enable_spread
        self.random_seed = random_seed
        self.max_teams = max_teams

        self.cores: List[BuildingIncidentCore] = []
        for htype in house_types:
            house = self._create_house(htype)
            sim = IncidentSimulator(
                house,
                base_incident_probability=incident_probability,
                random_seed=random_seed,
                enable_spread=enable_spread,
                passive_incident_decay=True,
                auto_resolve_incidents=False
            )
            core = BuildingIncidentCore(sim, max_active_incidents_per_building)
            self.cores.append(core)

        self.state_machine = AgentStateMachine(max_teams=max_teams)
        self.reward_strategy = CurrentReward(reward_config)

        self.possible_agents = [f"team_{i}" for i in range(max_teams)]
        self.agents = self.possible_agents[:]

        self.current_step = 0
        self.total_reward = 0.0
        self.penalized_overdue_incident_ids = set()
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
        total_overdue = sum(
            1 for c in self.cores for inc in c.simulator.active_incidents if inc.is_overdue)

        global_feats = np.array([
            total_incidents / (len(self.cores) *
                               self.max_active_incidents_per_building),
            total_overdue / max(1, total_incidents),
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
                def __init__(self, sim, sm, node_by_id, edge_by_id, bidx, step, penalized_set):
                    self.simulator = sim
                    self.state_machine = sm
                    self.node_by_id = node_by_id
                    self.edge_by_id = edge_by_id
                    self.building_idx = bidx
                    self.max_active_incidents = core.max_active_incidents
                    self.current_step = step
                    self.penalized_overdue_incident_ids = penalized_set

            shim = EnvShim(core.simulator, self.state_machine,
                           core.node_by_id, core.edge_by_id, building_idx,
                           self.current_step, self.penalized_overdue_incident_ids)
            reward = self.reward_strategy.calculate_action_reward(
                shim, agent_action)
            agent_rewards.append(reward)

        for core in self.cores:
            core.simulator.step()

        global_step_reward = self._global_step_reward()

        total_reward = sum(agent_rewards) + global_step_reward
        per_agent = [r + global_step_reward /
                     len(self.agents) for r in agent_rewards]

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
        info_dict = {
            agent: {
                "step": self.current_step,
                "total_reward": self.total_reward,
                "overdue_incidents": sum(1 for c in self.cores for inc in c.simulator.active_incidents if inc.is_overdue)
            } for agent in self.agents
        }

        if self.render_mode == "human":
            self.render()
        return obs_dict, reward_dict, terminated_dict, truncated_dict, info_dict

    def _global_step_reward(self) -> float:
        reward = 0.0
        new_overdue_ids = set()

        for core in self.cores:
            for inc in core.simulator.active_incidents:
                age = self.current_step - inc.start_time

                if inc.is_overdue and age > self.reward_strategy.config.max_incident_age:
                    hours_overdue = age - self.reward_strategy.config.max_incident_age
                    decay = 1.0 - \
                        (self.reward_strategy.config.severity_discount_rate *
                         hours_overdue / 24.0)
                    inc.severity = max(0.01, inc.severity * max(decay, 0.1))

                if inc.is_overdue and inc.incident_id not in self.penalized_overdue_incident_ids:
                    new_overdue_ids.add(inc.incident_id)

        if new_overdue_ids:
            penalty = self.reward_strategy.config.overdue_penalty * \
                len(new_overdue_ids)
            reward += penalty
            self.penalized_overdue_incident_ids.update(new_overdue_ids)
            print(
                f"⚠️ New overdue incidents: {len(new_overdue_ids)}, penalty: {penalty}")

        total_discounted_severity = 0.0
        for core in self.cores:
            for inc in core.simulator.active_incidents:
                if inc.is_overdue:
                    discount_factor = 0.3
                else:
                    discount_factor = 1.0
                total_discounted_severity += inc.severity * discount_factor

        reward -= total_discounted_severity * \
            self.reward_strategy.config.active_incident_penalty_multiplier

        total_incidents = sum(len(c.simulator.active_incidents)
                              for c in self.cores)
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
            sim = IncidentSimulator(
                house,
                base_incident_probability=self.incident_probability,
                random_seed=seed,
                enable_spread=self.enable_spread,
                passive_incident_decay=True,
                auto_resolve_incidents=False
            )
            core = BuildingIncidentCore(
                sim, self.max_active_incidents_per_building)

            if np.random.random() < 0.3:
                sim.create_incident(
                    np.random.choice(list(IncidentType)),
                    np.random.choice(house.nodes),
                    severity=np.random.uniform(0.4, 0.8)
                )
            self.cores.append(core)

        self.state_machine.reset()
        self.current_step = 0
        self.total_reward = 0.0
        self.penalized_overdue_incident_ids.clear()

        obs = self._get_observation()
        obs_dict = {agent: obs for agent in self.agents}
        info_dict = {agent: {"num_buildings": len(
            self.cores)} for agent in self.agents}
        return obs_dict, info_dict

    def render(self):
        if self.render_mode == "human":
            print(f"\n{'='*50}")
            print(f"Step {self.current_step}/{self.max_steps}")
            print(
                f"Active teams: {self.state_machine.active_teams}/{self.max_teams}")
            print(f"Total reward: {self.total_reward:.2f}")
            print(
                f"Penalized overdue incidents: {len(self.penalized_overdue_incident_ids)}")

            for i, core in enumerate(self.cores):
                incidents = core.simulator.active_incidents
                overdue = sum(1 for inc in incidents if inc.is_overdue)
                avg_severity = np.mean(
                    [inc.severity for inc in incidents]) if incidents else 0
                print(
                    f"\n🏢 Building {i}: {len(incidents)} incidents (overdue: {overdue}, avg severity: {avg_severity:.2f})")

                for inc in incidents[:3]:
                    age = self.current_step - inc.start_time
                    status = "⚠️ OVERDUE" if inc.is_overdue else "✓ active"
                    print(
                        f"   - {inc.incident_type.value} | severity={inc.severity:.2f} | age={age} | {status}")
