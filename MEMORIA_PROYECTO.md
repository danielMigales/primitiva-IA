# MEMORIA DEL PROYECTO — PRIMITIVA IA

Actualizado: 2026-10-12. Fuente principal: archivos existentes en este repositorio y cambios comprobados en GitHub. Este documento conserva el contexto del proyecto aunque se borren conversaciones de ChatGPT. **No equivale a recuperar literalmente todos los chats anteriores.**

## 1. Identidad y propósito
- Repositorio: https://github.com/danielMigales/primitiva-IA (rama principal: `main`).
- Aplicación: **LA PRIMITIVA CHATGPT PREDICTOR**, web instalable (PWA) con un widget Android independiente.
- Objetivo: estudiar resultados históricos de La Primitiva, generar combinaciones experimentales, contrastar estrategias con pruebas cronológicas y registrar predicciones anteriores a los sorteos.
- Prioridad acordada: **conservar lo que funciona, revisar antes de cambiar y avanzar mediante cambios pequeños y verificables**.
- Principio científico: un sorteo justo es aleatorio; **no existe ventaja predictiva demostrada** en el proyecto. No presentar patrones ni backtests exploratorios como garantías de acierto.

## 2. Aplicación web
- `index.html`: interfaz, sección **Laboratorio**, **RETO PREDICTOR**, explicación de metodología y datos históricos.
- `app.js`: carga/validación de sorteos, estadísticas, selección experimental, backtest, presentación de combinaciones, últimos cinco sorteos y panel del Reto Predictor.
- `manifest.json`: configuración de aplicación web instalable.
- Laboratorio: selector **5, 20, 50, 100, 500, 1000 y Todos**; botón **Analizar y generar**.
- El motor calcula frecuencias, retrasos, parejas, tríos y puntuaciones, y muestra una prueba retrospectiva frente a una referencia aleatoria. La selección del Laboratorio es experimental y **distinta** de la estrategia congelada del Reto Predictor.
- La opción **50 sorteos** se añadió el 2026-10-12 al selector de `index.html`, sin modificar el motor, que ya acepta cualquier tamaño numérico de ventana. Commit: `2ee9cbb01b6942bd2f5319c7ef69dc99e09d323c`.
- El código de `app.js` exige al menos 30 sorteos válidos para habilitar el botón; por tanto la opción de 5 y 20 requiere revisar si su disponibilidad es coherente con el diseño original (no cambiarla sin decidirlo).
- Los últimos cinco sorteos se muestran con resaltado de números repetidos.
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
- `scripts/generar_reto.py`: genera una predicción prospectiva a partir de la estrategia congelada, evitando registrar duplicados y usando solo sorteos anteriores al objetivo.
- `scripts/guardar_reto.py`: valida e incorpora registros, con comprobaciones de fechas, números y ventanas admitidas.
- `.github/workflows/reto-automatico.yml` y `guardar-reto.yml`: automatización/registro.
- Predicción existente al revisar el repositorio: objetivo **2026-10-12**, números **12, 17, 20, 24, 34, 40**, ventana 50, histórico hasta 2026-10-10. El JSON indica registro manual por commit y advierte que el timestamp del commit es la referencia de auditoría.
- **Atención técnica pendiente:** `scripts/guardar_reto.py` admite ventanas 5, 20, 100, 500, 1000 y 99999, pero no 50. Esto puede bloquear registros manuales con ventana 50; la opción nueva del Laboratorio no cambia automáticamente este validador. Revisar antes de modificarlo.

## 5. Estrategia congelada (no cambiar inadvertidamente)
- `data/reto-estrategia-congelada.json`: versión 1, estado `frozen`, fecha 2026-10-12.
- Estrategia: **parejas, ventana 50**, puntuación `greedy-pair-v1`; objetivo: **tres o más números principales**.
- `scripts/generar_reto.py` implementa la estrategia congelada; identificador `frozen-pair-50-v1`.
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

## 7. Widget Android
- Proyecto independiente en `android-widget/`, con código Java y configuración Gradle.
- Muestra la última combinación registrada en `data/reto-predictor.json`; al tocarlo abre la web.
- `.github/workflows/compilar-widget-android.yml`: compilación de APK de pruebas.
- Según `android-widget/README.md`, solicita actualización cada 30 minutos sujeta a Android y conexión; el APK de pruebas no está firmado para Play Store.

## 8. Mapa de archivos principales
- Interfaz: `index.html`, `app.js`, `manifest.json`.
- Histórico: `data/sorteos.json`, `update_data.py`.
- Predicciones: `data/reto-predictor.json`, `data/reto-estrategia-congelada.json`, `scripts/generar_reto.py`, `scripts/guardar_reto.py`.
- Aprendizaje: `scripts/aprender_reto.py`, `data/reto-aprendizaje.json`, archivos `data/reto-entrenamientos*.json` y `data/reto-*robustez.json`.
- Automatización: `.github/workflows/`.
- Android: `android-widget/`.

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
- Revisar la inconsistencia del validador de ventanas de `scripts/guardar_reto.py` respecto a 50 sorteos.
- Comprobar las opciones de 5 y 20 sorteos frente al mínimo de 30 registros requerido por la interfaz.
- Verificar la ejecución real de workflows y el estado de GitHub Pages/Android; la presencia de archivos **no demuestra** que todas las automatizaciones estén funcionando.
- Esperar la muestra prospectiva mínima prevista antes de evaluar cambios a la estrategia congelada.
- Las conversaciones borradas no pueden reconstruirse palabra por palabra desde el repositorio; añadir aquí cualquier decisión anterior que el usuario recuerde y que aún no esté documentada.

---
**Guía de continuidad:** este archivo es la memoria técnica durable del proyecto, no una promesa de memoria automática de ChatGPT. En un chat nuevo, basta pedir: «Abre el repositorio danielMigales/primitiva-IA, lee MEMORIA_PROYECTO.md y continuemos».


## 11. Privacidad y migración (2026-10-12)
El propietario quiere proteger el código de predicción manteniendo la web y el widget funcionales. Se confirmó que el repositorio original sigue público, con GitHub Pages activado; `app.js` ejecuta el algoritmo del Laboratorio en el navegador y el widget usa la URL pública del JSON de predicciones. Se creó `PLAN_PRIVACIDAD.md` (commit `19a4c522ddf6662cf1c129e8dec1db8a6552b99d`) con el orden de migración a un motor privado y un frontend público mínimo. **No se ha creado todavía el repositorio privado ni se ha cambiado la visibilidad**; la conexión disponible no ofrece operaciones de administración para ello. Evitar cambios que rompan Pages o la publicación automática. Las copias públicas anteriores no pueden retirarse retroactivamente.


## 13. Segunda fase de copia privada (2026-10-12)
Se copiaron a `danielMigales/Primitiva-IA-motor`: `update_data.py`, `diagnostico_selae.py`, `probar_selae.py`, `data/sorteos.json` y cinco workflows de actualización, reto y diagnóstico. En el repositorio privado, `actualizar.yml` y `reto-automatico.yml` se cambiaron a **solo `workflow_dispatch`** (sin cron) para no duplicar las ejecuciones del repositorio público; no se alteraron los workflows públicos. Comprobado que `app.js` descarga por rutas relativas `data/sorteos.json`, `data/reto-predictor.json` y `data/reto-aprendizaje.json`. Queda pendiente configurar la publicación selectiva y evitar exponer la lógica del Laboratorio ejecutada en el navegador. Las copias privadas no implican retirada de material público.
