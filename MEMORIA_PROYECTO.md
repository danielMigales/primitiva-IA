# MEMORIA DEL PROYECTO — PRIMITIVA IA

Actualizado: 2026-10-13. Fuente principal: archivos existentes en este repositorio y cambios comprobados en GitHub. Este documento conserva el contexto del proyecto aunque se borren conversaciones de ChatGPT. **No equivale a recuperar literalmente todos los chats anteriores.**

## 1. Identidad y propósito
- Repositorio: https://github.com/danielMigales/primitiva-IA (rama principal: `main`).
- Aplicación: **LA PRIMITIVA CHATGPT PREDICTOR**, web instalable (PWA).
- Objetivo: estudiar resultados históricos de La Primitiva, generar combinaciones experimentales, contrastar estrategias con pruebas cronológicas y registrar predicciones anteriores a los sorteos.
- Prioridad acordada: **conservar lo que funciona, revisar antes de cambiar y avanzar mediante cambios pequeños y verificables**.
- Principio científico: un sorteo justo es aleatorio; **no existe ventaja predictiva demostrada** en el proyecto. No presentar patrones ni backtests exploratorios como garantías de acierto.

## 2. Aplicación web
- `index.html`: interfaz actual con combinación designada, explicación individual y últimos cinco sorteos.
- `app.js`: carga el registro de predicciones y el histórico; muestra la predicción más reciente y, cuando consta su resultado, aciertos principales y reintegro. El motor de generación está en Python.
- `manifest.json`: manifiesto con apertura independiente e icono SVG. No hay service worker; no se ha comprobado instalación en Android ni funcionamiento sin conexión.
- El Laboratorio y su selector de ventanas pertenecen a una interfaz anterior; no están presentes en la versión actual. No evaluar sus antiguas opciones como funciones activas.
- Los últimos cinco sorteos muestran colores y etiquetas de repetición.
- La web no almacena en el móvil un historial permanente de predicciones.

## 3. Histórico y actualización
- `data/sorteos.json`: histórico utilizado por la app; en registros de evaluación del 2026-10-12 se indican **4200 sorteos** y fecha histórica máxima **2026-10-10**. Son datos registrados, no una auditoría oficial independiente.
- `update_data.py`: actualización y combinación de datos históricos.
- `.github/workflows/actualizar.yml`: automatización de actualización.
- `diagnostico_selae.py`, `probar_selae.py` y workflows relacionados: pruebas/diagnósticos de fuentes.
- `LEEME.txt` documenta publicación mediante GitHub Pages y actualización sin API de pago; puede contener instrucciones antiguas (por ejemplo, afirmar que no hay histórico precargado), así que **el código y los datos actuales prevalecen**.
- No asumir que la fuente histórica está oficialmente verificada por SELAE: comprobar fechas, integridad y resultados antes de extraer conclusiones.

## 4. Reto Predictor: registro verificable
- `data/reto-predictor.json`: registro versionado de predicciones; los commits GitHub permiten comprobar cuándo quedaron publicadas.
- `scripts/generar_reto.py`: usa `data/reto-estrategia-activa.json` (versión 2, recencia 30/90/365 días) y etiqueta las nuevas entradas con `strategyVersion: 2`. El identificador de implementación `unified-recency-z-30-90-365-v1` se conserva porque el cálculo no cambia. Evita duplicados; parejas/50 queda como versión anterior.
- `scripts/guardar_reto.py`: valida e incorpora registros, con comprobaciones de fechas, números y ventanas admitidas.
- `.github/workflows/reto-automatico.yml` y `guardar-reto.yml`: automatización/registro.
- Predicción existente al revisar el repositorio: objetivo **2026-10-12**, números **12, 17, 20, 24, 34, 40**, ventana 50, histórico hasta 2026-10-10. El JSON indica registro manual por commit y advierte que el timestamp del commit es la referencia de auditoría.
- **Validación corregida (2026-10-13):** ambos scripts usan `scripts/validar_reto.py`, que admite 5, 20, 50, 100, 365, 500, 1000 y 99999. Se valida cada entrada nueva antes de guardar; no se revalidan ni migran registros históricos.

## 5. Estrategia congelada (no cambiar inadvertidamente)
- `data/reto-estrategia-congelada.json`: versión 1, estado `frozen`, fecha 2026-10-12.
- Estrategia: **parejas, ventana 50**, puntuación `greedy-pair-v1`; objetivo: **tres o más números principales**.
- El registro histórico de parejas/50 usa `frozen-pair-50-v1`. El generador actual usa recencia 30/90/365; la configuración congelada se conserva sin cambios. No atribuir sus nuevas predicciones a la estrategia congelada.
- Regla escrita en la configuración: **no cambiar la estrategia hasta registrar y resolver al menos 30 sorteos prospectivos**; cualquier cambio posterior debe crear nueva versión.
- La elección procede de experimentos históricos exploratorios, no de una ventaja demostrada.

## 6. Aprendizaje y experimentos ya documentados
- `scripts/aprender_reto.py`: compara ventanas 20/50/100/500/1000 y modos `hot`, `cold`, `recent`, `balanced`; separa selección histórica y prueba cronológica posterior.
- `data/reto-aprendizaje.json` (2026-10-12): 4200 sorteos; estrategia mostrada **1000/cold**; 960 sorteos reservados; 740 aciertos totales frente a 705,31 esperados; **`hasDemonstratedAdvantage: false`**. Esta estrategia informativa no sustituye la estrategia congelada de parejas/50.
- `data/reto-entrenamientos.json`: cinco pruebas walk-forward, 2400 sorteos de prueba, **43** casos de tres o más aciertos frente a **44,73** esperados al azar.
- `data/reto-entrenamientos-avanzados.json`: 32 estrategias comparadas; 2400 sorteos de prueba, **47** casos de tres o más frente a **44,73** esperados.
- `data/reto-entrenamiento-adicional.json`: cuatro períodos de 300 sorteos; en el experimento de parejas/50 constan **33** casos de tres o más en 1200 sorteos, frente a referencia aleatoria **22,365**. Es un resultado exploratorio con comparaciones múltiples.
- `data/reto-robustez.json`: 13 pruebas cronológicas, 2600 sorteos de prueba, **55** casos de tres o más frente a **48,46** esperados; estrategia reescogida históricamente.
- `data/reto-parejas-trios-robustez.json`: 13 pruebas cronológicas, 2600 sorteos, **69** casos de tres o más frente a **48,46** esperados; selección histórica entre parejas/tríos/mixtas. **No es prueba prospectiva independiente**.
- Los distintos experimentos y períodos pueden solaparse; **no sumar sus resultados como si fueran muestras independientes**. Tampoco comparar solo la mejor estrategia sin considerar la búsqueda entre muchas variantes.
- Conclusión documentada: resultados interesantes para investigar, **sin evidencia concluyente de ventaja predictiva**.

## 7. Aplicación web
- El proyecto se centra exclusivamente en la aplicación web instalable (PWA).

## 8. Mapa de archivos principales
- Interfaz: `index.html`, `app.js`, `manifest.json`.
- Histórico: `data/sorteos.json`, `update_data.py`.
- Predicciones: `data/reto-predictor.json`, `data/reto-estrategia-congelada.json`, `scripts/generar_reto.py`, `scripts/guardar_reto.py`.
- Aprendizaje: `scripts/aprender_reto.py`, `data/reto-aprendizaje.json`, archivos `data/reto-entrenamientos*.json` y `data/reto-*robustez.json`.
- Automatización: `.github/workflows/`.

## 9. Normas para continuar en futuras conversaciones
1. Localizar y leer **este archivo** y el código actual del repositorio antes de hacer cambios.
2. No pedir al usuario que suba el código si GitHub sigue conectado; repositorio `danielMigales/primitiva-IA`.
3. Distinguir hechos verificados en GitHub, hipótesis y recuerdos de conversación no recuperados.
4. Mantener las funciones existentes salvo petición expresa; preferir cambios mínimos y comprobar su efecto.
5. No modificar sin autorización la estrategia congelada ni reescribir registros históricos de predicciones.
6. Registrar cada avance significativo en esta memoria: fecha, motivo, archivos, pruebas, commit y asuntos pendientes.
7. Revisar conflictos entre la interfaz, validadores, automatizaciones y documentación.
8. Tratar cualquier aparente mejora frente al azar con prudencia estadística y validación prospectiva.

## 10. Pendientes y limitaciones
- Auditar el origen y exactitud de `data/sorteos.json` frente a datos oficiales.
- Resuelta la admisión de 50 y 365 y la validación común. El usuario eligió recencia como versión 2 activa el 2026-10-13; parejas/50 queda preservada como configuración anterior.
- Las opciones antiguas del Laboratorio ya no están en la interfaz actual; revisar solo si se decide recuperarlas.
- Verificar la ejecución real de workflows y el estado de GitHub Pages; la presencia de archivos **no demuestra** que todas las automatizaciones estén funcionando.
- Esperar la muestra prospectiva mínima prevista antes de evaluar cambios a la estrategia congelada.
- Las conversaciones borradas no pueden reconstruirse palabra por palabra desde el repositorio; añadir aquí cualquier decisión anterior que el usuario recuerde y que aún no esté documentada.

---
**Guía de continuidad:** este archivo es la memoria técnica durable del proyecto, no una promesa de memoria automática de ChatGPT. En un chat nuevo, basta pedir: «Abre el repositorio danielMigales/primitiva-IA, lee MEMORIA_PROYECTO.md y continuemos».


## 11. Privacidad y migración (2026-10-12)
El propietario quiere proteger el código de predicción manteniendo la web funcional. Se confirmó que el repositorio original sigue público, con GitHub Pages activado; `app.js` ejecuta el algoritmo del Laboratorio en el navegador y el JSON de predicciones es público. Se creó `PLAN_PRIVACIDAD.md` (commit `19a4c522ddf6662cf1c129e8dec1db8a6552b99d`) con el orden de migración a un motor privado y un frontend público mínimo. **No se ha creado todavía el repositorio privado ni se ha cambiado la visibilidad**; la conexión disponible no ofrece operaciones de administración para ello. Evitar cambios que rompan Pages o la publicación automática. Las copias públicas anteriores no pueden retirarse retroactivamente.


## 13. Segunda fase de copia privada (2026-10-12)
Se copiaron a `danielMigales/Primitiva-IA-motor`: `update_data.py`, `diagnostico_selae.py`, `probar_selae.py`, `data/sorteos.json` y cinco workflows de actualización, reto y diagnóstico. En el repositorio privado, `actualizar.yml` y `reto-automatico.yml` se cambiaron a **solo `workflow_dispatch`** (sin cron) para no duplicar las ejecuciones del repositorio público; no se alteraron los workflows públicos. Comprobado que `app.js` descarga por rutas relativas `data/sorteos.json`, `data/reto-predictor.json` y `data/reto-aprendizaje.json`. Queda pendiente configurar la publicación selectiva y evitar exponer la lógica del Laboratorio ejecutada en el navegador. Las copias privadas no implican retirada de material público.

## 14. Validación del Reto Predictor (2026-10-13)
- Motivo: aceptar ventana 50 y evitar que el flujo automático de ventana 365 eluda la validación manual.
- Cambio mínimo funcional: extraer las comprobaciones existentes a `scripts/validar_reto.py`, añadir 50 y 365 a las ventanas admitidas y llamar al mismo validador antes de incorporar la entrada automática. Las reglas previas de fechas y números se mantienen.
- Archivos: ambos scripts de registro/generación, nuevo validador, `tests/test_reto.py`, ambos workflows del Reto y esta memoria. Los workflows ejecutan las comprobaciones antes del registro.
- Verificación: ocho pruebas con `python -m unittest discover -s tests -v`: ventanas válidas e inválidas, fechas y números, registro manual, duplicados/conflictos, rechazo de lotes sin escritura, generación automática y no-op. Pruebas en directorios temporales; predicciones y revisiones anteriores conservadas. Comparación adicional del generador antes/después: misma entrada y evidencias.
- Estrategia congelada, algoritmo de recencia, archivos de datos e histórico sin cambios. La corrección no convierte el generador en parejas/50.
- Commit: el commit que incorpora esta sección (consultar historial Git de este archivo).
- Limitación: comprobación local de las rutas ejecutadas por ambos workflows; no se lanzan workflows de producción ni se registran predicciones de prueba en el histórico real.

## 15. Revisión de la app (2026-10-13)
- Inspeccionada la web publicada y el código de `main`; la página carga la predicción del 15/10 y los cinco resultados recientes. No se observaron errores de la app en consola; apareció un aviso ajeno, de la extensión del navegador.
- Fallos reproducidos: JSON raíz nulo rompe la carga; números repetidos/no enteros y fechas imposibles se aceptan; explicaciones mal formadas provocan errores o muestran números ajenos; fallo del histórico o resultado pasado ausente se presenta como pendiente; el recuento semanal del reintegro incluye sorteos sin reintegro.
- Corregidos en `app.js`: validación de fechas y seis números únicos, manejo de JSON nulo y evidencias parciales, tarjetas de los números realmente seleccionados, estados de resultado separados con fecha de Madrid y denominador del reintegro limitado a datos válidos.
- `index.html`: nueva versión de caché del script. `tests/test_app.cjs`: nueve pruebas de carga/renderizado con DOM mínimo y sin dependencias; siete fallaban antes de la corrección y nueve pasan después. `.github/workflows/comprobar-app.yml`: comprobación automática del frontend en push/PR.
- Verificación adicional: 3.000 sorteos, máximo 2026-10-12, sin fechas duplicadas ni combinaciones inválidas, todos con reintegro 0–9; no equivale a cotejo oficial. Las ocho pruebas Python del Reto continúan pasando.
- Archivos de datos, estrategia y algoritmo de predicción sin cambios. Commit: el que incorpora esta sección.
- Limitaciones: inspección del navegador en escritorio y pruebas de lógica con DOM mínimo; no es prueba en un dispositivo Android real ni auditoría de la fuente SELAE. La presencia del manifiesto no garantiza capacidades offline.

## 16. Seguimiento de predicciones (2026-10-13)
- Petición: hacer operativo el seguimiento recomendado. Se añade a la web el historial completo de resultados declarados, incluidos cero aciertos, pendientes y ausencia de reintegro; se actualiza al cargar los JSON publicados.
- Resumen por identificador de algoritmo y ventana: registros resueltos, progreso hasta 30, aciertos principales, casos de tres o más y reintegros evaluables. No se mezclan estrategias ni se cuentan revisiones o duplicados como predicciones adicionales.
- Referencia matemática al azar para la misma cantidad de sorteos resueltos: 36/49 aciertos principales esperados por combinación, probabilidad hipergeométrica de tres o más y 0,1 para reintegro. No es simulación retrospectiva ni certificación de ventaja.
- Registro manual: conserva metadatos suministrados de algoritmo, evidencias y reintegro, tras la validación existente; antes los descartaba en entradas nuevas. Nunca sustituye registros existentes.
- Comprobaciones: trece pruebas del frontend y ocho del Reto; resultados por algoritmo, fallos, pendientes, duplicados, cobertura de reintegro, fórmula exacta y conservación de metadatos. Datos y estrategia congelada sin cambios.
- Situación actual: predicción 2026-10-12 de parejas/50 con 1 de 6 aciertos y sin reintegro registrado; predicción 2026-10-15 de recencia/365 pendiente. Son resultados según el histórico publicado, no una auditoría oficial independiente.
- Decisión posterior: el usuario eligió mantener recencia 30/90/365 como nueva versión; implementada en la sección 17. La configuración congelada anterior permanece intacta.
- Archivos: `app.js`, `index.html`, pruebas de app y Reto, `scripts/guardar_reto.py` y esta memoria. Commit: el que incorpora esta sección.

## 17. Estrategia activa versión 2 (2026-10-13)
- Elección explícita del usuario: «Mantener el motor actual: recencia 30/90/365, como nueva versión». Esta elección autoriza una nueva versión antes de completar los 30 sorteos del plan anterior; no altera su archivo ni sus registros.
- Nuevo archivo `data/reto-estrategia-activa.json`: versión 2 activa, pesos 0,45/0,35/0,20 para 30/90/365 días, recorte z a ±3, redondeo principal a cinco decimales y desempate numérico ascendente. Se conserva el ranking de reintegro existente.
- `scripts/generar_reto.py` lee la configuración activa, comprueba que coincide con el método elegido y añade `strategyVersion: 2` y `strategyFile` a las nuevas predicciones. Cambios de parámetros sin nueva implementación detienen la escritura.
- No se renombra el identificador de implementación terminado en v1: el motor matemático es el mismo. La versión de estrategia 2 identifica la nueva etapa prospectiva.
- La interfaz muestra el motor activo y separa la muestra v2 de las predicciones anteriores sin versión de estrategia. Empieza en 0/30; el registro del 15/10 queda intacto y no se reclasifica retrospectivamente.
- Los workflows existentes siguen registrando una entrada por objetivo, sin sustituir combinaciones ya publicadas. El workflow de comprobación verifica ahora frontend y Python, incluidos cambios de configuración o scripts.
- Verificación: catorce pruebas frontend y nueve Python; comprobación de parámetros alterados sin escritura, metadatos conservados y muestras por versión separadas. Comparación en directorios temporales con los 3.000 sorteos reales: mismos números, reintegro y evidencias antes/después; solo se añaden los dos campos de versión.
- Configuración congelada parejas/50, registros de predicción y resultados históricos preservados. Primer hito: 30 sorteos resueltos de v2, sin reajustar automáticamente los parámetros; no equivale a demostrar ventaja.
- Archivos: configuración activa, generador, interfaz, pruebas, workflow de comprobación y esta memoria. Commit: el que incorpora esta sección.
