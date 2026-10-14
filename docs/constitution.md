# 📜 Constitución del Proyecto — autonomous-software-factory
## Principios Innegociables del Software

1. **Simplicidad del Stack:** Python 3.12+, tipado estricto con Pydantic/dataclasses, Pytest. Cero dependencias pesadas sin justificación técnica.
2. **La Spec Manda:** El código refleja la spec aprobada; nada se implementa sin estar en `spec.md`.
3. **Clean Architecture y Funciones Puras:** Desacoplamiento total entre dominio y conectores. Inyección de dependencias y de `current_date`.
4. **Política de Tests (TDD):** 100% de tests en verde en `py -m pytest`. Ningún agente escribe código de producción sin un test que falle primero.
5. **Seguridad y Aislamiento:** Cero credenciales o secretos en código. Datos sensibles en variables de entorno `.env`.
6. **Rigor e Idioma:** Nombres técnicos claros, convenciones de commit formales y documentación verificable sin alucinación.
