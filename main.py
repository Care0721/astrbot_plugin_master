from astrbot.api.all import *

@register("dual_chat", "Care", "双向联系：底层直连修复版", "20.0.0")
class DualChatPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"
        # 记录用户的消息事件，用于回复
        self.user_events = {} 

    @command("联系主人")
    async def to_owner(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        if not msg: return
        
        s_id = str(event.get_sender_id())
        self.user_events[s_id] = event # 存下 event 对象
        
        forward_text = f"📩 新留言\n来自：{event.get_sender_name()}({s_id})\n内容：{msg}\n\n回复指令：/回复 {s_id} 内容"
        
        try:
            # 转发给你，直接发 QQ 号，框架会自动处理
            await self.context.send_message(self.owner_id, [Plain(forward_text)])
            yield event.plain_result("✅ 消息已发给主人。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败: {str(e)}")

    @command("回复")
    async def to_user(self, event: AstrMessageEvent):
        if str(event.get_sender_id()) != self.owner_id: return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_qq = parts[0].strip()
        content = parts[1].strip()

        # 尝试从记录里找之前的 event
        target_event = self.user_events.get(target_qq)
        
        try:
            from astrbot.api.message_components import At, Plain
            # 构造消息：艾特 + 内容
            msg_chain = [At(qq=target_qq), Plain(f" 收到主人回信：\n{content}")]

            if target_event:
                # 方案 A：如果有记录，直接用之前的 event 发回去，绝对不会报 session 错
                await self.context.send_message(target_event, msg_chain)
                yield event.plain_result(f"🚀 已回复给 {target_qq}")
            else:
                # 方案 B：如果没有记录（重启后），尝试直接投递数字 ID
                # 避开 "llbot:FriendMessage" 这种导致 unpack 报错的格式
                await self.context.send_message(target_qq, msg_chain)
                yield event.plain_result(f"🚀 (直连投递) 已发给 {target_qq}")
                
        except Exception as e:
            # 最后的保底：尝试用最原始的 send_message 字符串模式
            try:
                await self.context.send_message(target_qq, [Plain(f"主人回复：{content}")])
                yield event.plain_result("🚀 成功通过保底通道发送。")
            except Exception as e2:
                yield event.plain_result(f"❌ 彻底失败: {str(e2)}")
