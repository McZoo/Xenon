from graia.application import GroupMessage, Group, Member, MessageChain
from graia.application.message.elements.internal import Plain, At

import lib

import asyncio

plugin_spec = lib.plugin.XenonPluginSpec(
    lib.Version(0, 0, 1),
    "management"
)


def main(ctx: lib.XenonContext):
    @ctx.bcc.receiver(GroupMessage)
    async def stopper(group: Group, member: Member, msg: MessageChain):
        if msg.asDisplay() == '.stop' and await lib.permission.get_perm(member) >= lib.permission.OPERATOR:
            await ctx.app.sendGroupMessage(group=group, message=MessageChain.create(
                [At(member.id), Plain("\n"),
                 Plain("Shutting down service......")]))
            await ctx.app.sendGroupMessage(group=group, message=MessageChain.create(
                [Plain("Xenon service stopped.")]))
            await ctx.app.shutdown()

    @ctx.con.register(True)
    async def stopper(command: str):
        ctx.logger.info("Stopping...")
        if command == '.stop':
            asyncio.run_coroutine_threadsafe(ctx.app.shutdown(), ctx.loop)
            ctx.con.stop()
