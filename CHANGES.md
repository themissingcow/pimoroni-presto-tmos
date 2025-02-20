v1.0.0-alpha.x
==============

## Improvements

- Added `OS.Task.enqueue` to request the task is executed in the next
  run loop.

v1.0.0-alpha.3
==============

## New Features

- Added a button control classes to the `tmos_ui` module, along with
  supporting infrastructure in `Page`, so simplify the creation of
  on-screen controls. This also adds a default implementation of
  `Page.tick` that polls touch and triggers appropriate button events.
  A new `Page._draw` convenience has been added to streamline drawing
  a page's content. This is somewhat experimental and may change as more
  control types are developed. I may have missed a breaking change in
  here somewhere 🙃.
- Added `OS.update_display` to update the screen without a touch poll.
- Added `OS.message_handlers` method to retrieve the currently
  registered handlers.
- Added a `WindowManager` in the `tmos_ui` module, that simplifies
  building applications with multiple 'pages'.

## Improvements

- `touch_forces_execution` now causes an additional update immediately
  after a touch has ended. Allowing any necessary cleanup to be
  completed without waiting for the next scheduled execution.

## Bug Fixes

- Fixed intermittent screen wakes caused by the display state clock
  wrapping around.
- Ensured tasks are always executed immediately after they are
  re-activated (when an execution_frequency was specified), rather than
  at their previously scheduled next time.
- Fixed missing hoist of the `touch` instance in `OS.__init__`

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
