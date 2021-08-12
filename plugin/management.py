from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, At

import lib
from lib.command import CommandEvent

plugin_spec = lib.plugin.XenonPluginSpec(
    lib.Version(0, 0, 1),
    "management"
)


def main(ctx: lib.XenonContext):
    @ctx.bcc.receiver(CommandEvent)
    async def stopper(event: CommandEvent):
        if event.command == '.stop' and event.perm_lv >= lib.permission.OPERATOR:
            ctx.logger.info("Stopping...")
            if event.group:
                await ctx.app.sendGroupMessage(group=event.group, message=MessageChain.create(
                    [At(event.user), Plain("\n"),
                     Plain("Xenon service stopped.")]))
            elif event.user:
                await ctx.app.sendFriendMessage(event.user, MessageChain.create(
                    [Plain("Xenon service stopped.")]
                ))
            await ctx.app.shutdown()
