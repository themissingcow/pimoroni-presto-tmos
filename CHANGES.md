1.0.0aX
=======

## New Features

- Added an `active` property to `OS.Task` instances that controls
  whether the task should be executed by the run loop. This allows
  a task to be disabled, without removing it.
- `OS.add_task` now returns the corresponding `OS.Task` instance.
- `OS.remove_task` now also accepts an `OS.Task` instance.
