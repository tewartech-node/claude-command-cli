"""
Safety Rules: Your 3 governance rules enforced in code
1. "Will it harm?" → Cannot do it
2. "Will it cause chaos?" → Should not do it
3. "Will it cause destruction?" → Must not do it
"""


class SafetyRules:
    """Enforce your 3 rules on every decision"""

    # Your 3 Sacred Rules
    RULE_1 = "Will it harm?"
    RULE_2 = "Will it cause chaos?"
    RULE_3 = "Will it cause destruction?"

    def __init__(self):
        self.blocked_count = 0
        self.allowed_count = 0

    def can_execute(self, action: dict) -> bool:
        """Check if action violates any rules"""

        # Rule 1: "Will it harm?"
        if self._check_harm(action):
            self._log_blocked(action, self.RULE_1)
            return False

        # Rule 2: "Will it cause chaos?"
        if self._check_chaos(action):
            self._log_blocked(action, self.RULE_2)
            return False

        # Rule 3: "Will it cause destruction?"
        if self._check_destruction(action):
            self._log_blocked(action, self.RULE_3)
            return False

        self.allowed_count += 1
        return True

    def _check_harm(self, action: dict) -> bool:
        """Rule 1: Would this harm systems/data/users?"""

        # Prevent unencrypted secret access
        if action.get("accesses_secrets"):
            if not action.get("encrypted"):
                return True

        # Prevent security compromise
        if action.get("modifies_security"):
            return True

        # Prevent privacy violation
        if action.get("violates_privacy"):
            return True

        return False

    def _check_chaos(self, action: dict) -> bool:
        """Rule 2: Would this cause chaos/instability?"""

        # Prevent production changes without safeguards
        if action.get("target") == "production":
            if not action.get("has_rollback"):
                return True
            if not action.get("has_approval"):
                return True

        # Prevent critical config changes
        if action.get("modifies_critical_config"):
            return True

        # Prevent uncontrolled scaling
        if action.get("scales_infrastructure"):
            if not action.get("has_limits"):
                return True

        return False

    def _check_destruction(self, action: dict) -> bool:
        """Rule 3: Would this cause permanent destruction?"""

        # Agent can NEVER delete, destroy, or erase
        action_type = action.get("type", "").upper()
        if action_type in ["DELETE", "DESTROY", "ERASE", "DROP", "PURGE"]:
            return True

        # Prevent permanent data loss
        if action.get("causes_data_loss"):
            return True

        # Prevent unrecoverable changes
        if action.get("is_unrecoverable"):
            return True

        return False

    def _log_blocked(self, action: dict, rule: str):
        """Log blocked action"""
        self.blocked_count += 1
        action_name = action.get("name", "unknown")
        print(f"❌ BLOCKED: '{action_name}' violates '{rule}'")

    def get_stats(self) -> dict:
        """Get safety statistics"""
        total = self.blocked_count + self.allowed_count
        return {
            "blocked": self.blocked_count,
            "allowed": self.allowed_count,
            "total": total,
            "violation_rate": (
                self.blocked_count / total if total > 0 else 0
            )
        }

    @staticmethod
    def create_safe_action(
        name: str,
        command: str,
        args: dict = None,
        **kwargs
    ) -> dict:
        """Create a safe action (helper)"""
        return {
            "name": name,
            "command": command,
            "args": args or {},
            **kwargs
        }

    @staticmethod
    def create_protected_action(
        name: str,
        command: str,
        args: dict = None,
        has_rollback: bool = True,
        has_approval: bool = True,
        encrypted: bool = True,
        **kwargs
    ) -> dict:
        """Create a protected action for sensitive operations"""
        return {
            "name": name,
            "command": command,
            "args": args or {},
            "has_rollback": has_rollback,
            "has_approval": has_approval,
            "encrypted": encrypted,
            **kwargs
        }
