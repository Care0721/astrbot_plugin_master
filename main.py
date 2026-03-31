from astrbot.api.all import *

# 包装盒，解决 'str' object has no attribute 'chain' 报错
class SimpleChain:
    def __init__(self, text, at_qq=None):
        from astrbot.api.message_components import Plain, At
        self.chain = []
        if at_qq:
            self.chain.append(At(qq=at_qq)) # 注入艾特组件
            self.chain.append(Plain(" "))
        self.chain.append(Plain(text))

@register("contact_owner_pro", "Care", "联系主人：精准艾特版", "4.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        self.reply_map[sender_id] = event # 记录完整的 event 供后续艾特

        forward_text = (
            f"📩 【新留言】\n"
            f"👤 来自：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 转发给主人（由于你之前三段式地址报错，这里尝试动态获取你的平台信息）
            target = f"{event.message_event.platform}:FriendMessage:{self.owner_id}"
            await self.context.send_message(target, SimpleChain(forward_text))
            yield event.plain_result("✅ 已转发。")
        except:
            yield event.plain_result("⚠️ 转发失败，但记录已保存。")

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
            msg_box = SimpleChain(f"主人回信：\n{reply_content}", at_qq=target_id)
            
            if target_event:
                # 【精准艾特核心】：直接使用之前记录的 event 对象
                # 框架会自动识别该用户是在群聊还是私聊，并完成艾特
                await self.context.send_message(target_event, msg_box)
                yield event.plain_result(f"🚀 已在原频道回复并艾特 {target_id}")
            else:
                # 如果记录丢失，尝试根据当前指令的平台构造一个通用的 Session
                from astrbot.api.provider import Session
                platform = event.message_event.platform
                # 尝试猜测消息类型：如果是私聊指令则发私聊，否则发群聊
                forced_session = Session(
                    platform=platform,
                    message_type=event.message_event.message_type,
                    session_id=target_id
                )
                await self.context.send_message(forced_session, msg_box)
                yield event.plain_result(f"🚀 记录失踪，已尝试强制艾特投递至 {target_id}")
                
        except Exception as e:
            yield event.plain_result(f"❌ 投递失败：{str(e)}")
