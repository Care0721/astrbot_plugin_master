from astrbot.api.all import *
from astrbot.api.event.filter import command 
from astrbot.api.message_components import Plain, At

# --- 手动定义兼容层，解决找不到 MessageChain 的问题 ---
class CompatibleMessageChain:
    def __init__(self, components):
        # 核心修复：直接赋予它框架死活要找的 'chain' 属性
        self.chain = components if isinstance(components, list) else [components]

@register("contact_owner_pro", "Care", "联系主人Pro：终极兼容版", "2.3.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"
        self.owner_session = f"llbot:FriendMessage:{self.owner_id}"
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        message_content = event.message_str.strip()
        if not message_content:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        sender_name = event.get_sender_name()
        self.reply_map[sender_id] = event.session_id

        forward_text = (
            f"📩 【收到留言】\n"
            f"👤 发送者：{sender_name}\n"
            f"🆔 QQ号：{sender_id}\n"
            f"📍 来源：{event.session_id}\n"
            f"📝 内容：{message_content}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 使用包装盒发送：包装 Plain 组件
            await self.context.send_message(self.owner_session, CompatibleMessageChain([Plain(forward_text)]))
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
        target_session = self.reply_map.get(target_id) or f"llbot:FriendMessage:{target_id}"

        try:
            # 同样使用包装盒，把 At 和 Plain 塞进去
            msg_list = [At(qq=target_id), Plain(f" 收到主人的回信：\n\n{reply_content}")]
            await self.context.send_message(target_session, CompatibleMessageChain(msg_list))
            yield event.plain_result(f"🚀 已回复给 {target_id}")
        except Exception as e:
            yield event.plain_result(f"❌ 投递失败：{str(e)}")
