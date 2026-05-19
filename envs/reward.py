from __future__ import annotations

from dataclasses import dataclass
from loguru import logger

from incident_simulator import IncidentType
from .agent_action import AgentAction
from .agent_action_type import AgentActionType


@dataclass(frozen=True)
class RewardConfig:
    invalid_target_penalty: float = -1.0
    deploy_incident_reward: float = 1.0
    deploy_no_incidents_penalty: float = -0.5
    deploy_precondition_penalty: float = -2.0
    repair_no_team_penalty: float = -3.0
    repair_no_incidents_penalty: float = -0.3
    repair_effectiveness_multiplier: float = 0.5
    repair_severity_multiplier: float = 8.0
    repair_resolved_bonus: float = 15.0
    withdraw_no_team_penalty: float = -2.0
    withdraw_no_incidents_reward: float = 0.5
    withdraw_active_incidents_penalty: float = -1.0
    monitor_no_incidents_reward: float = 0.5
    monitor_active_incidents_penalty: float = -0.1
    shut_off_water_reward: float = 2.0
    shut_off_water_penalty: float = -0.5
    inspect_valid_target_reward: float = 0.2
    inspect_invalid_target_penalty: float = -0.5
    active_incident_penalty_multiplier: float = 0.2
    no_incidents_bonus: float = 1.0
    too_many_incidents_penalty: float = -2.0
    resolve_severity_threshold: float = 0.05


class CurrentReward:
    ACTION_HANDLERS = {
        AgentActionType.DEPLOY_TEAM: "_deploy_team_action",
        AgentActionType.WITHDRAW_TEAM: "_withdraw_team_action",
        AgentActionType.REPAIR: "_repair_action",
    }

    repair_incident_types = {
        IncidentType.GVS_RISER_FAILURE, IncidentType.GVS_PIPE_FAILURE,
        IncidentType.HVS_RISER_FAILURE, IncidentType.HVS_PIPE_FAILURE,
    }

    def __init__(self, config: RewardConfig | None = None):
        self.config = config or RewardConfig()

    def calculate_action_reward(self, env, action: AgentAction) -> float:
        handler_name = self.ACTION_HANDLERS.get(action.action_type)
        if handler_name is None:
            return 0.0
        return getattr(self, handler_name)(env, action)

    def calculate_step_reward(self, env) -> float:
        total_severity = sum(
            inc.severity for inc in env.simulator.active_incidents)
        reward = -total_severity * self.config.active_incident_penalty_multiplier
        if len(env.simulator.active_incidents) == 0:
            reward += self.config.no_incidents_bonus
        if len(env.simulator.active_incidents) > env.max_active_incidents:
            reward += self.config.too_many_incidents_penalty
        return reward

    def _get_element(self, env, action: AgentAction):
        if not action.target_id:
            return None
        if action.target_type == "node":
            return env.node_by_id.get(action.target_id)
        if action.target_type == "edge":
            return env.edge_by_id.get(action.target_id)
        return None

    def _deploy_team_action(self, env, action: AgentAction) -> float:
        element = self._get_element(env, action)
        if not element:
            return self.config.invalid_target_penalty

        building_idx = getattr(env, "building_idx", 0)
        if not env.state_machine.can_deploy(building_idx, action.target_id):
            return self.config.deploy_precondition_penalty
        env.state_machine.deploy(building_idx, action.target_id)
        incidents = env.simulator.get_incidents_on_element(element)
        return self.config.deploy_incident_reward if incidents else self.config.deploy_no_incidents_penalty

    def _withdraw_team_action(self, env, action: AgentAction) -> float:
        element = self._get_element(env, action)
        if not element:
            return self.config.invalid_target_penalty
        building_idx = getattr(env, "building_idx", 0)
        if not env.state_machine.has_team(building_idx, action.target_id):
            return self.config.withdraw_no_team_penalty
        env.state_machine.withdraw(building_idx, action.target_id)
        incidents = env.simulator.get_incidents_on_element(element)
        return self.config.withdraw_active_incidents_penalty if incidents else self.config.withdraw_no_incidents_reward

    def _repair_action(self, env, action: AgentAction) -> float:
        element = self._get_element(env, action)
        if not element:
            return self.config.invalid_target_penalty
        building_idx = getattr(env, "building_idx", 0)
        if not env.state_machine.can_repair(building_idx, action.target_id):
            return self.config.repair_no_team_penalty
        incidents = env.simulator.get_incidents_on_element(element)
        if not incidents:
            return self.config.repair_no_incidents_penalty
        reward = 0.0
        for inc in incidents:
            if inc.incident_type in self.repair_incident_types:
                reduction = action.get_effectiveness() * self.config.repair_effectiveness_multiplier
                inc.severity = max(0, inc.severity - reduction)
                reward += reduction * self.config.repair_severity_multiplier
                if inc.severity < self.config.resolve_severity_threshold:
                    env.simulator.resolve_incident(inc.incident_id)
                    reward += self.config.repair_resolved_bonus
                    logger.info(f"Incident {inc.incident_id} resolved")
        return reward
