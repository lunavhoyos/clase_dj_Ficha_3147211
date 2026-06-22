# Requirements Document

## Introduction

Este documento describe los requisitos funcionales del módulo **Gestión de Jornadas de Recolección** para el sistema Django CRM (`dcrm`, app `website`). Una jornada de recolección es un evento comunitario organizado en un barrio específico donde residentes llevan materiales reciclables a un punto de encuentro en una fecha y hora definidas.

El sistema maneja tres roles de usuario:
- **Administrador / Organizador**: puede crear, editar, cancelar y publicar jornadas.
- **Residente**: puede visualizar jornadas activas de su barrio.
- **Visitante no autenticado**: no tiene acceso al módulo.

> **Nota técnica**: El proyecto ya posee un modelo `Jornada` para gestión de turnos laborales. La nueva entidad se denominará `JornadaRecoleccion` para coexistir sin conflictos en la misma app `website`.

---

## Glossary

- **Sistema**: La aplicación web Django (`dcrm` / app `website`).
- **JornadaRecoleccion**: Evento comunitario de recolección de materiales reciclables con fecha, hora, punto de encuentro y cupo definidos.
- **Administrador**: Usuario autenticado perteneciente al grupo Django `ADMIN` o con flag `is_superuser`.
- **Organizador**: Usuario autenticado perteneciente al grupo Django `ORGANIZADOR`.
- **Residente**: Usuario autenticado sin rol privilegiado, asociado a un barrio.
- **Barrio**: Zona geográfica a la que pertenece un residente o una jornada de recolección.
- **Estado**: Valor del campo `estado` de `JornadaRecoleccion`; puede ser `pendiente`, `activa`, `finalizada` o `cancelada`.
- **Cupo_Maximo**: Número máximo de participantes permitidos en una `JornadaRecoleccion`.
- **Tipo_Material**: Categoría de material reciclable aceptado en la jornada (ej. plástico, vidrio, cartón); seleccionada de una lista controlada.
- **Punto_Encuentro**: Dirección física donde los residentes se presentan durante la jornada (máximo 255 caracteres).
- **Notificador**: Componente del Sistema responsable de enviar notificaciones a los usuarios.
- **Canal_Notificacion**: Medio por el cual el Notificador entrega mensajes; puede ser `email`, `web` o `push`.

---

## Requirements

### Requirement 1: Creación de jornada de recolección

**User Story:** Como administrador u organizador, quiero crear una jornada de recolección especificando todos sus datos, para que los residentes del barrio puedan conocer y asistir al evento.

#### Acceptance Criteria

1. IF un usuario sin rol `Administrador` u `Organizador` intenta acceder al formulario de creación de `JornadaRecoleccion`, THEN THE Sistema SHALL denegar el acceso y mostrar un mensaje indicando que no tiene permisos suficientes, sin mostrar el formulario.
2. WHEN un usuario autorizado envía el formulario de creación, THE Sistema SHALL requerir que los campos `fecha`, `hora`, `Punto_Encuentro` (máx. 255 caracteres), `Barrio` (máx. 100 caracteres) y `Tipo_Material` (seleccionado de lista controlada) estén presentes y no vacíos antes de persistir la jornada.
3. WHEN un usuario autorizado envía el formulario de creación, THE Sistema SHALL requerir que la combinación `fecha` + `hora` represente un momento estrictamente posterior al instante actual del servidor.
4. IF el formulario de creación contiene uno o más campos obligatorios vacíos o sin selección, THEN THE Sistema SHALL rechazar el envío y mostrar un mensaje de error identificando específicamente qué campos son inválidos.
5. IF la `fecha` y `hora` ingresadas corresponden a un momento pasado o igual al instante actual, THEN THE Sistema SHALL rechazar el envío y mostrar un mensaje indicando que la fecha y hora deben ser futuras.
6. WHEN el formulario de creación es enviado exitosamente, THE Sistema SHALL confirmar la creación y mostrar el registro de la `JornadaRecoleccion` recién creada.
7. IF se intenta guardar una `JornadaRecoleccion` con la misma combinación de `fecha`, `hora` y `Punto_Encuentro` que una jornada existente cuyo `Estado` no sea `cancelada`, THEN THE Sistema SHALL rechazar el guardado y mostrar un mensaje indicando el conflicto de lugar y horario.

---

### Requirement 2: Descripción y cupo máximo

**User Story:** Como administrador u organizador, quiero guardar una descripción detallada y un cupo máximo para la jornada, para que los residentes tengan información completa y el evento no exceda su capacidad.

#### Acceptance Criteria

1. WHEN un usuario autorizado guarda una `JornadaRecoleccion`, THE Sistema SHALL requerir que el campo `descripcion` contenga al menos 10 caracteres y no más de 500 caracteres.
2. WHEN un usuario autorizado guarda una `JornadaRecoleccion`, THE Sistema SHALL requerir que el campo `Cupo_Maximo` sea un entero entre 1 y 200 inclusive.
3. IF el campo `descripcion` contiene menos de 10 caracteres o más de 500 caracteres, THEN THE Sistema SHALL rechazar el guardado y mostrar un mensaje indicando el rango válido de longitud para la descripción.
4. IF el campo `Cupo_Maximo` es menor que 1 o mayor que 200, THEN THE Sistema SHALL rechazar el guardado y mostrar un mensaje indicando que el cupo debe estar en el rango válido.
5. IF se intenta guardar una `JornadaRecoleccion` con el mismo `Barrio`, `fecha` y `hora` (exacta, formato HH:MM) que otra jornada cuyo `Estado` sea `pendiente` o `activa`, THEN THE Sistema SHALL rechazar el guardado y mostrar un mensaje indicando que ya existe una jornada en ese barrio para esa fecha y hora.

---

### Requirement 3: Edición y cancelación de jornadas

**User Story:** Como administrador u organizador, quiero editar o cancelar una jornada que aún no ha comenzado, para corregir errores o suspender el evento de forma controlada.

#### Acceptance Criteria

1. IF la `JornadaRecoleccion` a editar tiene `Estado` diferente de `pendiente`, THEN THE Sistema SHALL denegar la operación de edición y mostrar un mensaje indicando que solo pueden editarse jornadas en estado pendiente.
2. IF la `JornadaRecoleccion` a cancelar tiene `Estado` diferente de `pendiente`, THEN THE Sistema SHALL denegar la operación de cancelación y mostrar un mensaje indicando que solo pueden cancelarse jornadas en estado pendiente.
3. IF un usuario autorizado intenta editar o cancelar una `JornadaRecoleccion` cuyo `Estado` no es `pendiente`, THEN THE Sistema SHALL rechazar la operación y mostrar un mensaje indicando que la operación no está permitida en el estado actual de la jornada.
4. WHEN un usuario autorizado solicita cancelar una `JornadaRecoleccion` cuyo número de inscritos supera el 50% del `Cupo_Maximo`, THE Sistema SHALL presentar una solicitud de confirmación explícita antes de ejecutar la cancelación; IF el usuario no confirma, THEN THE Sistema SHALL abortar la cancelación y preservar el estado actual de la jornada.
5. WHEN la cancelación de una `JornadaRecoleccion` se ejecuta exitosamente, THE Sistema SHALL actualizar el campo `Estado` de la jornada a `cancelada`.
6. WHEN un usuario autorizado intenta publicar una `JornadaRecoleccion` (cambiar `Estado` a `activa`) y la jornada no tiene ningún `Organizador` asignado, THEN THE Sistema SHALL rechazar la publicación y mostrar un mensaje indicando que se requiere al menos un organizador asignado antes de publicar.

---

### Requirement 4: Notificación a usuarios del barrio

**User Story:** Como administrador u organizador, quiero que el sistema notifique automáticamente a los residentes del barrio cuando se crea o edita una jornada, para que estén informados oportunamente.

#### Acceptance Criteria

1. WHEN se persiste exitosamente una nueva `JornadaRecoleccion`, THE Notificador SHALL generar y enviar una notificación dirigida a todos los usuarios activos cuyo `Barrio` coincida con el `Barrio` de la jornada, en un plazo máximo de 5 minutos desde la persistencia.
2. WHEN se guarda exitosamente una edición de una `JornadaRecoleccion` existente, THE Notificador SHALL generar y enviar una notificación de actualización dirigida a todos los usuarios activos del `Barrio` correspondiente, en un plazo máximo de 5 minutos desde el guardado.
3. THE Notificador SHALL enviar cada notificación a través del `Canal_Notificacion` configurado en las preferencias del Residente destinatario; los canales soportados son `email`, `web` y `push`.
4. IF el Residente no tiene un `Canal_Notificacion` configurado, THEN THE Notificador SHALL utilizar el canal `email` como canal predeterminado.
5. WHEN el `Canal_Notificacion` configurado para un Residente no está disponible en el momento de entrega, THE Notificador SHALL registrar el fallo y reintentar la entrega al menos una vez mediante el canal alternativo `email`.
6. THE Notificador SHALL enviar notificaciones únicamente a usuarios cuyo estado sea activo en el momento en que se genera la notificación; los usuarios que se vuelvan inactivos después de la generación de la notificación podrán recibir la entrega si el canal ya procesó el envío.

---

### Requirement 5: Visualización de jornadas activas

**User Story:** Como residente o administrador, quiero visualizar las jornadas de recolección activas, para conocer los próximos eventos disponibles.

#### Acceptance Criteria

1. WHEN un usuario autenticado accede al listado de jornadas, THE Sistema SHALL mostrar únicamente las `JornadaRecoleccion` cuyo `Estado` sea `activa` y cuya `fecha` sea mayor o igual a la fecha actual del servidor.
2. WHEN un Residente accede al listado de jornadas, IF el Residente tiene un `Barrio` asignado, THEN THE Sistema SHALL mostrar únicamente las jornadas cuyo `Barrio` coincida con el `Barrio` del Residente.
3. WHEN un Administrador u Organizador accede al listado de jornadas, THE Sistema SHALL mostrar todas las `JornadaRecoleccion` con `Estado` `activa` y fecha vigente, sin restricción de barrio.
4. IF no existen jornadas que cumplan los criterios de visualización para el Residente autenticado, THEN THE Sistema SHALL mostrar el mensaje "No hay jornadas activas disponibles en tu barrio".
5. IF no existen jornadas que cumplan los criterios de visualización para el Administrador u Organizador autenticado, THEN THE Sistema SHALL mostrar el mensaje "No hay jornadas activas disponibles".
6. THE Sistema SHALL mostrar por cada jornada en el listado los campos `titulo`, `fecha`, `hora`, `Punto_Encuentro`, `Barrio`, `Tipo_Material` y `Cupo_Maximo`, ordenados de forma ascendente por `fecha`.
7. WHEN una `JornadaRecoleccion` tiene su `Cupo_Maximo` completamente ocupado, THE Sistema SHALL indicar visualmente en el listado que la jornada no tiene cupo disponible.
