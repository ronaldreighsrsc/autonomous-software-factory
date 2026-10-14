import re


class ReflexionEngine:
    """
    Closed-Loop Reflexion Engine enforcing EARS-E1:
    When the test oracle fails (exit_code != 0), extracts the exact failure diff
    and stacktrace, strips environmental and token-heavy noise, and injects
    a clean corrective prompt into the next TDD iteration.
    """

    NOISE_PATTERNS = [
        r"^platform\s+.*$",
        r"^rootdir:.*$",
        r"^configfile:.*$",
        r"^test session starts.*$",
        r"^plugins:.*$",
        r"^collected \d+ item.*$",
    ]

    def sanitize_output(self, raw_output: str) -> str:
        """Strips redundant header, rootdir and platform tokens."""
        lines = raw_output.splitlines()
        cleaned_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            # Skip noise lines
            if any(re.match(pattern, stripped, re.IGNORECASE) for pattern in self.NOISE_PATTERNS):
                continue
            # Strip pure decorative equals lines
            if re.match(r"^={3,}\s*={3,}$", stripped):
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def build_corrective_observation(self, raw_output: str) -> str:
        """
        Constructs a structured feedback prompt formatted for the Coder agent.
        """
        sanitized = self.sanitize_output(raw_output)

        return (
            "=== OBSERVACIÓN DEL ORÁCULO DE PRUEBAS (FEEDBACK EN LAZO CERRADO) ===\n"
            "El oráculo determinista detectó fallos matemáticos en la suite de pruebas.\n"
            "Tu tarea es corregir la implementación mínima para satisfacer las aserciones.\n\n"
            "--- DETALLE DE FALLOS SANITIZADO ---\n"
            f"{sanitized}\n"
            "------------------------------------\n"
            "INSTRUCCIÓN: No asumas éxito verbal. Modifica el código para que pytest retorne exit_code == 0."
        )
