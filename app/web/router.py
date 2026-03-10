"""Web router for FastHTML-rendered frontend pages and browser assets."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import fasthtml.common as fh

Body = getattr(fh, "Body")
Button = getattr(fh, "Button")
Div = getattr(fh, "Div")
Form = getattr(fh, "Form")
H1 = getattr(fh, "H1")
H2 = getattr(fh, "H2")
H3 = getattr(fh, "H3")
Head = getattr(fh, "Head")
Header = getattr(fh, "Header")
Html = getattr(fh, "Html")
Input = getattr(fh, "Input")
Label = getattr(fh, "Label")
Link = getattr(fh, "Link")
Main = getattr(fh, "Main")
Meta = getattr(fh, "Meta")
Option = getattr(fh, "Option")
P = getattr(fh, "P")
Script = getattr(fh, "Script")
Style = getattr(fh, "Style")
NotStr = getattr(fh, "NotStr")
Section = getattr(fh, "Section")
Select = getattr(fh, "Select")
Span = getattr(fh, "Span")
Strong = getattr(fh, "Strong")
Title = getattr(fh, "Title")
Video = getattr(fh, "Video")
to_xml = fh.to_xml

_STYLE_CSS = '/**\n * Modern Chat UI Styles for ADK Streaming Demo\n */\n\n:root {\n  --primary-color: #4285f4;\n  --user-bubble-bg: #4285f4;\n  --agent-bubble-bg: #f1f3f4;\n  --user-text-color: #ffffff;\n  --agent-text-color: #202124;\n  --bg-color: #ffffff;\n  --border-color: #e0e0e0;\n  --input-bg: #f8f9fa;\n  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);\n  --shadow-lg: 0 4px 12px rgba(0, 0, 0, 0.15);\n}\n\n* {\n  margin: 0;\n  padding: 0;\n  box-sizing: border-box;\n}\n\nbody {\n  font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, \'Helvetica Neue\', Arial, sans-serif;\n  background-color: var(--bg-color);\n  color: #202124;\n  line-height: 1.6;\n  height: 100vh;\n  display: flex;\n  flex-direction: column;\n}\n\n/* Header */\nheader {\n  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n  color: white;\n  padding: 1.5rem 2rem;\n  box-shadow: var(--shadow-lg);\n  position: relative;\n}\n\nh1 {\n  font-size: 1.5rem;\n  font-weight: 600;\n  margin: 0;\n}\n\n.subtitle {\n  font-size: 0.875rem;\n  opacity: 0.9;\n  margin-top: 0.25rem;\n}\n\n/* Header Options (Proactivity, Affective Dialog checkboxes) */\n.header-options {\n  display: flex;\n  align-items: center;\n  gap: 1.25rem;\n  margin-top: 0.75rem;\n}\n\n.header-checkbox {\n  display: flex;\n  align-items: center;\n  gap: 0.375rem;\n  font-size: 0.8125rem;\n  cursor: pointer;\n  user-select: none;\n  opacity: 0.9;\n  transition: opacity 0.2s ease;\n}\n\n.header-checkbox:hover {\n  opacity: 1;\n}\n\n.header-checkbox input[type="checkbox"] {\n  width: 16px;\n  height: 16px;\n  cursor: pointer;\n  accent-color: #ffffff;\n}\n\n.header-checkbox span {\n  white-space: nowrap;\n}\n\n.connection-status {\n  position: absolute;\n  top: 1.5rem;\n  right: 2rem;\n  display: flex;\n  align-items: center;\n  gap: 0.5rem;\n  font-size: 0.875rem;\n}\n\n.status-indicator {\n  width: 8px;\n  height: 8px;\n  border-radius: 50%;\n  background-color: #34a853;\n}\n\n.status-indicator.disconnected {\n  background-color: #ea4335;\n}\n\n@keyframes pulse {\n  0%, 100% {\n    opacity: 1;\n  }\n  50% {\n    opacity: 0.5;\n  }\n}\n\n/* Main Layout: Split view for chat and console */\n.main-layout {\n  flex: 1;\n  display: flex;\n  max-width: 1800px;\n  width: 100%;\n  margin: 0 auto;\n  overflow: hidden;\n  gap: 0;\n}\n\n/* Main Container: Chat area (2/3 of the layout) */\n.container {\n  flex: 2;\n  display: flex;\n  flex-direction: column;\n  overflow: hidden;\n  border-right: 1px solid var(--border-color);\n}\n\n/* Messages Area */\n#messages {\n  flex: 1;\n  overflow-y: auto;\n  padding: 2rem;\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n  background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);\n}\n\n/* Scroll styling */\n#messages::-webkit-scrollbar {\n  width: 8px;\n}\n\n#messages::-webkit-scrollbar-track {\n  background: transparent;\n}\n\n#messages::-webkit-scrollbar-thumb {\n  background: #dadce0;\n  border-radius: 4px;\n}\n\n#messages::-webkit-scrollbar-thumb:hover {\n  background: #bdc1c6;\n}\n\n/* Message Bubbles */\n.message {\n  display: flex;\n  margin-bottom: 0.5rem;\n  animation: slideIn 0.3s ease-out;\n}\n\n@keyframes slideIn {\n  from {\n    opacity: 0;\n    transform: translateY(10px);\n  }\n  to {\n    opacity: 1;\n    transform: translateY(0);\n  }\n}\n\n.message.user {\n  justify-content: flex-end;\n}\n\n.message.agent {\n  justify-content: flex-start;\n}\n\n.bubble {\n  max-width: 70%;\n  padding: 0.75rem 1rem;\n  border-radius: 1.25rem;\n  word-wrap: break-word;\n  box-shadow: var(--shadow);\n  position: relative;\n}\n\n.message.user .bubble {\n  background-color: var(--user-bubble-bg);\n  color: var(--user-text-color);\n  border-bottom-right-radius: 0.25rem;\n}\n\n.message.agent .bubble {\n  background-color: var(--agent-bubble-bg);\n  color: var(--agent-text-color);\n  border-bottom-left-radius: 0.25rem;\n}\n\n.bubble-text {\n  margin: 0;\n  line-height: 1.5;\n}\n\n/* Interrupted message styling */\n.message.interrupted .bubble {\n  opacity: 0.6;\n  background-color: #e8eaed;\n  border-left: 3px solid #f4b400;\n}\n\n.message.interrupted .bubble::after {\n  content: \'interrupted\';\n  display: block;\n  font-size: 0.75rem;\n  color: #5f6368;\n  font-style: italic;\n  margin-top: 0.25rem;\n}\n\n/* Transcription message styling */\n.message.transcription.user .bubble {\n  opacity: 0.9;\n  border: 1px solid rgba(255, 255, 255, 0.3);\n}\n\n.message.transcription.user .bubble::before {\n  content: \'🎤\';\n  opacity: 0.8;\n  margin-right: 0.25rem;\n}\n\n/* Typing indicator */\n.typing-indicator {\n  display: inline-block;\n  margin-left: 0.25rem;\n  color: #5f6368;\n}\n\n.typing-indicator::after {\n  content: \'...\';\n  animation: ellipsis 1.5s infinite;\n}\n\n@keyframes ellipsis {\n  0%, 20% {\n    content: \'.\';\n  }\n  40% {\n    content: \'..\';\n  }\n  60%, 100% {\n    content: \'...\';\n  }\n}\n\n/* Image bubble styling */\n.bubble.image-bubble {\n  padding: 0.25rem;\n  max-width: 80%;\n}\n\n.bubble-image {\n  max-width: 100%;\n  max-height: 300px;\n  width: auto;\n  height: auto;\n  border-radius: 0.75rem;\n  display: block;\n  object-fit: contain;\n}\n\n/* Input Form */\n.input-container {\n  border-top: 1px solid var(--border-color);\n  background-color: white;\n  padding: 1.5rem 2rem;\n  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);\n}\n\n#messageForm {\n  display: flex;\n  gap: 1rem;\n  align-items: center;\n}\n\n.input-wrapper {\n  flex: 1;\n  display: flex;\n  gap: 0.75rem;\n}\n\n#message {\n  flex: 1;\n  padding: 0.875rem 1rem;\n  border: 1px solid var(--border-color);\n  border-radius: 1.5rem;\n  font-size: 1rem;\n  font-family: inherit;\n  background-color: var(--input-bg);\n  transition: all 0.2s ease;\n  outline: none;\n}\n\n#message:focus {\n  border-color: var(--primary-color);\n  background-color: white;\n  box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1);\n}\n\n/* Buttons */\nbutton {\n  padding: 0.875rem 1.5rem;\n  border: none;\n  border-radius: 1.5rem;\n  font-size: 0.9375rem;\n  font-weight: 500;\n  cursor: pointer;\n  transition: all 0.2s ease;\n  font-family: inherit;\n  white-space: nowrap;\n}\n\n#sendButton {\n  background-color: var(--primary-color);\n  color: white;\n}\n\n#sendButton:hover:not(:disabled) {\n  background-color: #3367d6;\n  box-shadow: var(--shadow);\n  transform: translateY(-1px);\n}\n\n#sendButton:disabled {\n  background-color: #dadce0;\n  color: #80868b;\n  cursor: not-allowed;\n  opacity: 0.6;\n}\n\n#startAudioButton {\n  background-color: #34a853;\n  color: white;\n}\n\n#startAudioButton:hover:not(:disabled) {\n  background-color: #2d8e47;\n  box-shadow: var(--shadow);\n  transform: translateY(-1px);\n}\n\n#startAudioButton:disabled {\n  background-color: #dadce0;\n  color: #80868b;\n  cursor: not-allowed;\n  opacity: 0.6;\n}\n\n#cameraButton {\n  background-color: #ea4335;\n  color: white;\n}\n\n#cameraButton:hover:not(:disabled) {\n  background-color: #d33426;\n  box-shadow: var(--shadow);\n  transform: translateY(-1px);\n}\n\n#cameraButton:disabled {\n  background-color: #dadce0;\n  color: #80868b;\n  cursor: not-allowed;\n  opacity: 0.6;\n}\n\n/* System Messages */\n.system-message {\n  text-align: center;\n  color: #5f6368;\n  font-size: 0.875rem;\n  padding: 0.5rem;\n  margin: 1rem 0;\n  font-style: italic;\n}\n\n/* Console Panel (1/3 of the layout) */\n.console-panel {\n  flex: 1;\n  display: flex;\n  flex-direction: column;\n  background-color: #1e1e1e;\n  color: #d4d4d4;\n  font-family: \'Monaco\', \'Menlo\', \'Ubuntu Mono\', \'Consolas\', \'source-code-pro\', monospace;\n  overflow: hidden;\n}\n\n.console-header {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  padding: 0.75rem 1rem;\n  background-color: #2d2d2d;\n  border-bottom: 1px solid #3e3e3e;\n}\n\n.console-header h2 {\n  font-size: 0.875rem;\n  font-weight: 600;\n  margin: 0;\n  color: #cccccc;\n  text-transform: uppercase;\n  letter-spacing: 0.5px;\n}\n\n.console-controls {\n  display: flex;\n  align-items: center;\n  gap: 0.75rem;\n}\n\n.console-checkbox {\n  display: flex;\n  align-items: center;\n  gap: 0.375rem;\n  font-size: 0.75rem;\n  color: #999999;\n  cursor: pointer;\n  user-select: none;\n}\n\n.console-checkbox input[type="checkbox"] {\n  width: 14px;\n  height: 14px;\n  cursor: pointer;\n  accent-color: #4285f4;\n}\n\n.console-checkbox span {\n  white-space: nowrap;\n}\n\n.console-clear-btn {\n  padding: 0.375rem 0.75rem;\n  font-size: 0.75rem;\n  background-color: #3e3e3e;\n  color: #cccccc;\n  border: 1px solid #4e4e4e;\n  border-radius: 0.25rem;\n  cursor: pointer;\n  transition: all 0.2s ease;\n}\n\n.console-clear-btn:hover {\n  background-color: #4e4e4e;\n  border-color: #5e5e5e;\n}\n\n.console-content {\n  flex: 1;\n  overflow-y: auto;\n  padding: 0.75rem;\n  font-size: 0.75rem;\n  line-height: 1.5;\n}\n\n/* Console entry */\n.console-entry {\n  margin-bottom: 0.75rem;\n  padding: 0.5rem;\n  border-left: 3px solid transparent;\n  background-color: rgba(255, 255, 255, 0.06);\n  border-radius: 0.25rem;\n  transition: background-color 0.2s ease;\n}\n\n.console-entry.outgoing {\n  border-left-color: #4285f4;\n}\n\n.console-entry.incoming {\n  border-left-color: #34a853;\n}\n\n.console-entry.error {\n  border-left-color: #ea4335;\n  background-color: rgba(234, 67, 53, 0.15);\n}\n\n/* Expandable console entries */\n.console-entry.expandable {\n  cursor: pointer;\n}\n\n.console-entry.expandable:hover {\n  background-color: rgba(255, 255, 255, 0.10);\n}\n\n.console-entry.expanded {\n  background-color: rgba(255, 255, 255, 0.08);\n}\n\n.console-entry-header {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  margin-bottom: 0.375rem;\n}\n\n.console-entry-left {\n  display: flex;\n  align-items: center;\n  gap: 0.5rem;\n}\n\n.console-entry-emoji {\n  font-size: 0.9rem;\n  line-height: 1;\n  display: inline-block;\n  user-select: none;\n  min-width: 16px;\n  text-align: center;\n}\n\n.console-expand-icon {\n  font-size: 0.6rem;\n  color: #858585;\n  width: 12px;\n  display: inline-block;\n  transition: transform 0.2s ease;\n  user-select: none;\n}\n\n.console-entry-type {\n  font-weight: 600;\n  font-size: 0.7rem;\n  text-transform: uppercase;\n  letter-spacing: 0.5px;\n}\n\n.console-entry.outgoing .console-entry-type {\n  color: #4285f4;\n}\n\n.console-entry.incoming .console-entry-type {\n  color: #34a853;\n}\n\n.console-entry.error .console-entry-type {\n  color: #ea4335;\n}\n\n.console-entry-author {\n  font-size: 0.65rem;\n  font-weight: 500;\n  padding: 0.125rem 0.375rem;\n  border-radius: 0.25rem;\n  text-transform: lowercase;\n  letter-spacing: 0.3px;\n  border: 1px solid;\n}\n\n/* Default style (for agents) */\n.console-entry-author {\n  background-color: rgba(156, 220, 254, 0.15);\n  color: #9cdcfe;\n  border-color: rgba(156, 220, 254, 0.3);\n}\n\n/* User author badge */\n.console-entry-author[data-author="user"] {\n  background-color: rgba(66, 133, 244, 0.2);\n  color: #80b3ff;\n  border-color: rgba(66, 133, 244, 0.4);\n}\n\n/* System author badge */\n.console-entry-author[data-author="system"] {\n  background-color: rgba(133, 133, 133, 0.2);\n  color: #b0b0b0;\n  border-color: rgba(133, 133, 133, 0.3);\n}\n\n.console-entry-timestamp {\n  color: #858585;\n  font-size: 0.65rem;\n}\n\n.console-entry-content {\n  color: #d4d4d4;\n  white-space: pre-wrap;\n  word-break: break-word;\n  font-size: 0.7rem;\n  line-height: 1.4;\n  padding-left: 2.5rem; /* Indent to align with header after emoji and icon */\n}\n\n.console-entry-content:empty {\n  display: none;\n}\n\n/* Style for quoted text in summaries (transcriptions, text responses) */\n.console-entry-content::first-line {\n  color: #e0e0e0;\n}\n\n.console-entry-json {\n  background-color: #252526;\n  padding: 0.5rem;\n  border-radius: 0.25rem;\n  margin-top: 0.5rem;\n  overflow-x: auto;\n  max-height: 400px;\n  overflow-y: auto;\n  transition: all 0.3s ease;\n}\n\n.console-entry-json.collapsed {\n  display: none;\n}\n\n.console-entry-json pre {\n  margin: 0;\n  color: #9cdcfe;\n}\n\n/* Highlight key fields in JSON */\n.json-key {\n  color: #9cdcfe;\n}\n\n.json-string {\n  color: #ce9178;\n}\n\n.json-number {\n  color: #b5cea8;\n}\n\n.json-boolean {\n  color: #569cd6;\n}\n\n.json-null {\n  color: #569cd6;\n}\n\n/* Console scrollbar */\n.console-content::-webkit-scrollbar {\n  width: 8px;\n}\n\n.console-content::-webkit-scrollbar-track {\n  background: #1e1e1e;\n}\n\n.console-content::-webkit-scrollbar-thumb {\n  background: #3e3e3e;\n  border-radius: 4px;\n}\n\n.console-content::-webkit-scrollbar-thumb:hover {\n  background: #4e4e4e;\n}\n\n/* JSON scrollbar */\n.console-entry-json::-webkit-scrollbar {\n  width: 6px;\n  height: 6px;\n}\n\n.console-entry-json::-webkit-scrollbar-track {\n  background: #1e1e1e;\n}\n\n.console-entry-json::-webkit-scrollbar-thumb {\n  background: #3e3e3e;\n  border-radius: 3px;\n}\n\n.console-entry-json::-webkit-scrollbar-thumb:hover {\n  background: #4e4e4e;\n}\n\n/* Responsive Design */\n@media (max-width: 768px) {\n  header {\n    padding: 1rem 1.5rem;\n  }\n\n  h1 {\n    font-size: 1.25rem;\n  }\n\n  .connection-status {\n    position: static;\n    margin-top: 0.5rem;\n  }\n\n  /* Stack console panel below chat on mobile */\n  .main-layout {\n    flex-direction: column;\n  }\n\n  .console-panel {\n    max-height: 300px;\n    border-top: 1px solid var(--border-color);\n  }\n\n  .container {\n    border-right: none;\n  }\n\n  #messages {\n    padding: 1rem;\n  }\n\n  .bubble {\n    max-width: 85%;\n  }\n\n  .input-container {\n    padding: 1rem;\n  }\n\n  #messageForm {\n    flex-direction: column;\n    gap: 0.75rem;\n  }\n\n  .input-wrapper {\n    width: 100%;\n    flex-direction: column;\n  }\n\n  button {\n    width: 100%;\n  }\n}\n\n/* Loading state */\n.loading {\n  display: inline-block;\n  width: 20px;\n  height: 20px;\n  border: 3px solid rgba(255, 255, 255, 0.3);\n  border-radius: 50%;\n  border-top-color: white;\n  animation: spin 0.8s linear infinite;\n}\n\n@keyframes spin {\n  to {\n    transform: rotate(360deg);\n  }\n}\n\n/* Camera Preview Modal */\n.modal {\n  display: none;\n  position: fixed;\n  z-index: 1000;\n  left: 0;\n  top: 0;\n  width: 100%;\n  height: 100%;\n  background-color: rgba(0, 0, 0, 0.7);\n  backdrop-filter: blur(4px);\n}\n\n.modal.show {\n  display: flex;\n  align-items: center;\n  justify-content: center;\n}\n\n.modal-content {\n  background-color: white;\n  border-radius: 1rem;\n  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);\n  max-width: 90%;\n  max-height: 90%;\n  width: 640px;\n  display: flex;\n  flex-direction: column;\n  animation: modalSlideIn 0.3s ease-out;\n}\n\n@keyframes modalSlideIn {\n  from {\n    opacity: 0;\n    transform: translateY(-20px);\n  }\n  to {\n    opacity: 1;\n    transform: translateY(0);\n  }\n}\n\n.modal-header {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  padding: 1.5rem;\n  border-bottom: 1px solid var(--border-color);\n}\n\n.modal-header h3 {\n  margin: 0;\n  font-size: 1.25rem;\n  font-weight: 600;\n  color: #202124;\n}\n\n.close-btn {\n  background: none;\n  border: none;\n  font-size: 2rem;\n  line-height: 1;\n  color: #5f6368;\n  cursor: pointer;\n  padding: 0;\n  width: 32px;\n  height: 32px;\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  border-radius: 50%;\n  transition: all 0.2s ease;\n}\n\n.close-btn:hover {\n  background-color: #f1f3f4;\n  color: #202124;\n}\n\n.modal-body {\n  padding: 1.5rem;\n  flex: 1;\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  background-color: #000;\n  border-radius: 0 0 1rem 1rem;\n}\n\n#cameraPreview {\n  width: 100%;\n  max-height: 480px;\n  border-radius: 0.5rem;\n  object-fit: contain;\n}\n\n.modal-footer {\n  padding: 1.5rem;\n  border-top: 1px solid var(--border-color);\n  display: flex;\n  gap: 1rem;\n  justify-content: flex-end;\n  background-color: white;\n  border-radius: 0 0 1rem 1rem;\n}\n\n.btn-primary {\n  background-color: var(--primary-color);\n  color: white;\n  padding: 0.875rem 1.5rem;\n  border: none;\n  border-radius: 1.5rem;\n  font-size: 0.9375rem;\n  font-weight: 500;\n  cursor: pointer;\n  transition: all 0.2s ease;\n  font-family: inherit;\n}\n\n.btn-primary:hover {\n  background-color: #3367d6;\n  box-shadow: var(--shadow);\n  transform: translateY(-1px);\n}\n\n.btn-secondary {\n  background-color: white;\n  color: #5f6368;\n  padding: 0.875rem 1.5rem;\n  border: 1px solid var(--border-color);\n  border-radius: 1.5rem;\n  font-size: 0.9375rem;\n  font-weight: 500;\n  cursor: pointer;\n  transition: all 0.2s ease;\n  font-family: inherit;\n}\n\n.btn-secondary:hover {\n  background-color: #f8f9fa;\n  border-color: #bdc1c6;\n}'

_RECALL_CSS = ':root {\n  --bg: #f1f3ee;\n  --ink: #1e2220;\n  --accent: #0d8b75;\n  --accent-2: #184c5f;\n  --panel: #ffffff;\n  --border: #d7ddd9;\n}\n\n* {\n  box-sizing: border-box;\n}\n\nbody {\n  margin: 0;\n  min-height: 100vh;\n  font-family: "Avenir Next", "Gill Sans", "Trebuchet MS", sans-serif;\n  color: var(--ink);\n  background:\n    radial-gradient(circle at 20% 10%, rgba(13, 139, 117, 0.12), transparent 32%),\n    radial-gradient(circle at 85% 15%, rgba(24, 76, 95, 0.16), transparent 28%),\n    linear-gradient(180deg, #eef4f2 0%, var(--bg) 70%);\n}\n\n.app-shell {\n  width: min(980px, 100% - 2rem);\n  margin: 1rem auto;\n  display: grid;\n  gap: 1rem;\n}\n\n.conversation-only-shell {\n  min-height: calc(100vh - 2rem);\n}\n\n.panel {\n  background: var(--panel);\n  border: 1px solid var(--border);\n  border-radius: 14px;\n  padding: 1rem;\n  box-shadow: 0 8px 20px rgba(16, 33, 29, 0.05);\n}\n\n.controls-panel {\n  display: grid;\n  gap: 1rem;\n}\n\n.conversation-panel {\n  min-height: calc(100vh - 2rem);\n  display: flex;\n  flex-direction: column;\n  padding: 0.75rem;\n}\n\n.debug-only[hidden] {\n  display: none !important;\n}\n\n.panel h2 {\n  margin-top: 0;\n  font-size: 1rem;\n}\n\n.section-header {\n  display: grid;\n  gap: 0.25rem;\n  margin-bottom: 0.4rem;\n}\n\n.section-copy {\n  margin: 0;\n  color: #50615c;\n  line-height: 1.4;\n}\n\n.controls-grid {\n  display: grid;\n  gap: 0.8rem;\n  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));\n}\n\n.controls label {\n  display: block;\n  font-size: 0.9rem;\n  margin-bottom: 0.35rem;\n}\n\nlabel {\n  display: grid;\n  gap: 0.35rem;\n  font-size: 0.9rem;\n}\n\ninput[type="text"] {\n  width: 100%;\n  border-radius: 10px;\n  border: 1px solid #b9c8c2;\n  font-size: 0.95rem;\n  padding: 0.6rem 0.7rem;\n  background: #fbfdfc;\n}\n\nselect {\n  width: 100%;\n  border-radius: 10px;\n  border: 1px solid #b9c8c2;\n  font-size: 0.95rem;\n  padding: 0.6rem 0.7rem;\n  background: #fbfdfc;\n}\n\n.row {\n  display: flex;\n  gap: 0.7rem;\n  flex-wrap: wrap;\n}\n\n.toggle-row {\n  align-items: center;\n}\n\n.checkbox-row {\n  display: inline-flex;\n  align-items: center;\n  gap: 0.45rem;\n}\n\n.action-row {\n  align-items: center;\n}\n\nbutton {\n  border: none;\n  border-radius: 10px;\n  padding: 0.55rem 0.8rem;\n  color: #ffffff;\n  background: linear-gradient(140deg, var(--accent), var(--accent-2));\n  font-size: 0.92rem;\n  cursor: pointer;\n}\n\n.secondary-button {\n  color: var(--ink);\n  background: #e5ece8;\n}\n\nbutton:disabled {\n  opacity: 0.6;\n  cursor: not-allowed;\n}\n\n.status-grid {\n  margin-top: 0.85rem;\n  display: grid;\n  gap: 0.45rem;\n  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));\n}\n\n.status-grid div {\n  border: 1px dashed #d2ddd8;\n  border-radius: 10px;\n  padding: 0.4rem 0.55rem;\n  display: flex;\n  flex-direction: column;\n  gap: 0.2rem;\n}\n\n.status-label {\n  font-size: 0.78rem;\n  color: #50615c;\n  text-transform: uppercase;\n  letter-spacing: 0.04em;\n}\n\n.text-form {\n  display: grid;\n  gap: 0.7rem;\n  grid-template-columns: minmax(0, 1fr) auto;\n  align-items: end;\n}\n\n.feed {\n  max-height: 260px;\n  overflow-y: auto;\n  display: flex;\n  flex-direction: column;\n  gap: 0.55rem;\n}\n\n.conversation-panel .feed {\n  max-height: none;\n  flex: 1;\n}\n\n.event {\n  border: 1px solid #d6e1dd;\n  background: #f8fbf9;\n  border-radius: 10px;\n  padding: 0.55rem;\n  animation: fade-in 180ms ease-out;\n}\n\n.event p {\n  margin: 0.15rem 0;\n}\n\n.meta {\n  font-size: 0.78rem;\n  color: #4c5a55;\n}\n\n@keyframes fade-in {\n  from {\n    opacity: 0;\n    transform: translateY(4px);\n  }\n  to {\n    opacity: 1;\n    transform: translateY(0);\n  }\n}\n\n@media (max-width: 640px) {\n  .app-shell {\n    width: min(980px, 100% - 1rem);\n    margin: 0.5rem auto;\n  }\n\n  .text-form {\n    grid-template-columns: 1fr;\n  }\n\n  .action-row button {\n    width: 100%;\n  }\n}'

router = APIRouter()

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def _frontend_head(*, title: str, css: str, script_href: str) -> Head:
    return Head(
        Title(title),
        Meta(charset="UTF-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        Link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/daisyui@5",
            type="text/css",
        ),
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style(NotStr(css)),
        Script(src=script_href, type="module"),
    )


def _main_page() -> Html:
    return Html(
        _frontend_head(
            title="ADK Bidi-streaming Demo",
            css=_STYLE_CSS,
            script_href="/assets/js/app.js",
        ),
        Body(
            Header(
                H1("ADK Bidi-streaming Demo"),
                Div("Real-time bidirectional streaming with Google ADK", cls="subtitle"),
                Div(
                    Label(
                        Input(
                            type="checkbox",
                            id="enableProactivity",
                            cls="checkbox checkbox-sm border-white/40 bg-white/10",
                        ),
                        Span("Proactivity", cls="label-text text-white"),
                        cls="header-checkbox label cursor-pointer justify-start gap-2",
                        title=(
                            "Enable model to proactively respond without explicit prompts "
                            "(Native audio models only)"
                        ),
                    ),
                    Label(
                        Input(
                            type="checkbox",
                            id="enableAffectiveDialog",
                            cls="checkbox checkbox-sm border-white/40 bg-white/10",
                        ),
                        Span("Affective Dialog", cls="label-text text-white"),
                        cls="header-checkbox label cursor-pointer justify-start gap-2",
                        title=(
                            "Enable model to detect and adapt to emotional cues "
                            "(Native audio models only)"
                        ),
                    ),
                    cls="header-options",
                ),
                Div(
                    Span(id="statusIndicator", cls="status-indicator"),
                    Span(
                        "Connecting...",
                        id="statusText",
                        cls="badge badge-outline border-white/40 text-white",
                    ),
                    cls="connection-status",
                ),
                cls="border-b border-white/20",
            ),
            Div(
                Div(
                    Div(id="messages", cls="bg-base-100/60"),
                    Div(
                        Form(
                            Div(
                                Input(
                                    type="text",
                                    id="message",
                                    name="message",
                                    placeholder="Type your message here...",
                                    autocomplete="off",
                                    cls="input input-bordered w-full rounded-full border-base-300 bg-base-100",
                                ),
                                Button("Send", type="submit", id="sendButton", cls="btn btn-primary", disabled=True),
                                Button("Start Audio", type="button", id="startAudioButton", cls="btn btn-success"),
                                Button("📷 Camera", type="button", id="cameraButton", cls="btn btn-error"),
                                cls="input-wrapper",
                            ),
                            id="messageForm",
                        ),
                        cls="input-container border-base-300 bg-base-100/90",
                    ),
                    cls="container bg-base-100/80 backdrop-blur-sm",
                ),
                Div(
                    Div(
                        H2("Event Console"),
                        Div(
                            Label(
                                Input(type="checkbox", id="showAudioEvents", cls="checkbox checkbox-xs"),
                                Span("Show audio", cls="label-text text-inherit"),
                                cls="console-checkbox label cursor-pointer gap-2",
                            ),
                            Button("Clear", id="clearConsole", cls="console-clear-btn btn btn-xs btn-ghost"),
                            cls="console-controls",
                        ),
                        cls="console-header",
                    ),
                    Div(id="consoleContent", cls="console-content"),
                    cls="console-panel border-l border-base-300",
                ),
                cls="main-layout",
            ),
            Div(
                Div(
                    Div(
                        H3("Camera Preview"),
                        Button("×", id="closeCameraModal", cls="close-btn btn btn-circle btn-ghost btn-sm"),
                        cls="modal-header card-body pb-4",
                    ),
                    Div(Video(id="cameraPreview", autoplay=True, playsinline=True), cls="modal-body"),
                    Div(
                        Button("Cancel", id="cancelCamera", cls="btn-secondary btn btn-ghost"),
                        Button("📷 Send Image", id="captureImage", cls="btn-primary btn btn-primary"),
                        cls="modal-footer",
                    ),
                    cls="modal-content card bg-base-100 shadow-2xl",
                ),
                id="cameraModal",
                cls="modal",
            ),
            data_theme="corporate",
            cls="min-h-screen bg-base-200 text-base-content",
        ),
    )


def _recall_page() -> Html:
    return Html(
        _frontend_head(
            title="Gemini Live Runtime",
            css=_RECALL_CSS,
            script_href="/assets/js/recall.js?v=20260308",
        ),
        Body(
            Main(
                Section(
                    Div(
                        H2("Debug Controls"),
                        P(
                            "Local-only controls for testing the same conversational runtime.",
                            cls="section-copy",
                        ),
                        cls="section-header",
                    ),
                    Div(
                        Label(
                            "WebSocket URL",
                            Input(type="text", id="wsUrl", spellcheck="false", cls="input input-bordered w-full"),
                            cls="form-control",
                        ),
                        Label(
                            "User ID",
                            Input(type="text", id="userId", spellcheck="false", cls="input input-bordered w-full"),
                            cls="form-control",
                        ),
                        Label(
                            "Session ID",
                            Input(type="text", id="sessionId", spellcheck="false", cls="input input-bordered w-full"),
                            cls="form-control",
                        ),
                        Label(
                            "Input source",
                            Select(
                                Option("None", value="none"),
                                Option("Microphone", value="microphone"),
                                id="inputSource",
                                cls="select select-bordered w-full",
                            ),
                            cls="form-control",
                        ),
                        cls="controls-grid",
                    ),
                    Div(
                        Label(
                            Input(type="checkbox", id="autoReconnect", checked=True, cls="checkbox checkbox-sm"),
                            Span("Auto reconnect", cls="label-text"),
                            cls="checkbox-row label cursor-pointer justify-start gap-2",
                        ),
                        Label(
                            Input(type="checkbox", id="autoEnableAudio", checked=True, cls="checkbox checkbox-sm"),
                            Span("Enable audio output on connect", cls="label-text"),
                            cls="checkbox-row label cursor-pointer justify-start gap-2",
                        ),
                        cls="row toggle-row",
                    ),
                    Div(
                        Button("Connect", type="button", id="connectButton", cls="btn btn-primary"),
                        Button("Disconnect", type="button", id="disconnectButton", cls="btn btn-neutral", disabled=True),
                        Button("Start Input", type="button", id="startInputButton", cls="btn btn-success", disabled=True),
                        Button("Stop Input", type="button", id="stopInputButton", cls="btn btn-warning", disabled=True),
                        Button("Enable Audio Output", type="button", id="enableAudioButton", cls="btn btn-accent"),
                        Button("Clear Feed", type="button", id="resetFeedButton", cls="secondary-button btn btn-ghost"),
                        cls="row action-row",
                    ),
                    Div(
                        Div(Span("Connection", cls="status-label"), Strong("idle", id="connectionState"), cls="rounded-box border border-base-300 bg-base-100/70"),
                        Div(Span("Input", cls="status-label"), Strong("none", id="inputState"), cls="rounded-box border border-base-300 bg-base-100/70"),
                        Div(Span("Audio Output", cls="status-label"), Strong("disabled", id="audioOutputState"), cls="rounded-box border border-base-300 bg-base-100/70"),
                        Div(Span("Session", cls="status-label"), Strong("unassigned", id="sessionState"), cls="rounded-box border border-base-300 bg-base-100/70"),
                        Div(Span("Last Event", cls="status-label"), Strong("waiting", id="lastEventState"), cls="rounded-box border border-base-300 bg-base-100/70"),
                        cls="status-grid",
                    ),
                    Form(
                        Label(
                            "Send text",
                            Input(
                                type="text",
                                id="textPrompt",
                                placeholder="Ask the agent something without using audio",
                                autocomplete="off",
                                cls="input input-bordered w-full",
                            ),
                            cls="form-control",
                        ),
                        Button("Send", type="submit", id="sendTextButton", cls="btn btn-primary", disabled=True),
                        id="textForm",
                        cls="text-form",
                    ),
                    cls="panel controls-panel debug-only card bg-base-100 shadow-xl",
                    hidden=True,
                ),
                Section(
                    Div(
                        H2("Agent Feed"),
                        P(
                            "Streamed model events, transcriptions, and runtime diagnostics appear here.",
                            cls="section-copy",
                        ),
                        cls="section-header debug-only",
                        hidden=True,
                    ),
                    Div(id="agentFeed", cls="feed"),
                    cls="panel conversation-panel card bg-base-100/95 shadow-xl",
                ),
                cls="app-shell conversation-only-shell",
            ),
            data_theme="emerald",
            cls="min-h-screen bg-base-200 text-base-content",
        ),
    )


@router.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the main demo page as FastHTML."""

    return HTMLResponse(to_xml(_main_page()))


@router.get("/recall", response_class=HTMLResponse)
async def recall_root() -> HTMLResponse:
    """Serve the Recall runtime page as FastHTML."""

    return HTMLResponse(to_xml(_recall_page()))


@router.get("/assets/{asset_path:path}")
async def frontend_asset(asset_path: str) -> FileResponse:
    """Serve browser assets from the app-owned asset directory."""

    asset_file = (ASSETS_DIR / asset_path).resolve()
    if not asset_file.is_file() or ASSETS_DIR.resolve() not in asset_file.parents:
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(asset_file)
