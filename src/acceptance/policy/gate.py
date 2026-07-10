from __future__ import annotations

from dataclasses import dataclass

from acceptance.matrices.matriz_a import MatrizAResult
from acceptance.matrices.matriz_b import MatrizBResult
from acceptance.matrices.matriz_c import MatrizCResult


@dataclass(frozen=True)
class GateResult:
    matriz_a: bool
    matriz_b: bool
    matriz_c: bool

    @property
    def release_ok(self) -> bool:
        return self.matriz_a and self.matriz_b and self.matriz_c

    @property
    def production_bind(self) -> bool:
        return self.release_ok

    @property
    def demo_mode(self) -> bool:
        return not self.release_ok


def combine_gate(
    ma: MatrizAResult,
    mb: MatrizBResult,
    mc: MatrizCResult,
) -> GateResult:
    return GateResult(
        matriz_a=ma.ok,
        matriz_b=mb.ok,
        matriz_c=mc.ok,
    )
