# Plan de privacidad de Primitiva IA

Estado: migración parcial; existe el repositorio privado `danielMigales/Primitiva-IA-motor` y se ha probado la publicación selectiva. La lógica del Laboratorio aún está expuesta en `app.js` público. El repositorio original continúa público y la aplicación sigue dependiendo de GitHub Pages.

## Arquitectura objetivo
- Repositorio privado ya creado: motor, scripts de aprendizaje, pruebas, estrategias congeladas, documentación interna y datos experimentales.
- Repositorio público mínimo: sitio estático y los archivos estrictamente necesarios para la web.
- Publicación de datos públicos: transferencia automática controlada desde el repositorio privado, sin credenciales en archivos públicos.
- Mantener trazabilidad de las predicciones previas al sorteo, sin reescribir registros históricos.

## Dependencias verificadas
- `index.html` carga `app.js`; el Laboratorio ejecuta su lógica de selección y backtest en el navegador. Por tanto, publicar `app.js` revela su algoritmo: no basta con ocultar scripts Python.
- El sitio utiliza `data/sorteos.json` y archivos de `data/reto-*.json` para mostrar resultados.
- El widget Android fue retirado del repositorio público el 2026-10-12; no debe considerarse una dependencia activa.
- `.github/workflows/actualizar.yml` y `reto-automatico.yml` generan y escriben archivos en el repositorio actual.
- GitHub Pages está activado en el repositorio público.

## Orden seguro de migración
1. Crear un repositorio PRIVADO nuevo desde GitHub, por ejemplo `primitiva-IA-motor`; comprobar permisos del conector.
2. Copiar allí los algoritmos y scripts, la memoria técnica y el historial de predicciones, conservando historial y referencias. No borrar ni cambiar la estrategia congelada.
3. Diseñar el Laboratorio público sin exponer el algoritmo: una versión pública limitada o un servicio privado con autenticación; no insertar tokens en JavaScript, APK o Pages.
4. Configurar Actions privadas para actualizar el histórico y generar predicciones; publicar únicamente JSON y recursos autorizados en el repositorio público mediante credenciales de mínimo privilegio.
5. Verificar la web, las actualizaciones, los enlaces y el registro previo al sorteo.
6. Solo entonces retirar del repositorio público los archivos sensibles. ATENCIÓN: eliminarlos del último commit no los elimina del historial Git ni de copias existentes. Para confidencialidad futura, valorar un repositorio público nuevo sin historial antiguo y migrar Pages; evaluar impacto de la URL de la web.
7. Comprobar el acceso del propietario al repositorio privado desde ChatGPT/GitHub tras la migración.

## Advertencias
- Convertir el repositorio original en privado ahora puede romper Pages o su acceso, según las condiciones de GitHub.
- Ninguna estrategia que ya estuvo pública puede considerarse secreta retroactivamente.
- El repositorio privado y la publicación selectiva ya se comprobaron, pero la migración de toda la lógica pública sigue pendiente.
