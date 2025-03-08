v1.0.0-alpha.x
==============

> [!IMPORTANT]
> This release requires Presto firmware 0.0.8 or later.

## Breaking Changes

- Adds support for firmware 0.0.8. As plasma is no longer used to manage
  the Presto LEDs, this removes the now redundant `glow_leds` and
  `glow_fps` kwargs from `OS.boot`.

v1.0.0-alpha.4
==============

> [!IMPORTANT]
> This release supports Presto firmware up to and including 0.0.7.

## Breaking Changes

- Refactored font scaling in `Theme`. `default_font_scale` is now
  `base_font_scale` and all text related calls now take a `rel_scale`
  parameter, that multiplies this. `line_height` is now
  `base_line_height`, and is the size of a line when `base_font_scale`
  is used for rendering.

## New Features

- `async` functions can now be added as tasks or UI event callbacks.
  They will be added to the main `asyncio` run loop. The OS will yield
  to the scheduler after each task. These tasks must `await` something,
  or the main OS run loop will be blocked as it would with a synchronous
  function. Adds `OS.run_async` if you wish to manage your own `asyncio`
  event loop.
- Added support for af fonts. A theme's font can be set to
  the name of a `.af` font file, which will switch rendering to
  PicoVector. When using af fonts, the scale is set in pixels.
- Added a "systray" to the `WindowManager`. This presents a list of
  registered pages, and allows direct navigation between them. It can be
  positioned at the top or the bottom of the screen and shrinks the page
  content region accordingly.
- Pages can now an update in the next run loop by setting their
  `needs_update` attribute to True.
- Added `Theme.text_scale` that will return the absolute font scale used
  by the theme, factoring in an optional `rel_scale`.

## Improvements

- The systray now only ticks once per second unless an update is needed.
- Added `OS.Task.enqueue` to request the task is executed in the next
  run loop.
- `LatchingButton` now updates on touch-end to allow the control to be
  left in a unchanged state by ending the touch outside of the control.
  It now calls on_button_cancel in that situation.
- A custom control class can now be provided to the `RadioButton`
  constructor, making it easier to customise presentation.

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
