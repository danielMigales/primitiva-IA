# Widget Android de La Primitiva
Proyecto Android independiente de la web existente. El widget muestra la última combinación registrada en `data/reto-predictor.json` y al tocarlo abre la web dentro de la aplicación. No guarda el histórico de predicciones en el teléfono.
## Compilación
GitHub Actions > Compilar widget Android > Run workflow. Descargar el artefacto `Primitiva-Predictor-Widget-APK`, extraer el ZIP e instalar `app-debug.apk` en Android. Es una compilación de pruebas, no un APK firmado para distribución en Play Store.
La actualización automática del widget depende de Android (intervalo solicitado: 30 minutos); requiere conexión. Los datos mostrados son la última predicción registrada, no necesariamente el próximo sorteo.
