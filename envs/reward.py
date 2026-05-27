from __future__ import annotations

from dataclasses import dataclass
from loguru import logger

from incident_simulator import IncidentType
from .agent_action import AgentAction
from .agent_action_type import AgentActionType


@dataclass(frozen=True)
class RewardConfig:
    invalid_target_penalty: float = -1.0
    deploy_incident_reward: float = 5.0
    deploy_no_incidents_penalty: float = -2.0
    deploy_precondition_penalty: float = -5.0
    repair_no_team_penalty: float = -10.0
    repair_no_incidents_penalty: float = -2.0
    repair_effectiveness_multiplier: float = 0.8
    repair_severity_multiplier: float = 15.0
    repair_resolved_bonus: float = 50.0
    repair_success_bonus: float = 20.0
    withdraw_no_team_penalty: float = -5.0
    withdraw_no_incidents_reward: float = 0.1
    withdraw_active_incidents_penalty: float = -5.0
    active_incident_penalty_multiplier: float = 1.0
    no_incidents_bonus: float = 0.0
    too_many_incidents_penalty: float = -5.0
    max_incident_age: int = 72
    overdue_penalty: float = -100.0
    resolve_bonus_decay_rate: float = 0.7
    min_resolve_bonus_factor: float = 0.3
    severity_discount_rate: float = 0.05
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

        # TODO: добавить здесь функцию из теории перспектив Канемана-Тверски
        return getattr(self, handler_name)(env, action)

    def calculate_step_reward(self, env) -> float:
        reward = 0.0

        new_overdue_ids = {
            inc.incident_id
            for inc in env.simulator.active_incidents
            if inc.is_overdue
            and inc.incident_id not in getattr(env, 'penalized_overdue_incident_ids', set())
        }

        if hasattr(env, 'penalized_overdue_incident_ids'):
            env.penalized_overdue_incident_ids.update(new_overdue_ids)

        if new_overdue_ids:
            penalty = self.config.overdue_penalty * len(new_overdue_ids)
            reward += penalty
            logger.warning(
                f"⚠️ New overdue incidents: {len(new_overdue_ids)}, penalty: {penalty}")

        total_discounted_severity = 0.0
        for inc in env.simulator.active_incidents:
            age = env.current_step - inc.start_time

            if inc.is_overdue and age > self.config.max_incident_age:
                hours_overdue = age - self.config.max_incident_age
                decay = 1.0 - \
                    (self.config.severity_discount_rate * hours_overdue / 24.0)

                inc.severity = max(0.01, inc.severity * max(decay, 0.1))

            if inc.is_overdue:
                discount_factor = 0.3
            else:
                discount_factor = 1.0

            total_discounted_severity += inc.severity * discount_factor

        reward -= total_discounted_severity * \
            self.config.active_incident_penalty_multiplier

        if len(env.simulator.active_incidents) == 0:
            reward += self.config.no_incidents_bonus

        if len(env.simulator.active_incidents) > env.max_active_incidents:
            reward += self.config.too_many_incidents_penalty

        return reward

    def _resolve_bonus_factor(self, incident, current_step: int) -> float:
        age = current_step - incident.start_time

        if age <= self.config.max_incident_age:
            factor = 1.0 - (age / self.config.max_incident_age) * \
                (1.0 - self.config.min_resolve_bonus_factor)
        else:
            hours_overdue = age - self.config.max_incident_age
            factor = self.config.min_resolve_bonus_factor * \
                (self.config.resolve_bonus_decay_rate ** (hours_overdue / 24))

        return max(self.config.min_resolve_bonus_factor, factor)

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

        if not incidents:
            return self.config.deploy_no_incidents_penalty

        return self.config.deploy_incident_reward

    def _withdraw_team_action(self, env, action: AgentAction) -> float:
        element = self._get_element(env, action)
        if not element:
            return self.config.invalid_target_penalty

        building_idx = getattr(env, "building_idx", 0)
        if not env.state_machine.has_team(building_idx, action.target_id):
            return self.config.withdraw_no_team_penalty

        env.state_machine.withdraw(building_idx, action.target_id)
        incidents = env.simulator.get_incidents_on_element(element)

        if incidents:
            return self.config.withdraw_active_incidents_penalty
        return self.config.withdraw_no_incidents_reward

    # def _repair_action(self, env, action: AgentAction) -> float:
    #     element = self._get_element(env, action)
    #     if not element:
    #         return self.config.invalid_target_penalty

    #     building_idx = getattr(env, "building_idx", 0)
    #     if not env.state_machine.can_repair(building_idx, action.target_id):
    #         return self.config.repair_no_team_penalty

    #     incidents = env.simulator.get_incidents_on_element(element)
    #     if not incidents:
    #         return self.config.repair_no_incidents_penalty

    #     reward = 0.0
    #     for inc in incidents:
    #         if inc.incident_type in self.repair_incident_types:
    #             reduction = action.get_effectiveness() * self.config.repair_effectiveness_multiplier
    #             old_severity = inc.severity
    #             inc.severity = max(0, inc.severity - reduction)

    #             reward += (old_severity - inc.severity) * \
    #                 self.config.repair_severity_multiplier

    #             if inc.severity < self.config.resolve_severity_threshold:
    #                 factor = self._resolve_bonus_factor(inc, env.current_step)
    #                 bonus = self.config.repair_resolved_bonus * factor
    #                 reward += bonus

    #                 env.simulator.resolve_incident(inc.incident_id)

    #                 age = env.current_step - inc.start_time
    #                 status = "overdue" if inc.is_overdue else "timely"
    #                 logger.info(
    #                     f"✅ Incident {inc.incident_id} resolved ({status}), age={age}, bonus_factor={factor:.2f}, total_bonus={bonus:.1f}")

    #     return reward

    # def _repair_action(self, env, action: AgentAction) -> float:
    #     element = self._get_element(env, action)
    #     if not element:
    #         return self.config.invalid_target_penalty

    #     building_idx = getattr(env, "building_idx", 0)
    #     if not env.state_machine.can_repair(building_idx, action.target_id):
    #         return self.config.repair_no_team_penalty

    #     incidents = env.simulator.get_incidents_on_element(element)
    #     if not incidents:
    #         return self.config.repair_no_incidents_penalty

    #     reward = 0.0
    #     for inc in incidents:
    #         if inc.incident_type in self.repair_incident_types:
    #             reward += 2.0

    #             reduction = action.get_effectiveness() * self.config.repair_effectiveness_multiplier
    #             old_severity = inc.severity
    #             inc.severity = max(0, inc.severity - reduction)

    #             severity_reduction = (old_severity - inc.severity)
    #             if severity_reduction > 0:
    #                 reward += severity_reduction * self.config.repair_severity_multiplier * 2  # удвоить

    #             if inc.severity < self.config.resolve_severity_threshold:
    #                 factor = self._resolve_bonus_factor(inc, env.current_step)
    #                 bonus = self.config.repair_resolved_bonus * factor
    #                 reward += bonus
    #                 env.simulator.resolve_incident(inc.incident_id)
    #                 logger.info(f"✅ Incident resolved, bonus: {bonus:.1f}")

    #     return reward

    def _repair_action(self, env, action: AgentAction) -> float:
        element = self._get_element(env, action)
        if not element:
            return self.config.invalid_target_penalty

        building_idx = getattr(env, "building_idx", 0)
        if not env.state_machine.can_repair(building_idx, action.target_id):
            logger.debug(
                f"REPAIR attempted without team at {building_idx}:{action.target_id}")
            return self.config.repair_no_team_penalty

        incidents = env.simulator.get_incidents_on_element(element)
        if not incidents:
            return self.config.repair_no_incidents_penalty

        reward = 0.0
        any_repaired = False

        for inc in incidents:
            if inc.incident_type in self.repair_incident_types:
                reduction = action.get_effectiveness() * self.config.repair_effectiveness_multiplier
                old_severity = inc.severity
                inc.severity = max(0, inc.severity - reduction)

                if old_severity > inc.severity:
                    any_repaired = True
                    severity_reduction = (old_severity - inc.severity)
                    reward += severity_reduction * self.config.repair_severity_multiplier

                if inc.severity < self.config.resolve_severity_threshold:
                    factor = self._resolve_bonus_factor(inc, env.current_step)
                    bonus = self.config.repair_resolved_bonus * factor
                    reward += bonus
                    env.simulator.resolve_incident(inc.incident_id)
                    logger.info(
                        f"✅ Incident {inc.incident_id} resolved, bonus={bonus:.1f}")

        if any_repaired:
            reward += self.config.repair_success_bonus

        return reward
