import asyncio
import os
from typing import Any, Optional
from autonomous_software_factory.engines.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerTrippedError,
)


class AntigravityWorkerAdapter:
    """
    Adapter interfacing with the Google Antigravity Agent Runtime SDK.
    Injects safety circuit breakers into thought streams and tool calls,
    preventing runaway loops and oscillations before execution occurs.
    """

    def __init__(
        self,
        role: str = "Coder",
        simulate_oscillation: bool = False,
    ):
        self.role = role
        self.simulate_oscillation = simulate_oscillation

    def execute_agent_step(
        self,
        prompt: str,
        circuit_breaker: CircuitBreaker,
        tool_name: str = "edit_file",
        tool_args: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Executes a single agent reasoning and action step under CircuitBreaker supervision.
        """
        # 1. Stream & record thoughts
        thought = f"[{self.role}] Formulating minimal patch for prompt: {prompt[:40]}..."
        circuit_breaker.record_thought(thought)

        if tool_args is not None:
            args = tool_args
        else:
            args = {
                "file": "core.py",
                "action": "apply_patch",
                "patch_version": len(circuit_breaker.call_history) + 1,
            }

        # 2. If simulating oscillation bug to test circuit breaker
        if self.simulate_oscillation:
            osc_args = {"file": "core.py", "action": "oscillate_bug"}
            # First execution
            circuit_breaker.verify_safety(tool_name, osc_args)
            circuit_breaker.record_step()
            # Second identical execution will trip anti-oscillation!
            circuit_breaker.verify_safety(tool_name, osc_args)
            circuit_breaker.record_step()

        # Normal execution
        circuit_breaker.verify_safety(tool_name, args)
        circuit_breaker.record_step()

        return {
            "status": "step_executed",
            "role": self.role,
            "tool": tool_name,
            "thought": thought,
        }

    def execute_live_sdk_step(
        self,
        prompt: str,
        circuit_breaker: CircuitBreaker,
        api_key: Optional[str] = None,
        workspace_dir: Optional[str] = None,
        enable_write_tools: bool = False,
    ) -> dict[str, Any]:
        """
        Executes a live agent turn via the official `google-antigravity` Python SDK (`v0.1.23+`),
        intercepting `response.thoughts` and `response.tool_calls` in real time through the
        5-Guard CircuitBreaker (`TRIPPED_OSCILLATION`, `TRIPPED_STEPS`, `TRIPPED_COST`).
        """
        import google.antigravity as agy  # type: ignore

        effective_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        async def _run_sdk_turn() -> dict[str, Any]:
            config_kwargs: dict[str, Any] = {
                "system_instructions": (
                    f"You are the [{self.role}] agent inside the Autonomous Software Factory. "
                    "Formulate minimal, deterministic Vertical Slice patches verified by pytest."
                ),
                "api_key": effective_key,
            }
            if workspace_dir:
                config_kwargs["workspaces"] = [workspace_dir]
            if enable_write_tools:
                config_kwargs["capabilities"] = agy.CapabilitiesConfig()

            config = agy.LocalAgentConfig(**config_kwargs)
            output_chunks: list[str] = []
            tool_calls_count = 0

            async with agy.Agent(config) as agent:
                response = await agent.chat(prompt)

                async for thought in response.thoughts:
                    circuit_breaker.record_thought(f"[{self.role}] {thought}")

                async for call in response.tool_calls:
                    call_args = call.args if isinstance(call.args, dict) else {"raw_args": str(call.args)}
                    circuit_breaker.verify_safety(call.name, call_args)
                    circuit_breaker.record_step()
                    tool_calls_count += 1

                async for token in response:
                    output_chunks.append(str(token))

            return {
                "status": "live_sdk_step_executed",
                "role": self.role,
                "tool_calls_count": tool_calls_count,
                "output": "".join(output_chunks),
            }

        return asyncio.run(_run_sdk_turn())

