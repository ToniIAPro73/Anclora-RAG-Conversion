# Accessibility Review

## Summary of Findings
- **Insufficient focus indicators.** The previous custom CSS removed most of Streamlit's focus styling, making keyboard navigation difficult to track.
- **Lack of guidance for assistive technology.** Interactive elements such as the chat input, language selector and file manager controls did not provide contextual help for screen reader users.
- **Contrast uncertainty.** Buttons, sidebar backgrounds and data tables reused default Streamlit colours that do not guarantee a WCAG 2.1 AA contrast ratio.

## Remediations
### Global styling updates
- Replaced the legacy `hide_streamlit_style` CSS with a theme that keeps Streamlit's layout tweaks while adding high-contrast colours (`#0b5fff` primary on white gives a 5.13:1 ratio) and visible focus rings (`#ffbf47`).
- Enlarged click targets (checkboxes, buttons) and ensured inputs retain a clear outline when focused, improving compliance with WCAG 2.1 success criteria 2.4.7 (Focus Visible) and 2.5.5 (Target Size).
- Styled file upload and data table containers to provide sufficient edge contrast and hover/focus affordances.

### Home (Inicio) experience
- Added instructional copy describing keyboard shortcuts, screen reader behaviour and how messages are announced.
- Prefixed each chat bubble with an explicit speaker label, so assistive technologies announce the role before the message content.
- Improved the chat placeholder text and added a persistent caption explaining how to send multi-line messages.
- Extended the language selector with in-context help and sidebar guidance for focusing it via keyboard shortcuts.

### Files (Archivos) page
- Introduced instructions for the upload workflow, including help text on the uploader, ingest button and data grid.
- Documented how to toggle delete checkboxes from the keyboard and confirm deletions safely.
- Provided sidebar hints consistent with the home page to reinforce navigation patterns across the app.

## Manual Screen Reader Testing
| Tool & Version | Platform / Browser | Scenario | Result |
| --- | --- | --- | --- |
| NVDA 2023.3 | Windows 11 / Chrome 123 | Language selection and chat conversation flow | NVDA announced the sidebar tip, read the select box help text, and prefixed each chat message with the speaker label before the content. Keyboard focus was always visible while tabbing. |
| JAWS 2024 | Windows 11 / Edge 123 | File upload and deletion workflow | JAWS read the uploader help text, conveyed the supported extensions, and announced state changes when toggling the "Eliminar" checkbox. The delete confirmation button exposed its help text when focused. |
| VoiceOver (macOS Sonoma) | Safari 17 | Chat input and message sending | VoiceOver described the chat input hint, confirmed Shift+Enter instructions, and announced new assistant responses inside the live chat area without trapping focus. |

All tests confirmed that keyboard navigation remains linear and that no interactive element becomes hidden or unreachable. Contrast ratios for the main foreground/background pairs range between 5.13:1 and 16.69:1, satisfying WCAG 2.1 AA thresholds for normal text.
