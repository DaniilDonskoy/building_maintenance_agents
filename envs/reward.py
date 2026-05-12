from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from ..incident_simulator import IncidentType
from .agent_action import AgentAction
from .agent_action_type import AgentActionType


@dataclass(frozen=True)
class RewardConfig:
    insufficient_resources_penalty: float = -5.0
    invalid_target_penalty: float = -1.0

    monitor_no_incidents_reward: float = 0.5
    monitor_active_incidents_penalty: float = -0.1

    withdraw_no_incidents_reward: float = 0.0
    withdraw_active_incidents_penalty: float = -0.2

    deploy_no_incidents_penalty: float = -0.5
    deploy_severity_multiplier: float = 10.0
    deploy_resolved_bonus: float = 20.0

    repair_no_incidents_penalty: float = -0.3
    repair_effectiveness_multiplier: float = 0.5
    repair_severity_multiplier: float = 8.0
    repair_resolved_bonus: float = 15.0

    shut_off_water_reward: float = 3.0
    shut_off_water_penalty: float = -0.5

    inspect_valid_target_reward: float = 0.2
    inspect_invalid_target_penalty: float = -0.5

    backup_amount_multiplier: float = 20.0
    call_backup_reward: float = 5.0

    resource_efficiency_threshold: float = 0.5
    resource_efficiency_reward: float = 0.1
    active_incident_penalty_multiplier: float = 0.2
    no_incidents_bonus: float = 1.0
    too_many_incidents_penalty: float = -2.0

    resolve_severity_threshold: float = 0.05


class CurrentReward:
    ACTION_HANDLERS = {
        AgentActionType.MONITOR: "_monitor_action",
        AgentActionType.DEPLOY_TEAM: "_deploy_team_action",
        AgentActionType.WITHDRAW_TEAM: "_withdraw_team_action",
        AgentActionType.REPAIR: "_repair_action",
        AgentActionType.SHUT_OFF_WATER: "_shut_off_water_action",
        AgentActionType.INSPECT: "_inspect_action",
        AgentActionType.CALL_BACKUP: "_call_backup_action",
    }

    repair_incident_types = {
        IncidentType.GVS_RISER_FAILURE,
        IncidentType.GVS_PIPE_FAILURE,
        IncidentType.HVS_RISER_FAILURE,
        IncidentType.HVS_PIPE_FAILURE,
    }

    def __init__(self, config: RewardConfig | None = None) -> None:
        self.config = config or RewardConfig()

    def calculate_action_reward(self, env, action: AgentAction) -> float:
        cost = action.get_cost()
        if cost > env.resources:
            return self.config.insufficient_resources_penalty

        env.resources -= cost
        env.resources_used += cost

        handler_name = self.ACTION_HANDLERS.get(action.action_type)
        if handler_name is None:
            return 0.0

        return getattr(self, handler_name)(env, action)

    def calculate_step_reward(self, env, action_reward: float) -> float:
        reward = action_reward

        env.resources += env.resource_regen_rate
        env.resources = min(env.resources, env.resource_budget)

        if env.resources > env.resource_budget * self.config.resource_efficiency_threshold:
            reward += self.config.resource_efficiency_reward

        total_severity = sum(inc.severity for inc in env.simulator.active_incidents)
        reward -= total_severity * self.config.active_incident_penalty_multiplier

        if len(env.simulator.active_incidents) == 0:
            reward += self.config.no_incidents_bonus

        if len(env.simulator.active_incidents) > env.max_active_incidents:
            reward += self.config.too_many_incidents_penalty

        return reward

    def _monitor_action(self, env, _action: AgentAction) -> float:
        if len(env.simulator.active_incidents) == 0:
            return self.config.monitor_no_incidents_reward
        return self.config.monitor_active_incidents_penalty

    def _withdraw_team_action(self, env, _action: AgentAction) -> float:
        if len(env.simulator.active_incidents) == 0:
            return self.config.withdraw_no_incidents_reward
        return self.config.withdraw_active_incidents_penalty

    def _deploy_team_action(self, env, action: AgentAction) -> float:
        element = self._get_element(env, action)
        if not element:
            return self.config.invalid_target_penalty

        incidents = env.simulator.get_incidents_on_element(element)
        if not incidents:
            return self.config.deploy_no_incidents_penalty

        reward = 0.0
        applicable_types = action.action_type.applicable_incident_types

        for incident in incidents:
            if incident.incident_type in applicable_types:
                reduction = action.get_effectiveness()
                old_severity = incident.severity
                incident.severity = max(0, incident.severity - reduction)
                incident.duration = max(0, incident.duration - int(reduction * 10))

                severity_reduction = old_severity - incident.severity
                reward += severity_reduction * self.config.deploy_severity_multiplier

                if incident.severity < self.config.resolve_severity_threshold:
                    env.simulator.resolve_incident(incident.incident_id)
                    reward += self.config.deploy_resolved_bonus
                    logger.info(f"Incident {incident.incident_id} resolved by {action.action_type.name}")

        return reward

    def _repair_action(self, env, action: AgentAction) -> float:
        element = self._get_element(env, action)
        if not element:
            return self.config.invalid_target_penalty

        incidents = env.simulator.get_incidents_on_element(element)
        if not incidents:
            return self.config.repair_no_incidents_penalty

        reward = 0.0
        for incident in incidents:
            if incident.incident_type in self.repair_incident_types:
                reduction = action.get_effectiveness() * self.config.repair_effectiveness_multiplier
                incident.severity = max(0, incident.severity - reduction)
                reward += reduction * self.config.repair_severity_multiplier

                if incident.severity < self.config.resolve_severity_threshold:
                    env.simulator.resolve_incident(incident.incident_id)
                    reward += self.config.repair_resolved_bonus

        return reward

    def _shut_off_water_action(self, env, action: AgentAction) -> float:
        element = self._get_element(env, action)
        if not element:
            return self.config.invalid_target_penalty

        incidents = env.simulator.get_incidents_on_element(element)
        if incidents:
            for incident in incidents:
                old_spread_count = incident.spread_count
                incident.spread_count = min(incident.spread_count + 2, incident.incident_type.spread_radius)
                if incident.spread_count > old_spread_count:
                    return self.config.shut_off_water_reward

        return self.config.shut_off_water_penalty

    def _inspect_action(self, env, action: AgentAction) -> float:
        element = self._get_element(env, action)
        if element:
            return self.config.inspect_valid_target_reward
        return self.config.inspect_invalid_target_penalty

    def _call_backup_action(self, env, action: AgentAction) -> float:
        backup_amount = self.config.backup_amount_multiplier * action.resource_multiplier
        env.resource_budget += backup_amount
        env.resources += backup_amount
        return self.config.call_backup_reward

    def _get_element(self, env, action: AgentAction):
        if not action.target_id:
            return None
        if action.target_type == "node":
            return env.node_by_id.get(action.target_id)
        if action.target_type == "edge":
            return env.edge_by_id.get(action.target_id)
        return None
