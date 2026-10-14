# Spec 001 — Autonomous Software Factory: Core Architecture & Closed-Loop Engine

**Estado:** aprobada  
**Autor:** Ronald Solares Chuquera, Ing. Civil Industrial (Univ. de Tarapacá, Top 6%)  
**Dominio:** AI Systems Engineering / Multi-Agent Systems / MLOps / Software Reliability  
**Repositorio Destino:** `C:\Users\ronal\autonomous-software-factory` ➔ `github.com/ronaldreighsrsc/autonomous-software-factory`

---

## 1. Contexto y Objetivo
En 2026, los "wrappers" de IA y los bucles descontrolados `while True` que invocan LLMs representan antipatrones frágiles en entornos de ingeniería: carecen de persistencia transaccional, divergen en bucles de gasto infinito y asumen verbalmente que el código funciona sin compilarlo.

`autonomous-software-factory` es un sistema agéntico industrial basado en **Teoría de Control en Lazo Cerrado**:
- Orquesta un cuarteto de agentes especializados (Specifier, Planner, Coder TDD, Reviewer) sobre un `StateGraph` fuertemente tipado.
- Cada iteración de código está gobernada por un **Oráculo Determinista Externo** (pytest, compiladores y linters).
- Criterio de parada matemático e incorruptible: `exit_code == 0` y cobertura requerida.
- Gobierna los recursos mediante **Loop Budgeting** y **Circuit Breakers** (límite de costo en USD, tope de pasos y detección de oscilaciones por hashing de llamadas a herramientas).

---

## 2. Usuarios y Actores
- **Tech Lead / Ingeniero Humano:** Define requerimientos en sintaxis EARS, autoriza cambios arquitectónicos en puertas de control (Gate 1) e inspecciona auditorías.
- **Specifier Agent:** Analiza el requerimiento o reporte de bug y formaliza la especificación técnica.
- **Planner Agent:** Descompone la spec en tareas atómicas (<30 min) y define contratos tipados con Pydantic.
- **Coder TDD Agent:** Genera primero la prueba en rojo, implementa el código mínimo y ajusta iterativamente tras recibir feedback del oráculo.
- **Reviewer Agent:** Audita calidad de código, tipado estático (Mypy), estilo (Ruff) e invariantes de seguridad.
- **Deterministic Oracle:** Ejecutor de entorno de tests que actúa como sensor de verdad en el lazo de realimentación.

---

## 3. Especificación de Requisitos Formales (EARS)

### Ubiquitous Requirements (Invariantes Universales)
- **EARS-U1 (Oráculo Determinista):** El sistema SIEMPRE utilizará el código de salida del ejecutor de tests (pytest) como única fuente de verdad para el éxito de una implementación, ignorando cualquier aseveración verbal del LLM.
- **EARS-U2 (Circuit Breakers):** El sistema SIEMPRE abortará la ejecución y entrará en modo seguro si una tarea supera los 8 pasos de auto-corrección, consume más de $0.25 USD o ejecuta la misma llamada a herramienta con argumentos idénticos por segunda vez consecutiva (detección de oscilación por hash).
- **EARS-U3 (Aislamiento de Entorno):** El sistema SIEMPRE ejecutará las modificaciones de código y pruebas dentro de un sandbox aislado o directorio acotado, impidiendo la alteración de ramas principales sin aprobación.

### Event-Driven Requirements
- **EARS-E1 (Inyección de Error en Lazo Cerrado):** CUANDO el oráculo de pruebas falle (`exit_code != 0`), el sistema DEBERÁ capturar el stacktrace y el diff relevante, sanitizarlos de tokens redundantes e inyectarlos como observación correctiva al agente codificador.
- **EARS-E2 (Human-in-the-Loop Asíncrono):** CUANDO el flujo alcance un punto de control de arquitectura (Gate 1 o ambigüedad >30%), el sistema DEBERÁ suspender la máquina de estados, persistir el snapshot en SQLite WAL y notificar al usuario sin bloquear hilos del sistema operativo.

### State-Driven Requirements
- **EARS-S1 (Modo Fast-Path vs. Multi-Agent):** MIENTRAS la tarea sea clasificada como bugfix cosmético o de formato, el sistema DEBERÁ resolverla mediante un único agente en TDD directo; MIENTRAS la tarea introduzca nuevas capacidades de esquema o interfaces, DEBERÁ activar el pipeline completo de 4 agentes.

---

## 4. Requisitos No Funcionales
- **RNF-1 (Latencia del Oráculo):** La evaluación determinista del oráculo debe resolver y parsear resultados en menos de 2.0 segundos sobre suites locales.
- **RNF-2 (Persistencia Inmune a Fallos):** Todos los estados y transiciones deben registrarse en SQLite con modo WAL (`PRAGMA journal_mode=WAL`), permitiendo time-travel debugging y rebobinado sin corrupción.
- **RNF-3 (Tipado Estricto):** 100% del código en Python 3.12 con anotaciones de tipo estrictas y validación de esquemas con Pydantic v2.

---

## 5. Criterios de Finalización
- 100% de tests unitarios e integrados pasando en `py -m pytest`.
- Suite de pruebas validando circuit breakers, oráculo determinista, máquina de estados y time-travel en SQLite WAL.
- Cobertura >90% en módulos del núcleo.
