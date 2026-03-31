from astrbot.api.all import *
from astrbot.api.event.filter import command 
from astrbot.api.message_components import Plain, At

# --- 依然保留这个“包装盒”，解决属性丢失问题 ---
class CompatibleMessageChain:
    def __init__(self, components):
        # 解决 'list' object has no attribute 'chain' 报错
        self.chain = components if isinstance(components, list) else [components]

@register("contact_owner_pro", "Care", "联系主人Pro：回归经典版", "2.5.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 主人QQ
        self.owner_id = "3524815759"
        # 这里的地址如果还是报错，我们会通过 event 动态获取
        self.owner_session = f"llbot:FriendMessage:{self.owner_id}"
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_content = event.message_str.strip()
        if not msg_content:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 存下整个 event，这是解决“缺少session_id”报错的关键
        self.reply_map[sender_id] = event

        forward_text = (
            f"📩 【收到留言】\n"
            f"👤 来自：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_content}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 转发给主人
            chain = CompatibleMessageChain([Plain(forward_text)])
            await self.context.send_message(self.owner_session, chain)
            yield event.plain_result("✅ 消息已转发。")
        except Exception as e:
            yield event.plain_result(f"⚠️ 转发异常：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_text = parts[0], parts[1]
        target_event = self.reply_map.get(target_id)

        try:
            msg_list = [At(qq=target_id), Plain(f" 收到回复：\n{reply_text}")]
            chain = CompatibleMessageChain(msg_list)
            
            if target_event:
                # 【核心修复】：如果能找到之前的 event，直接回传给它
                # 这样框架就不会报“缺少有效 session_id”了
                await self.context.send_message(target_event, chain)
            else:
                # 保底方案：手动拼 Session
                await self.context.send_message(f"llbot:FriendMessage:{target_id}", chain)
                
            yield event.plain_result(f"🚀 已投递给 {target_id}")
        except Exception as e:
            yield event.plain_result(f"❌ 投递失败：{str(e)}")
