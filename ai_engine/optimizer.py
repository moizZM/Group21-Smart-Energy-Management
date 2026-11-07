"""
Subsystem 3: AI Engine & Optimization
"""

import os
from enum import Enum
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class SubsystemStatus(Enum):
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"


class AlEngine:
    def __init__(self, component_id: int) -> None:
        self._component_id = component_id
        self._status = SubsystemStatus.INITIALIZED

    @property
    def component_id(self) -> int:
        return self._component_id

    def initialize(self) -> SubsystemStatus:
        self._status = SubsystemStatus.RUNNING
        return self._status


class EnergyAdvisor(AlEngine):
    def __init__(self, component_id: int, price_threshold: float = 0.30) -> None:
        super().__init__(component_id)
        self._price_threshold = price_threshold

    def recommend_battery_action(
        self, current_price: float, pv_generation: float
    ) -> str:
        if current_price > self._price_threshold and pv_generation < 1.0:
            return "DISCHARGE"
        elif current_price <= self._price_threshold or pv_generation >= 2.0:
            return "CHARGE"
        return "HOLD"


class Summarizer(AlEngine):
    def __init__(self, component_id: int, model_name: str = "gpt-4o-mini") -> None:
        super().__init__(component_id)
        self._model_name = model_name
        self._api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.client: Optional[Any] = None
        self._init_openai_client()

    def _init_openai_client(self) -> None:
        if self._api_key:
            try:
                from openai import OpenAI

                self.client = OpenAI(api_key=self._api_key)
            except Exception as e:
                print(f"[Warning]: Failed to initialize OpenAI client: {e}")

    def generate_sustainability_coach_report(self, metrics: Dict[str, Any]) -> str:
        prompt = (
            f"Building Energy Metrics:\n"
            f"- Total Cost: ${metrics.get('total_cost_usd', 0.0):.2f}\n"
            f"- Carbon Emitted: {metrics.get('total_carbon_kg', 0.0):.2f} kg\n"
            f"- Sustainability Score: {metrics.get('sustainability_score', 0):.1f}/100\n\n"
            f"Provide a concise, professional 2-sentence energy management recommendation."
        )

        if self.client and self._api_key:
            try:
                response = self.client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a smart grid energy efficiency coach.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=100,
                )
                if response and response.choices and len(response.choices) > 0:
                    msg = response.choices[0].message
                    if msg and msg.content:
                        return (
                            f"[Live OpenAI {self._model_name}]: {msg.content.strip()}"
                        )
            except Exception as e:
                return f"[API Error Fallback]: Could not reach OpenAI ({e}). Recommendation: Shift loads to off-peak hours."

        # Fallback offline report utilizing actual Logic Engine metrics
        return (
            f"AI Sustainability Coach: Total Cost ${metrics.get('total_cost_usd', 0.0):.2f}, "
            f"Carbon Emitted {metrics.get('total_carbon_kg', 0.0):.2f} kg, "
            f"Score {metrics.get('sustainability_score', 0.0):.1f}/100. "
            f"Recommendation: Optimize dishwasher and washing machine schedules during solar generation peaks."
        )
