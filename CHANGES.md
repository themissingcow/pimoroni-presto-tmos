v1.0.0-alpha.X
==============

## New Features

- Added `OS.update_display` to update the screen without a touch poll.
- Added `OS.message_handlers` method to retrieve the currently
  registered handlers.

## Bug Fixes

- Fixed intermittent screen wakes caused by the display state clock
  wrapping around.

v1.0.0-alpha.2
==============

## Breaking Changes

- Renamed `Task` properties:
  - `last_run_us` -> `last_execution_us`
  - `run_interval_us` -> `execution_interval_us`
- Renamed the `OS.add_task` `update_frequency` kwarg to
  `execution_frequency`.

## New Features

- Added a `touch_forces_execution` kwarg to `OS.add_task` and the
  corresponding `OS.Task` property. This causes the run loop to
  immediately execute the task when a touch is active, regardless of its
  specified `execution_frequency`.
- Added an `active` property to `OS.Task` instances that controls
  whether the task should be executed by the run loop. This allows
  a task to be disabled, without removing it.
- `OS.add_task` now returns the corresponding `OS.Task` instance.
- `OS.remove_task` now also accepts an `OS.Task` instance.
