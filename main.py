from astrbot.api.all import *
from astrbot.api.event.filter import command 
from astrbot.api.message_components import Plain

# 依然保留这个类，解决 'list' has no attribute 'chain' 报错
class CompatibleMessageChain:
    def __init__(self, components):
        self.chain = components if isinstance(components, list) else [components]

@register("contact_owner_pro", "Care", "联系主人Pro：纯净版", "2.7.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 1. 你的 ID
        self.owner_id = "3524815759"
        # 2. 尝试使用纯数字 ID，避开 session_id 格式校验报错
        self.owner_session = self.owner_id 
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_content = event.message_str.strip()
        if not msg_content:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 存下 event 以备回复使用
        self.reply_map[sender_id] = event

        forward_text = (
            f"📩 【收到留言】\n"
            f"👤 来自：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_content}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 使用包装盒发送纯文字，不加 At
            chain = CompatibleMessageChain([Plain(forward_text)])
            await self.context.send_message(self.owner_session, chain)
            yield event.plain_result("✅ 消息已转发。")
        except Exception as e:
            # 如果报错，直接尝试发送最原始的字符串
            try:
                await self.context.send_message(self.owner_session, forward_text)
                yield event.plain_result("✅ 消息已转发(文本模式)。")
            except:
                yield event.plain_result(f"⚠️ 转发异常：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        # 只有你能用这个指令
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_text = parts[0], parts[1]
        target_event = self.reply_map.get(target_id)

        # 构造纯文字消息（删掉了 At）
        reply_msg = f"收到主人的回信：\n\n{reply_text}"
        chain = CompatibleMessageChain([Plain(reply_msg)])

        try:
            if target_event:
                # 优先顺着 event 回去，解决“缺少有效 session_id”报错
                await self.context.send_message(target_event, chain)
            else:
                # 保底：用 QQ 号当 session_id 发送
                await self.context.send_message(target_id, chain)
            yield event.plain_result(f"🚀 已回复给 {target_id}")
        except Exception as e:
            try:
                # 最后的倔强：纯字符串尝试
                await self.context.send_message(target_id, reply_msg)
                yield event.plain_result(f"🚀 已回复(文本模式)")
            except:
                yield event.plain_result(f"❌ 投递失败：{str(e)}")
