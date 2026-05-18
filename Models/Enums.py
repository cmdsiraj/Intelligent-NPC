from enum import Enum


class BeliefType(Enum):
    RELATIONAL = 1   # describes an action between two entities (X did Y to Z)
    ATTRIBUTE  = 2   # describes a quality of a single entity (X is Y)


class Polarity(Enum):
    POSITIVE =  1
    NEGATIVE = -1


class EventType(Enum):
    # ── Relational — actions between two entities ──────────────────────────────
    THEFT   = 1    # taking something that isn't yours
    MURDER  = 2    # eliminating someone
    RESCUE  = 3    # saving someone from harm
    DONATE  = 4    # giving freely with no expectation
    TRADE   = 5    # mutual exchange, both parties benefit
    ACCUSE  = 6    # publicly blaming someone
    REPORT  = 7    # passing information to a third party
    PATROL  = 8    # monitoring, observing, keeping watch
    BETRAY  = 9    # breaking a trust or alliance
    PRAISE  = 10   # publicly endorsing or vouching for someone
    GOSSIP  = 11   # sharing unverified information about someone

    # ── Attribute — beliefs about a single entity's character ─────────────────
    IS_GOOD        = 1001
    IS_THIEF       = 1002
    IS_TRUSTWORTHY = 1003
    IS_DANGEROUS   = 1004
    IS_LOYAL       = 1005
    IS_DISHONEST   = 1006
    IS_HARDWORKING = 1007
    IS_MANIPULATIVE= 1008

    def get_belief_type(self) -> BeliefType:
        return BeliefType.ATTRIBUTE if self.value >= 1000 else BeliefType.RELATIONAL

    def get_polarity(self) -> Polarity:
        positive = {
            self.RESCUE, self.DONATE, self.TRADE, self.PRAISE,
            self.IS_GOOD, self.IS_TRUSTWORTHY, self.IS_LOYAL, self.IS_HARDWORKING
        }
        return Polarity.POSITIVE if self in positive else Polarity.NEGATIVE

    def get_base_belief(self) -> float:
        high   = {self.THEFT, self.MURDER, self.BETRAY, self.IS_THIEF, self.IS_DANGEROUS, self.IS_DISHONEST, self.IS_MANIPULATIVE}
        medium = {self.RESCUE, self.DONATE, self.PRAISE, self.ACCUSE, self.IS_GOOD, self.IS_TRUSTWORTHY, self.IS_LOYAL}
        low    = {self.TRADE, self.IS_HARDWORKING, self.REPORT}
        vlow   = {self.GOSSIP, self.PATROL}
        if self in high:   return 0.8
        if self in medium: return 0.6
        if self in low:    return 0.4
        if self in vlow:   return 0.25
        return 0.2


class EventRole(Enum):
    ACTOR   = 1   # the one performing the action
    TARGET  = 2   # the one the action is directed at
    WITNESS = 3   # present, aware, not directly involved


class CharacterRole(Enum):
    # ── Behavioural archetypes (scenario-agnostic) ────────────────────────────
    LEADER     = 1   # takes charge, initiates, high authority
    MEDIATOR   = 2   # peacekeeper, neutral, de-escalates conflict
    COMPETITOR = 3   # driven to win, measures self against others
    HELPER     = 4   # gives freely, high trust, others rely on them
    ANALYST    = 5   # observes and collects before acting
    NEWCOMER   = 6   # outsider building trust, uncertain standing
    WORKER     = 7   # focused, task-driven, avoids unnecessary drama
    INSTIGATOR = 8   # stirs things up, thrives on tension

    # ── Occupational roles (classic / medieval) ───────────────────────────────
    GUARD      = 101
    MERCHANT   = 102
    BLACKSMITH = 103
    TEACHER    = 104
    PRIEST     = 105
    FARMER     = 106

    def get_description(self) -> str:
        _desc = {
            "LEADER":     "takes charge, initiates action, carries natural authority",
            "MEDIATOR":   "keeps the peace, stays neutral, de-escalates conflict",
            "COMPETITOR": "driven to win, constantly measuring self against others",
            "HELPER":     "gives freely, trusted by all, others rely on them heavily",
            "ANALYST":    "observes and collects information before acting",
            "NEWCOMER":   "outsider still building trust, position is uncertain",
            "WORKER":     "focused and task-driven, avoids unnecessary drama",
            "INSTIGATOR": "stirs things up, thrives on tension and conflict",
            "GUARD":      "enforces rules, protective, driven by authority",
            "MERCHANT":   "trades and networks, always seeking value and leverage",
            "BLACKSMITH": "skilled and practical, reliable, action over words",
            "TEACHER":    "educates and guides, truth-seeking, principled",
            "PRIEST":     "morally driven, community-focused, spiritual authority",
            "FARMER":     "hardworking and grounded, sustains others quietly",
        }
        return _desc.get(self.name, "")
