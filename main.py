from astrbot.api.all import *

# 1. 升级消息包装盒：支持传入文字和需要 @ 的 QQ 号
class SimpleChain:
    def __init__(self, text, at_qq=None):
        from astrbot.api.message_components import Plain, At
        self.chain = []
        if at_qq:
            # 如果提供了 QQ 号，则在开头添加 At 组件
            self.chain.append(At(qq=at_qq))
            # 添加一个空格让消息更好看
            self.chain.append(Plain(" "))
        self.chain.append(Plain(text))

@register("contact_owner_pro", "Care", "联系主人：自动艾特版", "3.5.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 你的 QQ 号
        self.owner_id = "3524815759"
        # 严格的三段式 ID 格式
        self.owner_session = f"llbot:FriendMessage:{self.owner_id}"
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 存下 event 对象
        self.reply_map[sender_id] = event

        forward_text = (
            f"📩 【收到留言】\n"
            f"👤 来自：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 转发给主人时不需要艾特
            await self.context.send_message(self.owner_session, SimpleChain(forward_text))
            yield event.plain_result("✅ 消息已转发给主人。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_content = parts[0], parts[1]
        target_event = self.reply_map.get(target_id)

        try:
            # 【核心修改】：在这里传入 target_id，实现自动 @
            msg_box = SimpleChain(f"收到主人的回信：\n\n{reply_content}", at_qq=target_id)
            
            if target_event:
                # 记录存在时原路回传
                await self.context.send_message(target_event, msg_box)
                yield event.plain_result(f"🚀 已成功回复并艾特 {target_id}")
            else:
                # 记录不存在时尝试强制投递
                forced_target = f"llbot:FriendMessage:{target_id}"
                await self.context.send_message(forced_target, msg_box)
                yield event.plain_result(f"⚠️ 记录已丢失，已尝试强制艾特投递至 {target_id}")
        except Exception as e:
            yield event.plain_result(f"❌ 投递失败：{str(e)}")
