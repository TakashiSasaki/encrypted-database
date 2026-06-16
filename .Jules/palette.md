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
