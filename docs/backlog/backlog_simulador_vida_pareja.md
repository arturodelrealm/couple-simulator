# Backlog --- Simulador de Vida en Pareja

## 1. Visión del producto

Juego de simulación de vida en pareja pensado inicialmente para una
despedida de soltero/a.

Una persona (la novia) responde previamente un conjunto de situaciones.
Sus respuestas quedan guardadas.

Posteriormente, el novio juega la simulación:

1.  Crea/ingresa a la partida.
2.  Elige su avatar.
3.  Parte desde un estado inicial.
4.  Recibe situaciones una por una.
5.  Elige una alternativa.
6.  El estado de la pareja cambia.
7.  La respuesta se compara con la respuesta previamente dada por la
    novia.
8.  La simulación avanza en el tiempo.
9.  Al finalizar se muestra el estado final, la historia de la pareja,
    estadísticas y compatibilidad.

La primera versión debe priorizar:

-   Flujo completo de punta a punta.
-   Persistencia en backend.
-   Frontend amigable.
-   Avatar configurable mediante un subconjunto controlado de opciones
    de DiceBear.
-   Estado visible durante la simulación.
-   Timeline/historial.
-   Capacidad de extender preguntas y reglas sin modificar demasiado
    código.

------------------------------------------------------------------------

# 2. Stack inicial

## Backend

-   Python
-   FastAPI o Django + Django REST Framework
-   Base de datos relacional, preferentemente PostgreSQL
-   API REST
-   Modelos para partidas, jugadores, avatares, preguntas, respuestas y
    estado de simulación.

### Decisión pendiente

-   [ ] Elegir FastAPI vs Django/DRF.
-   [ ] Definir estrategia de migraciones.
-   [ ] Definir autenticación mínima para el acceso privado.

Para una primera versión no es necesario implementar un sistema completo
de usuarios si el juego será de uso personal.

## Frontend

-   React
-   TypeScript
-   Vite
-   CSS o Tailwind CSS
-   DiceBear para generación/renderizado de avatares.

### Objetivo visual

Interfaz de simulador, inspirada en juegos de carrera/simulación:

-   Estado actual siempre visible.
-   Decisión actual destacada.
-   Timeline/historial.
-   Cambios de estadísticas animados de forma sencilla.
-   Avatares como representación visual de los personajes.

------------------------------------------------------------------------

# 3. Arquitectura conceptual

``` text
                         FRONTEND
                            │
                            │ REST API
                            ▼
                         BACKEND
                            │
             ┌──────────────┼──────────────┐
             │              │              │
          Game          Questions       Simulation
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                         DATABASE
```

Conceptos principales:

``` text
Game
 ├── Player A (novia)
 │    └── Avatar
 │
 ├── Player B (novio)
 │    └── Avatar
 │
 ├── Answers
 │    ├── Player A answers
 │    └── Player B answers
 │
 ├── Simulation State
 │
 └── Timeline Events
```

Importante:

-   La respuesta de una persona y el resultado de la simulación son
    conceptos diferentes.
-   La respuesta de la novia se guarda antes de iniciar la simulación
    del novio.
-   La resolución de discrepancias entre respuestas puede mantenerse
    simple en V1.
-   No es necesario diseñar inicialmente un motor complejo que determine
    qué decisión "gana".

------------------------------------------------------------------------

# 4. MVP 0 --- Vertical slice inicial

## Objetivo

Tener una aplicación desplegable que conecte frontend, backend y base de
datos.

El primer milestone NO debe intentar implementar el juego completo.

Debe permitir:

``` text
Crear partida
    ↓
Ingresar nombre de la novia
    ↓
Crear/seleccionar avatar
    ↓
Guardar partida
    ↓
Recuperar partida
```

La idea es validar primero que todos los componentes están conectados.

------------------------------------------------------------------------

## 4.1 Backend mínimo

### Partida

-   [ ] Crear modelo `Game`.
-   [ ] Generar identificador único de partida.
-   [ ] Guardar nombre de la novia.
-   [ ] Guardar estado de la partida.
-   [ ] Crear migraciones.
-   [ ] Crear endpoint para crear partida.
-   [ ] Crear endpoint para obtener una partida.
-   [ ] Crear endpoint para actualizar datos de la novia.

Propuesta inicial:

``` http
POST /api/games
GET  /api/games/{game_id}
PATCH /api/games/{game_id}
```

Ejemplo:

``` json
{
  "name": "María"
}
```

------------------------------------------------------------------------

## 4.2 Avatar mínimo

-   [ ] Definir `AvatarConfig`.
-   [ ] Integrar DiceBear Avataaars.
-   [ ] Definir un subconjunto pequeño de opciones permitidas.
-   [ ] Implementar preview del avatar.
-   [ ] Permitir seleccionar opciones visualmente mediante tarjetas.
-   [ ] Guardar la configuración del avatar en backend.
-   [ ] Recuperar avatar desde backend.

Inicialmente limitar a:

-   2--4 opciones de cabello.
-   2--4 opciones de ojos.
-   3 opciones de ropa.
-   2--3 accesorios.

No intentar exponer todas las opciones disponibles en DiceBear.

------------------------------------------------------------------------

## 4.3 Frontend mínimo

Pantallas:

### Crear partida

``` text
Crear una nueva partida

Nombre de la novia:
[________________]

[Comenzar]
```

### Crear avatar

``` text
Crea tu personaje

             [ AVATAR ]

Cabello
[ avatar ] [ avatar ] [ avatar ]

Ojos
[ avatar ] [ avatar ] [ avatar ]

Ropa
[ avatar ] [ avatar ] [ avatar ]

Accesorios
[ avatar ] [ avatar ]

[Guardar personaje]
```

### Confirmación

``` text
Partida creada

María

[Avatar]

Partida: ABC123

[Continuar]
```

------------------------------------------------------------------------

## 4.4 Deploy inicial

-   [ ] Crear repositorio.
-   [ ] Separar frontend/backend.
-   [ ] Configurar variables de entorno.
-   [ ] Crear Dockerfiles.
-   [ ] Crear configuración para desarrollo local.
-   [ ] Configurar base de datos.
-   [ ] Deploy backend.
-   [ ] Deploy frontend.
-   [ ] Verificar comunicación frontend → backend en producción.
-   [ ] Verificar persistencia en producción.

### Criterio de finalización del MVP 0

Una partida creada desde internet debe poder:

1.  Crear una partida.
2.  Registrar el nombre de la novia.
3.  Crear un avatar.
4.  Guardar el avatar.
5.  Cerrar/recargar la página.
6.  Recuperar la partida y mostrar el avatar.

------------------------------------------------------------------------

# 5. MVP 1 --- Flujo completo de la novia

## Objetivo

Permitir que la novia responda todo el set de preguntas y dejar sus
respuestas guardadas.

### Eventos y preguntas

Un evento puede contener una o varias preguntas. Las respuestas no
necesariamente modifican directamente el estado de la simulación: pueden
acumular variables internas del evento y, al finalizar sus preguntas, el
motor determina un resultado.

``` text
Event
 ├── Questions
 │     └── QuestionOption
 │            └── OptionEffect
 │
 └── EventOutcome
       ├── OutcomeCondition
       └── OutcomeEffect
```

Tareas:

-   [ ] Crear modelo `Event`.
-   [ ] Crear modelo `Question`.
-   [ ] Crear modelo `QuestionOption`.
-   [ ] Crear modelo `OptionEffect`.
-   [ ] Asociar eventos y preguntas a una etapa.
-   [ ] Definir orden de eventos y preguntas.
-   [ ] Crear modelo `EventOutcome`.
-   [ ] Crear modelo `OutcomeCondition`.
-   [ ] Crear modelo `OutcomeEffect`.
-   [ ] Definir variables internas de un evento.
-   [ ] Definir operadores de condiciones (`=`, `!=`, `>`, `>=`, `<`,
    `<=`).
-   [ ] Crear endpoint para obtener un evento y sus preguntas.
-   [ ] Crear endpoint para guardar respuestas.
-   [ ] Crear servicio para evaluar el resultado del evento.
-   [ ] Aplicar los efectos del resultado al `SimulationState`.

Ejemplo:

``` text
Evento: Comprar una casa

Pregunta 1 → home_desire +3 / +1 / -2
Pregunta 2 → home_budget +1 / +2 / +3

home_desire >= 4 AND home_budget >= 2
    → Compran casa
       finances -15
       quality_of_life +10
       compatibility +5

home_desire < 4
    → Siguen arrendando
       finances +5
       quality_of_life +2
```

### Respuestas

``` text
Answer
 ├── game
 ├── player
 ├── question
 └── option
```

### Frontend

-   [ ] Pantalla de preguntas de la novia.
-   [ ] Mostrar una pregunta a la vez.
-   [ ] Mostrar opciones como tarjetas/botones.
-   [ ] Feedback visual al seleccionar.
-   [ ] Avanzar a la siguiente pregunta.
-   [ ] Mostrar progreso, por ejemplo `Pregunta 4 de 15`.
-   [ ] Permitir recuperar una partida incompleta.
-   [ ] Marcar la fase de respuestas como completada.

### Criterio de finalización

La novia puede responder todas las preguntas y sus respuestas quedan
persistidas en backend.

------------------------------------------------------------------------

# 6. MVP 2 --- Inicio del juego del novio

## Objetivo

Permitir que el segundo jugador entre a una partida previamente
preparada.

Flujo:

``` text
Partida existente
      ↓
Novia completó preguntas
      ↓
Novio entra
      ↓
Ingresa nombre
      ↓
Elige avatar
      ↓
Comienza simulación
```

### Backend

-   [ ] Agregar segundo jugador.
-   [ ] Estados de partida:
    -   `CREATED`
    -   `PLAYER_A_READY`
    -   `PLAYER_B_PLAYING`
    -   `FINISHED`
-   [ ] Validar que el novio no pueda comenzar antes de que la novia
    termine.
-   [ ] Guardar avatar del novio.

### Frontend

-   [ ] Pantalla de ingreso del novio.
-   [ ] Flujo de creación de avatar.
-   [ ] Pantalla de inicio de simulación.

------------------------------------------------------------------------

# 7. MVP 3 --- Estado de la simulación

## Estado inicial

Definir un estado inicial simple:

``` json
{
  "age": 22,
  "compatibility": 100,
  "finances": 50,
  "adventures": 50,
  "career": 50,
  "quality_of_life": 50,
  "children": 0
}
```

### Métricas

-   `compatibility`
-   `finances`
-   `adventures`
-   `career`
-   `quality_of_life`
-   `children`

### Reglas

-   [ ] Definir límites para estadísticas, por ejemplo 0--100.
-   [ ] Definir incrementos/decrementos por opción.
-   [ ] Definir cambios de edad.
-   [ ] Definir cuándo se pasa de una etapa a otra.
-   [ ] Definir efectos de cada respuesta.

No implementar todavía un motor complejo de resolución de conflictos.

------------------------------------------------------------------------

# 8. MVP 4 --- Simulación pregunta por pregunta

## Flujo

``` text
Estado actual
     ↓
Mostrar situación
     ↓
Mostrar opciones
     ↓
Novio responde
     ↓
Aplicar efectos
     ↓
Comparar con respuesta de novia
     ↓
Actualizar compatibilidad
     ↓
Registrar evento
     ↓
Mostrar resultado
     ↓
Siguiente pregunta
```

### Backend

-   [ ] Endpoint para obtener la siguiente pregunta.
-   [ ] Endpoint para responder una pregunta.
-   [ ] Aplicar efectos de la opción.
-   [ ] Comparar respuesta del novio con la respuesta de la novia.
-   [ ] Actualizar compatibilidad.
-   [ ] Persistir el nuevo estado.
-   [ ] Registrar evento de timeline.
-   [ ] Impedir responder dos veces la misma pregunta.
-   [ ] Mantener la simulación consistente si el usuario recarga la
    página.

### Frontend

-   [ ] Dashboard principal de simulación.
-   [ ] Mostrar edad/etapa.
-   [ ] Mostrar estadísticas.
-   [ ] Mostrar pregunta actual.
-   [ ] Mostrar opciones.
-   [ ] Animar cambios de estadísticas.
-   [ ] Mostrar feedback después de una decisión.
-   [ ] Botón para continuar.

------------------------------------------------------------------------

# 9. MVP 5 --- Timeline

## Objetivo

Representar visualmente la vida de la pareja.

Ejemplo:

``` text
22 ──────────────────────────────── 40
    │
    ● Primer trabajo
    │
    ● Primer viaje
    │
    ● Se casaron
    │
    ● Primer hijo
    │
    ▼
40 ──────────────────────────────── 60
    │
    ● Compraron casa
    │
    ● Cambio de carrera
```

### Backend

-   [ ] Crear modelo `TimelineEvent`.
-   [ ] Asociar evento a una decisión.
-   [ ] Guardar edad.
-   [ ] Guardar título.
-   [ ] Guardar descripción.
-   [ ] Guardar icono/categoría.
-   [ ] Endpoint para recuperar timeline.

### Frontend

-   [ ] Timeline vertical/horizontal.
-   [ ] Marcar etapa actual.
-   [ ] Destacar evento actual.
-   [ ] Mostrar eventos anteriores.
-   [ ] Añadir transición cuando aparece un nuevo evento.

------------------------------------------------------------------------

# 10. MVP 6 --- Etapas de vida

Definir tres etapas:

``` text
YOUTH
~20–40

ADULT
40–60

ELDERLY
60+
```

### Backend

-   [ ] Agregar `stage` a las preguntas.
-   [ ] Definir rango de edad por etapa.
-   [ ] Definir transición entre etapas.
-   [ ] Definir conjunto de preguntas por etapa.

### Frontend

-   [ ] Mostrar etapa actual.
-   [ ] Cambiar visualmente al cambiar de etapa.
-   [ ] Animación/transición entre etapas.
-   [ ] Cambiar potencialmente la apariencia de los personajes.

------------------------------------------------------------------------

# 11. MVP 7 --- Evolución de avatares

## Objetivo

Hacer que los personajes evolucionen visualmente.

Ejemplo:

``` text
JUVENTUD

👨 👩
casual


       ↓


ADULTEZ

👨 👩
formal / profesional


       ↓


VEJEZ

👴 👵
ropa/accesorios apropiados
```

### Diseño

-   [ ] Mantener identidad base del avatar.
-   [ ] Definir configuración por etapa.
-   [ ] Definir qué atributos pueden cambiar.
-   [ ] Definir subconjunto de opciones para cada etapa.
-   [ ] Generar previews de cada configuración.
-   [ ] Animar transición cuando cambia de etapa.

No intentar implementar envejecimiento realista.

------------------------------------------------------------------------

# 12. MVP 8 --- Hijos

## Objetivo

Representar visualmente a los hijos que aparecen durante la simulación.

### Backend

-   [ ] Crear modelo `Child`.
-   [ ] Guardar nombre opcional.
-   [ ] Guardar fecha/edad de nacimiento dentro de la simulación.
-   [ ] Guardar configuración de avatar.
-   [ ] Definir número máximo de hijos.
-   [ ] Definir cuándo puede aparecer un hijo.

### Avatar

-   [ ] Generar avatar del hijo usando DiceBear.
-   [ ] Utilizar una configuración derivada de los padres o un seed
    propio.
-   [ ] Mantener apariencia consistente.

### Frontend

-   [ ] Mostrar hijos junto a los padres.
-   [ ] Animación simple cuando aparece un nuevo hijo.
-   [ ] Mostrar hijos en timeline.
-   [ ] Mostrar cantidad de hijos en el estado principal.

------------------------------------------------------------------------

# 13. MVP 9 --- Resultado final

Al terminar todas las preguntas:

``` text
SIMULACIÓN COMPLETADA

❤️ Compatibilidad       84
💰 Finanzas             72
✈️ Aventuras            81
💼 Carrera              69
😊 Calidad de vida      87
👶 Hijos                 2
```

### Timeline

Mostrar la historia completa.

### Estadísticas

-   [ ] Estado final.
-   [ ] Evolución de cada estadística.
-   [ ] Máximo/mínimo alcanzado.
-   [ ] Cambios principales.

### Compatibilidad

-   [ ] Porcentaje final.
-   [ ] Cantidad de coincidencias.
-   [ ] Cantidad de diferencias.
-   [ ] Distribución por categoría.
-   [ ] Principales decisiones donde coincidieron.
-   [ ] Principales decisiones donde difirieron.

------------------------------------------------------------------------

# 14. MVP 10 --- Animaciones y polish

Solo después de que el juego sea funcional.

### Animaciones

-   [ ] Cambio de estadísticas.
-   [ ] Barra de progreso.
-   [ ] Aparición de eventos.
-   [ ] Cambio de etapa.
-   [ ] Aparición de hijos.
-   [ ] Transición de avatar.
-   [ ] Feedback al coincidir/no coincidir con la pareja.

### UI

-   [ ] Responsive para celular.
-   [ ] Mejorar tarjetas.
-   [ ] Mejorar tipografía.
-   [ ] Mejorar iconografía.
-   [ ] Loading states.
-   [ ] Error states.
-   [ ] Animaciones de transición entre preguntas.

Prioridad: **funcionalidad antes que animaciones complejas**.

------------------------------------------------------------------------

# 15. Exportación

## Resultado descargable

Objetivo:

``` text
Descargar resultado
        ↓
PDF / imagen / página
```

Contenido:

-   Nombre de la pareja.
-   Avatares finales.
-   Compatibilidad.
-   Estadísticas finales.
-   Timeline.
-   Decisiones principales.
-   Resumen de coincidencias/diferencias.

### Tareas

-   [ ] Definir formato inicial.
-   [ ] Generar página de resultados.
-   [ ] Agregar exportación a PDF.
-   [ ] Agregar opción para compartir resultado mediante URL, si resulta
    útil.

La exportación puede quedar para después de tener el juego funcionando.

------------------------------------------------------------------------

# 16. Modelo de datos preliminar

El modelo se organiza alrededor de **eventos**. Un evento puede contener
una o varias preguntas y producir un resultado cuyos efectos modifican
el estado de la simulación.

``` text
Game
 ├── id
 ├── status
 ├── created_at
 └── updated_at

Player
 ├── id
 ├── game
 ├── role
 ├── name
 └── avatar_config

Event
 ├── id
 ├── stage
 ├── order
 ├── name
 └── description

Question
 ├── id
 ├── event
 ├── order
 └── text

QuestionOption
 ├── id
 ├── question
 └── text

OptionEffect
 ├── id
 ├── option
 ├── variable
 └── value

Answer
 ├── id
 ├── game
 ├── player
 ├── question
 └── option

EventOutcome
 ├── id
 ├── event
 ├── name
 ├── description
 └── order

OutcomeCondition
 ├── id
 ├── outcome
 ├── variable
 ├── operator
 └── value

OutcomeEffect
 ├── id
 ├── outcome
 ├── variable
 └── value

SimulationState
 ├── game
 ├── age
 ├── relationship_status
 ├── compatibility
 ├── finances
 ├── adventures
 ├── career
 ├── quality_of_life
 └── children

TimelineEvent
 ├── id
 ├── game
 ├── age
 ├── stage
 ├── title
 ├── description
 └── category

Child
 ├── id
 ├── game
 ├── name
 ├── birth_age
 └── avatar_config
```

### Flujo de resolución

``` text
Event
  │
  ├── Question 1 ──→ Answer ──→ OptionEffect
  ├── Question 2 ──→ Answer ──→ OptionEffect
  └── Question N ──→ Answer ──→ OptionEffect
                         │
                         ▼
                  Event Variables
                         │
                         ▼
                 Outcome Conditions
                         │
                         ▼
                    Event Outcome
                     │          │
                     ▼          ▼
              SimulationState  TimelineEvent
```

Las respuestas de cada jugador se conservan independientemente del
resultado final del evento. Esto permite cambiar las reglas
posteriormente sin perder las respuestas originales.

El mismo evento puede utilizarse primero con la novia y luego con el
novio:

``` text
                 Event
                   │
          ┌────────┴────────┐
          │                 │
       Novia               Novio
          │                 │
      Answers A         Answers B
          │                 │
          └────────┬────────┘
                   ▼
          Comparación / reglas
                   │
                   ▼
            Compatibility
```

Este modelo es preliminar y puede simplificarse durante la
implementación.

# 17. Principios de diseño

## No sobre-diseñar el motor de simulación

La V1 no necesita una simulación económica realista.

Las opciones pueden tener efectos explícitos:

``` json
{
  "finances": -5,
  "career": 8,
  "adventures": 6,
  "quality_of_life": 3
}
```

## Separar contenido de código

Las preguntas deberían poder agregarse/modificarse sin tener que cambiar
la lógica principal.

Idealmente:

``` text
Question
  ↓
Options
  ↓
Effects
```

en lugar de tener reglas hardcodeadas por pregunta.

## Mantener las decisiones simples inicialmente

En V1:

``` text
respuesta novio == respuesta novia
    → aumenta/mantiene compatibilidad

respuesta novio != respuesta novia
    → reduce compatibilidad
```

El algoritmo exacto para resolver discrepancias puede diseñarse
posteriormente.

## Evitar simulación excesivamente granular

No simular cada año.

Usar:

``` text
Juventud
Adultez
Vejez
```

con un conjunto reducido de eventos representativos.

------------------------------------------------------------------------

# 18. Orden recomendado de implementación

### Fase A --- Vertical slice

-   [ ] Repositorio.
-   [ ] Backend.
-   [ ] Frontend.
-   [ ] Base de datos.
-   [ ] Crear partida.
-   [ ] Nombre de novia.
-   [ ] Avatar.
-   [ ] Persistencia.
-   [ ] Deploy.

**Objetivo:** tener una aplicación online funcional aunque todavía no
sea un juego.

### Fase B --- Primer juego jugable

-   [ ] Preguntas.
-   [ ] Respuestas de novia.
-   [ ] Persistencia de respuestas.
-   [ ] Segundo jugador.
-   [ ] Estado inicial.
-   [ ] Preguntas del novio.
-   [ ] Cambios de estado.
-   [ ] Compatibilidad básica.

**Objetivo:** poder jugar una partida completa con pocas preguntas.

### Fase C --- Experiencia

-   [ ] Timeline.
-   [ ] Etapas.
-   [ ] Animaciones.
-   [ ] Evolución de avatares.
-   [ ] Hijos.
-   [ ] Mejoras visuales.

### Fase D --- Resultado

-   [ ] Estadísticas.
-   [ ] Compatibilidad detallada.
-   [ ] Resumen.
-   [ ] Exportación.
-   [ ] Compartir resultado.

------------------------------------------------------------------------

# 19. Primera milestone concreta

La primera versión que debería existir en producción:

``` text
                         ONLINE

                           │
                           ▼

                    [ Crear partida ]
                           │
                           ▼
                   Nombre de la novia
                           │
                           ▼
                    Crear personaje
                           │
                 ┌─────────┼─────────┐
                 │         │         │
              Cabello     Ojos      Ropa
                 │         │         │
                 └─────────┼─────────┘
                           │
                           ▼
                     [ Guardar ]
                           │
                           ▼
                   Partida persistida
```

Nada más.

Si esto funciona correctamente desde un navegador en internet y los
datos sobreviven a un refresh, **el proyecto ya tiene su primera
vertical slice**.

A partir de ahí se puede construir el juego incrementalmente sin tener
que diseñar toda la aplicación antes de verla funcionando.
