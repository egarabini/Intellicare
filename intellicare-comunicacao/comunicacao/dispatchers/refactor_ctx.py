import os
import re

dispatchers_dir = r"c:\Users\egara\INTELLICARE\intellicare-comunicacao\comunicacao\dispatchers"

replacements = [
    (r"def send\(self, message: ChannelMessage\) ->", r"def send(self, message: ChannelMessage, ctx: Any = None) ->"),
    (r"def get_status\(self, channel_message_id: str\) ->", r"def get_status(self, channel_message_id: str, ctx: Any = None) ->"),
    (r"def cancel\(self, channel_message_id: str\) ->", r"def cancel(self, channel_message_id: str, ctx: Any = None) ->"),
    (r"def health_check\(self\) ->", r"def health_check(self, ctx: Any = None) ->"),
    (r"def test_send\(self, recipient: ResolvedRecipient\) ->", r"def test_send(self, recipient: ResolvedRecipient, ctx: Any = None) ->"),
    (r"def get_capabilities\(self\) ->", r"def get_capabilities(self, ctx: Any = None) ->"),
    (r"def validate_recipient\(self, recipient: ResolvedRecipient\) ->", r"def validate_recipient(self, recipient: ResolvedRecipient, ctx: Any = None) ->"),
    (r"import logging", "import logging\nfrom typing import Any"), # Ensure typing Any is imported
]

for fname in os.listdir(dispatchers_dir):
    if fname.endswith(".py") and fname != "refactor_ctx.py":
        filepath = os.path.join(dispatchers_dir, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        changed = False
        for old_p, new_p in replacements:
            if re.search(old_p, content):
                content = re.sub(old_p, new_p, content)
                changed = True

        # Special fixes for DispatcherManager
        if fname == "base.py":
            # Add ctx param to DispatcherManager methods
            mgr_methods = [
                (r"def dispatch\(self, channel: str, message: ChannelMessage\) ->", r"def dispatch(self, channel: str, message: ChannelMessage, ctx: Any = None) ->"),
                (r"def get_status\(self, channel: str, channel_message_id: str\) ->", r"def get_status(self, channel: str, channel_message_id: str, ctx: Any = None) ->"),
                (r"def cancel\(self, channel: str, channel_message_id: str\) ->", r"def cancel(self, channel: str, channel_message_id: str, ctx: Any = None) ->"),
                (r"def health_check\(self, channel: str\) ->", r"def health_check(self, channel: str, ctx: Any = None) ->"),
                (r"def get_health\(self, channel: str\) ->", r"def get_health(self, channel: str, ctx: Any = None) ->"),
                (r"def test_send\(self, channel: str, recipient: ResolvedRecipient\) ->", r"def test_send(self, channel: str, recipient: ResolvedRecipient, ctx: Any = None) ->"),
                (r"def get_capabilities\(self, channel: str\) ->", r"def get_capabilities(self, channel: str, ctx: Any = None) ->"),
                (r"def validate_recipient\(self, channel: str, recipient: ResolvedRecipient\) ->", r"def validate_recipient(self, channel: str, recipient: ResolvedRecipient, ctx: Any = None) ->"),
            ]
            for om, nm in mgr_methods:
                if re.search(om, content):
                    content = re.sub(om, nm, content)
                    changed = True
            
            # Now we must update the calls to the dispatchers to pass ctx=ctx if it was added
            call_replacements = [
                (r"await dispatcher\.send\(message\)", r"await dispatcher.send(message, ctx=ctx)"),
                (r"await dispatcher\.get_status\(channel_message_id\)", r"await dispatcher.get_status(channel_message_id, ctx=ctx)"),
                (r"await dispatcher\.cancel\(channel_message_id\)", r"await dispatcher.cancel(channel_message_id, ctx=ctx)"),
                (r"await dispatcher\.health_check\(\)", r"await dispatcher.health_check(ctx=ctx)"),
                (r"await dispatcher\.get_health\(\)", r"await dispatcher.get_health(ctx=ctx)"),
                (r"await dispatcher\.test_send\(recipient\)", r"await dispatcher.test_send(recipient, ctx=ctx)"),
                (r"await dispatcher\.is_available\(\)", r"await dispatcher.is_available()"), # is_available doesnt take ctx normally according to spec, maybe skip
                (r"dispatcher\.get_capabilities\(\)", r"dispatcher.get_capabilities(ctx=ctx)"),
                (r"await dispatcher\.supports_read_receipt\(\)", r"await dispatcher.supports_read_receipt()"),
                (r"await dispatcher\.supports_rich_content\(\)", r"await dispatcher.supports_rich_content()"),
                (r"dispatcher\.validate_recipient\(recipient\)", r"dispatcher.validate_recipient(recipient, ctx=ctx)")
            ]
            for oc, nc in call_replacements:
                content = content.replace(oc, nc)
        
        # Finally save
        if changed:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated {fname}")

