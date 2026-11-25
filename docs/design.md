# Design: Apple Human Interface Guidelines, on the web

Every screen of this project follows Apple's Human Interface Guidelines (HIG). The interface takes the idiom of the Apple platform that matches the device in front of the user: **iOS** on narrow screens, **iPadOS** on tablets, **macOS** on desktops, **tvOS** on televisions. It is one codebase with four idioms, not one responsive layout that stretches.

The authority is the HIG itself: <https://developer.apple.com/design/human-interface-guidelines>. This file is the working summary. Where it is silent, the HIG page for that component decides; where the two disagree, the HIG wins and this file gets corrected. Numbers below are the long-standing HIG values; check the current HIG page before relying on one for something new, because Apple revises them.

## 1. The rule

1. **Name the component before building it.** Every piece of UI is a named HIG component (navigation bar, tab bar, sidebar, sheet, popover, list, toolbar, alert, segmented control, ...) used for the purpose the HIG gives it. Name it the same way in the code (`.tab-bar`, `.sheet`, `.sidebar`).
2. **No invented components.** If the HIG has no component for the need, compose existing ones. If that truly cannot work, stop, propose the exception, and record it in `docs/decisions.md` once agreed.
3. **No other design language.** Nothing from Material Design, Fluent, Bootstrap or a UI kit's default look survives into a screen. See section 9.
4. **Tokens only.** Colours, type sizes, spacing, radii, durations and materials come from CSS custom properties defined once. A raw hex value, pixel font size or ad-hoc shadow in a component is a defect.
5. **Each idiom is designed, not derived.** Do not shrink the macOS layout to make the iOS one or stretch iOS to fill a desktop. Navigation structure changes between idioms; content and features do not.

## 2. Choosing the idiom

Decide from viewport width and input capability with media queries. Never read the browser's identification string, and never decide from the device brand: an Android phone gets the iOS idiom, a Windows laptop gets the macOS idiom.

| Idiom | Condition | Primary input |
|---|---|---|
| iOS | width < 744px | touch |
| iPadOS | width >= 744px and primary pointer coarse; or width 744-1023px with any pointer | touch, optional pointer and keyboard |
| macOS | width >= 1024px and `(hover: hover) and (pointer: fine)` | pointer and keyboard |
| tvOS | `data-idiom="tv"` on `<html>` | directional remote (arrow keys, Enter, Back) |

- A narrow window on a tablet or desktop (split view, a resized window) falls back to the iOS idiom below 744px. That matches the compact size class.
- Televisions cannot be detected reliably with media queries. The tv idiom is switched on explicitly: `?idiom=tv` in the address (remembered for the session) sets `data-idiom="tv"`, which overrides the three rows above. Automatic TV detection is UNVERIFIED; do not add it without testing on a real television browser.
- Define the conditions once (one stylesheet section or one module) and reuse them. Components never repeat a raw breakpoint.

## 3. Foundations (all idioms)

**Typeface.** San Francisco, in one of two ways. `docs/decisions.md` records which one this project uses; when it says nothing, it is the first.
- *Public or commercial projects (the default):* the system font, through the font stack `-apple-system, BlinkMacSystemFont, system-ui, "Helvetica Neue", "Segoe UI", Roboto, sans-serif`; monospace `ui-monospace, "SF Mono", Menlo, Consolas, monospace`. On Apple devices that is San Francisco. Never download or embed San Francisco or New York font files: Apple licenses them for designing software for Apple platforms, not for serving on the web.
- *Personal, private, non-commercial projects that have recorded it:* the SF Pro and SF Mono web fonts from the local store, served by the project itself, with the stack above behind them: `"SF Pro", -apple-system, ...` and `"SF Mono", ui-monospace, ...`. SF Pro is one variable font: set weights with `font-weight`, and leave `font-optical-sizing: auto` so text and display sizes get the right cut.

No other typeface without a recorded decision.

**Type scale.** Use the HIG text styles by name. Size/line-height in CSS px; weight regular unless stated.

| Style | iOS and iPadOS | macOS | tvOS (1920px wide) |
|---|---|---|---|
| Large Title | 34/41 | 26/32 | - |
| Title 1 | 28/34 | 22/26 | 76/96 medium |
| Title 2 | 22/28 | 17/22 | 57/66 medium |
| Title 3 | 20/25 | 15/20 | 48/56 medium |
| Headline | 17/22 semibold | 13/16 bold | 38/46 medium |
| Body | 17/22 | 13/16 | 29/36 medium |
| Callout | 16/21 | 12/15 | 31/38 medium |
| Subheadline | 15/20 | 11/14 | - |
| Footnote | 13/18 | 10/13 | - |
| Caption 1 | 12/16 | 10/13 | 25/32 medium |
| Caption 2 | 11/13 | 10/13 medium | 23/30 medium |

Sizes are set in `rem` so the user's browser text size scales them (the web equivalent of Dynamic Type). Layouts must survive 200% text size without clipping or overlap. Weights are regular, medium, semibold and bold only; no light or thin weights for text, no uppercase letter-spaced labels.

**Colour.** Use the HIG system colours by role, never by appearance, each with a light and a dark value. Light and dark both ship, selected by `prefers-color-scheme`; `prefers-contrast: more` raises separators and secondary text.

| Token | Light | Dark |
|---|---|---|
| label | `#000000` | `#FFFFFF` |
| secondary label | `rgb(60 60 67 / 0.6)` | `rgb(235 235 245 / 0.6)` |
| tertiary label | `rgb(60 60 67 / 0.3)` | `rgb(235 235 245 / 0.3)` |
| separator | `rgb(60 60 67 / 0.29)` | `rgb(84 84 88 / 0.6)` |
| background | `#FFFFFF` | `#000000` |
| secondary background | `#F2F2F7` | `#1C1C1E` |
| tertiary background | `#FFFFFF` | `#2C2C2E` |
| grouped background | `#F2F2F7` | `#000000` |
| grouped secondary background | `#FFFFFF` | `#1C1C1E` |
| blue (default accent) | `#007AFF` | `#0A84FF` |
| green | `#34C759` | `#30D158` |
| orange | `#FF9500` | `#FF9F0A` |
| red (destructive) | `#FF3B30` | `#FF453A` |
| yellow | `#FFCC00` | `#FFD60A` |
| gray | `#8E8E93` | `#8E8E93` |

One accent colour for the whole product marks interactive elements; it is the only colour that means "you can act on this". Red is for destructive actions only. Never convey state by colour alone. Text contrast is at least 4.5:1 (3:1 for text 20px and larger or bold). No decorative gradients, no coloured drop shadows.

**Materials and depth.** Bars, sidebars, sheets and popovers are translucent materials that float above content: a tinted semi-transparent background with `backdrop-filter: blur() saturate()`, a hairline edge, and an opaque fallback where `backdrop-filter` is unsupported or `prefers-reduced-transparency: reduce` is set. Material belongs to the navigation and control layer only; content (lists, cards, text) is opaque. Shadows are soft, neutral and rare (sheets, popovers, menus, the focused tvOS item); never the stacked elevation shadows of Material.

**Shape.** Rounded rectangles with consistent, concentric radii: an inner radius equals the outer radius minus the padding between them. Buttons that stand alone are capsules or rounded rectangles; no sharp corners, no pill-shaped text inputs on macOS.

**Spacing.** A 4px base unit; use multiples of 4 (8, 12, 16, 20, 24, 32). Content respects safe areas with `env(safe-area-inset-*)`, and the page is declared with `viewport-fit=cover`.

**Icons.** One icon set for the whole product, with weights matched to the adjacent text and sized with the text. Every icon-only control has an accessible name.
- *Public or commercial projects (the default):* an openly licensed outline set that follows the same conventions, recorded in `docs/decisions.md`. SF Symbols are not used: their licence restricts them to software for Apple platforms.
- *Personal, private, non-commercial projects that have recorded it:* SF Symbols, exported as SVG from the local store by name. Use the symbol the HIG uses for the meaning (`square.and.arrow.up` for share, `gearshape` for settings, `chevron.right` for disclosure), the `.fill` variant in tab bars and on selected items, the outline variant elsewhere, and the weight of the text beside it (regular with body, semibold with headline). Icons take `currentColor`; never recolour or redraw a symbol.

Apple's logos, product images and device frames are not used in either case.

**Motion.** Short and purposeful: 200-350ms, ease-out or spring-like curves, movement that explains where something came from (a pushed view slides in from the trailing edge, a sheet rises from the bottom, a popover grows from its anchor). `prefers-reduced-motion: reduce` replaces movement with a cross-fade. No bounce for decoration, no parallax scrolling, no scroll hijacking, no animation that delays input.

**Writing.** Sentence case for body text and macOS labels, title case for buttons, menu items and titles as the HIG specifies. Short, plain, no exclamation marks. Buttons are verbs ("Delete Photo", not "OK" or "Yes").

## 4. iOS idiom (narrow screens)

- **Navigation:** a tab bar at the bottom for 2-5 top-level sections (icon and one-word label each); a navigation stack inside each tab with a navigation bar at the top (back control on the leading side with the previous title, title centred or a large title that collapses on scroll, at most two actions on the trailing side). Tab bars never hold actions; toolbars do.
- **Layout:** one column. Margins 16px (20px on widths of 430px and more). Content scrolls under translucent bars. Use `100dvh`, not `100vh`.
- **Touch:** every target at least 44x44px. No hover states and nothing that only appears on hover. Pressed state is an immediate dim or highlight, removed on release; remove the browser's tap highlight.
- **Lists:** inset grouped lists for settings and forms (rows at least 44px tall, 10px group radius, separators inset to the text, a chevron for rows that navigate); plain lists for content. Swipe actions on rows where the HIG uses them, always with a visible alternative.
- **Presentation:** sheets rise from the bottom with a grabber and dismiss by drag or a Cancel/Done button; action sheets for choosing among actions from a control; alerts only for information that needs a decision, with at most two buttons side by side and three stacked.
- **Controls:** switches for on/off, segmented controls for 2-5 views of the same content, steppers, sliders, pickers and menus as specified. Text inputs use 17px text (anything below 16px makes Safari zoom the page).
- **Forbidden here:** hamburger menus and drawers, floating action buttons, top tab strips, toasts and snackbars, breadcrumbs, dense tables, footers with links.

## 5. iPadOS idiom (tablets)

- **Navigation:** a sidebar with a split view (sidebar about 320px, optionally a middle column about 375px, then the detail), or a tab bar at the top that can expand into a sidebar. The sidebar can be hidden; the detail then takes the full width. Never a phone layout centred with empty margins, never a bottom tab bar stretched across the width.
- **Layout:** both orientations are designed. Readable content width is capped (about 672px for text) and centred within its column. Margins 20-24px.
- **Presentation:** popovers anchored to the control that opened them replace action sheets; sheets are centred form sheets (about 540px wide) or page sheets, not full-width; alerts stay centred.
- **Input:** touch first (44x44px targets, same type scale as iOS), with pointer and keyboard as equals: hover highlights are allowed as an enhancement, every action in a context menu is also reachable by touch, and common keyboard shortcuts work.
- **Use the space:** multi-column lists and grids, inspectors, drag and drop between columns where it helps.

## 6. macOS idiom (desktops)

- **Structure:** a window-style layout: a translucent sidebar on the leading side (200-280px, resizable where practical, source-list rows 28px tall with small icons), a toolbar across the top of the content (about 52px, title on the leading side, icon buttons, a search field on the trailing side), then content; an optional inspector on the trailing side. No bottom tab bar, no large collapsing titles, no hamburger menu.
- **Density:** Body is 13px. Controls are 22-28px tall with 5-6px radii; rows 24-28px; targets at least 20x20px, 28x28px preferred. Do not reuse touch sizing here.
- **Pointer:** hover feedback is subtle and limited to toolbar buttons, menu items, links and rows; no hover growth or lift on cards. The mouse pointer stays the default arrow on buttons; the pointing hand is for links only. Right-click opens a context menu wherever the item has actions, and every such action is also in a visible menu or toolbar.
- **Keyboard:** everything is reachable by Tab and arrow keys. Focus is shown with the system focus ring: a 3px ring in the accent colour at about 50% opacity, following the control's shape, on `:focus-visible` only. Standard shortcuts are honoured (Command on Apple keyboards, Control elsewhere) and shown in menus.
- **Controls:** push buttons (the default action filled with the accent colour, placed trailing-most, Cancel to its leading side), pop-up buttons and pull-down menus instead of custom dropdowns, checkboxes and radio buttons for settings, segmented controls, tables with column headers, sortable columns and optional alternating rows, disclosure triangles for hierarchy.
- **Presentation:** sheets and alerts are centred modal dialogs over a dimmed window; popovers for transient detail; menus for lists of commands. Scrollbars are the overlay kind and are never restyled into something else.

## 7. tvOS idiom (televisions)

- **Focus is everything.** There is no pointer and no touch. Exactly one element has focus at all times, focus moves with the arrow keys in the direction pressed to the nearest focusable element, Enter activates, and Back/Escape returns one level. Every interactive element is reachable this way; nothing depends on hover, a click position or text selection. Restore focus to the element that opened a view when returning to it.
- **Focused appearance:** the focused item grows (about 1.05-1.1 scale), lifts with a soft shadow and brightens; unfocused neighbours stay flat. Leave room around items so the enlarged one does not clip. This replaces the outline focus ring.
- **Layout:** designed for 1920x1080 and viewed from across a room. Keep everything inside the safe area: 60px from the top and bottom, 80px from the sides. Scale the root font size with the viewport width so a 1280px or 3840px wide browser shows the same composition.
- **Navigation:** a tab bar at the top, then full-width shelves: horizontal rows of large image-led items that scroll sideways, stacked vertically. Depth is at most a few levels.
- **Type and targets:** nothing smaller than 23px; body 29px. Focusable items at least 66x66px, usually far larger.
- **Content:** images first, very little text, no dense forms. Avoid text entry; when unavoidable, offer the shortest possible input and a way to finish on another device.
- **Appearance:** light and dark are both supported; media-heavy screens favour dark.

## 8. Accessibility (required, all idioms)

Semantic HTML first, ARIA only where no element exists. Every input has a label; every image has alternative text or is marked decorative. Full keyboard operation with a visible focus indicator. Contrast as in section 3. Respect `prefers-reduced-motion`, `prefers-reduced-transparency`, `prefers-contrast` and `prefers-color-scheme`. Text scales to 200%. Screen-reader order follows visual order.

## 9. Never

- Material Design traits: ripples, floating action buttons, elevation shadows, snackbars and toasts, outlined text fields with floating labels, uppercase buttons, bottom navigation drawers.
- Hamburger menus and off-canvas drawers, in any idiom.
- A UI library's default theme left visible (Quasar/Material, Radix, Bootstrap, Tailwind UI look). If a framework brings components, they are restyled to the tokens here or replaced.
- Custom-drawn replacements for a control the HIG already defines, or a HIG control used for a different purpose (a switch that performs an action, a tab bar that holds buttons).
- Raw colours, font sizes, radii or shadows outside the token definitions; inline styles.
- Hover-only affordances on touch idioms; touch sizing on macOS; pointer assumptions on tvOS.
- Apple's font files or SF Symbols in a public or commercial project, or in any project that has not recorded the personal, private exception in `docs/decisions.md`. Where they are used, they never reach a public repository or a public or commercial deployment.
- Apple logos, device frames or screenshots of Apple software, anywhere. Follow the guidelines; do not pass the product off as Apple's.
- Carousels that auto-advance, scroll hijacking, parallax, splash screens that delay use, cookie-style banners stacked over content, decorative gradients and glows.

## 10. Checking a screen

A screen is not done until it has been opened in a real browser and compared with this file in every idiom it supports, in light and dark:

| Idiom | Viewport | Emulation |
|---|---|---|
| iOS | 393x852 | touch, coarse pointer, device scale 3 |
| iPadOS | 834x1194 and 1194x834 | touch, coarse pointer, device scale 2 |
| macOS | 1440x900 | mouse and keyboard |
| tvOS | 1920x1080 with `?idiom=tv` | keyboard only: arrow keys, Enter, Escape |

For each: the navigation structure is the one this file names for that idiom; no element is from section 9; targets meet the minimum size; nothing overflows or clips at 200% text size; the whole flow works with the idiom's primary input alone; reduced motion and reduced transparency still read well.
