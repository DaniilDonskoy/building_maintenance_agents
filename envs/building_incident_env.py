from __future__ import annotations

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Optional, Tuple, Any, Sequence
from loguru import logger

from ..incident_simulator import (
    IncidentSimulator, IncidentType
)
from ..house_graph import House
from ..house_graph.samples import House15Factory, House16Factory, House27Factory
from .incident_observation import IncidentObservation
from .agent_action_type import AgentActionType
from .agent_action import AgentAction
from .reward import CurrentReward, RewardConfig


class BuildingIncidentEnv(gym.Env):
    
    metadata = {'render_modes': ['human', 'ansi'], 'render_fps': 4}
    SIMPLE_ACTION_TYPES = (
        AgentActionType.MONITOR,
        AgentActionType.REPAIR,
        AgentActionType.SHUT_OFF_WATER,
        AgentActionType.CALL_BACKUP,
        AgentActionType.INSPECT,
        AgentActionType.DEPLOY_TEAM,
        AgentActionType.WITHDRAW_TEAM,
    )
    
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
        random_seed: Optional[int] = None,
        reward_strategy: CurrentReward | None = None,
        reward_config: RewardConfig | None = None,
        simple_action_space: bool = False,
        simple_action_names: Optional[Sequence[str]] = None,
        compact_observation: bool = False,
        passive_incident_decay: bool = True,
        auto_resolve_incidents: bool = True,
        initial_incident_probability: float = 0.2,
        search_action_space: bool = False,
        search_zone_count: int = 8,
        known_incident_slots: int = 3
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
        self.simple_action_space = simple_action_space
        self.simple_action_types = self._resolve_simple_action_types(simple_action_names)
        self.compact_observation = compact_observation
        self.passive_incident_decay = passive_incident_decay
        self.auto_resolve_incidents = auto_resolve_incidents
        self.initial_incident_probability = initial_incident_probability
        self.search_action_space = search_action_space
        self.search_zone_count = max(1, int(search_zone_count))
        self.known_incident_slots = max(1, int(known_incident_slots))
        
        self.house = self._create_house()
        self.simulator = IncidentSimulator(
            self.house,
            base_incident_probability=incident_probability,
            random_seed=random_seed,
            enable_spread=enable_spread,
            passive_incident_decay=passive_incident_decay,
            auto_resolve_incidents=auto_resolve_incidents
        )
        
        self.observer = IncidentObservation(self.simulator)
        
        self.current_step = 0
        self.resources = resource_budget
        self.resources_used = 0.0
        self.reward_total = 0.0
        self.episode_rewards = []
        self.penalized_overdue_incident_ids = set()
        self.last_new_overdue_incidents = 0
        self.last_action_index = None
        self.known_incident_ids = set()
        self.last_inspection_zone = None
        self.last_newly_known_incidents = 0
        self.last_repair_slot = None
        self.last_action_label = None
        if reward_strategy is not None:
            self.reward_strategy = reward_strategy
        else:
            self.reward_strategy = CurrentReward(reward_config)
        
        self.node_ids = [id(node) for node in self.house.nodes]
        self.edge_ids = [id(edge) for edge in self.house.edges]
        self.node_by_id = {id(node): node for node in self.house.nodes}
        self.edge_by_id = {id(edge): edge for edge in self.house.edges}
        self._build_search_zones()
        
        self._setup_spaces()
        
        self.history = []

    def _resolve_simple_action_types(
        self,
        action_names: Optional[Sequence[str]]
    ) -> Tuple[AgentActionType, ...]:
        if action_names is None:
            return self.SIMPLE_ACTION_TYPES

        return tuple(AgentActionType[name] for name in action_names)
    
    def _create_house(self) -> House:
        factories = {
            "15": House15Factory,
            "16": House16Factory,
            "27": House27Factory
        }
        factory = factories.get(self.house_type, House16Factory)
        return factory.build()
    
    def _setup_spaces(self):
        if self.search_action_space:
            self.action_space = spaces.Discrete(
                1 + self.search_zone_count + self.known_incident_slots
            )
        elif self.simple_action_space:
            self.action_space = spaces.Discrete(len(self.simple_action_types))
        else:
            # actions: [action_type, target_index, target_type, resource_multiplier]
            # action_type: 0 to len(AgentActionType) - 1
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
        
        sample_obs = self._get_observation()
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=sample_obs.shape,
            dtype=np.float32
        )

    def _get_observation(self) -> np.ndarray:
        if self.search_action_space:
            return self._get_search_observation()

        if not self.compact_observation:
            return self.observer.get_observation()

        active_incidents = self.simulator.active_incidents
        active_count = len(active_incidents)
        severities = [incident.severity for incident in active_incidents]
        durations = [incident.duration for incident in active_incidents]
        overdue_count = sum(1 for incident in active_incidents if incident.is_overdue)

        max_severity = max(severities, default=0.0)
        mean_severity = float(np.mean(severities)) if severities else 0.0
        total_severity = sum(severities)
        min_duration = min(durations, default=self.max_steps)

        return np.array([
            float(active_count > 0),
            min(active_count / max(1, self.max_active_incidents), 2.0),
            max_severity,
            mean_severity,
            min(total_severity / max(1, self.max_active_incidents), 2.0),
            min(max(min_duration, 0) / max(1, self.max_steps), 2.0),
            min(overdue_count / max(1, self.max_active_incidents), 2.0),
            self.resources / max(1.0, self.resource_budget),
        ], dtype=np.float32)

    def _build_search_zones(self) -> None:
        self.search_zone_by_location = {}
        for idx, node_id in enumerate(self.node_ids):
            self.search_zone_by_location[("node", node_id)] = idx % self.search_zone_count
        for idx, edge_id in enumerate(self.edge_ids):
            zone_idx = (idx + len(self.node_ids)) % self.search_zone_count
            self.search_zone_by_location[("edge", edge_id)] = zone_idx

        self.last_inspected_step_by_zone = np.full(
            self.search_zone_count,
            -self.max_steps,
            dtype=np.int32
        )

    def _get_incident_zone(self, incident) -> int:
        return self.search_zone_by_location.get(
            (incident.location_type, incident.location_id),
            0
        )

    def _get_known_active_incidents(self):
        return [
            incident for incident in self.simulator.active_incidents
            if incident.incident_id in self.known_incident_ids
        ]

    def _cleanup_known_incidents(self) -> None:
        active_ids = {incident.incident_id for incident in self.simulator.active_incidents}
        self.known_incident_ids.intersection_update(active_ids)

    def _get_search_observation(self) -> np.ndarray:
        active_incidents = self.simulator.active_incidents
        known_incidents = self._get_known_active_incidents()
        hidden_incidents = [
            incident for incident in active_incidents
            if incident.incident_id not in self.known_incident_ids
        ]

        features = [
            self.resources / max(1.0, self.resource_budget),
            float(len(active_incidents) > 0),
            min(len(known_incidents) / max(1, self.known_incident_slots), 2.0),
            min(len(hidden_incidents) / max(1, self.max_active_incidents), 2.0),
        ]

        for zone_idx in range(self.search_zone_count):
            zone_incidents = [
                incident for incident in active_incidents
                if self._get_incident_zone(incident) == zone_idx
            ]
            zone_known = [
                incident for incident in zone_incidents
                if incident.incident_id in self.known_incident_ids
            ]
            last_inspected = self.last_inspected_step_by_zone[zone_idx]
            inspected_age = self.current_step - last_inspected

            features.extend([
                float(len(zone_incidents) > 0),
                min(len(zone_known) / max(1, self.known_incident_slots), 2.0),
                max((incident.severity for incident in zone_known), default=0.0),
                min(max(inspected_age, 0) / max(1, self.max_steps), 2.0),
            ])

        known_by_severity = sorted(
            known_incidents,
            key=lambda incident: incident.severity,
            reverse=True
        )
        for slot_idx in range(self.known_incident_slots):
            if slot_idx >= len(known_by_severity):
                features.extend([0.0, 0.0, 0.0, 0.0, 0.0])
                continue

            incident = known_by_severity[slot_idx]
            features.extend([
                1.0,
                incident.severity,
                min(max(incident.duration, 0) / max(1, self.max_steps), 2.0),
                float(incident.is_overdue),
                self._get_incident_zone(incident) / max(1, self.search_zone_count - 1),
            ])

        return np.array(features, dtype=np.float32)
    
    def _parse_action(self, action: np.ndarray) -> AgentAction:
        if self.search_action_space:
            return self._parse_search_action(action)

        if self.simple_action_space:
            action_type_idx = int(np.asarray(action).reshape(-1)[0])
            action_type_idx = int(np.clip(action_type_idx, 0, len(self.simple_action_types) - 1))
            self.last_action_index = action_type_idx
            action_type = self.simple_action_types[action_type_idx]
            target_id, target_type = self._select_simple_action_target(action_type)

            return AgentAction(
                action_type=action_type,
                target_id=target_id,
                target_type=target_type,
                resource_multiplier=1.0
            )

        action = np.asarray(action, dtype=np.float32).reshape(-1)
        action_type_idx = int(np.clip(action[0], 0, len(AgentActionType) - 1))
        self.last_action_index = action_type_idx
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

    def _parse_search_action(self, action: np.ndarray) -> AgentAction:
        action_idx = int(np.asarray(action).reshape(-1)[0])
        max_idx = self.action_space.n - 1
        action_idx = int(np.clip(action_idx, 0, max_idx))

        self.last_action_index = action_idx
        self.last_inspection_zone = None
        self.last_repair_slot = None

        if action_idx == 0:
            self.last_action_label = "MONITOR"
            return AgentAction(action_type=AgentActionType.MONITOR)

        inspect_start = 1
        inspect_end = inspect_start + self.search_zone_count
        if inspect_start <= action_idx < inspect_end:
            zone_idx = action_idx - inspect_start
            self.last_inspection_zone = zone_idx
            self.last_action_label = f"INSPECT_ZONE_{zone_idx}"
            return AgentAction(
                action_type=AgentActionType.INSPECT,
                target_id=self.node_ids[0],
                target_type="node",
                resource_multiplier=1.0
            )

        slot_idx = action_idx - inspect_end
        self.last_repair_slot = slot_idx
        self.last_action_label = f"REPAIR_KNOWN_{slot_idx}"

        known_incidents = sorted(
            self._get_known_active_incidents(),
            key=lambda incident: incident.severity,
            reverse=True
        )
        if slot_idx >= len(known_incidents):
            return AgentAction(
                action_type=AgentActionType.REPAIR,
                target_id=self.node_ids[0],
                target_type="node",
                resource_multiplier=1.0
            )

        incident = known_incidents[slot_idx]
        return AgentAction(
            action_type=AgentActionType.REPAIR,
            target_id=incident.location_id,
            target_type=incident.location_type,
            resource_multiplier=1.0
        )

    def _select_simple_action_target(
        self,
        action_type: AgentActionType
    ) -> Tuple[Optional[int], Optional[str]]:
        targeted_actions = {
            AgentActionType.REPAIR,
            AgentActionType.DEPLOY_TEAM,
            AgentActionType.SHUT_OFF_WATER,
            AgentActionType.INSPECT,
        }

        if action_type not in targeted_actions:
            return None, None

        if not self.simulator.active_incidents:
            return self.node_ids[0], "node"

        incident = max(self.simulator.active_incidents, key=lambda inc: inc.severity)
        return incident.location_id, incident.location_type
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        self.last_new_overdue_incidents = 0
        self.last_newly_known_incidents = 0
        self.last_action_label = None
        parsed_action = self._parse_action(action)
        action_reward = self.reward_strategy.calculate_action_reward(self, parsed_action)
        
        sim_results = self.simulator.step()  # update simulator
        self._cleanup_known_incidents()
        
        reward = self.reward_strategy.calculate_step_reward(self, action_reward)
        self.reward_total += reward
        self.episode_rewards.append(reward)
        
        observation = self._get_observation()
        
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
            "overdue_incidents": sum(1 for inc in self.simulator.active_incidents if inc.is_overdue),
            "new_overdue_incidents": self.last_new_overdue_incidents,
            "known_incidents": len(self._get_known_active_incidents()),
            "hidden_incidents": len(self.simulator.active_incidents) - len(self._get_known_active_incidents()),
            "newly_known_incidents": self.last_newly_known_incidents,
            "inspected_zone": self.last_inspection_zone,
            "repair_slot": self.last_repair_slot,
            "total_reward": self.reward_total,
            "action": self.last_action_label or parsed_action.action_type.name,
            "action_index": self.last_action_index
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
            enable_spread=self.enable_spread,
            passive_incident_decay=self.passive_incident_decay,
            auto_resolve_incidents=self.auto_resolve_incidents
        )
        
        self.observer = IncidentObservation(self.simulator)  # update observations
        
        # reset states
        self.current_step = 0
        self.resources = self.resource_budget
        self.resources_used = 0.0
        self.reward_total = 0.0
        self.episode_rewards = []
        self.penalized_overdue_incident_ids = set()
        self.last_new_overdue_incidents = 0
        self.last_action_index = None
        self.known_incident_ids = set()
        self.last_inspection_zone = None
        self.last_newly_known_incidents = 0
        self.last_repair_slot = None
        self.last_action_label = None
        self.history = []
        
        self.node_ids = [id(node) for node in self.house.nodes]
        self.edge_ids = [id(edge) for edge in self.house.edges]
        self.node_by_id = {id(node): node for node in self.house.nodes}
        self.edge_by_id = {id(edge): edge for edge in self.house.edges}
        self._build_search_zones()
        
        if np.random.random() < self.initial_incident_probability:
            self.simulator.create_incident(
                np.random.choice(list(IncidentType)),
                np.random.choice(self.house.nodes),
                severity=np.random.uniform(0.3, 0.7)
            )
        
        observation = self._get_observation()
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

    def handle_inspect_action(self, _action: AgentAction) -> Optional[float]:
        if not self.search_action_space or self.last_inspection_zone is None:
            return None

        self.last_inspected_step_by_zone[self.last_inspection_zone] = self.current_step
        newly_known = [
            incident for incident in self.simulator.active_incidents
            if self._get_incident_zone(incident) == self.last_inspection_zone
            and incident.incident_id not in self.known_incident_ids
        ]

        for incident in newly_known:
            self.known_incident_ids.add(incident.incident_id)

        self.last_newly_known_incidents = len(newly_known)
        if newly_known:
            return (
                self.reward_strategy.config.inspect_valid_target_reward
                * len(newly_known)
            )

        return self.reward_strategy.config.inspect_invalid_target_penalty
    
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
