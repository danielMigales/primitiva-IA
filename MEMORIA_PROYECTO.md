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

## 18. Incidencias y cotejo de resultados (2026-10-13)
- Petición: detectar ausencia de predicciones/resultados y distinguir resultados cotejados con SELAE de pendientes.
- Interfaz: nuevo estado del seguimiento, próximo sorteo según calendario configurado (lunes/jueves/sábado), aviso de predicción ausente desde las 14:00 del día anterior y de resultado ausente desde las 12:00 del día siguiente, hora de Madrid. Se deja margen a los workflows; son avisos al cargar la página, sin mensajes ni notificaciones externas.
- Cada resultado reciente y evaluado muestra cotejo completo, solo números cotejados, pendiente o discrepancia. Solo se admite evidencia SELAE con fecha, copia de seis números, timestamp y URL de fuente; debe coincidir con los valores mostrados. El antiguo archivo de reintegros aislados no se trata como prueba de verificación de la combinación completa.
- Nuevo `data/verificacion-sorteos.json`: registro separado de cotejos, inicialmente vacío. `data/estado-actualizacion.json`: estado de cada ejecución futura, inicialmente `not-run`. No se añaden cotejos ficticios ni se reescriben resultados históricos.
- `update_data.py`: publica cotejos incluso de resultados ya existentes sin reescribir el histórico; informa fuente no disponible, histórico inválido y conflictos de números/reintegro. Ante conflicto no publica nuevos valores ni pruebas parciales del lote.
- Parser: acepta únicamente JSON inequívoco con fecha exacta, juego LAPR si consta, seis enteros válidos y reintegro explícito. HTML no se interpreta como resultado.
- Workflow de actualización: guarda informe y cotejos, y conserva el estado de fallo si hubo conflicto; el error no queda oculto como ejecución correcta. CI incluye las nuevas pruebas y archivos.
- Comprobaciones: 18 pruebas de frontend y 15 Python (33 en total), con horarios de Madrid, margen de actualización, fuente inaccesible, cotejo parcial/completo, conflictos sin escritura y parser estricto.
- Limitación observada: el endpoint existente devolvió HTTP 200 con HTML desde este entorno; al abrir la página oficial del 12/10/2026 se redirigió a aviso de geobloqueo de SELAE. No se acreditó ningún cotejo oficial nuevo. La automatización queda preparada para guardar evidencias cuando reciba JSON oficial válido; sigue pendiente disponer de una fuente oficial accesible en el entorno de ejecución.
- Motor de recencia v2, predicciones registradas y archivo de sorteos preservados. Los avisos no garantizan puntualidad de GitHub Actions ni sustituyen el cotejo oficial.
- Archivos: app, HTML, actualizador, informes separados, pruebas, workflows y esta memoria. Commit: el que incorpora esta sección.

## 19. Resaltado de aciertos (2026-10-13)
- Continuación autorizada del siguiente punto sugerido: comparación visual de predicciones y resultados.
- La predicción más reciente, si ya tiene resultado, y cada registro histórico resuelto muestran sus números acertados con borde y símbolo ✓. Se identifica también el reintegro acertado, exclusivamente si estaba registrado y consta en el resultado.
- Se muestra debajo la combinación publicada para facilitar la comparación. La marca dispone de etiqueta accesible y no depende solo del color. Una predicción pendiente no recibe marcas.
- Se mantiene visible el estado de cotejo SELAE junto al resultado; resaltar una coincidencia con el histórico no certifica su fuente.
- Comprobaciones: 21 pruebas frontend y 15 Python (36 total), incluidos aciertos principales/reintegro, predicciones pendientes y comparación de registros anteriores.
- Archivos: `app.js`, `index.html`, `tests/test_app.cjs` y esta memoria. Sin cambios de motor, estrategia, combinaciones o resultados. Commit: el que incorpora esta sección.

## 20. Evaluación retrospectiva CDM adaptado y KNN (2026-10-13)
- Petición: evaluar los candidatos investigados manteniendo recencia v2 activa.
- Nuevo experimento v1 en `scripts/evaluar_metodos.py`; configuración fijada antes de ejecutar en `data/evaluacion-metodos-config.json`, sin búsqueda de parámetros.
- Muestra: últimos 1.000 sorteos del histórico de 3.000, del 2019-03-02 al 2026-10-12, con 2.000 sorteos anteriores al primer objetivo. Walk-forward: cada combinación usa solo registros anteriores a su objetivo; una combinación por método y sorteo. Solo números principales.
- CDM adaptado: media posterior Dirichlet sobre frecuencias de aparición de los 49 números, prior uniforme de 1 y todo el pasado. No reproduce el modelo por posiciones numéricas del artículo; con este prior su ranking coincide con números calientes.
- KNN: estado del sorteo anterior codificado en 49 variables binarias, distancia de diferencia simétrica, 20 vecinos entre las últimas 500 transiciones históricas; empate por transición más reciente y, al escoger números, valor ascendente.
- Recencia: se extrae únicamente la función pura de ranking del generador actual, sin ejecutar su registro. Control: una combinación uniforme por objetivo y semilla fija 20261013. Referencia adicional: 2.000 réplicas bajo la distribución hipergeométrica; seis contrastes unilaterales (tres métodos x dos métricas) ajustados por Holm.
- Resultado (aciertos totales / sorteos con 3+): CDM adaptado 716/24; KNN 723/10; recencia v2 779/18; control uniforme 731/18. Referencia teórica: 734,694 aciertos y 18,638 sorteos con 3+.
- Ningún método obtuvo cinco ni seis aciertos. Ningún contraste supera el umbral 0,05 después del ajuste. Recencia: p ajustado de aciertos totales 0,19490; CDM adaptado: p ajustado de 3+ 0,65467. No se declara ventaja ni se cambia la estrategia.
- Limitaciones: histórico ya inspeccionado/utilizado en experimentos anteriores, no prueba prospectiva ni muestra completamente intacta; datos sin cotejo oficial completo; las implementaciones son adaptaciones especificadas, no clones de servicios comerciales. Holm no corrige toda la búsqueda previa del proyecto.
- Artefactos: resumen `data/evaluacion-metodos.json` y detalle de las 1.000 comparaciones en `data/evaluacion-metodos-detalle.jsonl`, con combinaciones, objetivos, corte histórico y aciertos. Se guardan SHA256 del histórico, generador y estrategia activa para reproducir la ejecución.
- Pruebas: seis nuevas comprobaciones (no usar resultados futuros, reproducibilidad, igual presupuesto de combinaciones, validación, ranking bayesiano y ajuste Holm); 42 pruebas totales (21 frontend y 21 Python).
- Motor, estrategia, predicciones prospectivas y sorteos preservados. Archivos: evaluador, configuración, resultados separados, pruebas, CI y memoria. Commit: el que incorpora esta sección.

## 21. Fuente oficial SELAE resuelta mediante notas de prensa (2026-10-13)
- Petición explícita: resolver la fuente SELAE. Se comprobó que la ruta antigua era HTML y que el buscador JSON oficial, con sus parámetros de fechas correctos, devolvía HTTP 406 tanto localmente como desde GitHub Actions (prueba read-only, commit fac5a9988c34c5a14f456ae1b02503b8ad89d0cb).
- Fuente accesible: PDFs oficiales publicados por el Departamento de Comunicación en `https://www.loteriasyapuestas.es/f/loterias/documentos/La%20Primitiva/Notas%20de%20prensa/`. Se descargó, extrajo y revisó visualmente la nota del 12/10/2026.
- `update_data.py` usa ahora estos PDFs, con límite de tamaño, firma PDF, dominio oficial, una página, cabecera de La Primitiva y fecha/weekday exactos. Se extraen únicamente seis números, complementario y reintegro del bloque de combinación, ignorando premios y Joker. Se valida complementario distinto de los principales y reintegro 0–9.
- Los nombres publicados alternan día/mes con o sin cero y SÁBADO/SABADO; se admiten convenciones acotadas, y solo HTTP 404 permite intentar el siguiente nombre. Otros errores y documentos ambiguos no se convierten en cotejos.
- Ventana reciente ampliada a 10 días para cubrir los cinco sorteos recientes. Descarga real y cotejo completo de 03/10, 05/10, 08/10, 10/10 y 12/10/2026: números y reintegro coinciden con el histórico existente.
- `data/verificacion-sorteos.json` conserva estos cinco cotejos con URL individual, timestamp y SHA256 del PDF. `data/estado-actualizacion.json`: confirmed, cinco resultados recibidos, sin conflictos. `data/sorteos.json` no se reescribe porque no hay resultados nuevos.
- Dependencia: `pypdf==6.10.0`, instalada por los workflows que ejecutan pruebas Python o actualizan resultados. El workflow read-only `fuente-selae.yml` ahora descarga la nota oficial y exige coincidencia con el último resultado.
- Comprobaciones locales: 46 pruebas (25 Python y 21 frontend), incluyendo fechas equivocadas, otro juego, bloques ambiguos, campos concatenados por la extracción PDF, duplicados y conflictos sin sustitución.
- La actualización diaria sigue programada a las 09:00 UTC. Si SELAE cambia el diseño o el nombre de una nota fuera de las convenciones reconocidas, se informa el fallo y se conserva el histórico.
- Esto verifica cinco resultados recientes, no los 3.000 sorteos completos ni el origen de todos los registros anteriores. Motor v2, predicciones y estrategia congelada preservados.
- Archivos: actualizador, lector/prueba de acceso, dependencia, workflows, cotejos/informe, pruebas y memoria. Commit: el que incorpora esta sección.

## 22. Auditoría reanudable del histórico (2026-10-13)
- Se revisan internamente los 3.000 registros: fechas, seis bolas únicas 1–49, reintegro 0–9 y fechas duplicadas. Sin errores estructurales; no demuestra completitud del calendario ni veracidad de resultados.
- Advertencia: los metadatos de cobertura declaran 2.999 sorteos/reintegros, frente a 3.000 existentes. Se registra en el informe sin reescribir el histórico.
- Primer lote real: 25 sorteos coinciden con SELAE (los cinco anteriores más veinte, desde 17/08 hasta 12/10/2026), números y reintegro; sin discrepancias.
- Cuatro consultas reales adicionales (01/01/2000, 02/01/2010, 02/01/2020 y 29/02/2024) agotaron las convenciones de nombre con HTTP 404. Se registran como documentos no localizados; no equivale a resultados incorrectos ni a inexistencia de otras fuentes oficiales.
- `scripts/auditar_historico.py` y `data/auditoria-historico.json`: progreso por fecha, SHA256 del histórico y de cada registro, comprobación estructural completa, evidencias individuales oficiales, discrepancias, documentos ausentes y errores separados. Reutiliza cotejos válidos y vuelve a revisar un registro si cambia.
- Solo las coincidencias generan entradas en `data/verificacion-sorteos.json`; los conflictos conservan el resultado oficial en el informe y retiran el cotejo anterior de esa fecha. Nunca escribe `sorteos.json`, predicciones, estrategias o evaluaciones.
- Los errores de acceso/red/formato detienen el lote y señalan el fallo; los 404 no impiden continuar con otras fechas. `fullyVerified` solo será true si todos los registros coinciden también en reintegro; terminar las consultas no equivale a verificarlo todo.
- Workflow `auditar-historico.yml`: diariamente a las 05:30 UTC, hasta 50 fechas pendientes y presupuesto de 10 minutos comprobado entre fechas; cinco fechas al publicar el workflow. Guarda el progreso y la evidencia. Concurrencia de auditoría limitada a una ejecución; push normal, sin forzar.
- Revisión explícita de documentos ausentes o discrepancias: `python scripts/auditar_historico.py --date AAAA-MM-DD` (repetible). Las fechas deben estar en el histórico.
- Ocho nuevas pruebas de reanudación, cambios del histórico, conflicto sin sobrescritura, retirada de cotejo anterior, documentos ausentes, errores que detienen el lote y reintegro incompleto. Total: 54 pruebas (33 Python y 21 frontend), superadas.
- La auditoría oficial completa sigue pendiente; las cifras del informe deben consultarse para el progreso actual, que aumentará en ejecuciones posteriores.


## 23. Motor adaptativo v3 (2026-10-17)
El usuario pide sustituir el recálculo fijo por aprendizaje real. Esta nueva petición sustituye la espera de 30 sorteos de v2: se archiva su configuración en `data/reto-estrategia-v2.json` y su generador en `scripts/generar_reto_v2.py`, conservando todas las predicciones. La del 17/10 permanece intacta; el nuevo motor comienza con las siguientes predicciones.

`scripts/modelo_adaptativo.py` implementa dos modelos logísticos online: principales y reintegro. Aprenden cuatro pesos (frecuencias normalizadas de 30/90/365 días y aparición anterior) y sesgos individuales, con descenso por gradiente regularizado después de cada resultado. Hiperparámetros fijos, sin selección por resultados de evaluación. El entrenamiento se reproduce cronológicamente desde cero sobre el histórico completo en cada ejecución; no duplica actualizaciones ni depende de un checkpoint obsoleto. Cada predicción se calcula antes de usar su resultado para ajustar los parámetros. Reintegros ausentes no generan etiquetas falsas.

`data/modelo-adaptativo.json` conserva pesos, cambios de los últimos cinco sorteos, hash del histórico/parámetros, puntuaciones de la siguiente propuesta y evaluación exploratoria sobre el último 20% del histórico (con 120 sorteos mínimos de calentamiento). Compara aciertos con el motor v2 archivado y referencia matemática uniforme, y error Brier con probabilidades uniformes. No es validación prospectiva ni demuestra ventaja; `hasDemonstratedAdvantage` permanece false. El histórico no está auditado completamente. El modelo puede aprender y rendir peor; no ocultar esa distinción ni sustituir los parámetros para maquillar resultados.

`generar_reto.py` entrena también si el próximo sorteo ya tiene predicción, sin sustituirla. Los workflows guardan el informe junto con las nuevas predicciones. La app carga el informe y muestra qué pesos cambiaron, hasta qué sorteo se entrenó y cómo rinde; separa la versión 3 de resultados anteriores. Las consultas de sesión a SELAE no entrenan el modelo del servidor: lo hace el proceso de actualización central después de guardar datos. El 404 del servicio de resultados al abrir sigue pendiente y no se resuelve con este cambio.

La comparación histórica de métodos anterior sigue usando explícitamente v2, con su código archivado; no se presenta como evaluación del nuevo motor. Las pruebas incluyen aprendizaje de una señal sintética, predicción antes de actualizar, determinismo, datos inválidos, reintegros ausentes, comparación fiel con v2, integración del generador, preservación del registro y visualización del informe.


## 24. Control de mejoras v4 (2026-10-17)
Petición: evaluar las mejoras antes de aplicarlas. `scripts/control_modelo.py` mantiene un campeón con pesos congelados (inicialmente el modelo v3 entrenado hasta el 15/10) y candidatos congelados, preparados cuando hay histórico nuevo. El entrenamiento v3 sigue produciendo aspirantes, pero sus pesos no se aplican a la combinación designada sin aprobar el control. Configuración v3 archivada en `data/reto-estrategia-v3.json`.

Cada candidato se compara con el campeón en 60 sorteos posteriores a su entrenamiento. Se guardan antes de cada sorteo puntuaciones completas de ambos, IDs, fecha de registro y corte del histórico en `data/control-modelo.json`. No se reconstruyen comparaciones retrospectivas. El código exige registro anterior a las 21:40 de Madrid y objetivo posterior al histórico. El commit acredita la publicación. Los resultados faltantes no se cuentan y una corrección de un resultado evaluado detiene el proceso para revisión.

Una sola decisión por ensayo, sin inspecciones repetidas para ascender antes: menor Brier medio, prueba unilateral exacta de signos a favor del candidato frente al campeón y a la probabilidad uniforme en los dos canales (principales y reintegro), y aciertos no inferiores al campeón ni a la expectativa uniforme en ambos. Umbral por comparación en el ensayo e: 0,05 / (4*e*(e+1)); gasto conservador de alfa entre cuatro comparaciones y sucesivos ensayos. No implica garantía ni ventaja demostrada. Si se rechaza, el campeón conserva exactamente sus pesos. Si se acepta, se copia el candidato evaluado, sin sustituirlo por un modelo reentrenado sin probar. Un nuevo ensayo usa un candidato entrenado con el histórico entonces disponible.

Las predicciones ya publicadas se conservan. Las nuevas entradas se etiquetan versión 4 y guardan ID de pesos aceptados y fecha de entrenamiento. Las características se calculan con los sorteos previos a cada objetivo, manteniendo los pesos congelados. La app muestra entrenamiento y control por separado, progreso 0/60, última decisión, motivo y comparación de aciertos. Al activar v4 no existen comparaciones prospectivas ni cambios aprobados: espera un sorteo nuevo para preparar el primer candidato distinto del campeón. El fallo 404 del servicio de sesión sigue fuera de este cambio.

El generador exige el estado de control persistido; si falta, falla sin adoptar silenciosamente un modelo nuevo. Los workflows guardan el estado junto con el informe y las nuevas predicciones. Pruebas de aceptación/rechazo, muestra insuficiente, ambos canales y referencias, empate, alfa entre ensayos, congelación de pesos, registros inmutables, límites horarios, resultados corregidos, estado ausente y representación en la app.


## 25. Resultados, balance y calidad de datos (2026-10-17)
Petición: reparar consulta a SELAE, ampliar balance de cada sorteo, detectar errores/huecos y conservar historial de cambios. Se revisó el Site appgprj_6ad134e99da481919a166eb639dc71bc: despliegue del 15/10 aún pendiente y sin URL publicada. La republicación de esa versión tuvo éxito; la dirección existente ya responde. Cloudflare rechazaba `redirect: error`; corregido a manual con rechazo de respuestas no exitosas. Se agregó AbortController, ruta raíz de estado y registro del error de fuente.

Comprobación real: JSON SELAE HTTP 403 desde el Worker. Alternativa PDF implementada con unpdf, extracción por posiciones, validación estricta de una página, cabecera, fecha, ocho bolas y URLs oficiales acotadas. Una nota real del 15/10 se pudo descargar localmente y su extracción coincide. Desde el Worker, los PDF también devuelven HTTP 403; última consulta real 20:43 Madrid. No afirmar que la consulta directa funciona: el 404 está resuelto pero el servicio devuelve 502 por bloqueo de fuentes. La actualización central Python/GitHub es independiente y sigue pudiendo cotejar cinco resultados. Si alguna fuente o fecha funciona, se conserva su evidencia individual sin descartar resultados correctos por otra fecha fallida. Fechas inaccesibles y PDF no localizados no se confunden con publicación pendiente. Código y detalles en api/README.md; fuente Sites y versiones guardadas.

`scripts/calidad_datos.py` revisa todos los registros: fechas reales/no futuras, duplicados, seis números distintos 1–49 y reintegro 0–9 (los ausentes se cuentan y no se inventan). Detecta calendario incorrecto y huecos internos en los últimos 90 días; los sorteos posteriores al último guardado se marcan pendientes, sin afirmar su estado de publicación. `data/calidad-datos.json`: 3.001 registros, sin errores ni huecos recientes y 320 cotejos completos en el momento de esta edición. No implica auditoría total. El generador escribe el informe y se detiene antes de entrenar o modificar pesos/predicciones si hay errores o huecos internos. Workflows guardan el informe de fallo y señalan ejecución fallida.

La app muestra calidad del histórico, fecha de revisión, cobertura oficial y pendientes; el balance del último sorteo incorpora el tamaño del ajuste de pesos correspondiente, identificado como reproducción cronológica. Se añade historial visible de decisiones con candidatos aceptados y rechazados, fecha, motivo, muestras, aciertos y IDs. Se conservan los paneles de incidencias/seguimiento previamente ocultos por petición del usuario. Sin modificar combinaciones registradas ni pesos del campeón. Pruebas de entradas inválidas, huecos/pendientes, ausencia de reintegro, error de calendario, bloqueo antes de escritura, error de red, parcialidad de PDF, URLs/evidencias y representación de balance/calidad/decisiones.


Canal adicional: RSS oficial de La Primitiva, validado localmente con siete resultados. Se prueba después del JSON y antes de PDF; ofrece enlace individual a cada escrutinio. Desde el servidor Sites la consulta siguió devolviendo 502 a las 20:46; no afirmar que la consulta directa esté reparada aunque el alojamiento ya esté publicado. Fuente Sites final 6af042754c07af7198672163c939e5e10461fa0e (versión 6). Pruebas finales: 50 Python y 45 Node, 95 en total. Completadas localmente, incluida conservación de resultados frente a fuentes parciales y controles de RSS. La app distingue el fallo de consulta de la ausencia de un resultado, y conserva el histórico central.


## 26. Consulta directa retirada; actualizaciones centrales con reintentos (2026-10-17)
Petición explícita del usuario después de explicar las consecuencias: retirar la consulta directa, conservar actualización central, añadir reintentos y mostrar última comprobación. La app ya no carga results-config.js/live-results.js ni llama a PrimitivaLive. results-config.js deja el endpoint en null. El servicio y el código histórico se conservan, sin usar desde la aplicación; no se elimina el Site ni se cambia su audiencia.

Al abrir, volver a primer plano o pulsar “Actualizar resultados publicados” se descargan los archivos centrales sin caché. La cabecera muestra la última comprobación central en hora de Madrid usando checkedAt (intento, no garantía de éxito), el último sorteo guardado, fuentes no disponibles y resultados esperados aún no incorporados. No atribuye la falta de archivo a que SELAE no haya publicado. Un informe ausente/inválido no inventa hora de revisión. Se elimina la frase de calidad que prometía consulta directa de sesión.

Workflow actualizar.yml: lunes/jueves/sábado a las 22:15, 22:30, 22:45 y 23:15, Europe/Madrid; recuperación martes/viernes/domingo a las 08:15. Son horas previstas, sujetas a las demoras de GitHub Actions. Cada intento conserva la cadena de cotejo, calidad, entrenamiento, control de candidatos y registro de la siguiente predicción; los registros existentes se preservan. No se modifican pesos ni predicciones al retirar la consulta.

Pruebas del recorrido real: abrir no llama al servicio aunque esté disponible en globalThis; se usan los resultados publicados; hora de comprobación en Madrid; estado de fuente no disponible; informe ausente; sorteo esperado pendiente de incorporar; ausencia de scripts de consulta en HTML. Las pruebas de la lógica retirada se conservan para auditarla, sin activarla en la app.


## 27. Interfaz compacta sin actualización manual (2026-10-17)
Petición: quitar botón de actualizar y hacer desplegable cada apartado. Se retiran el botón y su manejador. Los ocho apartados visibles usan details/summary nativos, inicialmente cerrados: actualización automática, combinación, control de mejoras, entrenamiento, balance, calidad, historial y últimos sorteos. Mantienen los IDs de los contenidos y sus datos; se abren con toque o teclado y conservan el estado abierto al actualizar su contenido. Los paneles de incidencias y seguimiento siguen ocultos por la petición anterior. Lectura al abrir o volver a primer plano y horarios centrales preservados. No hay consultas a SELAE desde el navegador. Comprobación de sintaxis, suite existente y revisión de estructura HTML.
