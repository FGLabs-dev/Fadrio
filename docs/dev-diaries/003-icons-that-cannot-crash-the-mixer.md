> Status: Draft; not published.
> Suggested community: r/Fadrio; flair: Development Update.
> Website slug: fadrio-dev-diary-03-icons-that-cannot-crash-the-mixer
> Image: docs/screenshots/fad-0502-application-icon.png (actual isolated silent fixture).

# Fadrio Dev Diary #3 — An icon should not be able to crash a mixer

Fadrio is the Linux application mixer I want to use myself: one recognizable application, one slider, and one mute action, even when that application owns several playback streams. This update makes those rows easier to recognize. It also found a surprisingly enthusiastic failure mode for a tiny PNG.

## From identity to something you can recognize

The resolver already knew where to find trusted local application icons. The window now actually uses them. Each row loads its validated PNG in the background, shows the application name beside it, and falls back to a readable initial when the artwork is missing or invalid.

The loading path keeps the existing rules: local XDG roots only, bounded file sizes and dimensions, a bounded disk cache, and no downloading. Only two searches/decodes run at once. The decoded thumbnail fits inside 64 × 64 pixels, including unusually tall or wide images. When a row disappears or its icon changes, obsolete work is canceled and replaced bitmaps are disposed.

There is a deliberate limitation here: this path currently supports PNG. An installed application with only an SVG icon gets the fallback. A missing icon should be a small visual inconvenience, not a reason to make the audio controls disappear.

## The PNG that had a header and very little ambition

For the rendered regression check, I copied the first 24 bytes of a valid PNG and left out the actual image data. The existing resolver accepted the signature and dimensions. Avalonia.Skia 12.1.2 then attempted to use a null codec and threw a `NullReferenceException`.

That originally took down the window. The UI now contains that specific decoder failure at the decode boundary and displays the initial instead. The real desktop check then drags the slider and toggles mute on the same fixture. This is why I want visual tests alongside unit tests: a plausible image header and a working mixer are different achievements.

The icon has been relieved of its responsibilities as application supervisor.

## What “mixed” means when one application has several streams

The row also shows a textual playback/mute state. `Playing` comes from the existing stream activity state; it is not a new signal meter. `Muted` does not depend on spotting a different color.

For multiple streams with different levels, the row retains the mixed-volume label. The tooltip and accessibility help now explain the action: moving the slider sets **every owned stream to the same level**. It does not silently preserve a ratio or invent a separate routing policy. Backend refreshes still reuse the same row objects, and an active gesture keeps its position while other applications change.

## What I actually checked

The local build passes **109 managed tests**, including 23 UI cases, plus two native tests, six Python roadmap/synchronization tests, and the isolated PipeWire integration scenario. Formatting and roadmap checks also pass.

In the actual 360 × 680 Avalonia window on this GNOME Wayland desktop through XWayland, the isolated silent fixture reaches 37% with a drag and 10% with Home plus ten Right keys. The mute button works. The controls remain usable after the damaged icon, and work again after stopping the private PipeWire daemon during a drag and restarting it.

The screenshot shows that controlled fixture and Fadrio's own icon. It is not a mockup or somebody's private application list.

Normal host-font startup also reached the window today. The previous startup stall did not reproduce, so I am keeping that investigation open rather than pretending to have found its cause. No host fonts were removed or restricted.

## Still an alpha, still development work

This is an application-row slice in FAD-0502. Output-device controls, tray/single-instance behavior, pinned/inactive rows and durable volume policies still need work. The broader KDE, native Wayland, scaling and screen-reader qualification matrix remains open. There is no new supported binary release from this change.

The implementation is under review; this diary is a draft for the website and Reddit, not a release announcement.

For a daily mixer, which missing behavior would you prioritize next: remembered application levels, pinned controls for applications that are currently silent, or quick access from the tray?
