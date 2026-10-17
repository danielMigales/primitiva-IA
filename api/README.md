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


## Reparación y estado del 17/10/2026
El primer despliegue del 15/10 seguía pendiente y no tenía URL publicada. Se reanudó la publicación el 17/10 y se confirmó el servicio en la dirección existente. Se corrigió además `redirect: error`, que Cloudflare Workers rechaza, usando `manual` y rechazando respuestas 3xx, y se sustituyó el temporizador por AbortController.

El JSON oficial responde HTTP 403 desde el servidor de Sites. Se añadió una alternativa con notas PDF oficiales (mismas convenciones acotadas del actualizador Python), extracción geométrica de una página con unpdf y validación de fecha, juego, seis números, complementario y reintegro. También los PDF devuelven HTTP 403 desde este servidor en la comprobación real del 17/10 a las 20:43 de Madrid. El servicio responde 502 cuando no puede verificar ninguna fuente. El 404 está reparado; la consulta directa NO debe presentarse como operativa mientras SELAE rechace el origen.

Si solo fallan algunas fechas, se devuelven los resultados verificables y `unavailableDates`; la app conserva el histórico para esas fechas y explica que no se pudieron comprobar. Un PDF no localizado no se presenta como prueba de que no haya resultado. Las evidencias conservan la URL individual de cada documento. La actualización central de GitHub Actions usa Python y pudo cotejar cinco resultados; es independiente de este bloqueo del alojamiento.

Fuente Sites sincronizada: commit 9496d473f6f05d6b5ba655935d09064e0edb746c, versión 5. Repositorio Sites conserva package.json, pnpm-lock.yaml, pnpm-workspace.yaml y scripts/build-worker.mjs. El Worker empaqueta unpdf/esbuild. La copia auditable de la lógica está en api/resultados.mjs y api/pdf-results.mjs; la importación de unpdf solo se ejecuta cuando se extrae un PDF. Las pruebas unitarias usan texto de prueba y extractores inyectados, además de la revisión local de una nota PDF real del 15/10. Comprobación completa: node --test tests/test_app.cjs tests/test_live_results.cjs tests/test_pdf_results.cjs.


Se añadió además el canal oficial RSS https://www.loteriasyapuestas.es/es/la-primitiva/resultados/.formatoRSS entre JSON y PDF. Valida juego, título, fecha real, fecha de publicación en Madrid, enlace oficial, combinación única, complementario y reintegro. La descarga local se pudo analizar para siete sorteos de octubre. El despliegue del 17/10 a las 20:46 sigue devolviendo 502 desde Sites: no hay verificación en directo satisfactoria desde ese origen. No confundir la accesibilidad local con la del servidor. Fuente Sites final: 6af042754c07af7198672163c939e5e10461fa0e, versión 6. El archivo api/rss-results.mjs conserva la lógica. Las pruebas añaden tests/test_rss_results.cjs. El canal RSS ausente muestra “aún no muestra el resultado” y no una afirmación sobre todos los canales de SELAE.
