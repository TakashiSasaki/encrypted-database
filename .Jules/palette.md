## 2024-05-18 - Tab Accessibility and Disabled State Hints
**Learning:** Found that custom tabs lack semantic roles out of the box, requiring explicit `role="tablist"`, `role="tab"`, and `role="tabpanel"` along with dynamic `aria-selected` tracking in JS. Furthermore, custom buttons don't have default disabled states in CSS. A screen reader also misses logs printed dynamically to a `div` without an `aria-live` attribute.
**Action:** Always add semantic roles/attributes to custom tabs, explicitly style `button:disabled`, and ensure dynamic console-like outputs have `aria-live="polite"` so updates are announced to screen readers nicely.

## 2024-06-13 - Browser Test Custom Tab Accessibility
**Learning:** Adding `role="tablist"`, `role="tab"`, and `role="tabpanel"` is not enough for custom tabs. They also require keyboard navigation (arrow keys for moving between tabs) and roving `tabindex` (where the active tab has `tabindex="0"` and others have `-1`) to be truly accessible. Additionally, custom elements like tabs need `:focus-visible` styling to ensure users tabbing through the UI can see which element has focus.
**Action:** When implementing custom tabs, always ensure keyboard arrow navigation is supported and `tabindex` is updated dynamically along with `aria-selected`. Ensure custom interactive elements have a clear `:focus-visible` outline.
## 2024-06-14 - Dynamic document.title for SPAs
**Learning:** In single-page applications or custom markdown viewers that dynamically swap out content via JavaScript, failing to update `document.title` breaks the experience for screen reader users and affects standard usability (browser history/tabs). ARIA live regions announce content, but the title remains the primary navigation context.
**Action:** Always verify that `document.title` is updated whenever a client-side route or primary document content changes.
## 2024-06-16 - Dynamic Aria-Current in SPA Markdown Viewers
**Learning:** Custom Single Page Applications (SPAs) that dynamically load content (like Markdown viewers) often neglect to update `aria-current="page"` on navigation links because the page itself never reloads. This breaks accessibility context for screen reader users and prevents styling the active state cleanly using CSS attributes.
**Action:** Always hook into the client-side routing/loading function (e.g., `loadMarkdown()`) to iterate over navigation links and dynamically add/remove `aria-current="page"` based on the current parsed state or URL parameters.

## 2024-06-16 - Clearing Aria-Current on Overlays/Index Views
**Learning:** If a custom SPA introduces an overlay or a "meta-view" (like an index or search page) that completely replaces the content without being represented by one of the primary static navigation links, leaving `aria-current="page"` on the previously viewed link causes a stale state. Assistive technology will falsely announce the user is still on that previous page.
**Action:** When swapping content to an overlay or non-navigational index, explicitly clear `aria-current` from all main navigation links.

## 2024-06-18 - Keyboard Accessibility for Custom Scrollable Regions
**Learning:** Elements with `overflow: auto` or `overflow: scroll` (like code blocks, logs, or wide data tables) are not focusable by default. Keyboard-only users cannot scroll these regions using arrow keys unless they can focus the container.
**Action:** Always add `tabindex="0"`, `role="region"`, and an accessible name (via `aria-label` or `aria-labelledby`) to custom scrollable containers. Additionally, ensure there is a clear `:focus-visible` styling for the container so users know it has focus.

## 2024-06-24 - Table Accessibility and Semantic Integrity
**Learning:** Adding `tabindex="0"` directly to a `<table>` to make it keyboard-scrollable breaks its semantic meaning for screen readers. Instead, the `<table>` should be wrapped in a focusable `<div>` container with `overflow: auto`, `tabindex="0"`, `role="region"`, and an appropriate `aria-label` (e.g., "Data table").
**Action:** When implementing keyboard-scrollable tables, always wrap the table in a container rather than applying focus attributes directly to the table element to preserve its native accessibility semantics.

## 2024-07-03 - Programmatic Focus Management vs aria-live for Client-Side Routing
**Learning:** Using `aria-live` on large content containers during client-side routing can be overwhelming and confusing for screen readers, as they may try to read the entire page content at once or incorrectly announce context. It is better to rely on semantic document structure and manage focus explicitly.
**Action:** When implementing client-side routing, remove `aria-live` from the main content container. Instead, explicitly call `.focus()` on a `<main>` container (which needs `tabindex="-1"` and `outline: none;`) and reset the scroll position to the top (`window.scrollTo(0, 0)`). This properly notifies screen readers of context changes and correctly resets visual position for sighted keyboard users.
