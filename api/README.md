# Consulta oficial al abrir la aplicación

Servicio público desplegado: https://primitiva-resultados-daniel.wittyeel5.chatgpt.site/api/resultados

Identidad de Sites: appgprj_6ad134e99da481919a166eb639dc71bc.
La URL de consulta está configurada en `results-config.js`.
El código desplegado corresponde a `api/resultados.mjs`.

GitHub Pages sirve archivos estáticos. SELAE no envía Access-Control-Allow-Origin
en su servicio de resultados, por lo que la app necesita este pequeño intermediario.
El servidor solo consulta un destino fijo de SELAE: no admite URLs arbitrarias,
credenciales, datos personales ni escrituras en GitHub. La respuesta CORS permite
la aplicación existente en https://danielmigales.github.io.

La apertura, la vuelta a primer plano y el botón de comprobación solicitan los
resultados. El histórico, los aciertos, las repeticiones y las evidencias se
recalculan juntos a partir de la respuesta validada. Las predicciones anteriores
se conservan; no se crean apuestas retrospectivas. La actualización de las 22:15
sigue guardando el histórico central. La consulta al abrir actualiza la sesión.

Una consulta correcta que no contiene sorteos esperados muestra las fechas aún
no publicadas. Un error de red, formato o servidor conserva el histórico y muestra
un fallo de consulta: no se afirma que SELAE no ha publicado algo que no se pudo
comprobar. Las discrepancias con resultados ya verificados detienen la mezcla.

Comprobaciones: `node --test tests/test_live_results.cjs tests/test_app.cjs`.
